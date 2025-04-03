import logging
import uuid
import requests
from fastapi import HTTPException
from database import supabase

def add_new_item_image(file):
    """
    Accepts either image bytes or a URL string.
    If a URL string is provided, fetch the image bytes.
    Then, upload the image as-is to Supabase storage.
    """
    try:
        # If file is a URL, fetch its content.
        if isinstance(file, str) and file.startswith("http"):
            response = requests.get(file)
            if response.status_code != 200:
                raise HTTPException(status_code=400, detail="Failed to fetch image from URL")
            file = response.content

        # Generate a unique filename; using PNG extension since we're not compressing.
        unique_filename = f"images/{uuid.uuid4()}.png"
        
        # Upload the file as-is.
        file_response = supabase.storage.from_('clothing-emojies').upload(unique_filename, file)
        
        # Check for an error.
        if hasattr(file_response, "error") and file_response.error:
            raise HTTPException(status_code=400, detail=str(file_response.error))
        elif isinstance(file_response, dict) and file_response.get("error"):
            raise HTTPException(status_code=400, detail=str(file_response["error"]))
        
        # Attempt to retrieve data. If no 'data' attribute exists, use the response object itself.
        data = getattr(file_response, "data", file_response)
        
        return {"message": "Item image added successfully", "data": data}
    except Exception as e:
        logging.error("❌ Adding Image Error: %s", e)
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")
