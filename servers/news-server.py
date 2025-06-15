from fastmcp import FastMCP
import requests
import os

mcp = FastMCP(name="NewsBriefMCP", host="0.0.0.0", port=8056)

# NewsAPI-KEY – für Entwicklung evtl. fest im Code oder über Umgebungsvariable
NEWSAPI_KEY = os.getenv("NEWSAPI_KEY", "0820629ca81b4f4aac665d8bb3bf6149")  # Achtung: Nicht produktiv verwenden!

def fetch_news(topic: str, max_results: int = 5):
    url = (
        "https://newsapi.org/v2/everything"
        f"?q={topic}&language=de&pageSize=10&sortBy=publishedAt&apiKey={NEWSAPI_KEY}"
    )
    response = requests.get(url)
    if response.status_code != 200:
        return [f"Fehler beim Abruf: {response.status_code}"]
    
    articles = response.json().get("articles", [])
    top_news = []

    for article in articles[:max_results]:
        title = article.get("title", "Kein Titel")
        source = article.get("source", {}).get("name", "Unbekannte Quelle")
        top_news.append(f"{title} ({source})")

    if not top_news:
        return ["Keine Nachrichten zum Thema gefunden."]
    
    return top_news

@mcp.tool()
def latest_news(topic: str) -> list[str]:
    """
    Gibt die 3–5 aktuellsten Nachrichten-Schlagzeilen zum Thema zurück.
    """
    return fetch_news(topic)

if __name__ == "__main__":
    mcp.run(transport="stdio")