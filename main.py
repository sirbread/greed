from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi import Request
from pydantic import BaseModel
from game_state import (
    add_submission,
    calculate_scores,
    current_round,
    reset_round
)
from datetime import datetime
import pytz

app = FastAPI()
templates = Jinja2Templates(directory="templates")

mst = pytz.timezone("America/Denver")

class Submission(BaseModel):
    user_id: int
    user_name: str
    number_selected: int

@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/submit/")
def submit(data: Submission):
    now = datetime.now(mst)
    if now > current_round["end_time"]:
        reset_round()
    add_submission(data.user_id, data.user_name, data.number_selected)
    return {"status": "submitted"}

@app.get("/scores/")
def scores():
    return calculate_scores()

@app.get("/round/")
def get_round_info():
    now = datetime.now(mst)
    remaining = current_round["end_time"] - now
    return {
        "round_id": current_round["round_id"],
        "time_left_minutes": int(remaining.total_seconds() // 60)
    }