from fastapi import FastAPI

thing = FastAPI()

@thing.get("/")

def dothing():
    return {"message": "chat is this real"}