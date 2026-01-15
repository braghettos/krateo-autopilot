from google.genai import types
import os

# --- Models ---
GEMINI_2_5_FLASH = "gemini-2.5-flash"
GEMINI_3_FLASH = "gemini-3-flash-preview"
GEMINI_2_5_PRO = "gemini-2.5-pro"
GEMINI_3_PRO = "gemini-3-pro-preview"

# --- Agents ---
AGENTS = [
    "auth_agent",
    "blueprint_agent",
    "documentation_agent",
    "portal_agent",
    "restaction_agent",
    "root_agent"
]

# --- Agents Prompts, Descriptions and Ports ---
PROMPT_LANGUAGE = os.getenv("PROMPT_LANGUAGE", "eng") # "ita" or "eng"
PROMPT = {}
DESCRIPTION = {}
for i, agent in enumerate(AGENTS):
    try:
        with open(f"prompts/{PROMPT_LANGUAGE}/{agent}.md", "r", encoding="utf-8") as f:
            PROMPT[agent] = f.read()
    except FileNotFoundError:
        pass
        
    try:
        with open(f"descriptions/{PROMPT_LANGUAGE}/{agent}.md", "r", encoding="utf-8") as f:
            DESCRIPTION[agent] = f.read()
    except FileNotFoundError:
        pass

PROMPT["global"] = "You are Krateo Autopilot, an advanced AI agent designed to assist platform engineers with the Krateo Platform."
PORT = 8001

GENERATE_CONTENT_CONFIG=types.GenerateContentConfig(
    safety_settings=[
        types.SafetySetting(
            category=types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
            threshold=types.HarmBlockThreshold.OFF,
        ),
    ]
)
