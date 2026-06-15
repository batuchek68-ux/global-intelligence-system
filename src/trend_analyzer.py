from collections import Counter
import json

INPUT = "data/clean_news.json"
OUTPUT = "data/trends.json"

def main():
    with open(INPUT, "r", encoding="utf-8") as f:
        data = json.load(f)

    words = []

    for item in data:
        title = item.get("title") or item.get("original") or ""
        words += title.lower().split()

    top = Counter(words).most_common(20)

    with open(OUTPUT, "w", encoding="utf-8") as f:
        json.dump(top, f, ensure_ascii=False, indent=2)

    print("trend built")

if __name__ == "__main__":
    main()
