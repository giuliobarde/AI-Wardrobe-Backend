# 📌 Import necessary modules
from fastapi import FastAPI, HTTPException, Depends, Security
from fastapi import security
from fastapi.security import HTTPAuthorizationCredentials
from pydantic import BaseModel
from database import supabase

# 📌 Initialize FastAPI app
app = FastAPI()

class User(BaseModel):
    email: str
    password: str

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