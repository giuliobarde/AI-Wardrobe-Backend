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
from openai_client import generateOutfit, setOccasion
from wardrobe_db import (
    add_clothing_item_db,
    delete_clothing_item_db,
    get_user_items_db
)
from database import supabase
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
    sub_type: str

class UserPreference(BaseModel):
    user_id: str
    preferred_fit: str
    preferred_colors: list
    preferred_formality: str
    preferred_patterns: list
    preferred_temperature: str

class SignupUser(BaseModel):
    first_name: str
    last_name: str
    username: str
    email: str
    password: str

class SigninUser(BaseModel):
    identifier: str  # Can be either email or username
    password: str    

class DeleteItem(BaseModel):
    item_id: str



# AI Chatbot Endpoint
@app.post("/chat/")
def chat(request: ChatRequest, user=Depends(get_current_user)):
    # Retrieve wardrobe items for the current user.
    # Here we select the 'sub_type' field from each clothing item.
    wardrobe_response = supabase.table("clothing_items").select("*").eq("user_id", user.id).execute()

    # Extract wardrobe items as a list of strings.
    wardrobe_items = wardrobe_response.data if wardrobe_response.data else []

    # Call generateOutfit with the occasion message, temperature, and wardrobe items.
    outfit_response = generateOutfit(request.user_message, request.temp, wardrobe_items)
    return {"response": outfit_response}



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
    setOccasion(item)
    item.user_id = user.id
    return add_clothing_item_db(item)


@app.get("/clothing_items/")
async def get_clothing_items(item_type: str, user=Depends(get_current_user)):
    return get_user_items_db(item_type, user)

@app.post("/delete_clothing_item")
async def delete_clothing_item(data: DeleteItem):
    return delete_clothing_item_db(data.item_id)

# User Preferences Endpoints
@app.post("/add_user_preference/")
async def add_user_preference(pref: UserPreference):
    data, error = supabase.table("user_preferences").insert(pref.dict()).execute()
    if error:
        return {"error": error}
    return {"message": "User preference added", "data": data}
