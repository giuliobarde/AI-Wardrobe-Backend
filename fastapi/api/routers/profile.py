from fastapi import APIRouter, Depends, HTTPException, File, Form, UploadFile
import logging
from typing import Optional

from api.models import UpdateProfile, UserPreference
from api.Database.auth import get_current_user
from api.Database.user_details import (
    update_user_profile_db,
    update_user_profile_image_db
)
from api.Database.database import supabase

logger = logging.getLogger(__name__)

router = APIRouter(
    tags=["user_profile"]
)

@router.post("/update_profile/")
async def update_user_profile(data: UpdateProfile, user=Depends(get_current_user)):
    try:
        updated = update_user_profile_db(data, user)
        return {"data": updated}
    except Exception as e:
        logger.error(f"Error in /update_profile/: {e}", exc_info=True)
        raise HTTPException(500, "Failed to update user profile")
    
@router.post("/update_profile_image/")
async def update_profile_image(
    profile_image: Optional[UploadFile] = File(None),
    remove_image: bool = Form(False),
    user=Depends(get_current_user)
):
    try:
        updated = await update_user_profile_image_db(profile_image, remove_image, user)
        return {"data": updated}
    except Exception as e:
        logger.error(f"Error in /update_profile_image/: {e}", exc_info=True)
        raise HTTPException(500, "Failed to update profile image")

@router.post("/add_user_preference/")
async def add_user_preference(pref: UserPreference):
    try:
        data, error = supabase.table("user_preferences").insert(pref.model_dump()).execute()
        if error:
            raise Exception(str(error))
        return {"message": "User preference added", "data": data}
    except Exception as e:
        logger.error(f"Error in /add_user_preference/: {e}", exc_info=True)
        raise HTTPException(500, "Failed to add user preference") 