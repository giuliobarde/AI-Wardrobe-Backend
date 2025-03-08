from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from auth import (
    sign_up_db, 
    sign_in_db, 
    get_session_db, 
    sign_out_db, 
    get_current_user
)
from huggingface import generateOutfit
from database import supabase  # Only needed if used in clothing endpoints
from datetime import datetime, timedelta, timezone

app = FastAPI()

# Middleware (CORS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Models
class ChatRequest(BaseModel):
    user_message: str
    temp: str

class ClothingItem(BaseModel):
    user_id: str
    item_type: str
    material: str
    color: str
    formality: str
    pattern: str
    fit: str
    suitable_for_weather: str
    suitable_for_occasion: str

class UserPreference(BaseModel):
    user_id: str
    preferred_fit: str
    preferred_colors: list
    preferred_formality: str
    preferred_patterns: list
    preferred_temperature: str

# New Models for authentication with additional fields:
class SignupUser(BaseModel):
    first_name: str
    last_name: str
    username: str
    email: str
    password: str

class SigninUser(BaseModel):
    identifier: str  # Can be either email or username
    password: str

# AI Chatbot Endpoint
@app.post("/chat/")
def chat(request: ChatRequest):
    response = generateOutfit(request.user_message, request.temp)
    return {"response": response}

# Authentication Endpoints
@app.post("/sign-up/")
async def sign_up(user: SignupUser):
    return sign_up_db(user)

@app.post("/sign-in/")
async def sign_in(user: SigninUser):
    return sign_in_db(user)

@app.get("/session/")
async def get_session(user=Depends(get_current_user)):
    return get_session_db(user)

@app.post("/sign-out/")
async def sign_out(user=Depends(get_current_user)):
    return sign_out_db(user)

# Clothing Item Endpoints
@app.post("/add_clothing_item/")
async def add_clothing_item(item: ClothingItem, user=Depends(get_current_user)):
    data, error = supabase.table("clothing_items").insert(item.dict()).execute()
    if error:
        return {"error": str(error)}
    return {"message": "Clothing item added successfully", "data": data}

@app.get("/clothing_items/")
async def get_clothing_items(user=Depends(get_current_user)):
    try:
        response = supabase.table("clothing_items").select("*").eq("user_id", user.id).execute()
        return {"data": response.data if response.data else []}
    except Exception as e:
        return {"error": f"Internal Server Error: {str(e)}"}

# User Preferences Endpoints
@app.post("/add_user_preference/")
async def add_user_preference(pref: UserPreference):
    data, error = supabase.table("user_preferences").insert(pref.dict()).execute()
    if error:
        return {"error": error}
    return {"message": "User preference added", "data": data}
