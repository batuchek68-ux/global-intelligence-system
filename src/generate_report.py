import json
from datetime import datetime

with open("output/trend.json", "r", encoding="utf-8") as f:
    trend = json.load(f)

dashboard = {
    "keywords": trend["keywords"],
    "topics": [],
    "updated_at": datetime.utcnow().isoformat()
}

with open("output/dashboard.json", "w", encoding="utf-8") as f:
    json.dump(dashboard, f, indent=2)

print("Dashboard generated")
