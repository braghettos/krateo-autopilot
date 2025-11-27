from google.genai import types

# --- Models ---
GEMINI_2_5_FLASH = "gemini-2.5-flash"
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
PROMPT_LANGUAGE = "eng" # Set to 'ita' or 'eng'
PROMPT = {}
DESCRIPTION = {}
PORT = {}
for i, agent in enumerate(AGENTS):
    with open(f"prompts/{PROMPT_LANGUAGE}/{agent}.md", "r", encoding="utf-8") as f:
        PROMPT[agent] = f.read()
        
    with open(f"descriptions/{PROMPT_LANGUAGE}/{agent}.md", "r", encoding="utf-8") as f:
        DESCRIPTION[agent] = f.read()
    
    PORT[agent] = 8001 + i

PROMPT["global"] = "You are Krateo Autopilot."

# MORE SECURE ALTERNATIVE
# def load_prompt(agent_name: str) -> str:
#     with open(f"prompts/{PROMPT_LANGUAGE}/{agent_name}.md", "r", encoding="utf-8") as f:
#         return f.read()

# def load_description(agent_name: str) -> str:
#     with open(f"descriptions/{PROMPT_LANGUAGE}/{agent_name}.md", "r", encoding="utf-8") as f:
#         return f.read()

# PORT = {agent: 8001 + i for i, agent in enumerate(AGENTS)}

GENERATE_CONTENT_CONFIG=types.GenerateContentConfig(
    safety_settings=[
        types.SafetySetting(
            category=types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
            threshold=types.HarmBlockThreshold.OFF,
        ),
    ]
)
