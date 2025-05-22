from datetime import datetime, timedelta
from collections import defaultdict
import pytz

mst = pytz.timezone("America/Denver")

ROUND_DURATION = 60  # 1 minute rounds

current_round = {
    "round_id": 1,
    "end_time": datetime.now(mst) + timedelta(seconds=ROUND_DURATION),
    "awaiting_submissions": [],
    "final_submissions": [],
}

user_totals = defaultdict(float)  # user_id -> total score

def ensure_round_current():
    now = datetime.now(mst)
    while now > current_round["end_time"]:
        finalize_round()
        reset_round()
        now = datetime.now(mst)

def reset_round():
    current_round["round_id"] += 1
    current_round["end_time"] = datetime.now(mst) + timedelta(seconds=ROUND_DURATION)
    current_round["awaiting_submissions"] = []
    current_round["final_submissions"] = []

def add_awaiting_submission(user_id: int, user_name: str, number_selected: int):
    for sub in current_round["awaiting_submissions"]:
        if sub["user_id"] == user_id:
            sub["number_selected"] = number_selected
            sub["user_name"] = user_name
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
    counts = defaultdict(int)
    for sub in current_round["awaiting_submissions"]:
        counts[sub["number_selected"]] += 1

    round_results = []
    for sub in current_round["awaiting_submissions"]:
        number = sub["number_selected"]
        count = counts[number]
        score = number / count if count > 0 else 0
        user_totals[sub["user_id"]] += score
        round_results.append({
            "user_id": sub["user_id"],
            "user_name": sub["user_name"],
            "number": number,
            "score_gained": score,
            "total_score": user_totals[sub["user_id"]]
        })
    current_round["final_submissions"] = round_results
    current_round["awaiting_submissions"] = []

def calculate_scores():
    leaderboard = []
    names = {sub["user_id"]: sub["user_name"] for sub in current_round["final_submissions"]}
    for user_id, total in user_totals.items():
        name = names.get(user_id, str(user_id))
        leaderboard.append({
            "user_id": user_id,
            "user_name": name,
            "total_score": total
        })
    leaderboard.sort(key=lambda x: -x["total_score"])
    return leaderboard