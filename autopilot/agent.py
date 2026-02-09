import os
import logging
from google.adk.agents import Agent
from google.adk.apps import App
from google.adk.apps.app import EventsCompactionConfig
from google.adk.apps.llm_event_summarizer import LlmEventSummarizer
from google.adk.agents.context_cache_config import ContextCacheConfig
from google.adk.models import Gemini

from agents.config import (
    AGENTS,
    DESCRIPTION,
    GEMINI_2_5_FLASH,
    GEMINI_3_FLASH,
    PORT,
    PROMPT,
)

log = logging.getLogger(__name__)

A2A_ENABLED = os.getenv("ENABLE_A2A", "false").lower() == "true"
SUB_AGENT_NAMES = [name for name in AGENTS if name != "root_agent"]

def _create_remote_sub_agents() -> list[Agent]:
    """Create sub-agents using A2A remote protocol."""
    try:
        from google.adk.agents.remote_a2a_agent import (
            AGENT_CARD_WELL_KNOWN_PATH,
            RemoteA2aAgent,
        )
        
        log.info("A2A enabled: configuring remote sub-agents")
        
        # Configure the client factory to support streaming
        # TODO: Uncomment a2a_client_factory parameter when https://github.com/google/adk-python/issues/3207 is resolved
        # from a2a.client.client import ClientConfig as A2AClientConfig
        # from a2a.client.client_factory import ClientFactory as A2AClientFactory
        # from a2a.types import TransportProtocol as A2ATransport
        
        # client_config = A2AClientConfig(
        #     streaming=True,
        #     polling=False,
        #     supported_transports=[A2ATransport.jsonrpc],
        # )
        # a2a_client_factory = A2AClientFactory(config=client_config)
        
        return [
            RemoteA2aAgent(
                name=agent_name,
                description=DESCRIPTION[agent_name],
                # NOTE: k8s does not allow underscores in service names and ADK does not allow dashes in agent names
                agent_card=f"http://{agent_name.replace('_', '-')}:{PORT}{AGENT_CARD_WELL_KNOWN_PATH}",
                # a2a_client_factory=a2a_client_factory  # TODO: Uncomment when issue #3207 is resolved
            )
            for agent_name in SUB_AGENT_NAMES
        ]
    except Exception as e:
        log.error(f"Failed to create remote sub-agents: {e}")
        raise RuntimeError("Cannot initialize remote sub-agents") from e

def _create_local_sub_agents() -> list[Agent]:
    """Create sub-agents as local Agent instances."""
    try:
        from agents.auth_agent.agent import root_agent as auth_agent
        from agents.blueprint_agent.agent import root_agent as blueprint_agent
        from agents.documentation_agent.agent import root_agent as documentation_agent
        from agents.portal_agent.agent import root_agent as portal_agent
        from agents.restaction_agent.agent import root_agent as restaction_agent
        
        log.info("A2A disabled: configuring local sub-agents")
        
        return [
            auth_agent,
            blueprint_agent,
            documentation_agent,
            portal_agent,
            restaction_agent,
        ]
    except Exception as e:
        log.error(f"Failed to create local sub-agents: {e}")
        raise RuntimeError("Cannot initialize local sub-agents") from e

def create_sub_agents() -> list[Agent]:
    """Create and return sub-agents based on A2A configuration."""
    if A2A_ENABLED:
        return _create_remote_sub_agents()
    else:
        return _create_local_sub_agents()

def create_root_agent() -> Agent:
    """Initialize the root agent with sub-agents."""
    try:
        return Agent(
            model=GEMINI_2_5_FLASH,
            name="root_agent",\
            instruction=PROMPT["root_agent"],
            description=DESCRIPTION["root_agent"],
            global_instruction=PROMPT["global"],
            sub_agents=create_sub_agents(),
        )
    except Exception as e:
        log.error(f"Failed to create root_agent: {e}")
        raise RuntimeError("Cannot initialize root_agent") from e

def create_app(agent: Agent) -> App:
    """Create the ADK application with event compaction."""
    try:
        summarization_llm = Gemini(model=GEMINI_2_5_FLASH)
        summarizer = LlmEventSummarizer(llm=summarization_llm)
        compaction_config = EventsCompactionConfig(
            summarizer=summarizer,
            compaction_interval=5,
            overlap_size=1,
        )
        
        context_cache_config = ContextCacheConfig(
            min_tokens=2048,
            ttl_seconds=600,
            cache_intervals=5,
        )
        
        return App(
            name="autopilot", # https://github.com/google/adk-python/issues/3522
            root_agent=agent,
            events_compaction_config=compaction_config,
            context_cache_config=context_cache_config,
        )
    except Exception as e:
        log.error(f"Failed to create App: {e}")
        raise RuntimeError("Cannot initialize App") from e

root_agent = create_root_agent()
app = create_app(root_agent)