# 📌 Import necessary modules
from fastapi import FastAPI, HTTPException, Depends, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from huggingface import generateOutfit
from database import supabase
from datetime import datetime, timedelta, timezone

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
active_sessions = {}  # { user_id: { "access_token": str, "last_active": datetime } }
SESSION_TIMEOUT = timedelta(minutes=20)

# 📌 Helper function: Get current user
def get_current_user(credentials: HTTPAuthorizationCredentials = Security(security)):
    token = credentials.credentials
    try:
        user_response = supabase.auth.get_user(token)
        print("🔍 Raw Supabase User Response:", user_response)

        if not hasattr(user_response, "user") or user_response.user is None:
            raise HTTPException(status_code=401, detail="Invalid or expired token")

        user_obj = user_response.user

        if user_obj.id not in active_sessions:
            active_sessions[user_obj.id] = {
                "access_token": token,
                "last_active": datetime.now(timezone.utc)
            }

        return user_obj

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

# New Models for authentication with additional fields:
class SignupUser(BaseModel):
    first_name: str
    last_name: str
    username: str
    email: str
    password: str

class SigninUser(BaseModel):
    identifier: str  # Can be either email or username
    password: str

# 📌 AI Chatbot Endpoint
@app.post("/chat/")
def chat(request: ChatRequest):
    response = generateOutfit(request.user_message, request.temp)
    return {"response": response}

# 📌 Authentication Endpoints
@app.post("/sign-up/")
async def sign_up(user: SignupUser):
    try:
        # Create the auth user via Supabase
        auth_response = supabase.auth.sign_up({
            "email": user.email,
            "password": user.password
        })
        print("🔍 Auth Response:", auth_response)  # Debug log

        # Use getattr to safely check for an error attribute.
        auth_error = getattr(auth_response, "error", None)
        if auth_error:
            raise HTTPException(status_code=400, detail=str(auth_error))
        
        user_id = auth_response.user.id
        if not user_id:
            raise HTTPException(status_code=400, detail="User creation failed")

        # Prepare profile data to insert into the profiles table.
        profile_data = {
            "id": user_id,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "username": user.username,
            "email": user.email,
        }
        print("📌 Profile Data Before Insert:", profile_data)  # Debug log

        # Insert additional profile data into the 'profiles' table.
        profile_response = supabase.table("profiles").insert(profile_data).execute()
        print("✅ Profile Insert Response:", profile_response)  # Debug log

        # Check if the profile insertion returned an error.
        profile_error = getattr(profile_response, "error", None)
        if profile_error:
            raise HTTPException(status_code=400, detail=str(profile_error))
        
        return {"message": "User registered successfully"}
    except Exception as e:
        print("❌ Sign-Up Error:", str(e))
        return {"error": f"Internal Server Error: {str(e)}"}


@app.post("/sign-in/")
async def sign_in(user: SigninUser):
    try:
        print("📌 Received Login Payload:", user.dict())
        # Determine if the identifier is an email or a username
        email_to_use = user.identifier
        if "@" not in user.identifier:
            # Assume it's a username; look up email from the profiles table
            profile_response = supabase.table("profiles").select("email").eq("username", user.identifier).execute()
            if not profile_response.data or len(profile_response.data) == 0:
                raise HTTPException(status_code=401, detail="User not found")
            email_to_use = profile_response.data[0]["email"]

        response = supabase.auth.sign_in_with_password({
            "email": email_to_use,
            "password": user.password,
        })

        if getattr(response, "error", None):
            raise HTTPException(status_code=401, detail=str(response.error))

        if not getattr(response, "session", None):
            raise HTTPException(status_code=401, detail="Invalid credentials or user does not exist.")

        access_token = response.session.access_token
        user_id = response.user.id

        active_sessions[user_id] = {
            "access_token": access_token,
            "last_active": datetime.now(timezone.utc)
        }

        return {"message": "Login successful", "user_id": user_id, "access_token": access_token}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")

@app.get("/session/")
async def get_session(user=Depends(get_current_user)):
    user_id = user.id

    session = active_sessions.get(user_id)
    if not session:
        raise HTTPException(status_code=401, detail="No active session found")

    if datetime.now(timezone.utc) - session["last_active"] > SESSION_TIMEOUT:
        del active_sessions[user_id]
        raise HTTPException(status_code=401, detail="Session expired due to inactivity")

    session["last_active"] = datetime.now(timezone.utc)
    return {"message": "Session active", "user_id": user_id, "access_token": session["access_token"]}

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
async def get_clothing_items(user=Depends(get_current_user)):
    try:
        response = supabase.table("clothing_items").select("*").eq("user_id", user.id).execute()
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
