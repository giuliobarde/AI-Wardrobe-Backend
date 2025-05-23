import os
import requests
import logging
from datetime import datetime
from typing import Optional, List
from dotenv import load_dotenv
from pydantic import BaseModel

# Load environment variables
load_dotenv()

# Constants
BASE_URL = os.getenv("WEATHER_BASE_URL", "http://api.weatherapi.com/v1")
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
    visibility: str

class HourlyForecast(BaseModel):
    """Model for hourly forecast data"""
    time: datetime
    temperature: float
    description: str
    feels_like: float
    humidity: int
    wind_speed: float
    chance_of_rain: int
    is_day: bool

class ForecastDay(BaseModel):
    """Model for daily forecast data"""
    date: datetime
    max_temp: float
    min_temp: float
    description: str
    chance_of_rain: int
    humidity: int
    wind_speed: float
    hourly_forecast: List[HourlyForecast]
    is_day: bool

class ForecastData(BaseModel):
    """Model for forecast response"""
    location: str
    forecast_days: List[ForecastDay]

def get_current_weather(lat: float, lon: float) -> Optional[WeatherData]:
    """
    Get current weather for the given coordinates.
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
            "q": f"{lat},{lon}",
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
            temperature=data["current"]["temp_f"],
            description=data["current"]["condition"]["text"],
            feels_like=data["current"]["feelslike_f"],
            humidity=data["current"]["humidity"],
            wind_speed=data["current"]["wind_kph"],
            location=data["location"]["name"],
            timestamp=timestamp,
            visibility=f"{data['current']['vis_miles']} miles"
        )
        
    except requests.RequestException as e:
        logger.error(f"Error fetching weather for coordinates {lat},{lon}: {e}")
        return None
    except KeyError as e:
        logger.error(f"Invalid response format from weather API: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error getting weather for coordinates {lat},{lon}: {e}")
        return None

def get_weather_forecast(lat: float, lon: float) -> Optional[ForecastData]:
    """
    Get 3-day weather forecast for the given coordinates.
    Returns formatted forecast data.
    """
    try:
        if not API_KEY:
            logger.error("Weather API key not found in environment variables")
            return None
            
        # Build URL for weatherapi.com forecast endpoint
        url = f"{BASE_URL}/forecast.json"
        params = {
            "key": API_KEY,
            "q": f"{lat},{lon}",
            "days": 3,  # Get 3 days forecast
            "aqi": "no",  # Don't include air quality data
            "alerts": "no"  # Don't include weather alerts
        }
        
        logger.info(f"Fetching forecast from URL: {url}")
        response = requests.get(url, params=params)
        response.raise_for_status()
        
        data = response.json()
        logger.info(f"Raw forecast API response: {data}")
        
        forecast_days = []
        
        # Process each forecast day
        for day in data["forecast"]["forecastday"]:
            # Process hourly forecast
            hourly_forecast = []
            for hour in day["hour"]:
                hourly_forecast.append(HourlyForecast(
                    time=datetime.strptime(hour["time"], "%Y-%m-%d %H:%M"),
                    temperature=hour["temp_f"],
                    description=hour["condition"]["text"],
                    feels_like=hour["feelslike_f"],
                    humidity=hour["humidity"],
                    wind_speed=hour["wind_kph"],
                    chance_of_rain=hour["chance_of_rain"],
                    is_day=hour["is_day"] == 1
                ))
            
            # Calculate if it's day or night based on the first hour of the day
            is_day = day["hour"][0]["is_day"] == 1
            
            forecast_day = ForecastDay(
                date=datetime.strptime(day["date"], "%Y-%m-%d"),
                max_temp=day["day"]["maxtemp_f"],
                min_temp=day["day"]["mintemp_f"],
                description=day["day"]["condition"]["text"],
                chance_of_rain=day["day"]["daily_chance_of_rain"],
                humidity=day["day"]["avghumidity"],
                wind_speed=day["day"]["maxwind_kph"],
                hourly_forecast=hourly_forecast,
                is_day=is_day
            )
            logger.info(f"Processed forecast day: {forecast_day}")
            forecast_days.append(forecast_day)
        
        forecast_data = ForecastData(
            location=data["location"]["name"],
            forecast_days=forecast_days
        )
        logger.info(f"Final forecast data: {forecast_data}")
        return forecast_data
        
    except requests.RequestException as e:
        logger.error(f"Error fetching weather forecast for coordinates {lat},{lon}: {e}")
        return None
    except KeyError as e:
        logger.error(f"Invalid response format from weather API: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error getting weather forecast for coordinates {lat},{lon}: {e}")
        return None