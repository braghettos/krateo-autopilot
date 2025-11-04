from google.adk.agents import Agent
import tools.common, tools.portal, tools.get_blueprint, tools.list_blueprints

# --- Models ---
GEMINI_2_5_FLASH = "gemini-2.5-flash"
GEMINI_2_5_PRO = "gemini-2.5-pro"

# --- Prompts ---
DOCUMENTATION_AGENT_PROMPT = open("prompts/documentation_agent.md").read()
ROOT_AGENT_PROMPT = open("prompts/root_agent.md").read()
AUTHENTICATION_AGENT_PROMPT = open("prompts/auth_agent.md").read()
COMPOSITION_AGENT_PROMPT = open("prompts/composition_agent.md").read()
PORTAL_AGENT_PROMPT = open("prompts/portal_agent.md").read() 
RESTACTION_AGENT_PROMPT = open("prompts/restaction_agent.md").read() 
    
# --- Restaction Agent ---
restaction_agent = None
try: 
    restaction_agent = Agent(
        name="restaction_agent",
        model=GEMINI_2_5_PRO,
        description="RESTAction Agent for Krateo Autopilot.", # crucial for delegation
        instruction=RESTACTION_AGENT_PROMPT,
        tools=[tools.common.create_file]
    )
    print(f"✅ Agent '{restaction_agent.name}' created using model '{restaction_agent.model}'.")
except Exception as e:
    print(f"❌ Could not create '{restaction_agent.name}' agent. Check API Key ({restaction_agent.model}). Error: {e}")

# --- Portal Agent ---
portal_agent = None
try: 
    portal_agent = Agent(
        name="portal_agent",
        model=GEMINI_2_5_PRO,
        description="Creates and manages portal sections (Krateo's frontend) and widgets. Applies portal manifests. Manages widgets (Forms, Buttons, Pages, Panels, etc.)", # Crucial for delegation
        instruction=PORTAL_AGENT_PROMPT,
        tools=[tools.portal.get_widgets, tools.portal.apply_manifest, tools.portal.validate_yaml]
    )
    print(f"✅ Agent '{portal_agent.name}' created using model '{portal_agent.model}'.")    
except Exception as e:
    print(f"❌ Could not create '{portal_agent.name}' agent. Check API Key ({portal_agent.model}). Error: {e}")    

# --- Composition Agent ---
composition_agent = None
try:
    composition_agent = Agent(
        model=GEMINI_2_5_PRO,
        name="composition_agent",
        instruction=COMPOSITION_AGENT_PROMPT,
        description="Creates Krateo compositions."# Crucial for delegation
                    "Can apply manifests (e.g. composition, compositiondefinition) to the cluster.",
        tools=[
            tools.common.apply_manifest, 
            tools.common.gen_values_schema_json,
            tools.list_blueprints.list_blueprints,
            tools.get_blueprint.get_blueprint,
        ]
    )
    print(f"✅ Agent '{composition_agent.name}' created using model '{composition_agent.model}'.")
except Exception as e:
    print(f"❌ Could not create '{composition_agent.name}' agent. Check API Key ({composition_agent.model}). Error: {e}")    

# --- Authentication Agent ---
auth_agent = None
try:
    auth_agent = Agent(
        model=GEMINI_2_5_FLASH,
        name="auth_agent",
        instruction=AUTHENTICATION_AGENT_PROMPT,
        description="Handles Krateo login and authentication" # Crucial for delegation
                    "It creates accounts in Krateo and answers questions about authentication."
                    "Handles Questions about `authn`, user `Secrets`, or the `User` custom resource in Krateo.",
        tools=[tools.common.apply_manifest, tools.common.get_admin_psw],
    )
    print(f"✅ Agent '{auth_agent.name}' created using model '{auth_agent.model}'.")
except Exception as e:
    print(f"❌ Could not create '{auth_agent.name}' agent. Check API Key ({auth_agent.model}). Error: {e}")      

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
                "It uses the `install_krateo` tool to install Krateo PlatformOps on the current Kubernetes cluster.",
    instruction=ROOT_AGENT_PROMPT,
    tools=[tools.common.install_krateo],
    sub_agents=[composition_agent, portal_agent, documentation_agent, auth_agent, restaction_agent]
)