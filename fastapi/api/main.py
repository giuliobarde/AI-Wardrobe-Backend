from typing import Optional, List, Dict, Any
from fastapi import FastAPI, Depends, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, field_validator
import logging

# Import modules from our application
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
from user_details import (
    update_user_profile_db
)
from outfits import (
    add_saved_outfit_db,
    get_saved_outfits_db,
    delete_saved_outfit_db,
    edit_favorite_outfit_db
)
from images import set_image
from database import supabase

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Virtual Wardrobe API",
    description="API for managing virtual wardrobe and generating outfit suggestions",
    version="1.0.0"
)

# Middleware setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models with enhanced validation using field_validator
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
    user_id: str = Field(..., description="User ID who owns this item")
    item_type: str = Field(..., description="General category of the item")
    material: str = Field(..., description="Material the item is made of")
    color: str = Field(..., description="Primary color of the item")
    formality: str = Field(..., description="Formality level of the item")
    pattern: str = Field(..., description="Pattern on the item")
    fit: str = Field(..., description="How the item fits")
    suitable_for_weather: str = Field(..., description="Weather conditions the item suits")
    suitable_for_occasion: str = Field(..., description="Occasions the item is suitable for")
    sub_type: str = Field(..., description="Specific type of the item")
    image_link: Optional[str] = Field(None, description="URL to image of the item")

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
    identifier: str  # Can be either email or username
    password: str

class DeleteByID(BaseModel):
    id: str = Field(..., description="ID of the item to delete")

class UpdateProfile(BaseModel):
    first_name: str
    last_name: str
    username: str

class OutfitData(BaseModel):
    user_id: str
    items: List[Dict[str, Any]]
    occasion: str
    favorite: bool = False

# Exception handler
@app.exception_handler(Exception)
async def generic_exception_handler(request, exc):
    logger.error(f"Uncaught exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An unexpected error occurred. Please try again later."}
    )

# AI Chatbot Endpoint
@app.post("/chat/", response_model_exclude_none=True)
async def chat(request: ChatRequest, user=Depends(get_current_user)):
    """
    Generate outfit suggestions based on user query and temperature
    """
    try:
        wardrobe_response = supabase.table("clothing_items").select("*").eq("user_id", user.id).execute()
        wardrobe_items = wardrobe_response.data if wardrobe_response.data else []
        
        if not wardrobe_items:
            return {"response": {
                "occasion": "all occasions",
                "outfit_items": [],
                "description": "Your wardrobe is empty. Please add some items first."
            }}
        
        outfit_response = generateOutfit(request.user_message, request.temp, wardrobe_items)
        return {"response": outfit_response}
    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate outfit suggestion"
        )

# Authentication Endpoints
@app.post("/sign-up/", status_code=status.HTTP_201_CREATED)
async def sign_up(user: SignupUser):
    """Register a new user"""
    try:
        return sign_up_db(user)
    except Exception as e:
        logger.error(f"Sign-up error: {e}", exc_info=True)
        if "already registered" in str(e).lower():
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User already exists")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Registration failed")

@app.post("/sign-in/")
async def sign_in(user: SigninUser):
    """Sign in an existing user"""
    try:
        return sign_in_db(user)
    except Exception as e:
        logger.error(f"Sign-in error: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

@app.get("/session/")
async def get_session(user=Depends(get_current_user)):
    """Get current user session"""
    return get_session_db(user)

@app.post("/sign-out/")
async def sign_out(user=Depends(get_current_user)):
    """Sign out current user"""
    return sign_out_db(user)

# Clothing Item Endpoints
@app.post("/add_clothing_item/", status_code=status.HTTP_201_CREATED)
async def add_clothing_item(item: ClothingItem, user=Depends(get_current_user)):
    """Add a new clothing item to the user's wardrobe"""
    try:
        # Convert to AIClothingItem for AI processing
        ai_item = AIClothingItem(
            user_id=item.user_id,
            item_type=item.item_type,
            material=item.material,
            color=item.color,
            formality=item.formality,
            pattern=item.pattern,
            fit=item.fit,
            suitable_for_weather=item.suitable_for_weather,
            suitable_for_occasion=item.suitable_for_occasion,
            sub_type=item.sub_type,
            image_link=item.image_link,
        )
        
        # Update with AI-determined occasions
        setOccasion(ai_item)
        # Transfer back to our item
        item.suitable_for_occasion = ai_item.suitable_for_occasion
        
        # Generate and set image
        set_image(item)
        
        # Ensure user_id is set correctly
        item.user_id = user.id
        
        return add_clothing_item_db(item)
    except Exception as e:
        logger.error(f"Error adding clothing item: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to add clothing item"
        )

@app.get("/clothing_items/")
async def get_clothing_items(
    item_type: str = None, 
    item_id: str = Query(None, alias="id"), 
    user=Depends(get_current_user)
):
    """Get clothing items by type or ID"""
    try:
        if item_id:
            return get_item_by_id_db(item_id, user)
        elif item_type:
            return get_user_items_db(item_type, user)
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail="Either item_type or item_id must be provided"
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting clothing items: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve clothing items"
        )

@app.get("/clothing_items/all/")
async def get_all_clothing_items(user=Depends(get_current_user)):
    """Get all clothing items for the current user"""
    try:
        return get_all_user_items_db(user)
    except Exception as e:
        logger.error(f"Error getting all clothing items: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve all clothing items"
        )

@app.post("/delete_clothing_item/")
async def delete_clothing_item(data: DeleteByID):
    """Delete a clothing item by ID"""
    try:
        return delete_clothing_item_db(data.id)
    except Exception as e:
        logger.error(f"Error deleting clothing item: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete clothing item"
        )

# User Endpoints
@app.post("/update_profile/")
async def update_user_profile(data: UpdateProfile, user=Depends(get_current_user)):
    """Update user profile information"""
    try:
        updated_user = update_user_profile_db(data, user)
        return {"data": updated_user}
    except Exception as e:
        logger.error(f"Error updating profile: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user profile"
        )

@app.post("/add_user_preference/", status_code=status.HTTP_201_CREATED)
async def add_user_preference(pref: UserPreference):
    """Add or update user style preferences"""
    try:
        data, error = supabase.table("user_preferences").insert(pref.model_dump()).execute()
        if error:
            raise Exception(str(error))
        return {"message": "User preference added", "data": data}
    except Exception as e:
        logger.error(f"Error adding user preference: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to add user preference"
        )

# Outfit Endpoints
@app.post("/add_saved_outfit/", status_code=status.HTTP_201_CREATED)
async def add_saved_outfit(outfit: OutfitData):
    """Save a generated outfit"""
    try:
        return add_saved_outfit_db(outfit)
    except Exception as e:
        logger.error(f"Error saving outfit: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save outfit"
        )

@app.get("/get_saved_outfits/")
async def get_saved_outfits(user=Depends(get_current_user)):
    """Get all saved outfits for the current user"""
    try:
        return get_saved_outfits_db(user)
    except Exception as e:
        logger.error(f"Error getting saved outfits: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve saved outfits"
        )

@app.post("/delete_saved_outfit/")
async def delete_saved_outfit(data: DeleteByID):
    """Delete a saved outfit by ID"""
    try:
        return delete_saved_outfit_db(data.id)
    except Exception as e:
        logger.error(f"Error deleting saved outfit: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete saved outfit"
        )

@app.post("/edit_favorite_outfit/")
async def edit_favorite_outfit(data: DeleteByID):
    """Toggle the favorite status of a saved outfit"""
    try:
        return edit_favorite_outfit_db(data.id)
    except Exception as e:
        logger.error(f"Error updating favorite status: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update favorite status"
        )