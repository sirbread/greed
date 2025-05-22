from collections import defaultdict
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

mst = ZoneInfo("America/Denver")
#print(datetime.now(mst))

current_round = {
    "id": 1,
    "start_time": datetime.now(mst),
    "end_time": datetime.now(mst) + timedelta(hours=5),
    "submissions": []
}

def add_submission(user_id: int, number_selected: int):
    current_round["submissions"].append({
        "user_id": user_id,
        "number_selected": number_selected

    })

def calculate_scores():
    counts = defaultdict(int)
    for sub in current_round["submissions"]:
        counts[sub["number_selected"]] += 1

    results = []
    for sub in current_round["submissions"]:
        number = sub["number_selected"]
        count = counts [number]
        score = number/count
        results.append({
            "user_id": sub["user_id"],
            "number": number,
            "score": score
        })

    return results

def reset_round():
    current_round["id"] += 1
    current_round["start_time"] = datetime.now(mst)
    current_round["end_time"] = datetime.now(mst) + timedelta(hours=5) #adjust here later for another time mayhaps
    current_round["submissions"] = []
    
    