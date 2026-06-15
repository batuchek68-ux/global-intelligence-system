import json
import os

with open("data/cleaned_news.json","r",encoding="utf-8") as f:
    news=json.load(f)

summaries=[]

for item in news[:50]:

    title=item["original"]

    summaries.append({
        "title":title,
        "summary":title
    })

os.makedirs("output",exist_ok=True)

with open("output/summary.json","w",encoding="utf-8") as f:
    json.dump(summaries,f,ensure_ascii=False,indent=2)

print("summary generated")
