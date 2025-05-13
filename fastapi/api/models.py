from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, field_validator


class ChatRequest(BaseModel):
    user_message: str = Field(..., description="User's query about outfit suggestions")
    temp: str = Field(..., description="Current outside temperature")

    @field_validator('user_message')
    @classmethod
    def validate_message(cls, v):
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