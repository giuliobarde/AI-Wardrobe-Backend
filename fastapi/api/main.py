import json
from typing import Optional, List, Dict, Any
from fastapi import FastAPI, Depends, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, field_validator
import logging

# Import your modules
from auth import (
    sign_up_db,
    sign_in_db,
    get_session_db,
    sign_out_db,
    get_current_user
)
from openai_client import (
    generateOutfit,
    setOccasion,
    ClothingItem as AIClothingItem
)
from wardrobe_db import (
    add_clothing_item_db,
    delete_clothing_item_db,
    get_user_items_db,
    get_item_by_id_db,
    get_all_user_items_db
)
from user_details import update_user_profile_db
from outfits import (
    add_saved_outfit_db,
    get_saved_outfits_db,
    delete_saved_outfit_db,
    edit_favorite_outfit_db
)
from images import set_image
from database import supabase

# Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Virtual Wardrobe API",
    description="API for managing virtual wardrobe and generating outfit suggestions",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ——— Models ———

class ChatRequest(BaseModel):
    user_message: str = Field(..., description="User's query about outfit suggestions")
    temp: str = Field(..., description="Current outside temperature")

    @field_validator('user_message')
    @classmethod
    def validate_message(cls, v):
        if len(v.strip()) < 3:
            raise ValueError("Message must be at least 3 characters")
        return v

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
    preferred_colors: List[str]
    preferred_formality: str
    preferred_patterns: List[str]
    preferred_temperature: str

class SignupUser(BaseModel):
    first_name: str
    last_name: str
    username: str
    email: str
    password: str
    gender:str

    @field_validator('password')
    @classmethod
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v

    @field_validator('email')
    @classmethod
    def validate_email(cls, v):
        if '@' not in v:
            raise ValueError("Invalid email format")
        return v

class SigninUser(BaseModel):
    identifier: str
    password: str

class DeleteByID(BaseModel):
    id: str = Field(..., description="ID of the item to delete")

class UpdateProfile(BaseModel):
    first_name: str
    last_name: str
    username: str
    gender: str

class OutfitData(BaseModel):
    user_id: str
    items: List[Dict[str, Any]]
    occasion: str
    favorite: bool = False

# ——— Global Exception Handler ———

@app.exception_handler(Exception)
async def generic_exception_handler(request, exc):
    logger.error(f"Uncaught exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An unexpected error occurred. Please try again later."}
    )

# ——— AI Chat Endpoint ———

@app.post("/chat/", response_model_exclude_none=True)
async def chat(request: ChatRequest, user=Depends(get_current_user)):
    try:
        wardrobe_resp = (
            supabase.table("clothing_items")
            .select("*")
            .eq("user_id", user.id)
            .execute()
        )
        wardrobe_items = wardrobe_resp.data or []
        if not wardrobe_items:
            return {
                "response": {
                    "occasion": "all occasions",
                    "outfit_items": [],
                    "description": "Your wardrobe is empty. Please add some items first."
                }
            }
        outfit_resp = generateOutfit(request.user_message, request.temp, wardrobe_items)
        return {"response": outfit_resp}
    except Exception as e:
        logger.error(f"Error in /chat/: {e}", exc_info=True)
        raise HTTPException(500, "Failed to generate outfit suggestion")

# ——— Auth Endpoints ———

@app.post("/sign-up/", status_code=status.HTTP_201_CREATED)
async def sign_up(user: SignupUser):
    try:
        return sign_up_db(user)
    except Exception as e:
        logger.error(f"Sign-up error: {e}", exc_info=True)
        if "already registered" in str(e).lower():
            raise HTTPException(status.HTTP_409_CONFLICT, "User already exists")
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Registration failed")

@app.post("/sign-in/")
async def sign_in(user: SigninUser):
    try:
        return sign_in_db(user)
    except Exception as e:
        logger.error(f"Sign-in error: {e}", exc_info=True)
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid credentials")

@app.get("/session/")
async def get_session(user=Depends(get_current_user)):
    return get_session_db(user)

@app.post("/sign-out/")
async def sign_out(user=Depends(get_current_user)):
    return sign_out_db(user)

# ——— Clothing Item Endpoints ———

@app.post("/add_clothing_item/", status_code=status.HTTP_201_CREATED)
async def add_clothing_item(item: ClothingItem, user=Depends(get_current_user)):
    try:
        ai_item = AIClothingItem(**item.model_dump())
        setOccasion(ai_item)
        item.suitable_for_occasion = ai_item.suitable_for_occasion
        set_image(item)
        item.user_id = user.id
        return add_clothing_item_db(item)
    except Exception as e:
        logger.error(f"Error in /add_clothing_item/: {e}", exc_info=True)
        raise HTTPException(500, "Failed to add clothing item")

@app.get("/clothing_items/")
async def get_clothing_items(
    item_type: Optional[str] = None,
    item_id: Optional[str] = Query(None, alias="id"),
    user=Depends(get_current_user)
):
    try:
        if item_id:
            return get_item_by_id_db(item_id, user)
        if item_type:
            return get_user_items_db(item_type, user)
        raise HTTPException(400, "Either item_type or item_id must be provided")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in /clothing_items/: {e}", exc_info=True)
        raise HTTPException(500, "Failed to retrieve clothing items")

@app.get("/clothing_items/all/")
async def get_all_clothing_items(user=Depends(get_current_user)):
    try:
        return get_all_user_items_db(user)
    except Exception as e:
        logger.error(f"Error in /clothing_items/all/: {e}", exc_info=True)
        raise HTTPException(500, "Failed to retrieve all clothing items")

# ——— New: Check if Item in Any Saved Outfits ———

@app.get("/check_item_in_outfits/")
async def check_item_in_outfits(
    item_id: str = Query(..., description="ID of the item to check"),
    user=Depends(get_current_user)
):
    try:
        resp = (
            supabase
            .table("saved_outfits")
            .select("id, items")
            .eq("user_id", user.id)
            .execute()
        )
        err = getattr(resp, "error", None)
        if err:
            raise HTTPException(400, f"Failed to load saved outfits: {err}")
        outfits = resp.data or []
        matches = [
            o for o in outfits
            if any(isinstance(i, dict) and i.get("id") == item_id for i in o.get("items", []))
        ]
        return {"data": matches}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in /check_item_in_outfits/: {e}", exc_info=True)
        return {"data": []}

# ——— Delete Clothing Item with Optional Cascade ———

@app.post("/delete_clothing_item/")
async def delete_clothing_item(
    data: DeleteByID,
    delete_outfits: bool = Query(False, description="Also delete saved outfits containing this item"),
    user=Depends(get_current_user)
):
    try:
        if delete_outfits:
            resp = (
                supabase
                .table("saved_outfits")
                .select("id, items")
                .eq("user_id", user.id)
                .execute()
            )
            err = getattr(resp, "error", None)
            if err:
                raise HTTPException(400, f"Failed to load saved outfits: {err}")
            outfits = resp.data or []
            to_delete_ids = [
                outfit["id"]
                for outfit in outfits
                if any(isinstance(i, dict) and i.get("id") == data.id for i in outfit.get("items", []))
            ]
            if to_delete_ids:
                del_resp = (
                    supabase
                    .table("saved_outfits")
                    .delete()
                    .in_("id", to_delete_ids)
                    .execute()
                )
                err2 = getattr(del_resp, "error", None)
                if err2:
                    raise HTTPException(400, f"Failed to delete saved outfits: {err2}")
        return delete_clothing_item_db(data.id)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in /delete_clothing_item/: {e}", exc_info=True)
        raise HTTPException(500, "Failed to delete clothing item")

# ——— Profile & Preference Endpoints ———

@app.post("/update_profile/")
async def update_user_profile(data: UpdateProfile, user=Depends(get_current_user)):
    try:
        updated = update_user_profile_db(data, user)
        return {"data": updated}
    except Exception as e:
        logger.error(f"Error in /update_profile/: {e}", exc_info=True)
        raise HTTPException(500, "Failed to update user profile")

@app.post("/add_user_preference/", status_code=status.HTTP_201_CREATED)
async def add_user_preference(pref: UserPreference):
    try:
        data, error = supabase.table("user_preferences").insert(pref.model_dump()).execute()
        if error:
            raise Exception(str(error))
        return {"message": "User preference added", "data": data}
    except Exception as e:
        logger.error(f"Error in /add_user_preference/: {e}", exc_info=True)
        raise HTTPException(500, "Failed to add user preference")

# ——— Saved Outfit Endpoints ———

@app.post("/add_saved_outfit/", status_code=status.HTTP_201_CREATED)
async def add_saved_outfit(outfit: OutfitData, user=Depends(get_current_user)):
    try:
        return add_saved_outfit_db(outfit)
    except Exception as e:
        logger.error(f"Error in /add_saved_outfit/: {e}", exc_info=True)
        raise HTTPException(500, "Failed to save outfit")

@app.get("/get_saved_outfits/")
async def get_saved_outfits(user=Depends(get_current_user)):
    try:
        return get_saved_outfits_db(user)
    except Exception as e:
        logger.error(f"Error in /get_saved_outfits/: {e}", exc_info=True)
        raise HTTPException(500, "Failed to retrieve saved outfits")

@app.post("/delete_saved_outfit/")
async def delete_saved_outfit(data: DeleteByID, user=Depends(get_current_user)):
    try:
        return delete_saved_outfit_db(data.id)
    except Exception as e:
        logger.error(f"Error in /delete_saved_outfit/: {e}", exc_info=True)
        raise HTTPException(500, "Failed to delete saved outfit")

@app.post("/edit_favorite_outfit/")
async def edit_favorite_outfit(data: DeleteByID, user=Depends(get_current_user)):
    try:
        return edit_favorite_outfit_db(data.id)
    except Exception as e:
        logger.error(f"Error in /edit_favorite_outfit/: {e}", exc_info=True)
        raise HTTPException(500, "Failed to update favorite status")
