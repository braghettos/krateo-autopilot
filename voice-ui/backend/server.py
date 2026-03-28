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
    "http://kagent-controller.kagent.svc.cluster.local:8083/api/a2a/krateo-system/krateo-autopilot/",
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
        "model": "gemini-2.5-flash-native-audio-latest",
    }


@app.post("/api/autopilot")
async def send_to_autopilot(req: AutopilotRequest):
    """
    Proxy a text message to the kagent A2A endpoint.

    1. POST to create a task with the user's message
    2. Poll GET until the task completes or times out
    3. Return the agent's response text
    """
    task_id = str(uuid.uuid4())
    session_id = req.session_id or str(uuid.uuid4())

    # A2A JSON-RPC: tasks/send
    a2a_payload = {
        "jsonrpc": "2.0",
        "id": task_id,
        "method": "tasks/send",
        "params": {
            "id": task_id,
            "sessionId": session_id,
            "message": {
                "role": "user",
                "parts": [{"type": "text", "text": req.message}],
            },
        },
    }

    async with httpx.AsyncClient(timeout=httpx.Timeout(POLL_TIMEOUT + 10)) as client:
        # Send the task
        try:
            resp = await client.post(A2A_ENDPOINT, json=a2a_payload)
            resp.raise_for_status()
        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=e.response.status_code, detail=str(e))
        except httpx.RequestError as e:
            raise HTTPException(status_code=502, detail=f"A2A endpoint unreachable: {e}")

        result = resp.json()

        # Check if the response already contains the completed result
        if "result" in result:
            task_result = result["result"]
            state = task_result.get("status", {}).get("state", "")
            if state == "completed":
                return _extract_response(task_result)

        # Poll for completion
        elapsed = 0
        while elapsed < POLL_TIMEOUT:
            await asyncio.sleep(POLL_INTERVAL)
            elapsed += POLL_INTERVAL

            poll_payload = {
                "jsonrpc": "2.0",
                "id": str(uuid.uuid4()),
                "method": "tasks/get",
                "params": {"id": task_id},
            }
            try:
                poll_resp = await client.post(A2A_ENDPOINT, json=poll_payload)
                poll_resp.raise_for_status()
                poll_result = poll_resp.json()
            except (httpx.HTTPStatusError, httpx.RequestError):
                continue

            if "result" in poll_result:
                task_data = poll_result["result"]
                state = task_data.get("status", {}).get("state", "")
                if state in ("completed", "failed"):
                    return _extract_response(task_data)

    raise HTTPException(status_code=504, detail="Autopilot request timed out")


def _extract_response(task_data: dict) -> dict:
    """Extract text from A2A task artifacts."""
    state = task_data.get("status", {}).get("state", "unknown")

    if state == "failed":
        error_msg = task_data.get("status", {}).get("message", "Agent returned an error")
        return {"text": f"Error: {error_msg}", "state": state}

    # Extract text from artifacts
    artifacts = task_data.get("artifacts", [])
    texts = []
    for artifact in artifacts:
        for part in artifact.get("parts", []):
            if part.get("type") == "text":
                texts.append(part["text"])

    # Fallback: check status message
    if not texts:
        status_msg = task_data.get("status", {}).get("message", "")
        if status_msg:
            texts.append(status_msg)

    response_text = "\n\n".join(texts) if texts else "No response from autopilot."
    return {"text": response_text, "state": state}


# Serve frontend static files
FRONTEND_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")
if os.path.isdir(FRONTEND_DIR):
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

    @app.get("/")
    async def index():
        return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))
