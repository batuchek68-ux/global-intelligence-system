import json
from datetime import datetime, timezone

with open("output/trend.json") as f:
    trend=json.load(f)

with open("data/summary.json") as f:
    summary=json.load(f)

dashboard={

    "updated_at":datetime.now(timezone.utc).isoformat(),

    "top_keywords":trend["top_keywords"],

    "top_news":summary[:20]

}

with open("output/dashboard.json","w") as f:
    json.dump(dashboard,f,indent=2)

print("dashboard ready")
