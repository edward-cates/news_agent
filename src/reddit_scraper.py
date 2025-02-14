import requests

class RedditScraper:
    """
    Scrape today's news stories from r/news.
    I want: the story title, and the link to the story.
    """
    
    def __init__(self):
        self.subreddit = "news"
        self.base_url = f"https://www.reddit.com/r/{self.subreddit}/hot.json"

    def get_stories(self, limit: int) -> list[dict]:
        """Get top news stories from r/news"""

        print("Getting news stories from Reddit.")

        stories = []
        headers = {
            'User-Agent': 'python:my.newsletter.app:v1.0.0 (by /u/Previous-Speaker2779)'
        }

        url = f"{self.base_url}?limit={limit}"
        response = requests.get(url, headers=headers)
            
        if response.status_code != 200:
            raise Exception(f"Failed to fetch data: {response.status_code}")

        data = response.json()
        posts = data['data']['children']
        
        for post in posts:
            data = post['data']
            if not data['stickied']:  # Skip stickied posts
                stories.append({
                    'title': data['title'],
                    'url': data['url']
                })
            
        return stories

def ingest_reddit_daily_news(limit: int = 20):
    scraper = RedditScraper()
    scraper.ingest_daily_news(limit=limit)

if __name__ == "__main__":
    print(
        RedditScraper().get_stories(limit=20)
    )
