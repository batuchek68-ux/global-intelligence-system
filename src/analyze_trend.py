import json
from collections import Counter

with open("data/raw_news.json", "r", encoding="utf-8") as f:
    news = json.load(f)

words = []

for item in news:
    title = item.get("title", "")
    words.extend(title.lower().split())

keywords = Counter(words).most_common(20)

result = {
    "keywords": keywords
}

with open("output/trend.json", "w", encoding="utf-8") as f:
    json.dump(result, f, indent=2)

print("Trend analysis complete")
