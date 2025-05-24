from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from game_state import (
    add_awaiting_submission,
    calculate_scores,
    current_round,
    reset_round,
    finalize_round,
    get_awaiting_submission,
    ensure_round_current,
    round_history,
    get_winner_info,
    WINNING_SCORE,
)
from graphs import generate_round_graphs
from datetime import datetime
import pytz
import os
from fastapi.staticfiles import StaticFiles

app = FastAPI()
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

mst = pytz.timezone("America/Denver")

last_winner_info = {"winner": False}
last_checked_round_id = 1

class Submission(BaseModel):
    user_id: int
    user_name: str
    number_selected: int

@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "winning_score": WINNING_SCORE})

@app.get("/help", response_class=HTMLResponse)
def help_page(request: Request):
    return templates.TemplateResponse("help.html", {"request": request})

@app.post("/submit/")
def submit(data: Submission):
    ensure_round_current()
    add_awaiting_submission(data.user_id, data.user_name, data.number_selected)
    return {"status": "submitted"}

@app.get("/scores/")
def scores():
    ensure_round_current()
    return calculate_scores()

@app.get("/round/")
def get_round_info():
    global last_winner_info, last_checked_round_id
    ensure_round_current()
    now = datetime.now(mst)
    remaining = current_round["end_time"] - now
    total_seconds = int(remaining.total_seconds())
    if total_seconds < 0:
        total_seconds = 0

    if last_checked_round_id != current_round["round_id"]:
        last_winner_info = get_winner_info()
        last_checked_round_id = current_round["round_id"]

    return {
        "round_id": current_round["round_id"],
        "time_left_seconds": total_seconds
    }

@app.get("/awaiting/")
def awaiting(user_id: int):
    ensure_round_current()
    sub = get_awaiting_submission(user_id)
    if sub:
        return {"user_id": sub["user_id"], "number_selected": sub["number_selected"]}
    else:
        return {}

@app.get("/awaiting/all")
def all_awaiting():
    ensure_round_current()
    return current_round["awaiting_submissions"]

@app.get("/final/all")
def all_final():
    ensure_round_current()
    return current_round["final_submissions"]

@app.get("/graphs", response_class=HTMLResponse)
def get_graphs(request: Request):
    min_num = 0
    max_num = 11
    image_filenames = generate_round_graphs(round_history, min_num, max_num)
    images = [(fname, idx + 1) for idx, fname in enumerate(image_filenames)]
    return templates.TemplateResponse("graphs.html", {"request": request, "images": images})

@app.get("/winner/")
def winner():
    return last_winner_info