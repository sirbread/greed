from datetime import datetime, timedelta
from collections import defaultdict
import pytz

mst = pytz.timezone("America/Denver")

current_round = {
    "round_id": 1,
    "end_time": datetime.now(mst) + timedelta(hours=5),
    "submissions": []
}

def reset_round():
    current_round["round_id"] += 1
    current_round["end_time"] = datetime.now(mst) + timedelta(hours=5)
    current_round["submissions"] = []

def add_submission(user_id: int, user_name: str, number_selected: int):
    current_round["submissions"].append({
        "user_id": user_id,
        "user_name": user_name,
        "number_selected": number_selected
    })

def calculate_scores():
    counts = defaultdict(int)
    for sub in current_round["submissions"]:
        counts[sub["number_selected"]] += 1

    results = []
    for sub in current_round["submissions"]:
        number = sub["number_selected"]
        count = counts[number]
        score = number / count
        results.append({
            "user_id": sub["user_id"],
            "user_name": sub["user_name"],
            "number": number,
            "score": score
        })

    return results
