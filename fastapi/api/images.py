import logging
import uuid
from pydantic import BaseModel
import requests
from fastapi import HTTPException
from database import supabase
from openai_client import generateImage

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
    image_link: str

def add_new_image(file):
    """
    Accepts either image bytes or a URL string.
    If a URL string is provided, fetch its content.
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
        
        # Upload the file to the specified Supabase storage bucket.
        file_response = supabase.storage.from_('clothing-emojies').upload(unique_filename, file)
        
        # Check for an error.
        if hasattr(file_response, "error") and file_response.error:
            raise HTTPException(status_code=400, detail=str(file_response.error))
        elif isinstance(file_response, dict) and file_response.get("error"):
            raise HTTPException(status_code=400, detail=str(file_response["error"]))
        
        # Attempt to retrieve data. Depending on your Supabase client this may vary.
        data = getattr(file_response, "data", file_response)
        
        return {"message": "Item image added successfully", "data": data, "filename": unique_filename}
    except Exception as e:
        logging.error("❌ Adding Image Error: %s", e)
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")
    
def add_new_item_image(file, item: ClothingItem):
    """
    Uploads the image file to Supabase storage and inserts a new record into the 'image_items' table
    with the image attributes and storage link.
    """
    # First, upload the image file.
    upload_result = add_new_image(file)
    
    # Construct the public URL for the uploaded image.
    # Adjust this based on your Supabase URL and bucket configuration.
    SUPABASE_URL = "https://qniouzdixmmtftnlkevs.supabase.co"
    bucket = "clothing-emojies"
    filename = upload_result.get("filename")
    if not filename:
        raise HTTPException(status_code=400, detail="Failed to obtain filename from upload result")
    image_link = f"{SUPABASE_URL}/storage/v1/object/public/{bucket}/{filename}"
    
    # Prepare the record with the image attributes.
    record = {
        "material": item.material,
        "color": item.color,
        "pattern": item.pattern,
        "sub_type": item.sub_type,
        "image_link": image_link,
    }
    
    # Insert the record into the image_items table.
    db_response = supabase.table("image_items").insert(record).execute()
    return db_response

def set_image(item: ClothingItem):
    """
    Checks if an image for the clothing item (based on material, color, pattern, and sub_type)
    already exists in the image_items table. 
    - If an image is found, sets item.image_link from the existing record and returns the record.
    - If not, generates an emoji-like image using generateImage, uploads it via add_new_item_image,
      sets item.image_link using the newly created record, and returns that record.
    """
    # Query the image_items table for an existing image with matching attributes.
    query_response = supabase.table("image_items").select("*") \
        .eq("material", item.material) \
        .eq("color", item.color) \
        .eq("pattern", item.pattern) \
        .eq("sub_type", item.sub_type) \
        .execute()

    if query_response.data and len(query_response.data) > 0:
        logging.info("Image already exists with the same attributes; using existing image.")
        # Assume we use the first returned record.
        item.image_link = query_response.data[0]["image_link"]
        return {"message": "Image already exists", "data": query_response.data}
    else:
        # No matching image exists, so generate a new image.
        image_bytes = generateImage(item)
        # Upload image and insert a new record in the image_items table.
        upload_result = add_new_item_image(image_bytes, item)
        # Extract the newly created image link from the insert result.
        if upload_result.data and len(upload_result.data) > 0:
            item.image_link = upload_result.data[0]["image_link"]
            return {"message": "New image created", "data": upload_result.data}
        else:
            raise HTTPException(status_code=500, detail="Failed to create new image record")
