import json
import os
from collections import Counter

INPUT_FILE = "data/raw_news.json"
OUTPUT_FILE = "output/trend.json"
DASHBOARD_FILE = "output/dashboard.json"


def analyze():

    if not os.path.exists(INPUT_FILE):
        print("No raw_news.json found")
        return

    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        news = json.load(f)

    words = []

    for item in news:
        title = item.get("title", "")
        words.extend(title.lower().split())

    counter = Counter(words)

    top_keywords = counter.most_common(20)

    trend_data = {
        "keywords": top_keywords
    }

    os.makedirs("output", exist_ok=True)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(trend_data, f, indent=2)

    dashboard_data = {
        "keywords": top_keywords,
        "topics": [
            {
                "name": k,
                "count": v
            }
            for k, v in top_keywords[:10]
        ],
        "updated_at": str(__import__("datetime").datetime.utcnow())
    }

    with open(DASHBOARD_FILE, "w", encoding="utf-8") as f:
        json.dump(
            dashboard_data,
            f,
            indent=2,
            ensure_ascii=False
        )

    print("Dashboard generated")


if __name__ == "__main__":
    analyze()
