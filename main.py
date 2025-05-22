from fastapi import FastAPI
from pydantic import BaseModel
from game_state import add_submission, calculate_scores, current_round, reset_round

from datetime import datetime
from zoneinfo import ZoneInfo

mst = ZoneInfo("America/Denver")

app = FastAPI()

class Submission(BaseModel):
    user_id: int
    user_name: str
    number_selected: int

@app.post("/submit/")
def submit(data: Submission):
    now = datetime.now(mst)
    if now > current_round["end_time"]:
        reset_round()
    add_submission(data.user_id, data.user_name, data.number_selected)
    return {"status": "submitted"}

@app.get("/scores/")
def get_scores():
    return calculate_scores()
@app.get("/round/")
def get_round_info():
    return {
        "round_id": current_round["id"],
        "time_left_minutes": max(0,int((current_round["end_time"]-datetime.now(mst)).total_seconds()//60))
    }