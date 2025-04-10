from typing import Optional
from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from auth import (
    sign_up_db, 
    sign_in_db, 
    get_session_db, 
    sign_out_db, 
    get_current_user
)
from openai_client import (
    generateOutfit, 
    setOccasion
)
from wardrobe_db import (
    add_clothing_item_db,
    delete_clothing_item_db,
    get_user_items_db,
    get_item_by_id_db,
    get_all_user_items_db
)
from user_details import (
    update_user_profile_db
)
from outfits import (
    add_saved_outfit_db
)
from images import set_image
from database import supabase
from typing import List, Dict

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
    image_link: Optional[str] = None

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

class UpdateProfile(BaseModel):
    first_name: str
    last_name: str
    username: str

class OutfitData(BaseModel):
    user_id: str
    items: List[Dict]
    occasion: str
    favourite: bool = False

# AI Chatbot Endpoint
@app.post("/chat/")
def chat(request: ChatRequest, user=Depends(get_current_user)):
    wardrobe_response = supabase.table("clothing_items").select("*").eq("user_id", user.id).execute()
    wardrobe_items = wardrobe_response.data if wardrobe_response.data else []
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
    set_image(item)
    item.user_id = user.id
    return add_clothing_item_db(item)

@app.get("/clothing_items/")
async def get_clothing_items(
    item_type: str = None, 
    item_id: str = Query(None, alias="id"), 
    user=Depends(get_current_user)
):
    if item_id:
        return get_item_by_id_db(item_id, user)
    elif item_type:
        return get_user_items_db(item_type, user)
    else:
        raise HTTPException(status_code=400, detail="Either item_type or item_id must be provided.")

@app.get("/clothing_items/all/")
async def get_all_clothing_items(user=Depends(get_current_user)):
    return get_all_user_items_db(user)

@app.post("/delete_clothing_item/")
async def delete_clothing_item(data: DeleteItem):
    return delete_clothing_item_db(data.item_id)

# User Endpoints
@app.post("/update_profile/")
async def update_user_profile(data: UpdateProfile, user=Depends(get_current_user)):
    updated_user = update_user_profile_db(data, user)
    return {"data": updated_user}

@app.post("/add_user_preference/")
async def add_user_preference(pref: UserPreference):
    data, error = supabase.table("user_preferences").insert(pref.model_dump()).execute()
    if error:
        return {"error": error}
    return {"message": "User preference added", "data": data}

# Outfit Endpoints
@app.post("/add_saved_outfit/")
async def add_saved_outfit(outfit: OutfitData):
    return add_saved_outfit_db(outfit)

@app.post("/remove_saved_outfit/")
async def remove_saved_outfit():
    return

@app.post("/edit_favourite_outfit/")
async def edit_favourite_outfit():
    return

@app.get("/get_favourite_outfits/")
async def get_favourite_outfits():
    return