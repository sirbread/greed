from datetime import datetime, timedelta
from collections import defaultdict
import pytz

mst = pytz.timezone("America/Denver")

ROUND_DURATION = 10  #seconds
WINNING_SCORE = 100  #points to win
GAME_START_TIME = datetime.now(mst) + timedelta(minutes=0.15) #change to days=x when !testing 

current_round = {
    "round_id": 1,
    "end_time": datetime.now(mst) + timedelta(seconds=ROUND_DURATION),
    "awaiting_submissions": [],
    "final_submissions": [],
}

user_names = {} 

user_totals = defaultdict(float)  
round_history = []  

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
    user_names[user_id] = user_name
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
    round_history.append({
        "counts": dict(counts),
        "final_submissions": list(round_results)
    })
    current_round["awaiting_submissions"] = []

def calculate_scores():
    leaderboard = []
    for user_id, total in user_totals.items():
        name = user_names.get(user_id, str(user_id))
        leaderboard.append({
            "user_id": user_id,
            "user_name": name,
            "total_score": total
        })
    leaderboard.sort(key=lambda x: -x["total_score"])
    return leaderboard

def get_winner_info():
    for user_id, total in user_totals.items():
        if total >= WINNING_SCORE:
            name = user_names.get(user_id, str(user_id))
            return {
                "winner": True,
                "user_id": user_id,
                "user_name": name,
                "score": total
            }
    return {"winner": False}

def get_greed_rate(user_id):
    total = 0
    count = 0
    for rnd in round_history:
        for sub in rnd.get("final_submissions", []):
            if sub["user_id"] == user_id:
                total += sub["number"]
                count += 1
    return total / count if count else 0