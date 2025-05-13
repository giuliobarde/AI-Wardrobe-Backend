from fastapi import APIRouter, Depends, HTTPException
import logging

from api.models import ChatRequest
from api.Database.auth import get_current_user
from api.llm.outfit import generateOutfit
from api.Database.database import supabase

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/chat",
    tags=["ai"]
)

@router.post("/", response_model_exclude_none=True)
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