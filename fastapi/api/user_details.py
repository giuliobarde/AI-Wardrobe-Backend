from fastapi import HTTPException
from database import supabase

def update_user_profile_db(data, user):
    """
    Updates the user profile in the 'profiles' table using the provided update data.

    Parameters:
        data (UpdateProfile): An instance of UpdateProfile with updated first_name, last_name, and username.
        user (object): The current user object containing the user's id.

    Returns:
        dict: The updated user profile data.

    Raises:
        HTTPException: If there is an error updating the profile.
    """
    update_data = {
        "first_name": data.first_name,
        "last_name": data.last_name,
        "username": data.username,
        "gender": data.gender
    }

    response = supabase.table("profiles").update(update_data).eq("id", user.id).execute()

    # Convert response to dict if necessary (if response is a pydantic model)
    try:
        resp = response.model_dump()
    except Exception:
        resp = response

    # Check if there is an error in the response.
    if resp.get("error"):
        error_message = resp["error"].get("message", "An error occurred while updating the profile.")
        raise HTTPException(status_code=400, detail=error_message)

    # Return the first (and presumably only) updated profile record.
    data_list = resp.get("data")
    if not data_list:
        raise HTTPException(status_code=400, detail="No data returned after profile update.")
    return data_list[0]
