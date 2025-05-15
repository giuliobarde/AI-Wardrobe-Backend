import os
import requests
import logging
from datetime import datetime
from typing import Optional
from dotenv import load_dotenv
from pydantic import BaseModel

# Load environment variables
load_dotenv()

# Constants
CITY = "New York"  # Hardcoded city
BASE_URL = os.getenv("WEATHER_BASE_URL", "http://api.weatherapi.com/v1/current.json")
API_KEY = os.getenv("WEATHER_API_KEY")

# Setup logging
logger = logging.getLogger(__name__)

class WeatherData(BaseModel):
    """Weather data model for response formatting"""
    temperature: float
    description: str
    feels_like: float
    humidity: int
    wind_speed: float
    location: str
    timestamp: datetime

def get_current_weather() -> Optional[WeatherData]:
    """
    Get current weather for New York (hardcoded).
    Returns formatted weather data.
    """
    try:
        if not API_KEY:
            logger.error("Weather API key not found in environment variables")
            return None
            
        # Build URL for weatherapi.com
        url = BASE_URL
        params = {
            "key": API_KEY,
            "q": CITY,
            "aqi": "no"  # Don't include air quality data
        }
        
        response = requests.get(url, params=params)
        response.raise_for_status()
        
        data = response.json()
        
        # Convert timestamp string to datetime
        timestamp = datetime.strptime(
            data["current"]["last_updated"], 
            "%Y-%m-%d %H:%M"
        )
        
        # Format the response according to our model
        return WeatherData(
            temperature=data["current"]["temp_c"],
            description=data["current"]["condition"]["text"],
            feels_like=data["current"]["feelslike_c"],
            humidity=data["current"]["humidity"],
            wind_speed=data["current"]["wind_kph"],
            location=data["location"]["name"],
            timestamp=timestamp
        )
        
    except requests.RequestException as e:
        logger.error(f"Error fetching weather for {CITY}: {e}")
        return None
    except KeyError as e:
        logger.error(f"Invalid response format from weather API: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error getting weather for {CITY}: {e}")
        return None