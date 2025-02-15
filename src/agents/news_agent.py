import json
import traceback
import requests
from bs4 import BeautifulSoup

from lasagna import (
    Message,
    known_models,
    build_simple_agent,
    noop_callback,
    flat_messages,
)

from src.reddit_scraper import RedditScraper
from src.agents.tool_call_filter import ToolCallFilter

MODEL_BINDER = known_models.BIND_ANTHROPIC_claude_35_sonnet()

"""
Use this tool to list all of today's news headlines, which
are typically one sentence, plus a link to the article.

:param: news_type: str: The type of news to get.
"""

def _get_todays_headlines() -> str:
    """
    Use this tool to list all of today's news headlines, which
    are typically one sentence, plus a link to the article.
    """
    try:
        headlines: list[dict] = RedditScraper().get_stories(limit=20)
        print("Got headlines.")
        headlines_str = json.dumps(headlines)
    except Exception as e:
        traceback.print_exc()
        raise e
    return headlines_str

def _get_article_html(url: str) -> str:
    """
    Use this tool to get the HTML of an article.

    :param: url: str: The URL of the article to get.
    """
    try:
        response = requests.get(url)
        # Strip HTML tags and limit to 10k chars
        soup = BeautifulSoup(response.text, 'html.parser')
        text = soup.get_text(separator=' ', strip=True)
        print(f"Success getting article: {text[:10000]}")
        return text[:10000]
    except Exception as e:
        traceback.print_exc()
        raise e

async def news_agent(
    user_preferences: str,
    todays_headlines: str,
    history: list[Message],
) -> list[Message]:
    my_agent = build_simple_agent(name = 'agent', tools = [
        # _get_todays_headlines,
        _get_article_html,
    ])
    my_bound_agent = MODEL_BINDER(my_agent)
    system_prompt = {
        'role': 'system',
        'text': '\n'.join([
            'You are an over-the-phone news browsing assistant. DO NOT USE BULLET LISTS! Just 3 consecutive sentences.',
            '---',
            f'Today\'s headlines: {todays_headlines}',
            '---',
            f'User preferences: {user_preferences}',
        ]),
    }
    filtered_history = ToolCallFilter(function_name='_get_article_html').filter(history)
    print(f"[debug:news_agent] {len(history)=}, {len(filtered_history)=}")
    history = flat_messages(
        agent_name = '',
        messages = [system_prompt, *filtered_history],
    )
    result = await my_bound_agent(noop_callback, [history])
    assert result['type'] == 'messages'
    return result['messages']

__all__ = [
    'news_agent', '_get_todays_headlines'
]
