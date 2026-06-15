import json
import re
import os

RAW_FILE = "data/raw_news.json"
OUTPUT_FILE = "data/cleaned_news.json"


def clean(text):
    text = text.lower()
    text = re.sub(r"[^a-z0-9\u4e00-\u9fff ]", "", text)
    return text.strip()


def main():

    if not os.path.exists(RAW_FILE):
        print("raw_news.json not found")
        return

    with open(RAW_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    seen = set()
    cleaned = []

    for item in data:

        title = item.get("title", "")

        title_clean = clean(title)

        if title_clean in seen:
            continue

        seen.add(title_clean)

        item["clean_title"] = title_clean

        cleaned.append(item)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(
            cleaned,
            f,
            ensure_ascii=False,
            indent=2
        )

    print(f"saved {len(cleaned)} articles")


if __name__ == "__main__":
    main()
