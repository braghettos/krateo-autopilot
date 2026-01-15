from google.adk.agents import Agent
from google.adk.a2a.utils.agent_to_a2a import to_a2a

from config import *

agent = "restaction_agent"
root_agent = None

try:
    root_agent = Agent(
        name=agent,
        model=GEMINI_2_5_PRO,
        description=DESCRIPTION[agent],    
        instruction=PROMPT[agent],
        global_instruction=PROMPT["global"], 
        generate_content_config=GENERATE_CONTENT_CONFIG
    )
except Exception as e:
    print(f"Could not create '{agent}' agent. Error: {e}")

a2a_app = to_a2a(root_agent, port=PORT, host=agent.replace("_","-"))
