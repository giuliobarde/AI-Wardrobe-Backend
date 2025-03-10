from fastapi import HTTPException
from database import supabase

def add_clothing_item_db(item):
    try:
        # Prepare the data for insertion
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
        }

        item_response = supabase.table("clothing_items").insert(item_data).execute()

        # Check for errors in the response.
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
    
        # Check for errors in the response.
        item_error = getattr(response, "error", None)
        if item_error:
            raise HTTPException(status_code=400, detail=str(item_error))
        
        return {"data": response.data if response.data else []}
    except Exception as e:
        print("❌ Retriving Item Error:", str(e))
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")
