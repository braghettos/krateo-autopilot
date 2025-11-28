import os
from google.adk.agents import Agent
from remote_agents.config import *

a2a_enabled = os.getenv("ENABLE_A2A", "false").lower() == "true"

if a2a_enabled:
    from google.adk.agents.remote_a2a_agent import AGENT_CARD_WELL_KNOWN_PATH
    from google.adk.agents.remote_a2a_agent import RemoteA2aAgent
    from a2a.client.client import ClientConfig as A2AClientConfig
    from a2a.client.client_factory import ClientFactory as A2AClientFactory
    from a2a.types import TransportProtocol as A2ATransport

    # Configure the client factory to support streaming
    client_config = A2AClientConfig(
        streaming=True,
        polling=False,
        supported_transports=[A2ATransport.jsonrpc],
    )
    a2a_client_factory = A2AClientFactory(config=client_config)

    sub_agents = [
        RemoteA2aAgent(
            name=agent_name,
            description=DESCRIPTION[agent_name],
            # NOTE: k8s does not allow underscores in service names and ADK does not allow dashes in agent names
            agent_card=f"http://{agent_name.replace("_","-")}:{PORT}{AGENT_CARD_WELL_KNOWN_PATH}",
            # a2a_client_factory=a2a_client_factory # TODO: Uncomment when `https://github.com/google/adk-python/issues/3207` is resolved
        )
        for agent_name in AGENTS
        if agent_name != "root_agent"   
    ]

    root_agent = Agent(
        model=GEMINI_2_5_FLASH,
        name="root_agent",
        instruction=PROMPT["root_agent"],
        description=DESCRIPTION["root_agent"],
        global_instruction=PROMPT["global"],
        sub_agents=sub_agents
    )
else:
    from remote_agents.auth_agent.agent import root_agent as auth_agent
    from remote_agents.blueprint_agent.agent import root_agent as blueprint_agent
    from remote_agents.documentation_agent.agent import root_agent as documentation_agent
    from remote_agents.portal_agent.agent import root_agent as portal_agent
    from remote_agents.restaction_agent.agent import root_agent as restaction_agent
    
    sub_agents = [
        auth_agent,
        blueprint_agent,
        documentation_agent,
        portal_agent,
        restaction_agent
    ]
    
root_agent = Agent(
        model=GEMINI_2_5_FLASH,
        name="root_agent",
        instruction=PROMPT["root_agent"],
        description=DESCRIPTION["root_agent"],
        global_instruction=PROMPT["global"],
        sub_agents=sub_agents
)