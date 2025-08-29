from google.adk.agents import Agent
from . import tools

# --- Models ---
GEMINI_2_5_FLASH = "gemini-2.5-flash"
GEMINI_2_5_PRO = "gemini-2.5-pro"

# --- Prompts ---
PORTAL_AGENT_PROMPT = open("prompts/portal_agent.md").read() 
COMPOSITION_AGENT_PROMPT = open("prompts/composition_agent_4.md").read()
ROOT_AGENT_PROMPT = open("prompts/krateo_autopilot_2.md").read()
DOCUMENTATION_AGENT_PROMPT = open("prompts/documentation_agent.md").read()
AUTHENTICATION_AGENT_PROMPT = open("prompts/authentication_agent.md").read()
GITHUB_AGENT_PROMPT = open("prompts/github_agent.md").read()

# -- Github Agent ---
github_agent = None
try:
    github_agent = Agent(
        model=GEMINI_2_5_FLASH,
        name="github_agent",
        instruction=GITHUB_AGENT_PROMPT,
        description="It creates repositories and manages files in GitHub.", # Crucial for delegation
        tools=[tools.create_repository, tools.create_or_update_file]
    )
    print(f"✅ Agent '{github_agent.name}' created using model '{github_agent.model}'.")
except Exception as e:
    print(f"❌ Could not create Github agent. Check API Key ({github_agent.model}). Error: {e}")    

# --- Authentication Agent ---
auth_agent = None
try:
    auth_agent = Agent(
        model=GEMINI_2_5_FLASH,
        name="auth_agent",
        instruction=AUTHENTICATION_AGENT_PROMPT,
        description="Handles authentication in Krateo." # Crucial for delegation
                    "It creates accounts in Krateo and answers questions about authentication.",
        tools=[tools.apply_manifest],
        sub_agents=[github_agent]
    )
    print(f"✅ Agent '{auth_agent.name}' created using model '{auth_agent.model}'.")
except Exception as e:
    print(f"❌ Could not create Authentication agent. Check API Key ({auth_agent.model}). Error: {e}")      

# --- Portal Agent ---
portal_agent = None
try:
    portal_agent = Agent(
        model=GEMINI_2_5_FLASH,
        name="portal_agent",
        instruction=PORTAL_AGENT_PROMPT,
        description="Creates the Portal section for Krateo compositions.", # Crucial for delegation
    )
    print(f"✅ Agent '{portal_agent.name}' created using model '{portal_agent.model}'.")
except Exception as e:
    print(f"❌ Could not create Greeting agent. Check API Key ({portal_agent.model}). Error: {e}")

# --- Composition Agent ---
composition_agent = None
try:
    composition_agent = Agent(
        model = GEMINI_2_5_PRO,
        name="composition_agent",
        instruction=COMPOSITION_AGENT_PROMPT,
        description="Creates Krateo compositions.", # Crucial for delegation
        tools=[tools.create_file, tools.apply_composition_definition, tools.apply_manifest],
        # sub_agents=[portal_agent],
    )
    print(f"✅ Agent '{composition_agent.name}' created using model '{composition_agent.model}'.")
except Exception as e:
    print(f"❌ Could not create Farewell agent. Check API Key ({composition_agent.model}). Error: {e}")

# --- Documentation Agent ---
documentation_agent = None
try:
    documentation_agent = Agent(
        model=GEMINI_2_5_FLASH,
        name="documentation_agent",
        instruction=DOCUMENTATION_AGENT_PROMPT,
        description="Handles any questions about Krateo PlatformOps and its components.", # Crucial for delegation
    )
    print(f"✅ Agent '{documentation_agent.name}' created using model '{documentation_agent.model}'.")
except Exception as e:
    print(f"❌ Could not create Documentation agent. Check API Key ({documentation_agent.model}). Error: {e}")  

# --- Root Agent ---    
root_agent = Agent(
    name="krateo_autopilot",
    model=GEMINI_2_5_FLASH,
    description="The main coordinator agent. Handles general questions about Krateo and delegates specific tasks to sub-agents."
                "It uses the composition_agent to create Krateo compositions and the portal_agent for creating portal sections."
                "It uses the documentation agent to answer questions about Krateo"
                "It uses the install_krateo tool to install Krateo PlatformOps on the current Kubernetes cluster.",
    instruction=ROOT_AGENT_PROMPT,
    tools=[tools.install_krateo, tools.apply_manifest],
    sub_agents=[composition_agent, documentation_agent, auth_agent]
)