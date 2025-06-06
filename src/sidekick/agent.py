"""
Simplified agent functionality for Sidekick CLI.
"""

from pydantic_ai import Agent

from sidekick.tools import TOOLS
from sidekick.types import SessionState
from sidekick.ui import agent_output


def get_or_create_agent(model: str, session: SessionState):
    """Get or create an agent instance for the given model."""
    if model not in session.agents:
        session.agents[model] = Agent(
            model=model,
            tools=TOOLS,
        )
    return session.agents[model]


async def process_request(model: str, message: str, session: SessionState):
    """Process a user request with the agent."""
    agent = get_or_create_agent(model, session)

    # Use message history if available
    message_history = session.messages.copy() if session.messages else []

    # Run the agent
    result = await agent.run(message, message_history=message_history)

    # Store messages for context
    if hasattr(result, "_all_messages"):
        session.messages.extend(result._all_messages)

    # Display the response
    if result.data:
        await agent_output(result.data)
