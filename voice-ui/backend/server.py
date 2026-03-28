"""
Voice UI Backend — FastAPI proxy between the browser and the kagent A2A endpoint.

Serves the static frontend and proxies voice-transcribed messages
to the Krateo Autopilot agent via the A2A protocol.
"""

import os
import asyncio
import uuid

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

A2A_ENDPOINT = os.environ.get(
    "A2A_ENDPOINT",
    "http://kagent-controller.krateo-system.svc.cluster.local:8083/api/a2a/krateo-system/krateo-autopilot/",
)
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
POLL_INTERVAL = 2  # seconds
POLL_TIMEOUT = 120  # seconds

app = FastAPI(title="Krateo Voice UI")


class AutopilotRequest(BaseModel):
    message: str
    session_id: str | None = None


@app.get("/api/config")
async def get_config():
    """Return non-sensitive configuration for the frontend."""
    return {
        "geminiApiKey": GEMINI_API_KEY,
        "model": "gemini-3.1-flash-live-preview",
    }


@app.post("/api/autopilot")
async def send_to_autopilot(req: AutopilotRequest):
    """
    Proxy a text message to the kagent A2A endpoint.

    1. POST to create a task with the user's message
    2. Poll GET until the task completes or times out
    3. Return the agent's response text
    """
    request_id = str(uuid.uuid4())
    context_id = req.session_id

    a2a_payload = {
        "jsonrpc": "2.0",
        "id": request_id,
        "method": "message/send",
        "params": {
            "message": {
                "role": "user",
                "parts": [{"kind": "text", "text": req.message}],
            },
        },
    }
    if context_id:
        a2a_payload["params"]["contextId"] = context_id

    async with httpx.AsyncClient(timeout=httpx.Timeout(POLL_TIMEOUT + 10)) as client:
        try:
            resp = await client.post(A2A_ENDPOINT, json=a2a_payload)
            resp.raise_for_status()
        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=e.response.status_code, detail=str(e))
        except httpx.RequestError as e:
            raise HTTPException(status_code=502, detail=f"A2A endpoint unreachable: {e}")

        result = resp.json()

        if "error" in result:
            error = result["error"]
            raise HTTPException(status_code=500, detail=error.get("message", str(error)))

        if "result" in result:
            return _extract_response(result["result"])

    raise HTTPException(status_code=504, detail="No result from autopilot")


def _extract_response(result_data: dict) -> dict:
    """Extract text from A2A message/send result."""
    context_id = result_data.get("contextId", "")

    artifacts = result_data.get("artifacts", [])
    texts = []
    for artifact in artifacts:
        for part in artifact.get("parts", []):
            if part.get("kind") == "text":
                texts.append(part["text"])

    # Fallback: check history for assistant messages
    if not texts:
        for msg in result_data.get("history", []):
            if msg.get("role") == "agent":
                for part in msg.get("parts", []):
                    if part.get("kind") == "text":
                        texts.append(part["text"])

    response_text = "\n\n".join(texts) if texts else "No response from autopilot."
    return {"text": response_text, "contextId": context_id}


class SuggestionsRequest(BaseModel):
    user_message: str
    agent_response: str


@app.post("/api/suggestions")
async def get_suggestions(req: SuggestionsRequest):
    """Generate 3-4 context-aware follow-up questions using Gemini Flash."""
    if not GEMINI_API_KEY:
        return {"suggestions": []}

    prompt = f"""Based on this conversation with a Kubernetes platform assistant, suggest exactly 4 short follow-up questions the user might want to ask next. Each question should be concise (under 8 words), actionable, and different from each other.

User asked: {req.user_message}
Assistant responded: {req.agent_response[:1000]}

Return ONLY a JSON array of 4 strings, nothing else. Example: ["Check pod logs", "Scale deployment to 3", "Show recent events", "List services"]"""

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}"

    async with httpx.AsyncClient(timeout=15) as client:
        try:
            resp = await client.post(url, json={
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {
                    "temperature": 0.7,
                    "maxOutputTokens": 500,
                    "thinkingConfig": {"thinkingBudget": 0},
                },
            })
            resp.raise_for_status()
            data = resp.json()
            text = data["candidates"][0]["content"]["parts"][0]["text"]
            # Parse JSON array from response (strip markdown fences if present)
            import re as _re
            import json as _json
            # Extract JSON array from response, handling markdown fences
            match = _re.search(r'\[.*?\]', text, _re.DOTALL)
            if not match:
                return {"suggestions": []}
            suggestions = _json.loads(match.group(0))
            if isinstance(suggestions, list):
                return {"suggestions": suggestions[:4]}
        except Exception:
            pass

    return {"suggestions": []}


# Serve frontend static files
FRONTEND_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")
if os.path.isdir(FRONTEND_DIR):
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

    @app.get("/")
    async def index():
        return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))
