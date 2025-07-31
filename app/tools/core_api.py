import time
import urllib3
import json
from pydantic import BaseModel, Field
from app.config import CORE_API_KEY

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class CoreAPIWrapper(BaseModel):
    base_url: str = "https://api.core.ac.uk/v3"
    top_k_results: int = Field(default=1)

    def search(self, query: str) -> str:
        http = urllib3.PoolManager()
        max_retries = 5

        for attempt in range(max_retries):
            response = http.request(
                'GET',
                f"{self.base_url}/search/outputs",
                headers={"Authorization": f"Bearer {CORE_API_KEY}"},
                fields={"q": query, "limit": self.top_k_results}
            )
            if 200 <= response.status < 300:
                results = json.loads(response.data.decode("utf-8")).get("results", [])
                if not results:
                    return "No relevant results were found"
                return self.format_results(results)
            elif attempt < max_retries - 1:
                time.sleep(2 ** (attempt + 2))
        return f"Failed to fetch data. Last response: {response.status}"

    def format_results(self, results):
        formatted = []
        for r in results:
            authors = ' and '.join([a['name'] for a in r.get("authors", [])])
            formatted.append(
                f"📄 *Title:* {r.get('title')}\n"
                f"📅 *Date:* {r.get('publishedDate') or r.get('yearPublished')}\n"
                f"✍️ *Authors:* {authors}\n"
                f"🔗 *URL:* {r.get('sourceFulltextUrls') or r.get('downloadUrl')}\n"
                f"📚 *Abstract:* {r.get('abstract')}\n"
                f"{'-'*60}"
            )
        return "\n\n".join(formatted)
