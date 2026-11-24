import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.intelligence import summarize

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
        text = summarize(title, title[:120])
        content, generated_by = text if isinstance(text, tuple) else (text, "rules")
        summary.append({
            "title": title,
            "summary": content,
            "generated_by": generated_by,
            "source": item.get("source", "unknown"),
            "time": item.get("time", ""),
        })

    os.makedirs("data", exist_ok=True)

    with open(OUTPUT, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    llm_count = sum(1 for s in summary if s.get("generated_by") == "llm")
    print(f"[OK] saved {len(summary)} items (llm={llm_count}, rules={len(summary) - llm_count})")


if __name__ == "__main__":
    main()
