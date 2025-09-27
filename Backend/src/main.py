# main.py
from fastapi import FastAPI

app = FastAPI()

# Simple GET endpoint
@app.get("/")
async def root():
    return {"message": "Hello, FastAPI!"}

# Simple POST endpoint
@app.post("/greet")
async def greet(name: str):
    return {"message": f"Hello, {name}!"}
