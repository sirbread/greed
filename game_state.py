from datetime import datetime, timedelta
from collections import defaultdict
import pytz

mst = pytz.timezone("America/Denver")
ROUND_DURATION = 60 #seconds

current_round = {
    "round_id": 1,
    "end_time": datetime.now(mst) + timedelta(seconds=60),
    "awaiting_submissions": [],  
    "final_submissions": [],    
}

def reset_round():
    current_round["round_id"] += 1
    current_round["end_time"] = datetime.now(mst) + timedelta(seconds=60)
    current_round["awaiting_submissions"] = []
    current_round["final_submissions"] = []

def add_awaiting_submission(user_id: int, user_name: str, number_selected: int):
    for sub in current_round["awaiting_submissions"]:
        if sub["user_id"] == user_id:
            sub["number_selected"] = number_selected
            sub["user_name"] = user_name  # in case name changed
            return
    current_round["awaiting_submissions"].append({
        "user_id": user_id,
        "user_name": user_name,
        "number_selected": number_selected
    })

def get_awaiting_submission(user_id: int):
    for sub in current_round["awaiting_submissions"]:
        if sub["user_id"] == user_id:
            return sub
    return None

def finalize_round():
    current_round["final_submissions"] = current_round["awaiting_submissions"].copy()
    current_round["awaiting_submissions"] = []

def calculate_scores():
    counts = defaultdict(int)
    for sub in current_round["final_submissions"]:
        counts[sub["number_selected"]] += 1

    results = []
    for sub in current_round["final_submissions"]:
        number = sub["number_selected"]
        count = counts[number]
        score = number / count if count > 0 else 0
        results.append({
            "user_id": sub["user_id"],
            "user_name": sub["user_name"],
            "number": number,
            "score": score
        })

    return results