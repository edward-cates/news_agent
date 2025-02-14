import json
import traceback
import requests

from lasagna import (
    Message,
    known_models,
    build_simple_agent,
    noop_callback,
    flat_messages,
)

from src.reddit_scraper import RedditScraper

MODEL_BINDER = known_models.BIND_ANTHROPIC_claude_35_sonnet()

def _check_if_user_message(message: Message) -> bool:
    return message['role'] == 'human'

def _filter_history(history: list[Message]) -> list[Message]:
    return [
        message for message in history
        if not _check_if_user_message(message)
    ]

def noop_tool() -> str:
    """
    This tool does nothing.
    """
    return "noop"

async def user_preferences_agent(user_preferences: str, history: list[Message]) -> list[Message]:
    my_agent = build_simple_agent(name = 'agent', tools = [noop_tool])
    my_bound_agent = MODEL_BINDER(my_agent)
    messages = [
        {
            'role': 'system',
            'text': '\n'.join([
                'You are an over-the-phone news browsing assistant and just finished a call with a user.',
                'In 4 sentences, summarize their interests and news preferences.',
                '---',
                f'Here are their old preferences: {user_preferences}',
                '---',
                f'Conversation history: {history}',
            ]),
        },
        {
            'role': 'human',
            'text': 'What are my preferences?',
        },
    ]
    history = flat_messages(
        agent_name = '',
        messages = messages,
    )
    result = await my_bound_agent(noop_callback, [history])
    assert result['type'] == 'messages'
    return result['messages']

__all__ = [
    'user_preferences_agent',
]
