from google.adk.agents import Agent
from google.adk.a2a.utils.agent_to_a2a import to_a2a

from config import *
from tools.portal import get_widgets, apply_manifest
from tools.common import validate_yaml

agent = "portal_agent"
root_agent = None

try:
    root_agent = Agent(
        name=agent,
        model=GEMINI_3_PRO,
        description=DESCRIPTION[agent],    
        instruction=PROMPT[agent],
        global_instruction=PROMPT["global"], 
        generate_content_config=GENERATE_CONTENT_CONFIG,
        tools=[
            get_widgets, 
            apply_manifest,
            validate_yaml
        ]
    )
except Exception as e:
    print(f"Could not create '{agent}' agent. Error: {e}")

a2a_app = to_a2a(root_agent, port=PORT, host=agent.replace("_","-"))
