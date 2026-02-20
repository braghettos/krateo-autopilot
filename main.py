# Taken from https://google.github.io/adk-docs/deploy/gke/#code-files

import uuid
import logging
import os

import httpx
import uvicorn
from fastapi import FastAPI, HTTPException
from google.adk.cli.fast_api import get_fast_api_app
from database.database_config import DatabaseConfig

# Configure logging
log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
logging.basicConfig(
    level=getattr(logging, log_level, logging.INFO),
    format="[%(levelname)s] - [%(asctime)s] - [%(name)s]: %(message)s"
)
log = logging.getLogger(__name__)

# Get the directory where main.py is located
AGENT_DIR = os.path.dirname(os.path.abspath(__file__))

DEFAULT_PORT = 8080

# Example allowed origins for CORS
ALLOWED_ORIGINS = [
    "http://localhost",
    "http://localhost:8080",
    "*"
]

LOGO_CONFIG = {
    "text": "Krateo Autopilot",
    "image_url": "https://raw.githubusercontent.com/krateoplatformops/krateo-v2-docs/main/static/img/black-only-square.png"
}

def create_app() -> FastAPI:
    db_config = DatabaseConfig()  # reads DB_USERNAME, DB_PASSWORD, etc. from env automatically
    session_uri = db_config.get_session_service_uri()

    return get_fast_api_app(
        agents_dir=AGENT_DIR,
        session_service_uri=session_uri,
        allow_origins=ALLOWED_ORIGINS,
        web=True,
        logo_text=LOGO_CONFIG["text"],
        logo_image_url=LOGO_CONFIG["image_url"]
    )

# Initialize the FastAPI app
app = create_app()

@app.get("/health/startup")
async def startup_check():
    try:
        session_id = f"s_startup_probe_{uuid.uuid4().hex[:8]}"
        user_id = "u_startup_probe"
        app_name = "autopilot"
        
        async with httpx.AsyncClient(timeout=5.0) as client:
            await client.post(
                f"http://localhost:{DEFAULT_PORT}/apps/{app_name}/users/{user_id}/sessions/{session_id}",
                headers={"Content-Type": "application/json"}
            )
            log.info("Startup probe session created successfully")
            
            response = await client.post(
                f"http://localhost:{DEFAULT_PORT}/run",
                headers={"Content-Type": "application/json"},
                json={
                    "appName": app_name,
                    "userId": user_id,
                    "sessionId": session_id,
                    "newMessage": {
                        "role": "user",
                        "parts": [{"text": "Hello"}]
                    }
                }
            )
            
            response.raise_for_status()
            log.info("Startup probe completed successfully")
            return {"status": "ready"}
            
    except Exception as e:
        log.error(f"Startup probe failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Startup check failed: {str(e)}")

if __name__ == "__main__":
    """Run the application server."""
    port = int(os.environ.get("PORT", DEFAULT_PORT))
    uvicorn.run(app, host="0.0.0.0", port=port)