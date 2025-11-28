# Taken from https://google.github.io/adk-docs/deploy/gke/#code-files

import os

import uvicorn
from fastapi import FastAPI
from google.adk.cli.fast_api import get_fast_api_app
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format="[%(levelname)s] - [%(asctime)s] - [%(name)s]: %(message)s"
)
log = logging.getLogger(__name__)

# Get the directory where main.py is located
AGENT_DIR = os.path.dirname(os.path.abspath(__file__))

# Session serivce set up
CLUSTER_NAME = os.getenv('CLUSTER_NAME')
DB_USERNAME = os.getenv('DB_USERNAME')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_NAME = os.getenv('DB_NAME')

if all([CLUSTER_NAME, DB_USERNAME, DB_PASSWORD, DB_NAME]):
    DB_HOST = f"{CLUSTER_NAME}-rw"
    DB_PORT = 5432
    SESSION_SERVICE_URI = f"postgresql+asyncpg://{DB_USERNAME}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    log.info(f"Using PostgreSQL session service at {DB_HOST}:{DB_PORT}/{DB_NAME}")
else:
    SESSION_SERVICE_URI = "sqlite:///./sessions.db"
    log.info("Using local SQLite session service")

# Example allowed origins for CORS
ALLOWED_ORIGINS = ["http://localhost", "http://localhost:8080", "*"]
# Set web=True if you intend to serve a web interface, False otherwise
SERVE_WEB_INTERFACE = True

# Call the function to get the FastAPI app instance
# Ensure the agent directory name ('capital_agent') matches your agent folder
app: FastAPI = get_fast_api_app(
    agents_dir=AGENT_DIR,
    session_service_uri=SESSION_SERVICE_URI,
    allow_origins=ALLOWED_ORIGINS,
    web=SERVE_WEB_INTERFACE,
)

# You can add more FastAPI routes or configurations below if needed
# Example:
# @app.get("/hello")
# async def read_root():
#     return {"Hello": "World"}

if __name__ == "__main__":
    # Use the PORT environment variable provided by Cloud Run, defaulting to 8080
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))