from fastapi import APIRouter, Depends, HTTPException, Query, status
import logging
from typing import Optional

from api.models import ClothingItem, ItemID
from api.Database.auth import get_current_user
from api.llm.item import setOccasion
from api.llm.models import ClothingItem as AIClothingItem
from api.Database.wardrobe import (
    add_clothing_item_db,
    delete_clothing_item_db,
    edit_favorite_item_db,
    get_user_items_db,
    get_item_by_id_db,
    get_all_user_items_db,
    check_item_in_outfits_db
)
from api.Database.images import set_image

logger = logging.getLogger(__name__)

router = APIRouter(
    tags=["clothing"]
)

@router.post("/add_clothing_item/", status_code=status.HTTP_201_CREATED)
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

@router.get("/clothing_items/")
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

@router.get("/clothing_items/all/")
async def get_all_clothing_items(user=Depends(get_current_user)):
    try:
        return get_all_user_items_db(user)
    except Exception as e:
        logger.error(f"Error in /clothing_items/all/: {e}", exc_info=True)
        raise HTTPException(500, "Failed to retrieve all clothing items")
    
@router.post("/edit_favorite_item/")
async def edit_favorite_item(data: ItemID, user=Depends(get_current_user)):
    try:
        return edit_favorite_item_db(data.id)
    except Exception as e:
        logger.error(f"Error in /edit_favorite_item/: {e}", exc_info=True)
        raise HTTPException(500, "Failed to update favorite status")

@router.get("/check_item_in_outfits/")
async def check_item_in_outfits(
    item_id: str = Query(..., description="ID of the item to check"),
    user=Depends(get_current_user)
):
    try:
        return check_item_in_outfits_db(item_id, user.id)
    except Exception as e:
        logger.error(f"Error in /check_item_in_outfits/: {e}", exc_info=True)
        return {"data": []}

@router.post("/delete_clothing_item/")
async def delete_clothing_item(
    data: ItemID,
    delete_outfits: bool = Query(True, description="Delete all saved outfits containing this item"),
    user=Depends(get_current_user)
):
    try:
        return delete_clothing_item_db(data.id, delete_outfits, user.id)
    except Exception as e:
        logger.error(f"Error in /delete_clothing_item/: {e}", exc_info=True)
        raise HTTPException(500, "Failed to delete clothing item") 