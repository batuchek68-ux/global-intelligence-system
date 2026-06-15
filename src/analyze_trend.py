import json
from collections import Counter
import re

with open("data/cleaned_news.json","r",encoding="utf-8") as f:
    news=json.load(f)

words=[]

for item in news:

    title=item["title"]

    tokens=re.findall(r"\b[a-zA-Z]{3,}\b",title)

    words.extend(tokens)

counter=Counter(words)

top=counter.most_common(30)

with open("output/trend.json","w") as f:
    json.dump({
        "top_keywords":top
    },f,indent=2)

print("trend generated")
