from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, field_validator, ConfigDict


class WeatherData(BaseModel):
    temperature: float = Field(..., description="Temperature in degrees")
    description: str = Field(..., description="Weather description")
    feels_like: float = Field(..., description="Feels like temperature")
    humidity: float = Field(..., description="Humidity percentage")
    wind_speed: float = Field(..., description="Wind speed")
    location: str = Field(..., description="Location name")
    timestamp: str = Field(..., description="Timestamp of weather data")

    model_config = ConfigDict(from_attributes=True)

    @field_validator('temperature', 'feels_like')
    @classmethod
    def validate_temperature(cls, v):
        if not isinstance(v, (int, float)):
            raise ValueError(f"Temperature must be a number, got {type(v)}")
        return float(v)

    @field_validator('humidity')
    @classmethod
    def validate_humidity(cls, v):
        if not isinstance(v, (int, float)):
            raise ValueError(f"Humidity must be a number, got {type(v)}")
        if not 0 <= float(v) <= 100:
            raise ValueError(f"Humidity must be between 0 and 100, got {v}")
        return float(v)

    @field_validator('wind_speed')
    @classmethod
    def validate_wind_speed(cls, v):
        if not isinstance(v, (int, float)):
            raise ValueError(f"Wind speed must be a number, got {type(v)}")
        if float(v) < 0:
            raise ValueError(f"Wind speed cannot be negative, got {v}")
        return float(v)


class ChatRequest(BaseModel):
    user_message: str = Field(..., description="User's query about outfit suggestions")
    weather_data: WeatherData = Field(..., description="Current weather data")

    model_config = ConfigDict(from_attributes=True)

    @field_validator('user_message')
    @classmethod
    def validate_message(cls, v):
        if not isinstance(v, str):
            raise ValueError(f"Message must be a string, got {type(v)}")
        if len(v.strip()) < 3:
            raise ValueError("Message must be at least 3 characters")
        return v


class ClothingItem(BaseModel):
    user_id: str
    item_type: str
    material: str
    color: str
    formality: str
    pattern: str
    fit: str
    suitable_for_weather: str
    suitable_for_occasion: str
    sub_type: str
    image_link: Optional[str] = None


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
    gender: str

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
    identifier: str
    password: str


class ItemID(BaseModel):
    id: str = Field(..., description="ID of the item")


class UpdateProfile(BaseModel):
    first_name: str
    last_name: str
    username: str
    gender: str


class OutfitData(BaseModel):
    user_id: str
    items: List[Dict[str, Any]]
    occasion: str
    favorite: bool = False 