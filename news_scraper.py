import asyncio
import os
from typing import Dict, List
import httpx
from aiolimiter import AsyncLimiter
from tenacity import retry, stop_after_attempt, wait_exponential
from dotenv import load_dotenv
from utils import summarize_with_anthropic_news_script

load_dotenv()


class NewsScraper:
    _rate_limiter = AsyncLimiter(5, 1)  # 5 requests/second
    SERPER_ENDPOINT = "https://google.serper.dev/search"

    def __init__(self):
        self.api_key = os.getenv("SERPER_API_KEY")
        if not self.api_key:
            raise ValueError("Missing SERPER_API_KEY in environment")
        self.headers = {
            "X-API-KEY": self.api_key,
            "Content-Type": "application/json"
        }

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    async def scrape_news(self, topics: List[str]) -> Dict[str, str]:
        """Fetch and summarize news articles using Serper API"""
        results = {}

        async with httpx.AsyncClient(timeout=20) as client:
            for topic in topics:
                async with self._rate_limiter:
                    try:
                        payload = {"q": topic, "num": 10}
                        response = await client.post(
                            self.SERPER_ENDPOINT,
                            headers=self.headers,
                            json=payload
                        )
                        response.raise_for_status()
                        data = response.json()

                        # Extract titles/snippets from Serper's news or organic results
                        items = data.get("news") or data.get("organic") or []
                        headlines = [
                            f"{item.get('title', '')}: {item.get('snippet', '')}"
                            for item in items
                        ]
                        combined_headlines = " ".join(headlines[:10])

                        # Summarize with Anthropic
                        summary = summarize_with_anthropic_news_script(
                            api_key=os.getenv("ANTHROPIC_API_KEY"),
                            headlines=combined_headlines
                        )

                        results[topic] = summary or "No summary generated."
                    except Exception as e:
                        results[topic] = f"Error: {str(e)}"

                    await asyncio.sleep(1)  # gentle pacing between topics

        return {"news_analysis": results}

# if __name__ == "__main__":
#     import asyncio

#     async def test_serper():
#         scraper = NewsScraper()
#         result = await scraper.scrape_news(["Bihar elections"])
#         print("\n📰 Test Output:\n", result)

#     asyncio.run(test_serper())
