import json
import os

INPUT = "data/clean_news.json"
OUTPUT = "output/summary.json"

if not os.path.exists(INPUT):
    print("clean_news.json not found")
    exit()

with open(INPUT, "r", encoding="utf-8") as f:
    data = json.load(f)

summary = []

for item in data:
    title = item.get("title") or item.get("original") or ""

    if not title:
        continue

    summary.append({
        "title": title,
        "summary": title[:120]
    })
        "title": title,
        "summary": title[:120]
    })

os.makedirs("output", exist_ok=True)

with open(OUTPUT, "w", encoding="utf-8") as f:
    json.dump(summary, f, ensure_ascii=False, indent=2)

print(f"saved {len(summary)} summaries")
