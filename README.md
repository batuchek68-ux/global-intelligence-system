# global-intelligence-system
import requests
import json

def fetch_news():
    url = "https://api.gdeltproject.org/api/v2/doc/doc?query=economy&mode=ArtList&format=json"

    try:
        response = requests.get(url, timeout=10)
        data = response.json()
    except Exception as e:
        print("API error:", e)
        return []

    news = []

    # 更安全写法（避免结构错误）
    articles = data.get("articles") or data.get("result") or []

    for item in articles:
        news.append({
            "title": item.get("title", ""),
            "source": item.get("sourceCountry", ""),
            "url": item.get("url", ""),
            "time": item.get("seendate", "")
        })

    with open("data/raw_news.json", "w", encoding="utf-8") as f:
        json.dump(news, f, indent=2, ensure_ascii=False)

    print(f"Fetched {len(news)} news items")

if __name__ == "__main__":
    fetch_news()
