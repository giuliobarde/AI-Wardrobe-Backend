from fastapi import APIRouter, Depends, HTTPException
import logging

from api.models import OutfitData, ItemID
from api.Database.auth import get_current_user
from api.Database.outfits import (
    add_saved_outfit_db,
    get_saved_outfits_db,
    delete_saved_outfit_db,
    edit_favorite_outfit_db
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/outfit",
    tags=["outfits"]
)

@router.post("/add_saved_outfit/", status_code=201)
async def add_saved_outfit(outfit: OutfitData, user=Depends(get_current_user)):
    try:
        return add_saved_outfit_db(outfit)
    except Exception as e:
        logger.error(f"Error in /add_saved_outfit/: {e}", exc_info=True)
        raise HTTPException(500, "Failed to save outfit")

@router.get("/get_saved_outfits/")
async def get_saved_outfits(user=Depends(get_current_user)):
    try:
        return get_saved_outfits_db(user)
    except Exception as e:
        logger.error(f"Error in /get_saved_outfits/: {e}", exc_info=True)
        raise HTTPException(500, "Failed to retrieve saved outfits")

@router.post("/delete_saved_outfit/")
async def delete_saved_outfit(data: ItemID, user=Depends(get_current_user)):
    try:
        return delete_saved_outfit_db(data.id)
    except Exception as e:
        logger.error(f"Error in /delete_saved_outfit/: {e}", exc_info=True)
        raise HTTPException(500, "Failed to delete saved outfit")

@router.post("/edit_favorite_outfit/")
async def edit_favorite_outfit(data: ItemID, user=Depends(get_current_user)):
    try:
        return edit_favorite_outfit_db(data.id)
    except Exception as e:
        logger.error(f"Error in /edit_favorite_outfit/: {e}", exc_info=True)
        raise HTTPException(500, "Failed to update favorite status") 