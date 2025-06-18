import json
import logging
from typing import Dict, List, Set, Tuple, Optional
from langchain_core.messages import SystemMessage, HumanMessage
from dataclasses import dataclass
from enum import Enum

from api.llm.client import llm_client
from api.llm.config import ai_config
from api.llm.occasion import determineOccasions




# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)




class ItemType(Enum):
    TOP = "top"
    BOTTOM = "bottom"
    SHOES = "shoes"
    OUTERWEAR = "outerwear"
    ACCESSORY = "accessory"
    DRESS = "dress"
    SUIT = "suit"

    @classmethod
    def from_string(cls, value: str) -> 'ItemType':
        """Safely convert a string to ItemType, handling common variations."""
        if not value:
            raise ValueError("Item type cannot be empty")
            
        value = value.lower().strip()
        # Handle common variations and typos
        type_mapping = {
            'tops': cls.TOP,
            'top': cls.TOP,
            'bottoms': cls.BOTTOM,
            'bottom': cls.BOTTOM,
            'shoe': cls.SHOES,
            'shoes': cls.SHOES,
            'footwear': cls.SHOES,
            'outer': cls.OUTERWEAR,
            'outerware': cls.OUTERWEAR,  # Common typo
            'outerwear': cls.OUTERWEAR,
            'jacket': cls.OUTERWEAR,
            'coat': cls.OUTERWEAR,
            'accessories': cls.ACCESSORY,
            'accessory': cls.ACCESSORY,
            'dresses': cls.DRESS,
            'dress': cls.DRESS,
            'suits': cls.SUIT,
            'suit': cls.SUIT
        }
        
        if value in type_mapping:
            return type_mapping[value]
            
        # Try to find a close match
        for valid_type in cls:
            if valid_type.value in value or value in valid_type.value:
                return valid_type
                
        raise ValueError(f"Invalid item type: {value}")

class FormalityLevel(Enum):
    VERY_LOW = "very low"
    LOW = "low"
    SOMEWHAT_LOW = "somewhat low"
    MEDIUM = "medium"
    SOMEWHAT_HIGH = "somewhat high"
    HIGH = "high"
    VERY_HIGH = "very high"
    BUSINESS_CASUAL = "business casual"
    SMART_CASUAL = "smart casual"
    CASUAL = "casual"
    BUSINESS_FORMAL = "business formal"
    COCKTAIL = "cocktail"
    BLACK_TIE = "black tie"
    WHITE_TIE = "white tie"

@dataclass
class WardrobeItem:
    id: str
    item_type: ItemType
    material: str
    color: str
    formality: FormalityLevel
    pattern: str
    fit: str
    suitable_for_weather: List[str]
    suitable_for_occasion: List[str]
    sub_type: str
    image_link: Optional[str] = None
    favorite: bool = False

    @classmethod
    def from_dict(cls, data: Dict) -> 'WardrobeItem':
        """Create a WardrobeItem from a dictionary with error handling."""
        try:
            # Safely convert item_type
            item_type = ItemType.from_string(data.get('item_type', ''))
            
            # Safely convert formality with fallback
            try:
                formality = FormalityLevel(data.get('formality', 'medium').lower())
            except ValueError:
                formality = FormalityLevel.MEDIUM
                logger.warning(f"Invalid formality level for item {data.get('id')}, defaulting to MEDIUM")
            
            # Safely convert weather and occasion lists
            weather = data.get('suitable_for_weather', '')
            weather_list = weather.split(',') if isinstance(weather, str) else weather or []
            
            occasion = data.get('suitable_for_occasion', '')
            occasion_list = occasion.split(',') if isinstance(occasion, str) else occasion or []
            
            return cls(
                id=data['id'],
                item_type=item_type,
                material=data.get('material', 'unknown'),
                color=data.get('color', 'unknown'),
                formality=formality,
                pattern=data.get('pattern', 'solid'),
                fit=data.get('fit', 'regular'),
                suitable_for_weather=weather_list,
                suitable_for_occasion=occasion_list,
                sub_type=data.get('sub_type', ''),
                image_link=data.get('image_link'),
                favorite=data.get('favorite', False)
            )
        except Exception as e:
            logger.error(f"Error converting wardrobe item {data.get('id', 'unknown')}: {str(e)}")
            raise ValueError(f"Invalid wardrobe item data: {str(e)}")

    def to_dict(self) -> Dict:
        """Convert WardrobeItem to dictionary."""
        return {
            'id': self.id,
            'item_type': self.item_type.value,
            'material': self.material,
            'color': self.color,
            'formality': self.formality.value,
            'pattern': self.pattern,
            'fit': self.fit,
            'suitable_for_weather': ','.join(self.suitable_for_weather),
            'suitable_for_occasion': ','.join(self.suitable_for_occasion),
            'sub_type': self.sub_type,
            'image_link': self.image_link,
            'favorite': self.favorite
        }

    def is_suitable_for_weather(self, weather_data: Dict) -> bool:
        """Check if item is suitable for given weather conditions."""
        temp = weather_data.get("temperature", 0)
        feels_like = weather_data.get("feels_like", temp)
        description = weather_data.get("description", "").lower()
        humidity = weather_data.get("humidity", 0)
        wind_speed = weather_data.get("wind_speed", 0)
        
        # Use feels_like temperature for more accurate comfort assessment
        effective_temp = feels_like
        
        # More granular temperature ranges
        if effective_temp < 10 and "very cold" not in self.suitable_for_weather:
            return False
        elif effective_temp < 15 and "cold" not in self.suitable_for_weather:
            return False
        elif effective_temp > 30 and "very hot" not in self.suitable_for_weather:
            return False
        elif effective_temp > 25 and "hot" not in self.suitable_for_weather:
            return False
            
        # Enhanced weather condition checks
        if any(condition in description for condition in ["rain", "drizzle", "shower"]) and "rainy" not in self.suitable_for_weather:
            return False
        if any(condition in description for condition in ["snow", "sleet", "flurries"]) and "snowy" not in self.suitable_for_weather:
            return False
        if wind_speed > 20 or "wind" in description:
            if "windy" not in self.suitable_for_weather and not any(material in self.material.lower() for material in ["windproof", "wind-resistant"]):
                return False
                
        # Humidity-based checks
        if humidity > 70 and "humid" not in self.suitable_for_weather:
            if not any(material in self.material.lower() for material in ["cotton", "linen", "breathable", "moisture-wicking"]):
                return False
                
        # Check forecast if available
        forecast = weather_data.get("forecast", {})
        if forecast:
            forecast_high = forecast.get("high", temp)
            forecast_low = forecast.get("low", temp)
            
            # If there's a significant temperature range, check if item can handle both extremes
            if forecast_high - forecast_low > 10:
                if not any(condition in self.suitable_for_weather for condition in ["layered", "versatile"]):
                    return False
            
        return True

    def is_suitable_for_occasion(self, occasion: str) -> bool:
        """Check if item is suitable for given occasion."""
        occasion = occasion.lower()
        return any(
            occ.lower() in occasion or occasion in occ.lower()
            for occ in self.suitable_for_occasion
        )




def filter_suitable_items(wardrobe_items: List[WardrobeItem], 
                         weather_data: Dict, 
                         occasion: str) -> List[WardrobeItem]:
    """
    Filter wardrobe items based on weather and occasion suitability.
    
    Args:
        wardrobe_items: List of wardrobe items
        weather_data: Weather data dictionary containing temperature, description, etc.
        occasion: Target occasion
        
    Returns:
        Filtered list of suitable wardrobe items
    """
    filtered_items = []
    
    for item in wardrobe_items:
        # Check weather and occasion suitability using the new methods
        if not item.is_suitable_for_weather(weather_data):
            if item.item_type not in [ItemType.ACCESSORY, ItemType.SHOES]:
                continue
                
        if not item.is_suitable_for_occasion(occasion):
            # Allow slight mismatch for some occasions
            if not (("formal" in occasion.lower() and "semi-formal" in item.suitable_for_occasion) or
                    ("casual" in occasion.lower() and "smart casual" in item.suitable_for_occasion)):
                continue
                
        filtered_items.append(item)
    
    return filtered_items




def categorize_wardrobe(wardrobe_items: List[WardrobeItem]) -> Dict[ItemType, List[WardrobeItem]]:
    """
    Categorize wardrobe items by their type for easier outfit composition.
    
    Args:
        wardrobe_items: List of wardrobe items
        
    Returns:
        Dictionary with categories as keys and lists of items as values
    """
    categories = {item_type: [] for item_type in ItemType}
    
    for item in wardrobe_items:
        categories[item.item_type].append(item)
            
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




def format_wardrobe_items(wardrobe_items: List[WardrobeItem]) -> Tuple[List[str], Set[str]]:
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
        wardrobe_ids.add(item.id)
        formatted_items.append(
            f"Item ID: {item.id}, Type: {item.item_type.value}, "
            f"Material: {item.material}, "
            f"Color: {item.color}, "
            f"Formality: {item.formality.value}, "
            f"Pattern: {item.pattern}, "
            f"Fit: {item.fit}, "
            f"Weather Suitability: {', '.join(item.suitable_for_weather)}, "
            f"Occasion Suitability: {', '.join(item.suitable_for_occasion)}, "
            f"Sub Type: {item.sub_type}"
        )
    
    return formatted_items, wardrobe_ids




def build_prompt(user_message: str, 
                weather_data: Dict, 
                formatted_items: List[str], 
                target_occ: str, 
                config: Dict) -> str:
    """
    Build the LLM prompt for outfit generation.
    
    Args:
        user_message: User's message
        weather_data: Weather data dictionary
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
    
    # Build comprehensive weather guidance
    temp = weather_data.get("temperature", 0)
    feels_like = weather_data.get("feels_like", temp)
    forecast = weather_data.get("forecast", {})
    forecast_high = forecast.get("high", temp)
    forecast_low = forecast.get("low", temp)
    description = weather_data.get("description", "").lower()
    humidity = weather_data.get("humidity", 0)
    wind_speed = weather_data.get("wind_speed", 0)
    
    weather_guidance = []
    
    # Temperature range guidance
    temp_range = forecast_high - forecast_low if forecast_high and forecast_low else 0
    if temp_range > 15:
        weather_guidance.append(
            f"Temperature will vary significantly today ({temp_range}°C range from {forecast_low}°C to {forecast_high}°C). "
            "Prioritize versatile, layered pieces that can be easily added or removed throughout the day."
        )
    elif temp_range > 10:
        weather_guidance.append(
            f"Temperature will vary moderately today ({temp_range}°C range from {forecast_low}°C to {forecast_high}°C). "
            "Consider items that can be layered or adjusted for comfort."
        )
    
    # Current temperature guidance with feels-like consideration
    if feels_like < 10 or "very cold" in description:
        weather_guidance.append(
            "Current conditions are very cold. Prioritize thermal layers, insulated outerwear, and warm accessories. "
            "Consider materials like wool, fleece, or thermal fabrics."
        )
    elif feels_like < 15 or "cold" in description:
        weather_guidance.append(
            "Current conditions are cold. Prioritize warmth with appropriate layers and outerwear. "
            "Consider materials that provide good insulation."
        )
    elif feels_like > 30 or "very hot" in description:
        weather_guidance.append(
            "Current conditions are very hot. Prioritize lightweight, breathable materials and minimal layers. "
            "Consider moisture-wicking fabrics and loose-fitting items."
        )
    elif feels_like > 25 or "hot" in description:
        weather_guidance.append(
            "Current conditions are hot. Prioritize breathable materials and lighter clothing. "
            "Consider natural fibers like cotton or linen."
        )
    
    # Forecast-specific guidance
    if forecast_high and forecast_low:
        if forecast_high > 35:
            weather_guidance.append(
                "It will get very hot later. Avoide multiple layers and prioritize breathable materials. Avoid sweatshirts and sweaters."
            )
        elif forecast_high > 30:
            weather_guidance.append(
                "It will get quite hot later. Include items that can be easily removed and prioritize breathable materials. Avoid sweatshirts and sweaters."
            )
        elif forecast_high > 25:
            weather_guidance.append(
                "It will get quite warm later. Include items that can be easily removed or adjusted."
            )
        if forecast_low < 10:
            weather_guidance.append(
                "It will get very cold later. Include items that can be easily added for warmth, such as thermal layers or insulated outerwear."
            )
        elif forecast_low < 15:
            weather_guidance.append(
                "It will get cold later. Include items that can be easily added for warmth."
            )
    
    # Enhanced weather conditions guidance
    if any(condition in description for condition in ["rain", "drizzle", "shower"]):
        weather_guidance.append(
            "Include waterproof or water-resistant outerwear and footwear. "
            "Consider quick-drying materials and avoid fabrics that absorb water easily."
        )
        
    if any(condition in description for condition in ["snow", "sleet", "flurries"]):
        weather_guidance.append(
            "Include insulated, waterproof outerwear and footwear. "
            "Consider thermal layers and materials that provide good insulation."
        )
        
    if wind_speed > 30 or "strong wind" in description:
        weather_guidance.append(
            "Strong winds expected. Prioritize wind-resistant outerwear and secure accessories. "
            "Consider materials that provide wind protection."
        )
    elif wind_speed > 20 or "windy" in description:
        weather_guidance.append(
            "Windy conditions expected. Consider wind-resistant layers and secure accessories."
        )
        
    if humidity > 80 or "very humid" in description:
        weather_guidance.append(
            "Very humid conditions. Choose moisture-wicking fabrics and avoid heavy materials. "
            "Consider breathable, quick-drying items."
        )
    elif humidity > 70 or "humid" in description:
        weather_guidance.append(
            "Humid conditions. Choose moisture-wicking fabrics and avoid heavy materials."
        )
    
    # Add UV index guidance if available
    uv_index = weather_data.get("uv_index", 0)
    if uv_index > 8:
        weather_guidance.append(
            "Very high UV index. Include sun protection items and consider covering exposed skin."
        )
    elif uv_index > 6:
        weather_guidance.append(
            "High UV index. Consider sun protection items."
        )
    
    weather_guidance_text = " ".join(weather_guidance) if weather_guidance else "Consider the current weather conditions when selecting items."
    
    # Combined prompt for outfit generation and refinement
    combined_prompt = f"""
Step: Generate and Refine Outfit Suggestion.
You are a style assistant tasked with generating an outfit suggestion based on the following details and guardrails.

1. Use chain-of-thought reasoning to consider the user's message, weather conditions, and wardrobe.
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

6. {weather_guidance_text}

7. IMPORTANT: Each item ID must be unique in the outfit. Do not include the same item ID more than once.
8. IMPORTANT: Ensure that each item's type classification (tops, bottoms, shoes, etc.) matches its actual type. For example, don't classify a shirt as shoes.

Examples for guidance:
Example 1 (Wedding):
Candidate: [White Dress Shirt, Navy Suit Pants, Black Dress Shoes, Navy Suit Jacket]
Final Output: {{"occasion": "wedding", "outfit_items": [{{"id": "ex1_1", "sub_type": "White Dress Shirt", "color": "White", "item_type": "top"}}, {{"id": "ex1_2", "sub_type": "Navy Suit Pants", "color": "Navy", "item_type": "bottom"}}, {{"id": "ex1_3", "sub_type": "Black Dress Shoes", "color": "Black", "item_type": "shoes"}}, {{"id": "ex1_4", "sub_type": "Navy Suit Jacket", "color": "Navy", "item_type": "outerwear"}}], "description": "An elegant and classic wedding ensemble."}}

Example 2 (Dinner Party):
Candidate: [Black Dress Shirt, Dark Jeans, Brown Loafers, Grey Blazer]
Final Output: {{"occasion": "dinner party", "outfit_items": [{{"id": "ex3_1", "sub_type": "Black Dress Shirt", "color": "Black", "item_type": "top"}}, {{"id": "ex3_2", "sub_type": "Dark Jeans", "color": "Dark Blue", "item_type": "bottom"}}, {{"id": "ex3_3", "sub_type": "Brown Loafers", "color": "Brown", "item_type": "shoes"}}, {{"id": "ex3_4", "sub_type": "Grey Blazer", "color": "Grey", "item_type": "outerwear"}}], "description": "A stylish and contemporary outfit perfect for a dinner party."}}

Example 3 (Hot Weather Casual):
Candidate: [White T-Shirt, Khaki Shorts, Brown Sandals, Straw Hat]
Final Output: {{"occasion": "casual outing", "outfit_items": [{{"id": "ex4_1", "sub_type": "White T-Shirt", "color": "White", "item_type": "top"}}, {{"id": "ex4_2", "sub_type": "Khaki Shorts", "color": "Beige", "item_type": "bottom"}}, {{"id": "ex4_3", "sub_type": "Brown Sandals", "color": "Brown", "item_type": "shoes"}}, {{"id": "ex4_4", "sub_type": "Straw Hat", "color": "Natural", "item_type": "accessory"}}], "description": "A comfortable and breezy outfit for hot weather."}}

Now, with these rules:
{rules_text}

And the following details:
Occasion: {user_message}
Weather Conditions: Current Temperature {temp}°C, {description}, Humidity {humidity}%, Wind Speed {wind_speed} km/h
Forecast: High {forecast_high}°C, Low {forecast_low}°C
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




def check_duplicate_items(outfit_items: List[Dict]) -> Tuple[bool, str]:
    """
    Check if an outfit has duplicate item IDs or mismatched type classifications.
    
    Args:
        outfit_items: List of outfit items
        
    Returns:
        Tuple of (is_valid, reason)
    """
    # Check for duplicate IDs
    item_ids = {}
    for item in outfit_items:
        item_id = item.get("id")
        if item_id in item_ids:
            return False, f"Duplicate item ID found: {item_id}"
        item_ids[item_id] = item.get("item_type")
    
    return True, "No duplicate items found"


def validate_outfit_composition(outfit_items: List[Dict]) -> Tuple[bool, str, Dict]:
    """
    Validate that an outfit meets basic composition requirements:
    - Exactly one pair of shoes
    - Either one bottom OR one dress (not both)
    - At least one top (unless a dress is selected)
    - Appropriate number of accessories and outerwear
    
    Args:
        outfit_items: List of outfit items
        
    Returns:
        Tuple of (is_valid, reason, item_counts)
    """
    # Count item types
    item_counts = {
        "top": 0,
        "bottom": 0,
        "shoes": 0,
        "outerwear": 0,
        "accessory": 0,
        "dress": 0,
        "suit": 0,
        "other": 0
    }
    
    for item in outfit_items:
        item_type = item.get("item_type", "").lower()
        if item_type in item_counts:
            item_counts[item_type] += 1
        else:
            item_counts["other"] += 1
    
    # Check shoes requirement
    if item_counts["shoes"] == 0:
        return False, "Missing shoes. Every outfit must include exactly one pair of shoes.", item_counts
    elif item_counts["shoes"] > 1:
        return False, f"Too many shoes ({item_counts['shoes']}). Outfit should include exactly one pair of shoes.", item_counts
    
    # Check bottoms vs dress requirement
    has_bottom = item_counts["bottom"] > 0
    has_dress = item_counts["dress"] > 0
    has_suit = item_counts["suit"] > 0
    
    if not (has_bottom or has_dress or has_suit):
        return False, "Missing bottom or dress. Outfit must include either pants/skirt, a dress, or a suit.", item_counts
    
    if has_bottom and item_counts["bottom"] > 1:
        return False, f"Too many bottom items ({item_counts['bottom']}). Outfit should include at most one bottom item.", item_counts
    
    # Check top requirement (unless dress or suit is present)
    if not (has_dress or has_suit) and item_counts["top"] == 0:
        return False, "Missing top. Outfit must include at least one top unless a dress or suit is selected.", item_counts
    
    if item_counts["top"] > 2:
        return False, f"Too many tops ({item_counts['top']}). Outfit should include at most two tops.", item_counts
    
    # Outerwear check
    if item_counts["outerwear"] > 2:
        return False, f"Too many outerwear items ({item_counts['outerwear']}). Outfit should include at most two outerwear pieces.", item_counts
    
    # Accessory check
    if item_counts["accessory"] > 3:
        return False, f"Too many accessories ({item_counts['accessory']}). Outfit should include at most three accessories.", item_counts
    
    # Total items check
    total_items = sum(item_counts.values())
    if total_items < 3:
        return False, f"Too few items ({total_items}). Outfit should include at least 3 items.", item_counts
    if total_items > 7:
        return False, f"Too many items ({total_items}). Outfit should include at most 7 items.", item_counts
    
    return True, "Outfit composition is valid.", item_counts




def process_outfit_issues(outfit_json: Dict, 
                         wardrobe_items: List[Dict], 
                         wardrobe_ids: Set[str]) -> Dict:
    """
    Process outfit validation issues and attempt to fix them.
    
    Args:
        outfit_json: The outfit JSON to validate and fix
        wardrobe_items: Full list of wardrobe items
        wardrobe_ids: Set of valid wardrobe IDs
        
    Returns:
        Fixed outfit JSON if possible, otherwise original with warnings
    """
    # First validate the outfit composition
    valid_composition, composition_reason, item_counts = validate_outfit_composition(outfit_json.get("outfit_items", []))
    
    # If composition is invalid, try to fix it
    if not valid_composition:
        # Create maps for faster lookups
        item_type_map = {}
        for item in wardrobe_items:
            item_type = item.get("item_type", "").lower()
            if item_type not in item_type_map:
                item_type_map[item_type] = []
            item_type_map[item_type].append(item)
        
        # Get current item IDs to avoid duplicates
        current_ids = {item.get("id") for item in outfit_json.get("outfit_items", [])}
        
        # Check if we need to add shoes
        if item_counts["shoes"] == 0:
            if "shoes" in item_type_map and item_type_map["shoes"]:
                # Find a suitable shoe to add
                for shoe in item_type_map["shoes"]:
                    if shoe.get("id") not in current_ids:
                        outfit_json["outfit_items"].append({
                            "id": shoe.get("id"),
                            "sub_type": shoe.get("sub_type", "Shoes"),
                            "color": shoe.get("color", "Unknown"),
                            "item_type": "shoes"
                        })
                        outfit_json["warnings"] = outfit_json.get("warnings", []) + ["Added missing shoes automatically"]
                        break
        
        # Check if we need to remove extra bottoms (keep only the first one)
        if item_counts["bottom"] > 1:
            bottom_items = [item for item in outfit_json["outfit_items"] if item.get("item_type") == "bottom"]
            to_keep = bottom_items[0]
            outfit_json["outfit_items"] = [
                item for item in outfit_json["outfit_items"] 
                if item.get("item_type") != "bottom" or item.get("id") == to_keep.get("id")
            ]
            outfit_json["warnings"] = outfit_json.get("warnings", []) + [
                f"Removed extra bottom items, kept only {to_keep.get('sub_type', 'one bottom item')}"
            ]
        
        # Check if we need to add a top when no dress/suit is present
        if not (item_counts["dress"] > 0 or item_counts["suit"] > 0) and item_counts["top"] == 0:
            if "top" in item_type_map and item_type_map["top"]:
                # Find a suitable top to add
                for top in item_type_map["top"]:
                    if top.get("id") not in current_ids:
                        outfit_json["outfit_items"].append({
                            "id": top.get("id"),
                            "sub_type": top.get("sub_type", "Top"),
                            "color": top.get("color", "Unknown"),
                            "item_type": "top"
                        })
                        outfit_json["warnings"] = outfit_json.get("warnings", []) + ["Added missing top automatically"]
                        break
        
        # Check if we need to add a bottom when no dress/suit is present
        if not (item_counts["dress"] > 0 or item_counts["suit"] > 0) and item_counts["bottom"] == 0:
            if "bottom" in item_type_map and item_type_map["bottom"]:
                # Find a suitable bottom to add
                for bottom in item_type_map["bottom"]:
                    if bottom.get("id") not in current_ids:
                        outfit_json["outfit_items"].append({
                            "id": bottom.get("id"),
                            "sub_type": bottom.get("sub_type", "Bottom"),
                            "color": bottom.get("color", "Unknown"),
                            "item_type": "bottom"
                        })
                        outfit_json["warnings"] = outfit_json.get("warnings", []) + ["Added missing bottom automatically"]
                        break
    
    # Update the composition validation after fixes
    valid_composition, composition_reason, item_counts = validate_outfit_composition(outfit_json.get("outfit_items", []))
    
    # If still invalid, add warning
    if not valid_composition:
        outfit_json["warnings"] = outfit_json.get("warnings", []) + [f"Composition issue: {composition_reason}"]
    
    return outfit_json




def validate_outfit(outfit_json: Dict, 
                   wardrobe_ids: Set[str], 
                   target_occ: str,
                   wardrobe_items: List[Dict]) -> Dict:
    """
    Validate and enhance the outfit response.
    
    Args:
        outfit_json: Generated outfit JSON
        wardrobe_ids: Set of valid wardrobe IDs
        target_occ: Target occasion
        wardrobe_items: Original wardrobe items for type verification
        
    Returns:
        Validated and enhanced outfit JSON
    """
    # Create a mapping of item IDs to their correct types
    wardrobe_id_to_type = {item.get("id"): item.get("item_type") for item in wardrobe_items if "id" in item}
    wardrobe_id_to_item = {item.get("id"): item for item in wardrobe_items if "id" in item}
    
    # Validate candidate item IDs and ensure correct type
    valid_outfit_items = []
    seen_ids = set()
    seen_types = {ItemType.SHOES: 0, ItemType.BOTTOM: 0, ItemType.TOP: 0}
    
    for candidate_item in outfit_json.get("outfit_items", []):
        item_id = candidate_item.get("id")
        
        # Skip duplicate items
        if item_id in seen_ids:
            logger.warning("Duplicate item with id %s found in outfit. Removing duplicate.", item_id)
            continue
        
        # Verify item exists in wardrobe
        if item_id in wardrobe_ids:
            # Get the correct type from the wardrobe
            correct_type = ItemType.from_string(wardrobe_id_to_type.get(item_id, ""))
            
            # Check if we already have too many of this type
            if correct_type in seen_types:
                if correct_type == ItemType.SHOES and seen_types[correct_type] >= 1:
                    logger.warning("Too many shoes in outfit. Skipping item %s", item_id)
                    continue
                elif correct_type == ItemType.BOTTOM and seen_types[correct_type] >= 1:
                    logger.warning("Too many bottom items in outfit. Skipping item %s", item_id)
                    continue
                elif correct_type == ItemType.TOP and seen_types[correct_type] >= 2:
                    logger.warning("Too many top items in outfit. Skipping item %s", item_id)
                    continue
            
            # Update the item type and increment counter
            candidate_item["item_type"] = correct_type.value
            seen_types[correct_type] = seen_types.get(correct_type, 0) + 1
                
            # Ensure other item fields are correct too
            original_item = wardrobe_id_to_item.get(item_id, {})
            for field in ["sub_type", "color"]:
                if field in original_item and (field not in candidate_item or not candidate_item.get(field)):
                    candidate_item[field] = original_item.get(field)
                    
            valid_outfit_items.append(candidate_item)
            seen_ids.add(item_id)
        else:
            logger.warning("Candidate item with id %s not found in wardrobe. Removing item.", item_id)
    
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
    
    # Process outfit composition issues
    outfit_json = process_outfit_issues(outfit_json, wardrobe_items, wardrobe_ids)
    
    # Run additional outfit checks
    is_balanced, balance_reason = check_outfit_balance(outfit_json.get("outfit_items", []))
    is_coherent, coherence_reason = check_style_coherence(outfit_json.get("outfit_items", []))
    has_no_duplicates, duplicate_reason = check_duplicate_items(outfit_json.get("outfit_items", []))
    
    # Add warnings if necessary
    if not is_balanced or not is_coherent or not has_no_duplicates:
        warnings = outfit_json.get("warnings", [])
        if not is_balanced:
            warnings.append(f"Balance issue: {balance_reason}")
        if not is_coherent:
            warnings.append(f"Coherence issue: {coherence_reason}")
        if not has_no_duplicates:
            warnings.append(f"Duplicate issue: {duplicate_reason}")
            
        outfit_json["warnings"] = warnings
    
    return outfit_json




def generateOutfit(user_message: str, weather_data: Dict, wardrobe_items: List[Dict]) -> Dict:
    """
    Generates an outfit suggestion based on the user's message, weather data,
    and wardrobe items.
    
    Args:
        user_message: The user's query or request
        weather_data: Weather data dictionary containing temperature, description, etc.
        wardrobe_items: List of items from the user's wardrobe
        
    Returns:
        A dictionary with occasion, outfit items, and description
    """
    try:
        # Convert wardrobe items to WardrobeItem objects with error handling
        wardrobe_objects = []
        invalid_items = []
        
        for item in wardrobe_items:
            try:
                wardrobe_objects.append(WardrobeItem.from_dict(item))
            except ValueError as e:
                logger.warning(f"Skipping invalid wardrobe item: {str(e)}")
                invalid_items.append(item.get('id', 'unknown'))
                continue
        
        if not wardrobe_objects:
            raise ValueError("No valid wardrobe items found")
            
        if invalid_items:
            logger.warning(f"Skipped {len(invalid_items)} invalid wardrobe items: {', '.join(invalid_items)}")
        
        # Determine target occasion and configuration
        target_occ = determineOccasions(user_message)
        config = ai_config.get_occasion_config(target_occ)
        
        # Filter wardrobe items based on suitability
        filtered_items = filter_suitable_items(wardrobe_objects, weather_data, target_occ)
        
        # If too few items remain after filtering, use the original list
        if len(filtered_items) < 10:
            logger.info("Too few items after filtering (%d). Using original wardrobe.", len(filtered_items))
            filtered_items = wardrobe_objects
        
        # Ensure we have at least one item of each required type
        item_types_available = {}
        for item in filtered_items:
            if item.item_type not in item_types_available:
                item_types_available[item.item_type] = []
            item_types_available[item.item_type].append(item)
        
        # Check for required types
        required_types = [ItemType.TOP, ItemType.BOTTOM, ItemType.SHOES]
        missing_types = []
        
        for req_type in required_types:
            if req_type not in item_types_available or not item_types_available[req_type]:
                missing_types.append(req_type)
                
        if missing_types:
            logger.warning("Missing required item types: %s. Adding from original wardrobe.", 
                          ", ".join(t.value for t in missing_types))
            for item in wardrobe_objects:
                if item.item_type in missing_types and item not in filtered_items:
                    filtered_items.append(item)
        
        # Format wardrobe items
        formatted_items, wardrobe_ids = format_wardrobe_items(filtered_items)
        
        # Set generation temperature based on occasion formality
        generation_temp = ai_config.get_occasion_temperature(target_occ)
        llm_client.with_temperature(generation_temp)
        
        # Categorize items by type for the prompt
        categorized = categorize_wardrobe(filtered_items)
        
        # Add type counts to the prompt
        type_counts = {item_type.value: len(items) for item_type, items in categorized.items() if items}
        type_counts_str = ", ".join(f"{count} {item_type}" for item_type, count in type_counts.items())
        
        # Build the prompt with explicit guidance about required item types
        combined_prompt = build_prompt(
            user_message=user_message,
            weather_data=weather_data,
            formatted_items=formatted_items,
            target_occ=target_occ,
            config=config
        )
        
        # Add explicit instructions about composition requirements
        combined_prompt += f"\n\nIMPORTANT REQUIREMENTS:\n"
        combined_prompt += f"1. Each item ID must be unique in the outfit. Do not include the same item ID more than once.\n"
        combined_prompt += f"2. EXACTLY ONE pair of shoes is required (shoes, item_type='shoes').\n"
        combined_prompt += f"3. EXACTLY ONE bottom item is required (pants, skirt, shorts, item_type='bottom') UNLESS a dress or suit is included.\n"
        combined_prompt += f"4. At least one top item is required (shirt, blouse, t-shirt, item_type='top') UNLESS a dress or suit is included.\n"
        combined_prompt += f"5. Available item types in wardrobe: {type_counts_str}.\n"
        combined_prompt += f"6. Double-check item types before finalizing - each item must have its correct type classification.\n"
        
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
        
        try:
            outfit_json = json.loads(generated)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM output as JSON: {str(e)}\nOutput: {generated}")
            raise ValueError("Failed to generate valid outfit JSON")
        
        # Convert outfit items back to dictionaries for validation
        outfit_items_dict = [item.to_dict() for item in filtered_items]
        
        # Validate and enhance outfit
        validated_outfit = validate_outfit(outfit_json, wardrobe_ids, target_occ, outfit_items_dict)
        
        # Double check composition requirements are met
        valid_composition, composition_reason, item_counts = validate_outfit_composition(validated_outfit.get("outfit_items", []))
        if not valid_composition:
            logger.warning("Outfit composition invalid after validation: %s", composition_reason)
            # Add warnings to the outfit
            validated_outfit["warnings"] = validated_outfit.get("warnings", []) + [f"Composition issue: {composition_reason}"]
            
            # If critical requirements are missing, retry with a clearer prompt once
            if "Missing shoes" in composition_reason or "Too many shoes" in composition_reason or "Missing bottom" in composition_reason:
                logger.info("Critical composition requirements missing. Retrying with clearer prompt.")
                combined_prompt += f"\n\nPREVIOUS ATTEMPT FAILED: {composition_reason}. Please strictly adhere to the outfit composition requirements."
                
                # Retry generation
                messages = [
                    SystemMessage(content=combined_prompt),
                    HumanMessage(content="Please provide your final refined JSON output, ensuring exactly one pair of shoes and exactly one bottom item (unless a dress/suit is included).")
                ]
                
                generated = llm_client.invoke(messages)
                
                # Parse and validate the retry
                if "```json" in generated:
                    generated = generated.split("```json")[1].split("```")[0].strip()
                elif "```" in generated:
                    generated = generated.split("```")[1].strip()
                
                try:
                    retry_outfit_json = json.loads(generated)
                    retry_validated_outfit = validate_outfit(retry_outfit_json, wardrobe_ids, target_occ, outfit_items_dict)
                    
                    # Check if the retry fixed the issues
                    retry_valid, retry_reason, _ = validate_outfit_composition(retry_validated_outfit.get("outfit_items", []))
                    if retry_valid:
                        logger.info("Retry successful. Using retry outfit.")
                        validated_outfit = retry_validated_outfit
                    else:
                        logger.warning("Retry failed: %s. Using original outfit with warnings.", retry_reason)
                except Exception as e:
                    logger.error("Error in retry parsing: %s", e)
        
        return validated_outfit
        
    except json.JSONDecodeError as e:
        logger.error("JSON parsing error: %s in: %s", e, generated)
        outfit_json = {
            "occasion": target_occ if 'target_occ' in locals() else "unknown",
            "outfit_items": [],
            "description": "Failed to generate a valid outfit. Please try again.",
            "styling_tips": "Try again with a more specific request.",
            "warnings": ["Failed to parse generated output as JSON."]
        }
    except Exception as e:
        logger.error("Error in generateOutfit: %s", e)
        outfit_json = {
            "occasion": target_occ if 'target_occ' in locals() else "unknown",
            "outfit_items": [],
            "description": "An error occurred while generating your outfit. Please try again.",
            "styling_tips": "Try again with a more specific request.",
            "warnings": [f"Error: {str(e)}"]
        }
    
    return outfit_json