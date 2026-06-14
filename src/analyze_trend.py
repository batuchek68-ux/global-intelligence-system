import json
import os
from collections import Counter

STOPWORDS = {
    "the","is","of","and","to","in","for","on","a",
    "with","at","from","by","an","be","that","this"
}

with open("data/raw_news.json","r",encoding="utf-8") as f:
    news = json.load(f)

words = []

for item in news:
    for w in item.get("title","").lower().split():
        w = "".join(c for c in w if c.isalnum())
        if len(w) > 2 and w not in STOPWORDS:
            words.append(w)

counter = Counter(words)

top = [w for w,_ in counter.most_common(20)]

os.makedirs("output", exist_ok=True)

with open("output/trend.json","w") as f:
    json.dump({"keywords": top}, f, indent=2)

with open("output/dashboard.json","w") as f:
    json.dump({"keywords": top, "topics": top[:10]}, f, indent=2)

print("OK")
