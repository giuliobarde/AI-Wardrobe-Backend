from fastapi import HTTPException
from database import supabase

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
    
def check_item_in_outfits_db(item_id: str):
    try:
        # Query saved_outfits where the item_id exists in the items array
        response = supabase.table("saved_outfits").select("*").contains("items", [item_id]).execute()
        
        item_error = getattr(response, "error", None)
        if item_error:
            raise HTTPException(status_code=400, detail=str(item_error))
        
        outfits = response.data if response.data else []
        return {"data": outfits, "count": len(outfits)}
    except Exception as e:
        print("❌ Checking Item in Outfits Error:", str(e))
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")

def delete_clothing_item_db(item_id: str):
    try:
        response = supabase.table("clothing_items").delete().eq("id", item_id).execute()
        try:
            if response.error:
                raise HTTPException(status_code=400, detail=str(response.error))
        except AttributeError:
            pass
        return {"data": response.data if hasattr(response, "data") and response.data else []}
    except Exception as e:
        print("❌ Deleting Item Error:", str(e))
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")
