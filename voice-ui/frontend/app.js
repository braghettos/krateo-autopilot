/**
 * Krateo Autopilot Voice UI
 *
 * Connects to Gemini Multimodal Live API via WebSocket for native
 * audio input/output. Uses function calling to bridge voice requests
 * to the Krateo Autopilot A2A endpoint.
 */

const GEMINI_WS_BASE = "wss://generativelanguage.googleapis.com/ws/google.ai.generativelanguage.v1beta.GenerativeService.BidiGenerateContent";
const INPUT_SAMPLE_RATE = 16000;
const OUTPUT_SAMPLE_RATE = 24000;
const CHUNK_SIZE = 4096;

let ws = null;
let mediaStream = null;
let audioContext = null;
let scriptProcessor = null;
let playbackContext = null;
// playback uses gapless scheduling via AudioContext.currentTime
let isListening = false;
let sessionId = self.crypto?.randomUUID?.() || (Math.random().toString(36).slice(2) + Date.now().toString(36));

const micBtn = document.getElementById("mic-btn");
const statusEl = document.getElementById("status");
const hintEl = document.getElementById("hint");
const transcriptLog = document.getElementById("transcript-log");
const waveformCanvas = document.getElementById("waveform");
const waveformCtx = waveformCanvas.getContext("2d");

// --- UI helpers ---

function setStatus(state, text) {
  statusEl.className = `status ${state}`;
  statusEl.textContent = text;
}

function addMessage(role, text) {
  const div = document.createElement("div");
  div.className = `msg ${role}`;
  div.textContent = text;
  transcriptLog.appendChild(div);
  transcriptLog.parentElement.scrollTop = transcriptLog.parentElement.scrollHeight;
}

function drawWaveform(data) {
  waveformCtx.fillStyle = "#161b22";
  waveformCtx.fillRect(0, 0, waveformCanvas.width, waveformCanvas.height);
  waveformCtx.strokeStyle = isListening ? "#60a5fa" : "#4ade80";
  waveformCtx.lineWidth = 2;
  waveformCtx.beginPath();
  const step = Math.ceil(data.length / waveformCanvas.width);
  const mid = waveformCanvas.height / 2;
  for (let i = 0; i < waveformCanvas.width; i++) {
    const idx = i * step;
    const val = idx < data.length ? data[idx] : 0;
    const y = mid + val * mid;
    if (i === 0) waveformCtx.moveTo(i, y);
    else waveformCtx.lineTo(i, y);
  }
  waveformCtx.stroke();
}

// --- Audio capture ---

async function startAudioCapture() {
  mediaStream = await navigator.mediaDevices.getUserMedia({
    audio: { sampleRate: INPUT_SAMPLE_RATE, channelCount: 1, echoCancellation: true },
  });

  audioContext = new AudioContext({ sampleRate: INPUT_SAMPLE_RATE });
  const source = audioContext.createMediaStreamSource(mediaStream);

  // ScriptProcessor for PCM extraction (AudioWorklet would be better but more setup)
  scriptProcessor = audioContext.createScriptProcessor(CHUNK_SIZE, 1, 1);
  scriptProcessor.onaudioprocess = (e) => {
    if (!isListening || !ws || ws.readyState !== WebSocket.OPEN) return;

    const float32 = e.inputBuffer.getChannelData(0);
    drawWaveform(float32);

    // Convert float32 [-1,1] to int16 PCM
    const int16 = new Int16Array(float32.length);
    for (let i = 0; i < float32.length; i++) {
      const s = Math.max(-1, Math.min(1, float32[i]));
      int16[i] = s < 0 ? s * 0x8000 : s * 0x7fff;
    }

    // Send as base64-encoded PCM (Gemini 3.1 format)
    const bytes = new Uint8Array(int16.buffer);
    // Encode in chunks to avoid call stack overflow on large buffers
    let b64 = "";
    for (let off = 0; off < bytes.length; off += 8192) {
      b64 += String.fromCharCode(...bytes.subarray(off, off + 8192));
    }
    b64 = btoa(b64);
    ws.send(JSON.stringify({
      realtimeInput: {
        audio: {
          mimeType: `audio/pcm;rate=${INPUT_SAMPLE_RATE}`,
          data: b64,
        },
      },
    }));
  };

  source.connect(scriptProcessor);
  scriptProcessor.connect(audioContext.destination);
}

function stopAudioCapture() {
  if (scriptProcessor) {
    scriptProcessor.disconnect();
    scriptProcessor = null;
  }
  if (audioContext) {
    audioContext.close();
    audioContext = null;
  }
  if (mediaStream) {
    mediaStream.getTracks().forEach((t) => t.stop());
    mediaStream = null;
  }
}

// --- Audio playback (gapless scheduling) ---

let nextPlayTime = 0;

function initPlayback() {
  playbackContext = new AudioContext({ sampleRate: OUTPUT_SAMPLE_RATE });
  nextPlayTime = 0;
}

function enqueueAudio(b64Data) {
  // Decode base64 to Int16 PCM
  const binary = atob(b64Data);
  const bytes = new Uint8Array(binary.length);
  for (let i = 0; i < binary.length; i++) bytes[i] = binary.charCodeAt(i);
  const int16 = new Int16Array(bytes.buffer);

  // Convert to float32
  const float32 = new Float32Array(int16.length);
  for (let i = 0; i < int16.length; i++) {
    float32[i] = int16[i] / (int16[i] < 0 ? 0x8000 : 0x7fff);
  }

  // Schedule this chunk to play immediately after the previous one
  const buffer = playbackContext.createBuffer(1, float32.length, OUTPUT_SAMPLE_RATE);
  buffer.getChannelData(0).set(float32);
  const source = playbackContext.createBufferSource();
  source.buffer = buffer;
  source.connect(playbackContext.destination);

  const now = playbackContext.currentTime;
  const startAt = Math.max(now, nextPlayTime);
  source.start(startAt);
  nextPlayTime = startAt + buffer.duration;

  drawWaveform(float32.slice(0, 300));
}

// --- A2A proxy ---

async function sendToAutopilot(message) {
  addMessage("system", "Sending to Autopilot...");
  setStatus("thinking", "Autopilot thinking...");
  try {
    const resp = await fetch("/api/autopilot", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message, session_id: sessionId }),
    });
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
    const data = await resp.json();
    return data;
  } catch (err) {
    return { text: `Error contacting autopilot: ${err.message}` };
  }
}

// --- Gemini Live WebSocket ---

async function connect() {
  setStatus("connecting", "Connecting...");
  micBtn.disabled = true;

  // Fetch API key from backend
  let apiKey;
  try {
    const cfg = await fetch("/api/config").then((r) => r.json());
    apiKey = cfg.geminiApiKey;
  } catch {
    setStatus("disconnected", "Failed to load config");
    return;
  }

  if (!apiKey) {
    setStatus("disconnected", "No API key configured");
    addMessage("system", "GEMINI_API_KEY not set on backend");
    return;
  }

  const model = "gemini-3.1-flash-live-preview";
  const url = `${GEMINI_WS_BASE}?key=${apiKey}`;

  ws = new WebSocket(url);
  ws.binaryType = "arraybuffer";

  ws.onopen = () => {
    // Send session setup
    ws.send(JSON.stringify({
      setup: {
        model: `models/${model}`,
        generationConfig: {
          responseModalities: ["AUDIO"],
          speechConfig: {
            voiceConfig: {
              prebuiltVoiceConfig: { voiceName: "Aoede" },
            },
          },
        },
        systemInstruction: {
          parts: [{
            text: `You are the voice interface for Krateo Autopilot, a Kubernetes platform operations assistant.

Your job:
- For greetings and simple questions, respond directly with your voice.
- For ANY request related to Kubernetes, infrastructure, deployments, pods, helm, blueprints, observability, alerts, troubleshooting, or platform operations — use the send_to_autopilot tool.
- After getting the tool result, summarize the key points naturally in speech. Don't read raw YAML or JSON — interpret and explain.
- Be concise and conversational. You're a voice assistant, not a text dump.
- Introduce yourself as "Krateo Autopilot" when first greeted.`,
          }],
        },
        tools: [{
          functionDeclarations: [{
            name: "send_to_autopilot",
            description: "Send a request to the Krateo Autopilot AI agent. Use this for any Kubernetes, infrastructure, platform, observability, helm, blueprint, or deployment related request.",
            parameters: {
              type: "OBJECT",
              properties: {
                message: {
                  type: "STRING",
                  description: "The user's request to send to the Krateo Autopilot agent",
                },
              },
              required: ["message"],
            },
          }],
        }],
        inputAudioTranscription: {},
        outputAudioTranscription: {},
      },
    }));
  };

  ws.onmessage = async (event) => {
    let msg;
    try {
      const text = event.data instanceof ArrayBuffer
        ? new TextDecoder().decode(event.data)
        : event.data;
      msg = JSON.parse(text);
    } catch {
      return;
    }

    // Setup complete
    if (msg.setupComplete) {
      setStatus("connected", "Connected");
      micBtn.disabled = false;
      hintEl.textContent = "Click the microphone to start";
      initPlayback();
      addMessage("system", "Connected to Gemini Live");
      return;
    }

    // Server content (audio, transcriptions, tool calls)
    const sc = msg.serverContent;
    if (sc) {
      // Model turn — audio output
      if (sc.modelTurn && sc.modelTurn.parts) {
        for (const part of sc.modelTurn.parts) {
          if (part.inlineData && part.inlineData.mimeType?.startsWith("audio/")) {
            enqueueAudio(part.inlineData.data);
          }
        }
      }

      // Input transcription (what the user said)
      if (sc.inputTranscription && sc.inputTranscription.text) {
        addMessage("user", sc.inputTranscription.text);
      }

      // Output transcription (what Gemini said)
      if (sc.outputTranscription && sc.outputTranscription.text) {
        addMessage("agent", sc.outputTranscription.text);
      }

      // Turn complete
      if (sc.turnComplete) {
        setStatus("listening", "Listening...");
      }
    }

    // Tool call from Gemini
    const tc = msg.toolCall;
    if (tc && tc.functionCalls) {
      for (const call of tc.functionCalls) {
        if (call.name === "send_to_autopilot") {
          const userMsg = call.args?.message || "";
          const result = await sendToAutopilot(userMsg);
          if (result.contextId) sessionId = result.contextId;
          const responseText = result.text || "No response.";

          // Send tool response back to Gemini
          ws.send(JSON.stringify({
            toolResponse: {
              functionResponses: [{
                id: call.id,
                name: call.name,
                response: { result: responseText },
              }],
            },
          }));

          setStatus("listening", "Listening...");

          // Update context-aware suggestions
          lastUserMessage = userMsg;
          lastAgentResponse = responseText;
          refreshSuggestions();
        }
      }
    }
  };

  ws.onerror = () => {
    setStatus("disconnected", "Connection error");
    addMessage("system", "WebSocket error");
  };

  ws.onclose = (e) => {
    setStatus("disconnected", "Disconnected");
    micBtn.disabled = true;
    micBtn.classList.remove("active");
    isListening = false;
    stopAudioCapture();
    if (e.code !== 1000) {
      addMessage("system", `Disconnected (code ${e.code})`);
    }
  };
}

// --- Mic button ---

micBtn.addEventListener("click", async () => {
  if (!isListening) {
    try {
      await startAudioCapture();
      isListening = true;
      micBtn.classList.add("active");
      setStatus("listening", "Listening...");
      hintEl.textContent = "Speak now — click again to pause";
    } catch (err) {
      addMessage("system", `Microphone error: ${err.message}`);
    }
  } else {
    isListening = false;
    micBtn.classList.remove("active");
    stopAudioCapture();
    setStatus("connected", "Connected");
    hintEl.textContent = "Click the microphone to start";
    // Clear waveform
    waveformCtx.fillStyle = "#161b22";
    waveformCtx.fillRect(0, 0, waveformCanvas.width, waveformCanvas.height);
  }
});

// --- Suggestion chips (context-aware) ---

const suggestionsEl = document.getElementById("suggestions");
let lastUserMessage = "";
let lastAgentResponse = "";

function attachChipListeners() {
  suggestionsEl.querySelectorAll(".suggestion").forEach((btn) => {
    btn.addEventListener("click", () => handleChipClick(btn.textContent));
  });
}

async function handleChipClick(text) {
  suggestionsEl.classList.add("hidden");
  addMessage("user", text);

  const result = await sendToAutopilot(text);
  if (result.contextId) sessionId = result.contextId;
  const responseText = result.text || "No response.";

  // Display the response as text in the transcript
  addMessage("agent", responseText);
  setStatus("connected", "Connected");

  // Generate new context-aware suggestions
  lastUserMessage = text;
  lastAgentResponse = responseText;
  await refreshSuggestions();
}

async function refreshSuggestions() {
  try {
    const resp = await fetch("/api/suggestions", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        user_message: lastUserMessage,
        agent_response: lastAgentResponse,
      }),
    });
    if (!resp.ok) return;
    const data = await resp.json();
    if (data.suggestions && data.suggestions.length > 0) {
      suggestionsEl.innerHTML = data.suggestions
        .map((s) => `<button class="suggestion">${s}</button>`)
        .join("");
      attachChipListeners();
      suggestionsEl.classList.remove("hidden");
    }
  } catch {
    // Silently ignore — suggestions are optional
  }
}

// Also extract options from agent responses (numbered lists, bullet points)
function extractOptionsFromResponse(text) {
  // Match patterns like "1. Option A" or "- Option B" or "* Option C"
  const lines = text.split("\n");
  const options = [];
  for (const line of lines) {
    const match = line.match(/^\s*(?:\d+[\.\)]\s*|[-*]\s+)\*{0,2}(.+?)\*{0,2}\s*$/);
    if (match && match[1].length > 3 && match[1].length < 80) {
      // Skip lines that look like descriptions rather than actionable options
      const opt = match[1].replace(/\*{1,2}/g, "").trim();
      if (!opt.includes(":") || opt.indexOf(":") > 30) {
        options.push(opt);
      }
    }
  }
  return options.slice(0, 4);
}

// Initial static chips
attachChipListeners();

// --- Init ---

connect();
