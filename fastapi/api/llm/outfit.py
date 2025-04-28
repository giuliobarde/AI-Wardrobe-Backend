import json
import logging
from typing import Dict, List, Set
from langchain_core.messages import SystemMessage, HumanMessage

from .client import llm_client
from .config import ai_config
from .occasion import determineOccasions

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def generateOutfit(user_message: str, outside_temp: str, wardrobe_items: List[Dict]) -> Dict:
    """
    Generates an outfit suggestion based on the user's message, outside temperature,
    and wardrobe items.
    
    Args:
        user_message: The user's query or request
        outside_temp: The outside temperature description
        wardrobe_items: List of items from the user's wardrobe
        
    Returns:
        A dictionary with occasion, outfit items, and description
    """
    # Determine target occasion and configuration
    target_occ = determineOccasions(user_message)
    config = ai_config.get_occasion_config(target_occ)
    
    # Set generation temperature based on occasion formality
    generation_temp = ai_config.get_occasion_temperature(target_occ)
    llm_client.with_temperature(generation_temp)
    
    # Build rules text
    rules_text = (
        f"Allowed items: {', '.join(config['items']) if config.get('items') else 'Any'}, "
        f"Rules: {config.get('rules', '')}, "
        f"Strictness: {config.get('strictness', '')}, "
        f"Description: {config.get('description', '')}\n"
        f"IMPORTANT: Do not include any items with 'tuxedo' or 'tailcoat' in their sub_type "
        f"if the occasion is not a 'black tie event' or 'white tie event'."
    )
    
    # Format wardrobe items
    formatted_items = []
    wardrobe_ids: Set[str] = set()
    
    for item in wardrobe_items:
        item_id = item.get('id', 'N/A')
        wardrobe_ids.add(item_id)
        formatted_items.append(
            f"Item ID: {item_id}, Type: {item.get('item_type', 'N/A')}, "
            f"Material: {item.get('material', 'unknown')}, "
            f"Color: {item.get('color', 'unknown')}, "
            f"Formality: {item.get('formality', 'N/A')}, "
            f"Pattern: {item.get('pattern', 'N/A')}, "
            f"Fit: {item.get('fit', 'N/A')}, "
            f"Weather Suitability: {item.get('suitable_for_weather', 'N/A')}, "
            f"Occasion Suitability: {item.get('suitable_for_occasion', 'N/A')}, "
            f"Sub Type: {item.get('sub_type', 'N/A')}"
        )
    
    wardrobe_text = "The user's wardrobe includes: " + " | ".join(formatted_items) + "."
    
    # Combined prompt for outfit generation and refinement
    combined_prompt = f"""
Step: Generate and Refine Outfit Suggestion.
You are a style assistant tasked with generating an outfit suggestion based on the following details and guardrails.
1. Use chain-of-thought reasoning to consider the user's message, outside temperature, and wardrobe.
2. Ensure that only items from the provided wardrobe (with matching Item IDs) are selected.
3. Do not include any items with 'tuxedo' or 'tailcoat' in their sub_type if the occasion is not a 'black tie event' or 'white tie event'.
4. The outfit must consist of 3 to 6 items, including exactly one pair of shoes, exactly one pair of pants, between one and two tops, and between one and two outerwear pieces (if applicable).

Examples for guidance:
Example 1 (Wedding):
Candidate: [White Dress Shirt, Navy Suit Pants, Black Dress Shoes, Navy Suit Jacket]
Final Output: {{"occasion": "wedding", "outfit_items": [{{"id": "ex1_1", "sub_type": "White Dress Shirt", "color": "White"}}, {{"id": "ex1_2", "sub_type": "Navy Suit Pants", "color": "Navy"}}, {{"id": "ex1_3", "sub_type": "Black Dress Shoes", "color": "Black"}}, {{"id": "ex1_4", "sub_type": "Navy Suit Jacket", "color": "Navy"}}], "description": "An elegant and classic wedding ensemble."}}

Example 2 (Dinner Party):
Candidate: [Black Dress Shirt, Dark Jeans, Brown Loafers, Grey Blazer]
Final Output: {{"occasion": "dinner party", "outfit_items": [{{"id": "ex3_1", "sub_type": "Black Dress Shirt", "color": "Black"}}, {{"id": "ex3_2", "sub_type": "Dark Jeans", "color": "Dark Blue"}}, {{"id": "ex3_3", "sub_type": "Brown Loafers", "color": "Brown"}}, {{"id": "ex3_4", "sub_type": "Grey Blazer", "color": "Grey"}}], "description": "A stylish and contemporary outfit perfect for a dinner party."}}

Now, with these rules:
{rules_text}

And the following details:
Occasion: {user_message}
Outside Temperature: {outside_temp}
{wardrobe_text}

Generate your chain-of-thought reasoning (if any) and then output the final refined JSON object in the format:
{{
  "occasion": "<occasion string>",
  "outfit_items": [
    {{"id": "<item id>", "sub_type": "<item sub type>", "color": "<item color>"}},
    ... (3 to 6 items)
  ],
  "description": "<One short sentence describing the outfit>"
}}

Output only the final JSON object (with no extra text).
"""
    
    messages = [
        SystemMessage(content=combined_prompt),
        HumanMessage(content="Please provide your final refined JSON output.")
    ]
    
    try:
        generated = llm_client.invoke(messages)
        
        # Optionally remove stray chain-of-thought text if present
        if "### Output:" in generated:
            generated = generated.split("### Output:")[-1].strip()
        
        outfit_json = json.loads(generated)
    except json.JSONDecodeError as e:
        logger.error("JSON parsing error: %s in: %s", e, generated)
        outfit_json = {
            "occasion": target_occ,
            "outfit_items": [],
            "description": "Failed to generate a valid outfit. Please try again."
        }
    except Exception as e:
        logger.error("Error in generateOutfit: %s", e)
        outfit_json = {
            "occasion": target_occ,
            "outfit_items": [],
            "description": "An error occurred while generating your outfit. Please try again."
        }
    
    # Validate candidate item IDs
    valid_outfit_items = []
    for candidate_item in outfit_json.get("outfit_items", []):
        if candidate_item.get("id") in wardrobe_ids:
            valid_outfit_items.append(candidate_item)
        else:
            logger.warning("Candidate item with id %s not found in wardrobe. Removing item.", 
                          candidate_item.get("id"))
    
    outfit_json["outfit_items"] = valid_outfit_items
    
    # Additional check for Black Tie and Very Formal Events
    if target_occ in ["black tie event", "very formal occasion", "white tie event"]:
        found_formal_top = any(
            any(keyword in candidate_item.get("sub_type", "").lower() 
                for keyword in ["tuxedo", "tailcoat", "suit"])
            for candidate_item in outfit_json.get("outfit_items", [])
        )
        
        found_dress_shoes = any(
            "dress shoes" in candidate_item.get("sub_type", "").lower() or 
            "oxford" in candidate_item.get("sub_type", "").lower()
            for candidate_item in outfit_json.get("outfit_items", [])
        )
        
        notes = []
        if not found_formal_top:
            notes.append("Formal occasions require a tuxedo, tailcoat, or equivalent formal suit. Consider renting one if necessary.")
        if not found_dress_shoes:
            notes.append("Ensure you have appropriate dress shoes.")
        
        if notes:
            outfit_json["description"] += " " + " ".join(notes)
    
    return outfit_json