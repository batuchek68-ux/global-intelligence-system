import json
import os
from collections import Counter

INPUT = "data/clean_news.json"
OUTPUT = "data/trends.json"

def main():

    if not os.path.exists(INPUT):
        print("[ERROR] clean_news.json not found - run preprocess first")
        return

    with open(INPUT, "r", encoding="utf-8") as f:
        data = json.load(f)

    words = []

    for item in data:
        title = item.get("clean_title") or item.get("title") or item.get("original") or ""
        words += title.lower().split()

    top = Counter(words).most_common(20)

    os.makedirs("data", exist_ok=True)

    with open(OUTPUT, "w", encoding="utf-8") as f:
        json.dump(top, f, ensure_ascii=False, indent=2)

    print(f"[OK] trends saved: {len(top)} items")

if __name__ == "__main__":
    main()
