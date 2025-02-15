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

def _filter_history(history: list[Message]) -> list[str]:
    return [
        message['text'] for message in history
        if message['role'] == 'human'
    ]

class MessageTool:
    def __init__(self, messages: list[str]):
        self.messages = messages

    def __call__(self) -> list[str]:
        """
        Returns the messages I sent in the conversation, which contain my preferences.
        """
        return _filter_history(self.messages)

async def user_preferences_agent(user_preferences: str, user_history: list[Message]) -> list[Message]:
    my_agent = build_simple_agent(name = 'agent', tools = [MessageTool(user_history)])
    my_bound_agent = MODEL_BINDER(my_agent)
    messages = [
        {
            'role': 'system',
            'text': '\n'.join([
                'You are an over-the-phone news browsing assistant and just finished a call with a user.',
                'In 4 sentences, summarize their interests and news preferences.',
                '---',
                f'Here are their old preferences: {user_preferences}',
            ]),
        },
        {
            'role': 'human',
            'text': 'What are my preferences?',
        },
    ]
    new_history = flat_messages(
        agent_name = '',
        messages = messages,
    )
    result = await my_bound_agent(noop_callback, [new_history])
    assert result['type'] == 'messages'
    return result['messages']

__all__ = [
    'user_preferences_agent',
]

