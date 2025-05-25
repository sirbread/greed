from fastapi import FastAPI, Request, Header, HTTPException, status, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from dotenv import load_dotenv
import os

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
    ROUND_DURATION,
)
from graphs import generate_round_graphs
from datetime import datetime
import pytz
from fastapi.staticfiles import StaticFiles

import firebase_admin
from firebase_admin import auth as firebase_auth, credentials

import db 
import re

load_dotenv()

FIREBASE_ADMINSDK_JSON = os.getenv("FIREBASE_ADMINSDK_JSON")

cred = credentials.Certificate(FIREBASE_ADMINSDK_JSON)
firebase_admin.initialize_app(cred)

app = FastAPI()
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

mst = pytz.timezone("America/Denver")

last_winner_info = {"winner": False}
last_checked_round_id = 1

class Submission(BaseModel):
    number_selected: int

class UsernameRequest(BaseModel):
    username: str

def verify_firebase_token(authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing or invalid Authorization header")
    token = authorization.split(" ", 1)[1]
    try:
        decoded_token = firebase_auth.verify_id_token(token)
        return decoded_token
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Firebase ID token")

def get_db():
    db_session = db.SessionLocal()
    try:
        yield db_session

    finally:
            db_session.close()

@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("index.html", {
        "request": request,
        "winning_score": WINNING_SCORE,
        "firebase_api_key": os.getenv("FIREBASE_API_KEY"),
        "firebase_auth_domain": os.getenv("FIREBASE_AUTH_DOMAIN"),
        "firebase_project_id": os.getenv("FIREBASE_PROJECT_ID"),
        "firebase_storage_bucket": os.getenv("FIREBASE_STORAGE_BUCKET"),
        "firebase_messaging_sender_id": os.getenv("FIREBASE_MESSAGING_SENDER_ID"),
        "firebase_app_id": os.getenv("FIREBASE_APP_ID"),
    })

@app.get("/help", response_class=HTMLResponse)
def help_page(request: Request):
    return templates.TemplateResponse("help.html", {"request": request})

@app.post("/submit/")
def submit(data: Submission, user=Depends(verify_firebase_token)):
    ensure_round_current()
    user_id = user["uid"]
    user_name = user.get("name") or user.get("email") or "Anonymous"
    add_awaiting_submission(user_id, user_name, data.number_selected)
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
def awaiting(user_id: str):
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
    min_num = 1
    max_num = 10
    image_filenames = generate_round_graphs(round_history, min_num, max_num)
    images = [(fname, idx + 1) for idx, fname in enumerate(image_filenames)]
    return templates.TemplateResponse("graphs.html", {"request": request, "images": images})

@app.get("/winner/")
def winner():
    return last_winner_info

@app.get("/config/")
def get_config():
    return {"round_duration_seconds": ROUND_DURATION}

@app.post("/set-username/")
def set_username(req: UsernameRequest, user = Depends(verify_firebase_token), db_session=Depends(get_db)):
    username = req.username.strip()
