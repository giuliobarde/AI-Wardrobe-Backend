from fastapi import HTTPException
from database import supabase

def add_saved_outfit_db(outfit):

    try:
        outfit_data = {
            "user_id": outfit.user_id,
            "items": outfit.items,
            "occasion": outfit.occasion,
            "favourite": outfit.favourite 
        }

        response = supabase.table("saved_outfits").insert(outfit_data).execute()
        item_error = getattr(response, "error", None)
        if item_error:
            raise HTTPException(status_code=400, detail=str(item_error))
        return {"message": "Outfit added successfully", "data": response.data}
    except Exception as e:
        print("❌ Adding Item Error:", str(e))
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")

def remove_saved_outfit_db():
    return

def edit_favourite_outfit_db():
    return

def get_favourite_outfits_db():
    return