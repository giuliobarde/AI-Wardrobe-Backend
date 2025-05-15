from fastapi import APIRouter, Depends, HTTPException, status
import logging
from api.Database.auth import get_current_user
from api.Weather.weather import get_current_weather, WeatherData

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/weather",
    tags=["weather"]
)

@router.get("/current", response_model=WeatherData)
async def current_weather(user=Depends(get_current_user)):
    """
    Get current weather data for New York (hardcoded).
    """
    weather_data = get_current_weather()
    
    if not weather_data:
        logger.error("Failed to get weather data")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, 
            detail="Weather service unavailable"
        )
    
    return weather_data

# This endpoint is prepared for future implementation but commented out for now
# @router.get("/location/{location}", response_model=WeatherData)
# async def location_weather(
#     location: str,
#     user=Depends(get_current_user)
# ):
#     """
#     Get weather data for a specific location.
#     This can be a city name, postal code, or latitude,longitude.
#     
#     Example: /weather/location/London
#              /weather/location/10001
#              /weather/location/40.7128,-74.006
#     """
#     weather_data = get_weather_for_location(location)
#     
#     if not weather_data:
#         logger.error(f"Failed to get weather data for location: {location}")
#         raise HTTPException(
#             status_code=status.HTTP_503_SERVICE_UNAVAILABLE, 
#             detail="Weather service unavailable or location not found"
#         )
#     
#     return weather_data
