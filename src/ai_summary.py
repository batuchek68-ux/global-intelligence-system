import json
import os

INPUT = "data/clean_news.json"
OUTPUT = "data/summary.json"

def safe_get(item):
    return item.get("title") or item.get("original") or "unknown"

def main():
    if not os.path.exists(INPUT):
        print("missing input")
        return

    with open(INPUT, "r", encoding="utf-8") as f:
        data = json.load(f)

    summary = []

    for item in data:
        title = safe_get(item)

        summary.append({
            "title": title,
            "summary": title[:120],
            "source": item.get("source", "unknown"),
            "time": item.get("time", "")
        })

    os.makedirs("data", exist_ok=True)

    with open(OUTPUT, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    print(f"[OK] saved {len(summary)} items")

if __name__ == "__main__":
    main()
