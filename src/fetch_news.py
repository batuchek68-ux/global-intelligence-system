import feedparser
import json
import os

RSS_URL = "https://news.google.com/rss?hl=en-US&gl=US&ceid=US:en"

feed = feedparser.parse(RSS_URL)

articles = []

for entry in feed.entries[:50]:
    articles.append({
        "title": entry.title,
        "link": entry.link,
        "published": getattr(entry, "published", "")
    })

os.makedirs("data", exist_ok=True)

with open("data/raw_news.json", "w", encoding="utf-8") as f:
    json.dump(articles, f, indent=2, ensure_ascii=False)

print(f"Saved {len(articles)} articles")
