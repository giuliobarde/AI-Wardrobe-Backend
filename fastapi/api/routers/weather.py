from fastapi import APIRouter, Depends, HTTPException, status
import logging
from api.Database.auth import get_current_user
from api.Weather.weather import get_current_weather, get_weather_forecast, WeatherData, ForecastData

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

@router.get("/forecast", response_model=ForecastData)
async def weather_forecast(user=Depends(get_current_user)):
    """
    Get 3-day weather forecast for New York (hardcoded).
    Returns forecast data including temperature ranges, conditions, and precipitation chances.
    """
    forecast_data = get_weather_forecast()
    
    if not forecast_data:
        logger.error("Failed to get weather forecast data")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, 
            detail="Weather forecast service unavailable"
        )
    
    return forecast_data