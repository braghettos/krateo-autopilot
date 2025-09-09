from google.adk.agents import Agent
from google.adk.tools import agent_tool
from . import tools

GEMINI_2_5_PRO = "gemini-2.5-pro"

PORTAL_AGENT_PROMPT = open("prompts/agent-tool/portal-agent.md").read() 
COMPOSITION_AGENT_PROMPT = open("prompts/agent-tool/composition-agent.md").read()

portal_agent = None     
try:    
    portal_agent = Agent(
        model=GEMINI_2_5_PRO,
        name="portal_agent",
        instruction=PORTAL_AGENT_PROMPT,
        description="Creates the portal section", # Crucial for delegation
    )
    print(f"✅ Agent '{portal_agent.name}' created using model '{portal_agent.model}'.")
except Exception as e:      
    print(f"❌ Could not create Portal agent. Check API Key ({portal_agent.model}). Error: {e}")
    
portal_agent_tool = agent_tool.AgentTool(agent=portal_agent) # Wrap the agent

composition_agent = None
try:
    composition_agent = Agent(
        model=GEMINI_2_5_PRO,
        name="agent",
        instruction=COMPOSITION_AGENT_PROMPT,
        description="Creates Krateo compositions.", # Crucial for delegation
        tools=[tools.create_file, tools.apply_composition_definition, tools.apply_manifest, portal_agent_tool]
    )
    print(f"✅ Agent '{composition_agent.name}' created using model '{composition_agent.model}'.")
except Exception as e:
    print(f"❌ Could not create Github agent. Check API Key ({composition_agent.model}). Error: {e}")    
    
root_agent = composition_agent