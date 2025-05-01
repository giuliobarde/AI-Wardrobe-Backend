import json
import logging
from typing import Dict, List, Set, Optional, Tuple
from langchain_core.messages import SystemMessage, HumanMessage

from .client import llm_client
from .config import ai_config
from .occasion import determineOccasions

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def filter_suitable_items(wardrobe_items: List[Dict], 
                         outside_temp: str, 
                         occasion: str) -> List[Dict]:
    """
    Filter wardrobe items based on weather and occasion suitability.
    
    Args:
        wardrobe_items: List of wardrobe items
        outside_temp: Temperature description
        occasion: Target occasion
        
    Returns:
        Filtered list of suitable wardrobe items
    """
    filtered_items = []
    
    # Parse temperature to determine weather condition
    temp_lower = outside_temp.lower()
    is_cold = any(word in temp_lower for word in ["cold", "freezing", "chilly", "cool"])
    is_hot = any(word in temp_lower for word in ["hot", "warm", "humid", "balmy"])
    
    for item in wardrobe_items:
        # Check weather suitability
        weather_suitable = item.get("suitable_for_weather", "").lower()
        if (is_cold and "cold" not in weather_suitable) or (is_hot and "hot" not in weather_suitable):
            if item.get("item_type") not in ["accessories", "shoes"]:  # Always include accessories and shoes
                continue
                
        # Check occasion suitability
        occasion_suitable = item.get("suitable_for_occasion", "").lower()
        if occasion and occasion.lower() not in occasion_suitable and "any" not in occasion_suitable:
            # Allow slight mismatch for some occasions
            if not (("formal" in occasion.lower() and "semi-formal" in occasion_suitable) or
                    ("casual" in occasion.lower() and "smart casual" in occasion_suitable)):
                continue
                
        filtered_items.append(item)
    
    return filtered_items


def categorize_wardrobe(wardrobe_items: List[Dict]) -> Dict[str, List[Dict]]:
    """
    Categorize wardrobe items by their type for easier outfit composition.
    
    Args:
        wardrobe_items: List of wardrobe items
        
    Returns:
        Dictionary with categories as keys and lists of items as values
    """
    categories = {
        "tops": [],
        "bottoms": [],
        "shoes": [],
        "outerwear": [],
        "accessories": [],
        "dresses": [],
        "suits": []
    }
    
    for item in wardrobe_items:
        item_type = item.get("item_type", "").lower()
        
        if item_type == "top":
            categories["tops"].append(item)
        elif item_type == "bottom":
            categories["bottoms"].append(item)
        elif item_type == "shoes":
            categories["shoes"].append(item)
        elif item_type in ["jacket", "coat", "outerwear"]:
            categories["outerwear"].append(item)
        elif item_type == "accessory":
            categories["accessories"].append(item)
        elif item_type == "dress":
            categories["dresses"].append(item)
        elif item_type == "suit":
            categories["suits"].append(item)
            
    return categories


def check_outfit_balance(outfit_items: List[Dict]) -> Tuple[bool, str]:
    """
    Check if an outfit has a balanced composition of items.
    
    Args:
        outfit_items: List of outfit items
        
    Returns:
        Tuple of (is_balanced, reason)
    """
    # Count different types of items
    item_types = {}
    for item in outfit_items:
        item_type = item.get("item_type", "unknown").lower()
        item_types[item_type] = item_types.get(item_type, 0) + 1
    
    # Check for basic outfit requirements
    has_top = item_types.get("top", 0) >= 1 or item_types.get("dress", 0) >= 1 or item_types.get("suit", 0) >= 1
    has_bottom = item_types.get("bottom", 0) >= 1 or item_types.get("dress", 0) >= 1 or item_types.get("suit", 0) >= 1
    has_shoes = item_types.get("shoes", 0) >= 1
    
    if not has_top:
        return False, "Missing a top item"
    if not has_bottom:
        return False, "Missing a bottom item"
    if not has_shoes:
        return False, "Missing shoes"
    
    # Check for excessive items
    if item_types.get("top", 0) > 2:
        return False, "Too many tops (maximum 2)"
    if item_types.get("bottom", 0) > 1:
        return False, "Too many bottoms (maximum 1)"
    if item_types.get("shoes", 0) > 1:
        return False, "Too many shoes (maximum 1)"
    if item_types.get("outerwear", 0) > 2:
        return False, "Too many outerwear pieces (maximum 2)"
    
    return True, "Outfit is balanced"


def check_style_coherence(outfit_items: List[Dict]) -> Tuple[bool, str]:
    """
    Check if the outfit has coherent style, colors, and patterns.
    
    Args:
        outfit_items: List of outfit items
        
    Returns:
        Tuple of (is_coherent, reason)
    """
    formality_levels = [item.get("formality", "").lower() for item in outfit_items]
    patterns = [item.get("pattern", "").lower() for item in outfit_items]
    colors = [item.get("color", "").lower() for item in outfit_items]
    
    # Check formality coherence
    if "formal" in formality_levels and "casual" in formality_levels:
        return False, "Mixed formality levels: formal and casual items together"
    
    # Check pattern mixing
    pattern_count = sum(1 for p in patterns if p and p != "solid" and p != "none")
    if pattern_count > 2:
        return False, "Too many patterns (maximum 2 patterned items)"
    
    # Check color harmony
    # This is a simplified check - could be made more sophisticated
    if len(set(colors)) > 4:
        return False, "Too many different colors (maximum 4)"
    
    return True, "Outfit style is coherent"


def format_wardrobe_items(wardrobe_items: List[Dict]) -> Tuple[List[str], Set[str]]:
    """
    Format wardrobe items for prompt and return set of IDs.
    
    Args:
        wardrobe_items: List of wardrobe items
        
    Returns:
        Tuple of (formatted_items_list, wardrobe_ids_set)
    """
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
    
    return formatted_items, wardrobe_ids


def build_prompt(user_message: str, 
                outside_temp: str, 
                formatted_items: List[str], 
                target_occ: str, 
                config: Dict) -> str:
    """
    Build the LLM prompt for outfit generation.
    
    Args:
        user_message: User's message
        outside_temp: Outside temperature
        formatted_items: Formatted wardrobe items
        target_occ: Target occasion
        config: Occasion configuration
        
    Returns:
        Complete prompt string
    """
    # Build rules text
    rules_text = (
        f"Allowed items: {', '.join(config['items']) if config.get('items') else 'Any'}, "
        f"Rules: {config.get('rules', '')}, "
        f"Strictness: {config.get('strictness', '')}, "
        f"Description: {config.get('description', '')}\n"
        f"IMPORTANT: Do not include any items with 'tuxedo' or 'tailcoat' in their sub_type "
        f"if the occasion is not a 'black tie event' or 'white tie event'."
    )
    
    wardrobe_text = "The user's wardrobe includes: " + " | ".join(formatted_items) + "."
    
    weather_guidance = ""
    if "cold" in outside_temp.lower() or "chilly" in outside_temp.lower():
        weather_guidance = "Since it's cold, prioritize warmth with appropriate layers and outerwear."
    elif "hot" in outside_temp.lower() or "warm" in outside_temp.lower():
        weather_guidance = "Since it's hot, prioritize breathable materials and lighter clothing."
    
    # Combined prompt for outfit generation and refinement
    combined_prompt = f"""
Step: Generate and Refine Outfit Suggestion.
You are a style assistant tasked with generating an outfit suggestion based on the following details and guardrails.

1. Use chain-of-thought reasoning to consider the user's message, outside temperature, and wardrobe.
2. Ensure that only items from the provided wardrobe (with matching Item IDs) are selected.
3. Do not include any items with 'tuxedo' or 'tailcoat' in their sub_type if the occasion is not a 'black tie event' or 'white tie event'.
4. The outfit must consist of 3 to 6 items, including:
   - Exactly one pair of shoes
   - Either one pair of pants OR one dress/skirt (not both)
   - Between one and two tops (unless a dress is selected)
   - Between zero and two outerwear pieces depending on weather
   - Between zero and two accessories to complete the look

5. Consider color harmony and pattern coordination:
   - Limit to 3-4 colors maximum in the entire outfit
   - Avoid mixing more than 2 patterns
   - Ensure the formality level is consistent across all items

6. {weather_guidance}

Examples for guidance:
Example 1 (Wedding):
Candidate: [White Dress Shirt, Navy Suit Pants, Black Dress Shoes, Navy Suit Jacket]
Final Output: {{"occasion": "wedding", "outfit_items": [{{"id": "ex1_1", "sub_type": "White Dress Shirt", "color": "White"}}, {{"id": "ex1_2", "sub_type": "Navy Suit Pants", "color": "Navy"}}, {{"id": "ex1_3", "sub_type": "Black Dress Shoes", "color": "Black"}}, {{"id": "ex1_4", "sub_type": "Navy Suit Jacket", "color": "Navy"}}], "description": "An elegant and classic wedding ensemble."}}

Example 2 (Dinner Party):
Candidate: [Black Dress Shirt, Dark Jeans, Brown Loafers, Grey Blazer]
Final Output: {{"occasion": "dinner party", "outfit_items": [{{"id": "ex3_1", "sub_type": "Black Dress Shirt", "color": "Black"}}, {{"id": "ex3_2", "sub_type": "Dark Jeans", "color": "Dark Blue"}}, {{"id": "ex3_3", "sub_type": "Brown Loafers", "color": "Brown"}}, {{"id": "ex3_4", "sub_type": "Grey Blazer", "color": "Grey"}}], "description": "A stylish and contemporary outfit perfect for a dinner party."}}

Example 3 (Hot Weather Casual):
Candidate: [White T-Shirt, Khaki Shorts, Brown Sandals, Straw Hat]
Final Output: {{"occasion": "casual outing", "outfit_items": [{{"id": "ex4_1", "sub_type": "White T-Shirt", "color": "White"}}, {{"id": "ex4_2", "sub_type": "Khaki Shorts", "color": "Beige"}}, {{"id": "ex4_3", "sub_type": "Brown Sandals", "color": "Brown"}}, {{"id": "ex4_4", "sub_type": "Straw Hat", "color": "Natural"}}], "description": "A comfortable and breezy outfit for hot weather."}}

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
    {{"id": "<item id>", "sub_type": "<item sub type>", "color": "<item color>", "item_type": "<item type>"}},
    ... (3 to 6 items)
  ],
  "description": "<One short sentence describing the outfit>",
  "styling_tips": "<One short tip for wearing or accessorizing this outfit>"
}}

Output only the final JSON object (with no extra text).
"""
    return combined_prompt


def validate_outfit(outfit_json: Dict, 
                   wardrobe_ids: Set[str], 
                   target_occ: str) -> Dict:
    """
    Validate and enhance the outfit response.
    
    Args:
        outfit_json: Generated outfit JSON
        wardrobe_ids: Set of valid wardrobe IDs
        target_occ: Target occasion
        
    Returns:
        Validated and enhanced outfit JSON
    """
    # Validate candidate item IDs
    valid_outfit_items = []
    for candidate_item in outfit_json.get("outfit_items", []):
        if candidate_item.get("id") in wardrobe_ids:
            valid_outfit_items.append(candidate_item)
        else:
            logger.warning("Candidate item with id %s not found in wardrobe. Removing item.", 
                          candidate_item.get("id"))
    
    outfit_json["outfit_items"] = valid_outfit_items
    
    # Ensure required fields exist
    if "styling_tips" not in outfit_json:
        outfit_json["styling_tips"] = "Try tucking in the shirt and adding a simple accessory to complete the look."
    
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
            outfit_json["styling_tips"] = " ".join(notes) + " " + outfit_json.get("styling_tips", "")
    
    return outfit_json


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
    try:
        # Determine target occasion and configuration
        target_occ = determineOccasions(user_message)
        config = ai_config.get_occasion_config(target_occ)
        
        # Filter wardrobe items based on suitability
        filtered_items = filter_suitable_items(wardrobe_items, outside_temp, target_occ)
        
        # If too few items remain after filtering, use the original list
        if len(filtered_items) < 10:
            logger.info("Too few items after filtering (%d). Using original wardrobe.", len(filtered_items))
            filtered_items = wardrobe_items
        
        # Format wardrobe items
        formatted_items, wardrobe_ids = format_wardrobe_items(filtered_items)
        
        # Set generation temperature based on occasion formality
        generation_temp = ai_config.get_occasion_temperature(target_occ)
        llm_client.with_temperature(generation_temp)
        
        # Build the prompt
        combined_prompt = build_prompt(
            user_message=user_message,
            outside_temp=outside_temp,
            formatted_items=formatted_items,
            target_occ=target_occ,
            config=config
        )
        
        # Generate outfit suggestion
        messages = [
            SystemMessage(content=combined_prompt),
            HumanMessage(content="Please provide your final refined JSON output.")
        ]
        
        generated = llm_client.invoke(messages)
        
        # Optionally remove stray chain-of-thought text if present
        if "### Output:" in generated:
            generated = generated.split("### Output:")[-1].strip()
        
        # Extract JSON content if wrapped in markdown code blocks
        if "```json" in generated:
            generated = generated.split("```json")[1].split("```")[0].strip()
        elif "```" in generated:
            generated = generated.split("```")[1].strip()
        
        outfit_json = json.loads(generated)
        
        # Validate and enhance outfit
        validated_outfit = validate_outfit(outfit_json, wardrobe_ids, target_occ)
        
        return validated_outfit
        
    except json.JSONDecodeError as e:
        logger.error("JSON parsing error: %s in: %s", e, generated)
        outfit_json = {
            "occasion": target_occ,
            "outfit_items": [],
            "description": "Failed to generate a valid outfit. Please try again.",
            "styling_tips": "Try again with a more specific request."
        }
    except Exception as e:
        logger.error("Error in generateOutfit: %s", e)
        outfit_json = {
            "occasion": target_occ if 'target_occ' in locals() else "unknown",
            "outfit_items": [],
            "description": "An error occurred while generating your outfit. Please try again.",
            "styling_tips": "Try again with a more specific request."
        }
    
    return outfit_json