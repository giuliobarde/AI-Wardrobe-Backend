from datetime import datetime, timedelta, timezone
from fastapi import HTTPException, Security, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from .database import supabase
import logging
from api.Weather.weather import get_current_weather


# 📌 Active session storage
active_sessions = {}
SESSION_TIMEOUT = timedelta(minutes=20)


# 📌 Security (Token Authentication)
security = HTTPBearer()

# Logger for auth module
logger = logging.getLogger(__name__)


# 📌 Get Current User
def get_current_user(credentials: HTTPAuthorizationCredentials = Security(security)):
    token = credentials.credentials
    try:
        user_response = supabase.auth.get_user(token)

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



# 📌 Sign Up Function
def sign_up_db(user):
    try:
        # Create the auth user via Supabase
        auth_response = supabase.auth.sign_up({
            "email": user.email,
            "password": user.password
        })

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
            "gender": user.gender,
        }

        # Insert additional profile data into the 'profiles' table.
        profile_response = supabase.table("profiles").insert(profile_data).execute()

        # Check if the profile insertion returned an error.
        profile_error = getattr(profile_response, "error", None)
        if profile_error:
            raise HTTPException(status_code=400, detail=str(profile_error))
        
        return {"message": "User registered successfully"}
    except Exception as e:
        print("❌ Sign-Up Error:", str(e))
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")



# 📌 Sign In Function
async def sign_in_db(user):
    try:
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

        # After successful authentication
        access_token = response.session.access_token
        user_id = response.user.id

        # Query for additional profile details
        profile_response = supabase.table("profiles") \
            .select("first_name, last_name, username, member_since, gender, profile_image_url") \
            .eq("id", user_id) \
            .execute()

        if profile_response.data and len(profile_response.data) > 0:
            profile_data = profile_response.data[0]
        else:
            profile_data = {}

        active_sessions[user_id] = {
            "access_token": access_token,
            "last_active": datetime.now(timezone.utc)
        }

        # Fetch weather data for New York (hardcoded)
        try:
            weather_data = get_current_weather()
            if weather_data:
                # Convert Pydantic model to dict
                weather_info = weather_data.dict()
                # Convert datetime to string for JSON serialization
                weather_info["timestamp"] = weather_info["timestamp"].isoformat()

            else:
                weather_info = None

        except Exception as e:
            logger.error(f"Error fetching weather data during login: {e}")
            weather_info = None


        return {
            "message": "Login successful",
            "user_id": user_id,
            "access_token": access_token,
            "first_name": profile_data.get("first_name"),
            "last_name": profile_data.get("last_name"),
            "username": profile_data.get("username"),
            "member_since": profile_data.get("member_since"),
            "gender": profile_data.get("gender"),
            "profile_image_url": profile_data.get("profile_image_url"),
            "weather": weather_info
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")



# 📌 Get Session Function
def get_session_db(user):
    user_id = user.id
    session = active_sessions.get(user_id)

    if not session:
        raise HTTPException(status_code=401, detail="No active session found")

    if datetime.now(timezone.utc) - session["last_active"] > SESSION_TIMEOUT:
        del active_sessions[user_id]
        raise HTTPException(status_code=401, detail="Session expired due to inactivity")

    session["last_active"] = datetime.now(timezone.utc)
    return {"message": "Session active", "user_id": user_id, "access_token": session["access_token"]}



# 📌 Sign Out Function
def sign_out_db(user):
    user_id = user.id
    if user_id in active_sessions:
        del active_sessions[user_id]
    try:
        supabase.auth.sign_out()
        return {"message": "User successfully signed out"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to log out: {str(e)}")
