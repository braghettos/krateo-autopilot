from google.adk.agents import Agent

# --- Models ---
GEMINI_2_5_PRO = "gemini-2.5-pro"

# --- Prompts ---
PROMPT = open("prompts/restaction-agent.md").read() 

# --- Root Agent ---    
root_agent = Agent(
    name="restaction_agent",
    model=GEMINI_2_5_PRO,
    description="RESTACTION Agent for Krateo Autopilot.",
    instruction=PROMPT,
)