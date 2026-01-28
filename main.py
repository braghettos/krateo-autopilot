# Taken from https://google.github.io/adk-docs/deploy/gke/#code-files

import logging
import os

import uvicorn
from fastapi import FastAPI
from google.adk.cli.fast_api import get_fast_api_app

# Configure logging
log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
logging.basicConfig(
    level=getattr(logging, log_level, logging.INFO),
    format="[%(levelname)s] - [%(asctime)s] - [%(name)s]: %(message)s"
)
log = logging.getLogger(__name__)
print(f"Logging level set to: {log_level}")

# Get the directory where main.py is located
AGENT_DIR = os.path.dirname(os.path.abspath(__file__))

DEFAULT_PORT = 8080
DEFAULT_DB_PORT = 5432
SQLITE_SESSION_URI = "sqlite:///./sessions.db"

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

def get_session_service_uri() -> str:
    """Construct the session service URI."""
    cluster_name = os.getenv('CLUSTER_NAME')
    db_username = os.getenv('DB_USERNAME')
    db_password = os.getenv('DB_PASSWORD')
    db_name = os.getenv('DB_NAME')
    
    if all([cluster_name, db_username, db_password, db_name]):
        db_host = f"{cluster_name}-rw"
        uri = (
            f"postgresql+asyncpg://{db_username}:{db_password}"
            f"@{db_host}:{DEFAULT_DB_PORT}/{db_name}"
        )
        log.info(f"Using PostgreSQL session service at {db_host}:{DEFAULT_DB_PORT}/{db_name}")
        return uri
    
    log.info("Using local SQLite session service")
    return SQLITE_SESSION_URI


def create_app() -> FastAPI:
    """Create the FastAPI application."""
    session_uri = get_session_service_uri()
    
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

# Additional routes can be added here
# Example:
# @app.get("/health")
# async def health_check():
#     return {"status": "healthy"}

if __name__ == "__main__":
    """Run the application server."""
    port = int(os.environ.get("PORT", DEFAULT_PORT))
    uvicorn.run(app, host="0.0.0.0", port=port)