from fastapi import HTTPException
from .database import supabase

def add_saved_outfit_db(outfit):
    try:
        outfit_data = {
            "user_id": outfit.user_id,
            "items": outfit.items,
            "occasion": outfit.occasion,
            "favorite": outfit.favorite 
        }

        response = supabase.table("saved_outfits").insert(outfit_data).execute()
        item_error = getattr(response, "error", None)
        if item_error:
            raise HTTPException(status_code=400, detail=str(item_error))
        return {"message": "Outfit added successfully", "data": response.data}
    except Exception as e:
        print("❌ Adding Item Error:", str(e))
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")

def get_saved_outfits_db(user):
    try:
        response = supabase.table("saved_outfits").select("*").eq("user_id", user.id).execute()
        item_error = getattr(response, "error", None)
        if item_error:
            raise HTTPException(status_code=400, detail=str(item_error))
        return {"data": response.data if response.data else []}
    except Exception as e:
        print("❌ Retrieving Outfit Error:", str(e))
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")

def delete_saved_outfit_db(outfit_id: str):
    try:
        response = supabase.table("saved_outfits").delete().eq("id", outfit_id).execute()
        try:
            if response.error:
                raise HTTPException(status_code=400, detail=str(response.error))
        except AttributeError:
            pass
        return {"data": response.data if hasattr(response, "data") and response.data else []}
    except Exception as e:
        print("❌ Deleting Outfit Error:", str(e))
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")

def edit_favorite_outfit_db(outfit_id: str):
    try:
        # First, get the current favorite value
        get_response = supabase.table("saved_outfits").select("favorite").eq("id", outfit_id).execute()
        item_error = getattr(get_response, "error", None)
        if item_error:
            raise HTTPException(status_code=400, detail=str(item_error))
        
        if not get_response.data or len(get_response.data) == 0:
            raise HTTPException(status_code=404, detail="Outfit not found")
        
        # Get the current value and set the new value to the opposite
        current_favorite = get_response.data[0]["favorite"]
        new_favorite = not current_favorite
        
        # Update the favorite status to the opposite value
        update_response = supabase.table("saved_outfits").update({"favorite": new_favorite}).eq("id", outfit_id).execute()
        item_error = getattr(update_response, "error", None)
        if item_error:
            raise HTTPException(status_code=400, detail=str(item_error))
        
        return {"message": "Favorite status updated successfully", "data": update_response.data}
    except Exception as e:
        print("❌ Editing Favorite Status Error:", str(e))
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")