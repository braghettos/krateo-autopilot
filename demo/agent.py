from google.adk.tools.mcp_tool.mcp_session_manager import StreamableHTTPConnectionParams
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset
from google.adk.tools import agent_tool
from google.adk.agents import Agent
import tools.common, tools.github, tools.portal
import os

# --- Models ---
GEMINI_2_5_FLASH = "gemini-2.5-flash"
GEMINI_2_5_PRO = "gemini-2.5-pro"

# --- Prompts ---
DOCUMENTATION_AGENT_PROMPT = open("prompts/documentation_agent.md").read()
ROOT_AGENT_PROMPT = open("prompts/krateo_autopilot_2.md").read()
AUTHENTICATION_AGENT_PROMPT = open("prompts/authentication_agent.md").read()
COMPOSITION_AGENT_PROMPT = open("prompts/agent-tool/composition-agent-6.md").read()
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
        description="This agent is specialized for performing Git and GitHub operations." # Crucial for delegation
        "It directly interacts with the GitHub API and the user's local filesystem to manage repositories." 
        "Delegate a user's request to this agent if the intent involves creating or modifying repositories, branches, files, or pull requests on GitHub.",
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
            tools.github.create_repo_from_template, # TODO: remove when the MCP server above supports it
            tools.github.get_file_contents, # TODO: remove when the MCP server above supports it
            tools.common.read_file 
        ],
    )
    print(f"✅ Agent '{github_agent.name}' created using model '{github_agent.model}'.")
except Exception as e:    
    print(f"❌ Could not create Github agent. Check API Key ({github_agent.model}). Error: {e}")
    
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
        description="Creates and manages portal sections (Krateo's frontend) and widgets.", # Crucial for delegation
        instruction=PORTAL_AGENT_PROMPT,
        tools=[tools.portal.get_widgets, tools.portal.create_file, tools.portal.apply_manifest],
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
        tools=[tools.common.create_file, tools.common.apply_manifest, tools.common.gen_values_schema_json]
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
    sub_agents=[composition_agent, portal_agent, documentation_agent, auth_agent, github_agent]
)