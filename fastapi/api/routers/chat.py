from fastapi import APIRouter, Depends, HTTPException, Request
import logging
import json

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
async def chat(request: Request, user=Depends(get_current_user)):
    try:
        # Log the raw request body
        body = await request.body()
        logger.info(f"Raw request body: {body.decode()}")
        
        # Parse the request body manually first to see what we're getting
        try:
            raw_data = json.loads(body)
            logger.info(f"Parsed request data: {raw_data}")
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse request body as JSON: {e}")
            raise HTTPException(400, "Invalid JSON in request body")
            
        # Now try to parse with Pydantic model
        try:
            chat_request = ChatRequest(**raw_data)
            logger.info(f"Successfully parsed ChatRequest: {chat_request}")
        except Exception as e:
            logger.error(f"Failed to parse request as ChatRequest: {str(e)}")
            raise HTTPException(422, f"Invalid request data: {str(e)}")

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
        
        # Convert temperature to string as expected by generateOutfit
        weather_data = {
            "temperature": chat_request.weather_data.temperature,
            "description": chat_request.weather_data.description,
            "feels_like": chat_request.weather_data.feels_like,
            "humidity": chat_request.weather_data.humidity,
            "wind_speed": chat_request.weather_data.wind_speed,
            "location": chat_request.weather_data.location,
            "timestamp": chat_request.weather_data.timestamp
        }
        
        logger.info(f"Processed weather data: {weather_data}")
        
        outfit_resp = generateOutfit(chat_request.user_message, weather_data, wardrobe_items)
        return {"response": outfit_resp}
    except Exception as e:
        logger.error(f"Error in /chat/: {e}", exc_info=True)
        raise HTTPException(500, f"Failed to generate outfit suggestion: {str(e)}") 