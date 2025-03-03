# 📌 Import necessary modules
from fastapi import FastAPI, HTTPException, Depends, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from huggingface import generateOutfit
from database import supabase

# 📌 Initialize FastAPI app
app = FastAPI()

# 📌 Middleware (CORS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 📌 Security (Token Authentication)
security = HTTPBearer()

# 📌 Active session storage
active_sessions = {}

# 📌 Helper function: Get current user
def get_current_user(credentials: HTTPAuthorizationCredentials = Security(security)):
    token = credentials.credentials
    try:
        user_response = supabase.auth.get_user(token)
        print("🔍 Raw Supabase User Response:", user_response)

        if not hasattr(user_response, "user") or user_response.user is None:
            raise HTTPException(status_code=401, detail="Invalid or expired token")

        return user_response.user

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve user: {str(e)}")

# 📌 Health Check Endpoint
@app.get("/")
def healthcheck():
    return {"message": "Health check check"}

# 📌 Models
class ChatRequest(BaseModel):
    user_message: str
    temp: str

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

class UserPreference(BaseModel):
    user_id: str
    preferred_fit: str
    preferred_colors: list
    preferred_formality: str
    preferred_patterns: list
    preferred_temperature: str

class User(BaseModel):
    email: str
    password: str

# 📌 AI Chatbot Endpoint
@app.post("/chat")
def chat(request: ChatRequest):
    response = generateOutfit(request.user_message, request.temp)
    return {"response": response}

# 📌 Authentication Endpoints
@app.post("/sign-up/")
async def sign_up(user: User):
    try:
        supabase.auth.sign_up({"email": user.email, "password": user.password})
        return {"message": "User registered successfully"}
    except Exception as e:
        return {"error": f"Internal Server Error: {str(e)}"}

@app.post("/sign-in/")
async def sign_in(user: User):
    try:
        response = supabase.auth.sign_in_with_password({"email": user.email, "password": user.password})

        if response.session is None:
            raise HTTPException(status_code=401, detail="Invalid credentials or user does not exist.")

        access_token = response.session.access_token
        user_id = response.user.id  

        active_sessions[user_id] = access_token

        return {"message": "Login successful", "user_id": user_id, "access_token": access_token}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")

@app.get("/session/")
async def get_session(user=Depends(get_current_user)):
    user_id = user.id

    if user_id not in active_sessions:
        raise HTTPException(status_code=401, detail="No active session found")

    return {"message": "Session active", "user_id": user_id, "access_token": active_sessions[user_id]}

@app.post("/sign-out/")
async def sign_out(user=Depends(get_current_user)):
    user_id = user.id

    if user_id in active_sessions:
        del active_sessions[user_id]
    
    try:
        supabase.auth.sign_out()
        return {"message": "User successfully signed out"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to log out: {str(e)}")

# 📌 Clothing Item Endpoints
@app.post("/add_clothing_item/")
async def add_clothing_item(item: ClothingItem, user=Depends(get_current_user)):
    data, error = supabase.table("clothing_items").insert(item.dict()).execute()
    if error:
        return {"error": str(error)}
    return {"message": "Clothing item added successfully", "data": data}

@app.get("/clothing_items/")
async def get_clothing_items():
    try:
        response = supabase.table("clothing_items").select("*").execute()
        return {"data": response.data if response.data else []}
    except Exception as e:
        return {"error": f"Internal Server Error: {str(e)}"}

# 📌 User Preferences Endpoints
@app.post("/add_user_preference/")
async def add_user_preference(pref: UserPreference):
    data, error = supabase.table("user_preferences").insert(pref.dict()).execute()
    if error:
        return {"error": error}
    return {"message": "User preference added", "data": data}
