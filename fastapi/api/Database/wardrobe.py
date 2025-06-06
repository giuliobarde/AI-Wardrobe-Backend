from fastapi import HTTPException
from .database import supabase

def add_clothing_item_db(item):
    try:
        item_data = {
            "user_id": item.user_id,
            "item_type": item.item_type,
            "material": item.material,
            "color": item.color,
            "formality": item.formality,
            "pattern": item.pattern,
            "fit": item.fit,
            "suitable_for_weather": item.suitable_for_weather,
            "suitable_for_occasion": item.suitable_for_occasion,
            "sub_type": item.sub_type,
            "image_link": item.image_link
        }
        item_response = supabase.table("clothing_items").insert(item_data).execute()
        item_error = getattr(item_response, "error", None)
        if item_error:
            raise HTTPException(status_code=400, detail=str(item_error))
        return {"message": "Item added successfully", "data": item_response.data}
    except Exception as e:
        print("❌ Adding Item Error:", str(e))
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")

def get_user_items_db(item_type, user):
    try:
        response = supabase.table("clothing_items").select("*").eq("user_id", user.id).eq("item_type", item_type).execute()
        item_error = getattr(response, "error", None)
        if item_error:
            raise HTTPException(status_code=400, detail=str(item_error))
        return {"data": response.data if response.data else []}
    except Exception as e:
        print("❌ Retrieving Item Error:", str(e))
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")

def get_item_by_id_db(item_id: str, user):
    try:
        response = supabase.table("clothing_items").select("*").eq("id", item_id).eq("user_id", user.id).execute()
        item_error = getattr(response, "error", None)
        if item_error:
            raise HTTPException(status_code=400, detail=str(item_error))
        return {"data": response.data if response.data else []}
    except Exception as e:
        print("❌ Retrieving Item by ID Error:", str(e))
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")

def get_all_user_items_db(user):
    try:
        response = supabase.table("clothing_items")\
            .select("*")\
            .eq("user_id", user.id)\
            .order("added_date", desc=True)\
            .execute()
        item_error = getattr(response, "error", None)
        if item_error:
            raise HTTPException(status_code=400, detail=str(item_error))
        return {"data": response.data if response.data else []}
    except Exception as e:
        print("❌ Retrieving All Items Error:", str(e))
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")
    
def edit_favorite_item_db(item_id: str):
    try:
        # First, get the current favorite value
        get_response = supabase.table("clothing_items").select("favorite").eq("id", item_id).execute()
        item_error = getattr(get_response, "error", None)
        if item_error:
            raise HTTPException(status_code=400, detail=str(item_error))
        
        if not get_response.data or len(get_response.data) == 0:
            raise HTTPException(status_code=404, detail="Item not found")
        
        # Get the current value and set the new value to the opposite
        current_favorite = get_response.data[0]["favorite"]
        new_favorite = not current_favorite
        
        # Update the favorite status to the opposite value
        update_response = supabase.table("clothing_items").update({"favorite": new_favorite}).eq("id", item_id).execute()
        item_error = getattr(update_response, "error", None)
        if item_error:
            raise HTTPException(status_code=400, detail=str(item_error))
        
        return {"message": "Favorite status updated successfully", "data": update_response.data}
    except Exception as e:
        print("❌ Editing Favorite Status Error:", str(e))
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")
    
def check_item_in_outfits_db(item_id: str, user_id: str):
    try:
        # Query saved_outfits for the specific user
        resp = (
            supabase
            .table("saved_outfits")
            .select("id, items")
            .eq("user_id", user_id)
            .execute()
        )
        
        err = getattr(resp, "error", None)
        if err:
            raise HTTPException(status_code=400, detail=f"Failed to load saved outfits: {err}")
        
        outfits = resp.data or []
        matches = [
            o for o in outfits
            if any(isinstance(i, dict) and i.get("id") == item_id for i in o.get("items", []))
        ]
        
        return {"data": matches}
    except HTTPException:
        raise
    except Exception as e:
        print("❌ Checking Item in Outfits Error:", str(e))
        return {"data": []}

def delete_clothing_item_db(item_id: str, delete_outfits: bool = False, user_id: str = None):
    try:
        # If cascade delete is enabled, delete associated outfits first
        if delete_outfits and user_id:
            # Get outfits containing this item
            outfit_resp = (
                supabase
                .table("saved_outfits")
                .select("id, items")
                .eq("user_id", user_id)
                .execute()
            )
            
            err = getattr(outfit_resp, "error", None)
            if err:
                raise HTTPException(status_code=400, detail=f"Failed to load saved outfits: {err}")
            
            outfits = outfit_resp.data or []
            to_delete_ids = [
                outfit["id"]
                for outfit in outfits
                if any(isinstance(i, dict) and i.get("id") == item_id for i in outfit.get("items", []))
            ]
            
            # Delete associated outfits if any found
            if to_delete_ids:
                del_resp = (
                    supabase
                    .table("saved_outfits")
                    .delete()
                    .in_("id", to_delete_ids)
                    .execute()
                )
                err2 = getattr(del_resp, "error", None)
                if err2:
                    raise HTTPException(status_code=400, detail=f"Failed to delete saved outfits: {err2}")
        
        # Delete the clothing item
        response = supabase.table("clothing_items").delete().eq("id", item_id).execute()
        try:
            if response.error:
                raise HTTPException(status_code=400, detail=str(response.error))
        except AttributeError:
            pass
        
        return {"data": response.data if hasattr(response, "data") and response.data else []}
    except HTTPException:
        raise
    except Exception as e:
        print("❌ Deleting Item Error:", str(e))
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")
