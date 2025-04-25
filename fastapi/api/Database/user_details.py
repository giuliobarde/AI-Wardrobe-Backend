import os
import uuid
from fastapi import HTTPException
from .database import supabase

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

async def update_user_profile_image_db(profile_image, remove_image, user):
    """
    Updates the user's profile image in the 'profiles' table.

    Parameters:
        profile_image (UploadFile): The profile image file to upload (None if removing)
        remove_image (bool): Flag to indicate if the profile image should be removed
        user (object): The current user object containing the user's id.

    Returns:
        dict: The updated user profile data with the new image URL.

    Raises:
        HTTPException: If there is an error updating the profile image.
    """
    # First, get the current user profile to check if they already have a profile image
    current_profile = supabase.table("profiles").select("profile_image_url").eq("id", user.id).execute()
    
    try:
        current_profile_data = current_profile.data
        if current_profile_data and len(current_profile_data) > 0:
            current_image_url = current_profile_data[0].get("profile_image_url")
        else:
            current_image_url = None
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error retrieving current profile: {str(e)}")
    
    update_data = {}
    
    # Function to extract clean file path from URL
    def extract_file_path(url):
        if not url:
            return None
            
        # Remove query parameters if any
        clean_url = url.split('?')[0]
        
        # Extract the file path from the bucket path
        if "/pics/" in clean_url:
            # Get the specific filename after the /pics/ path
            return f"pics/{clean_url.split('/pics/')[1]}"
        elif "/user-profiles/" in clean_url:
            # Try with bucket name
            parts = clean_url.split("/user-profiles/")
            if len(parts) > 1:
                return parts[1]
                
        print(f"Warning: Could not parse image URL properly: {url}")
        return None
    
    # Function to delete an image from storage
    def delete_image_from_storage(url):
        try:
            file_path = extract_file_path(url)
            if not file_path:
                print(f"Could not extract file path from URL: {url}")
                return False
                
            print(f"Attempting to delete file at path: {file_path}")
            delete_response = supabase.storage.from_("user-profiles").remove([file_path])
            print(f"Delete response: {delete_response}")
            
            # Check if the response indicates success
            if delete_response and not (hasattr(delete_response, "error") and delete_response.error):
                print(f"Successfully deleted image at path: {file_path}")
                return True
            else:
                print(f"Warning: Error deleting image at path: {file_path}")
                return False
        except Exception as e:
            print(f"Exception while deleting image: {str(e)}")
            return False
    
    # CASE 1: Remove the image
    if remove_image:
        update_data["profile_image_url"] = None
        
        # Delete the old image from storage if it exists
        if current_image_url:
            delete_image_from_storage(current_image_url)
    
    # CASE 2 & 3: Add a new image or update existing image
    elif profile_image:
        # Generate a unique filename
        file_extension = os.path.splitext(profile_image.filename)[1]
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        
        # Read file content
        file_content = await profile_image.read()
        
        # Upload to Supabase Storage
        storage_path = f"pics/{unique_filename}"
        storage_response = supabase.storage.from_("user-profiles").upload(
            storage_path, file_content
        )
        
        if isinstance(storage_response, dict) and storage_response.get("error"):
            raise HTTPException(
                status_code=400,
                detail=f"Error uploading image: {storage_response['error']}"
            )
        elif hasattr(storage_response, "error") and storage_response.error:
            raise HTTPException(
                status_code=400,
                detail=f"Error uploading image: {storage_response.error}"
            )
        
        # Get the public URL for the uploaded file
        image_url = supabase.storage.from_("user-profiles").get_public_url(storage_path)
        update_data["profile_image_url"] = image_url
        
        # If updating an existing image, delete the old one after successfully uploading the new one
        if current_image_url:
            delete_image_from_storage(current_image_url)

    # Only proceed with the update if we have data to update
    if update_data:
        response = supabase.table("profiles").update(update_data).eq("id", user.id).execute()
        
        # Convert response to dict if necessary
        try:
            resp = response.model_dump()
        except AttributeError:
            resp = response
        
        # Check if there is an error in the response
        if isinstance(resp, dict) and resp.get("error"):
            error_message = resp["error"].get("message", "An error occurred while updating the profile image.")
            raise HTTPException(status_code=400, detail=error_message)
        
        # Return the updated profile record
        data_list = resp.get("data") if isinstance(resp, dict) else getattr(resp, "data", None)
        if not data_list:
            raise HTTPException(status_code=400, detail="No data returned after profile image update.")
        return data_list[0]
    
    raise HTTPException(status_code=400, detail="No action was taken for profile image update.")