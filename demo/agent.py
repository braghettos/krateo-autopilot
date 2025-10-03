from google.adk.tools.mcp_tool.mcp_session_manager import StreamableHTTPConnectionParams
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset
from google.adk.tools import agent_tool
from google.adk.agents import Agent
from . import tools, git_tools
import os

# --- Models ---
GEMINI_2_5_FLASH = "gemini-2.5-flash"
GEMINI_2_5_PRO = "gemini-2.5-pro"

# --- Prompts ---
DOCUMENTATION_AGENT_PROMPT = open("prompts/documentation_agent.md").read()
ROOT_AGENT_PROMPT = open("prompts/krateo_autopilot_2.md").read()
AUTHENTICATION_AGENT_PROMPT = open("prompts/authentication_agent.md").read()
COMPOSITION_AGENT_PROMPT = open("prompts/agent-tool/composition-agent-5.md").read()
PORTAL_AGENT_PROMPT = open("prompts/portal-agent-granular/portal-agent-4.md").read() 
RESTACTION_AGENT_PROMPT = open("prompts/restaction-agent.md").read() 
GITHUB_AGENT_PROMPT = open("prompts/agent-tool/github-agent.md").read()

# -- Github Agent ---
github_agent = None
try:    
    github_agent = Agent(
        model=GEMINI_2_5_FLASH,
        name='github_agent',
        instruction=GITHUB_AGENT_PROMPT,
        description="Creates repositories and manages files in GitHub.", # Crucial for delegation
        tools=[
            MCPToolset(
                connection_params=StreamableHTTPConnectionParams(
                    url="https://api.githubcopilot.com/mcp/",
                    headers={
                        "Authorization": f"Bearer {os.getenv('GITHUB_TOKEN')}"
                    }
                ),
                tool_filter=['create_or_update_file', 'create_pull_request', 'create_branch']
            ), 
            git_tools.create_repo_from_template, # TODO: remove when the MCP server above supports it
            git_tools.get_file_contents, # TODO: remove when the MCP server above supports it
            tools.read_file 
        ],
    )
    print(f"✅ Agent '{github_agent.name}' created using model '{github_agent.model}'.")
except Exception as e:    
    print(f"❌ Could not create Github agent. Check API Key ({github_agent.model}). Error: {e}")
    
github_agent_tool = agent_tool.AgentTool(agent=github_agent) # Wrap the agent

# --- Restaction Agent ---
restaction_agent = None
try: 
    restaction_agent = Agent(
        name="restaction_agent",
        model=GEMINI_2_5_PRO,
        description="RESTACTION Agent for Krateo Autopilot.", # crucial for delegation
        instruction=RESTACTION_AGENT_PROMPT,
    )
    print(f"✅ Agent '{restaction_agent.name}' created using model '{restaction_agent.model}'.")
except Exception as e:
    print(f"❌ Could not create '{restaction_agent.name}' agent. Check API Key ({restaction_agent.model}). Error: {e}")
restaction_agent_tool = agent_tool.AgentTool(agent=restaction_agent) # Wrap the agent

# --- Portal Agent ---
portal_agent = None
try: 
    portal_agent = Agent(
        name="portal_agent",
        model=GEMINI_2_5_PRO,
        description="Portal Agent for Krateo Autopilot.",
        instruction=PORTAL_AGENT_PROMPT,
        tools=[tools.get_widgets, tools.check_yamls, tools.apply_manifest]
        # tools=[tools.get_widgets, tools.check_yamls, tools.apply_manifest, restaction_agent_tool]
    )
    print(f"✅ Agent '{portal_agent.name}' created using model '{portal_agent.model}'.")
except Exception as e:
    print(f"❌ Could not create '{portal_agent.name}' agent. Check API Key ({portal_agent.model}). Error: {e}")    
# portal_agent_tool = agent_tool.AgentTool(agent=portal_agent) # Wrap the agent

# --- Composition Agent ---
composition_agent = None
try:
    composition_agent = Agent(
        model=GEMINI_2_5_PRO,
        name="composition_agent",
        instruction=COMPOSITION_AGENT_PROMPT,
        description="Creates Krateo compositions.", # Crucial for delegation
        tools=[tools.create_file, tools.apply_manifest, tools.gen_values_schema_json, github_agent_tool]
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
        description="Handles Krateo login, authentication, or password management" # Crucial for delegation
                    "It creates accounts in Krateo and answers questions about authentication."
                    "Handles Questions about `authn`, user `Secrets`, or the `User` custom resource in Krateo.",
        tools=[tools.apply_manifest, tools.get_admin_psw],
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
                "It uses the composition_agent to create Krateo compositions and the portal_agent for creating portal sections."
                "It uses the documentation agent to answer questions about Krateo"
                "It uses the install_krateo tool to install Krateo PlatformOps on the current Kubernetes cluster.",
    instruction=ROOT_AGENT_PROMPT,
    tools=[tools.install_krateo],
    sub_agents=[composition_agent, portal_agent, documentation_agent, auth_agent]
)