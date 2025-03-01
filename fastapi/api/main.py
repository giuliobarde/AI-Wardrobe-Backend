from fastapi import FastAPI
from pydantic import BaseModel
from huggingface import genearateOutfit

app = FastAPI()

# Health check endpoint
@app.get("/")
def healthcheck():
    return {"message": "Health check check"}

# Define request model
class ChatRequest(BaseModel):
    user_message: str

# AI Chatbot endpoint
@app.post("/chat")
def chat(request: ChatRequest):
    response = genearateOutfit(request.user_message, "40C")
    return {"response": response}
