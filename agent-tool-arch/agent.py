from google.adk.tools.mcp_tool.mcp_session_manager import StreamableHTTPConnectionParams
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset
from google.adk.agents import Agent, LlmAgent
from google.adk.tools import agent_tool
from . import tools, git_tools
import os

GEMINI_2_5_PRO = "gemini-2.5-pro"
GEMINI_2_5_FLASH = "gemini-2.5-flash"

PORTAL_AGENT_PROMPT = open("prompts/agent-tool/portal-agent.md").read() 
COMPOSITION_AGENT_PROMPT = open("prompts/agent-tool/composition-agent-2.md").read()
GITHUB_AGENT_PROMPT = open("prompts/agent-tool/github-agent.md").read()

github_agent = None
try:    
    github_agent = LlmAgent(
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
            tools.read_file 
        ],
    )
    print(f"✅ Agent '{github_agent.name}' created using model '{github_agent.model}'.")
except Exception as e:    
    print(f"❌ Could not create Github agent. Check API Key ({github_agent.model}). Error: {e}")
    
github_agent_tool = agent_tool.AgentTool(agent=github_agent) # Wrap the agent

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
        tools=[tools.create_file, tools.apply_composition_definition, tools.apply_manifest, portal_agent_tool, github_agent_tool]
    )
    print(f"✅ Agent '{composition_agent.name}' created using model '{composition_agent.model}'.")
except Exception as e:
    print(f"❌ Could not create Github agent. Check API Key ({composition_agent.model}). Error: {e}")    
    
root_agent = composition_agent