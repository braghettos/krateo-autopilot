from google.adk.agents import Agent
from . import tools 

# --- Models ---
GEMINI_2_5_PRO = "gemini-2.5-pro"

# --- Prompts ---
PROMPT = open("prompts/portal-agent-granular/portal-agent.md").read() 
 
# --- Root Agent ---    
root_agent = Agent(
    name="krateo_autopilot",
    model=GEMINI_2_5_PRO,
    description="PORTAL Agent for Krateo Autopilot.",
    instruction=PROMPT,
    tools=[tools.get_widgets, tools.check_yamls]
)

