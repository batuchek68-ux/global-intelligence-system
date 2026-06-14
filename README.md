import requests
import json
import os


def fetch_news():
    url = "https://api.gdeltproject.org/api/v2/doc/doc?query=economy&mode=ArtList&format=json"

    try:
        response = requests.get(url, timeout=20)
        data = response.json()
    except Exception as e:
        print("API error:", e)
        return

    news = []

    articles = data.get("articles", [])

    for item in articles:
        news.append({
            "title": item.get("title", ""),
            "source": item.get("sourceCountry", ""),
            "url": item.get("url", ""),
            "time": item.get("seendate", "")
        })

    os.makedirs("data", exist_ok=True)

    with open("data/raw_news.json", "w", encoding="utf-8") as f:
        json.dump(news, f, indent=2, ensure_ascii=False)

    print(f"Fetched {len(news)} news items")


if __name__ == "__main__":
    fetch_news()
