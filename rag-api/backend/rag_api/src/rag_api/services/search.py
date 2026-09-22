import os
import requests
from dotenv import load_dotenv

load_dotenv()
SERPER_API_KEY = os.getenv("SERPER_API_KEY")

def web_search(query: str, num_results: int = 3) -> tuple[str, list[str]]:
    if not SERPER_API_KEY:
        return "", []
    
    try:
        response = requests.post(
            "https://google.serper.dev/search",
            headers={"X-API-KEY": SERPER_API_KEY},
            json={"q": query}
        )
        data = response.json()
        
        results = []
        links = []
        
        if "organic" in data:
            for item in data["organic"][:num_results]:
                results.append(f"Title: {item.get('title', '')}\nSnippet: {item.get('snippet', '')}")
                links.append(item.get("link", ""))
        
        return "\n\n".join(results), links
    
    except Exception:
        return "", []