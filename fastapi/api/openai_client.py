import os
import re
import json
import logging
from typing import Dict, List, Set, Optional, Union, Any
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel

from openai import OpenAI
import requests
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")
if not openai_api_key:
    raise EnvironmentError("OPENAI_API_KEY environment variable not set")

# Models
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
    image_link: Optional[str] = None

class OutfitItem(BaseModel):
    id: str
    sub_type: str
    color: str

class OutfitResponse(BaseModel):
    occasion: str
    outfit_items: List[OutfitItem]
    description: str

# Config management class with JSON file loading
class AIConfig:
    _instance = None
    _config = None
    
    @classmethod
    def get_instance(cls):
        """Get singleton instance of AIConfig"""
        if cls._instance is None:
            cls._instance = cls()
            cls._instance._load_config()
        return cls._instance
    
    def _load_config(self):
        """Load configuration from JSON file"""
        # Path to the config file, relative to this script
        config_path = Path(__file__).parent / 'config' / 'ai_config.json'
        try:
            with open(config_path, 'r') as f:
                self._config = json.load(f)
                logger.info(f"AI config loaded successfully from {config_path}")
        except Exception as e:
            logger.error(f"Failed to load config from {config_path}: {e}")
            # Provide a minimal default config in case file loading fails
            self._config = {
                "allowed_occasions": ["all occasions"],
                "occasion_config": {"all occasions": {"items": [], "rules": "", "strictness": "Low", "description": ""}},
                "occasion_temperature": {"all occasions": 0.5}
            }
    
    def get_allowed_occasions(self) -> List[str]:
        """Get list of all allowed occasions"""
        return self._config.get("allowed_occasions", ["all occasions"])
    
    def get_occasion_config(self, occasion: str = None) -> Dict[str, Any]:
        """Get configuration for a specific occasion or all occasions"""
        occasion_configs = self._config.get("occasion_config", {})
        if occasion:
            return occasion_configs.get(occasion, occasion_configs.get("all occasions", {}))
        return occasion_configs
    
    def get_occasion_temperature(self, occasion: str) -> float:
        """Get temperature setting for a specific occasion"""
        temp_map = self._config.get("occasion_temperature", {})
        return temp_map.get(occasion, 0.5)


class LLMClient:
    """Interface for language model interactions"""
    
    def __init__(self, api_key: str = None, model_name: str = "gpt-3.5-turbo"):
        """Initialize LLM client with appropriate configuration"""
        self.api_key = api_key or openai_api_key
        self.model_name = model_name
        self.llm = self._create_llm(temperature=0.5)
    
    def _create_llm(self, temperature: float) -> ChatOpenAI:
        """Create a new LLM instance with the given temperature"""
        return ChatOpenAI(
            openai_api_key=self.api_key,
            temperature=temperature,
            top_p=1,
            model_name=self.model_name
        )
    
    def with_temperature(self, temperature: float) -> None:
        """Update the LLM with a new temperature setting"""
        self.llm = self._create_llm(temperature)
    
    def invoke(self, messages: List[Union[SystemMessage, HumanMessage]]) -> str:
        """Send a request to the language model and return the response"""
        try:
            response = self.llm.invoke(messages)
            return response.content.strip()
        except Exception as e:
            logger.error("Error invoking LLM: %s", e)
            raise


# Create a singleton LLM client
llm_client = LLMClient()
# Initialize the config
ai_config = AIConfig.get_instance()


def determineOccasions(user_message: str) -> str:
    """
    Determines the target occasion by querying the LLM.
    If the LLM response doesn't match an allowed occasion, falls back to local matching.
    
    Args:
        user_message: The user's input message
        
    Returns:
        A string representing the detected occasion
    """
    allowed_occasions = ai_config.get_allowed_occasions()
    prompt = (
        f"Based on the following user message, determine the most appropriate occasion "
        f"for generating an outfit. Choose from the following options: {', '.join(allowed_occasions)}.\n\n"
        f"User message: \"{user_message}\".\n\n"
        f"Return only the chosen occasion exactly as one of the options."
    )
    
    try:
        # Use a moderate temperature for occasion determination
        llm_client.with_temperature(0.3)
        messages = [SystemMessage(content=prompt)]
        generated = llm_client.invoke(messages)
        
        # Check if the output (case-insensitive) is in the allowed occasions
        for occ in allowed_occasions:
            if occ.lower() == generated.lower():
                return occ
        
        # If no match, use fallback
        return fallback_determineOccasions(user_message)
    except Exception as e:
        logger.error("Error in determineOccasions LLM query: %s", e)
        return fallback_determineOccasions(user_message)


def fallback_determineOccasions(user_message: str) -> str:
    """
    Fallback method to determine the occasion using local regex matching and synonyms.
    
    Args:
        user_message: The user's input message
        
    Returns:
        A string representing the detected occasion, defaulting to "all occasions"
    """
    lower_msg = user_message.lower()
    
    # Exact matching with allowed phrases sorted by length (longest first)
    for occ in sorted(ai_config.get_occasion_config().keys(), key=len, reverse=True):
        pattern = r'\b' + re.escape(occ) + r'\b'
        if re.search(pattern, lower_msg):
            return occ
    
    # Synonyms mapping for common alternate phrases
    synonyms = {
        "very formal": "very formal occasion",
        "black tie": "black tie event",
        "white tie": "white tie event",
        "interview": "job interview",
        "dinner": "dinner party",
        "office": "work",
        "gym": "gym",
        "casual": "casual outing",
        "date": "date night",
        "party": "party",
        "formal": "general formal occasion",
        "informal": "general informal occasion"
    }
    
    for key, value in synonyms.items():
        pattern = r'\b' + re.escape(key) + r'\b'
        if re.search(pattern, lower_msg):
            return value
    
    return "all occasions"


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


def setOccasion(item: ClothingItem) -> ClothingItem:
    """
    Updates the clothing item with one or more suitable occasion tags.
    
    Args:
        item: The clothing item to analyze
        
    Returns:
        The updated clothing item with suitable occasions
    """
    allowed_occasions = ai_config.get_allowed_occasions()
    prompt = (
        f"Given a clothing item with the following details:\n"
        f"Item type: {item.item_type}\n"
        f"Material: {item.material}\n"
        f"Color: {item.color}\n"
        f"Formality: {item.formality}\n"
        f"Pattern: {item.pattern}\n"
        f"Fit: {item.fit}\n"
        f"Suitable for weather: {item.suitable_for_weather}\n"
        f"Sub-type: {item.sub_type}\n\n"
        "Which occasion(s) is this item most suitable for? Please choose one or more from the following list:\n"
        f"{', '.join(allowed_occasions)}\n\n"
        "Return your answer as a JSON object with a single key \"occasions\" that maps to a list of occasion strings. "
        "Do not output any extra text."
    )
    
    # Use a moderate temperature for sensible but somewhat diverse occasion matching
    llm_client.with_temperature(0.3)
    messages = [SystemMessage(content=prompt)]
    
    try:
        generated = llm_client.invoke(messages)
        logger.info("setOccasion LLM response: %s", generated)
        
        parsed = json.loads(generated)
        occasions = parsed.get("occasions", [])
        valid_occasions = [opt for opt in occasions if opt in allowed_occasions]
        
        if not valid_occasions:
            valid_occasions = ["all occasions"]
    except Exception as e:
        logger.error("Error in setOccasion: %s", e)
        valid_occasions = ["all occasions"]
    
    item.suitable_for_occasion = ", ".join(valid_occasions)
    return item


def generateImage(item: ClothingItem) -> bytes:
    """
    Generates an emoji-style illustration of a clothing item using DALL·E 3.
    
    Args:
        item: The clothing item to generate an image for
        
    Returns:
        Raw image data as bytes
    """
    # Modified prompt to avoid Apple logo inclusion
    prompt = (
        f"Create a minimalist emoji-style illustration of a {item.color} {item.material} {item.sub_type} "
        f"with a {item.pattern} pattern. The illustration must be simple, glossy, and vector-like, "
        f"centered on a pure white background. The clothing item should be well-lit with subtle shadows "
        f"to define its shape. Use clean lines and vibrant colors in a modern emoji aesthetic. "
        f"IMPORTANT: Do not include any logos, text, watermarks, decorators, or brand identifiers of any kind. "
        f"The image should only show the clothing item itself with absolutely no Apple logo or any other symbol. "
    )
    
    try:
        # Initialize the OpenAI client
        client = OpenAI(api_key=openai_api_key)
        
        # Call DALL·E 3 via OpenAI's API with enhanced parameters
        response = client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            n=1,
            size="1024x1024",
            quality="hd",
            response_format="url",
            style="natural"  # Using natural style to reduce branding elements
        )
        
        # Retrieve the URL of the generated image
        image_url = response.data[0].url
        
        # Download the image data from the URL with timeout and error handling
        r = requests.get(image_url, timeout=30)
        r.raise_for_status()  # Raises an exception for HTTP errors
        
        return r.content
    except requests.exceptions.RequestException as e:
        logger.error("Failed to download the generated image: %s", e)
        raise Exception(f"Failed to download the generated image: {str(e)}")
    except Exception as e:
        logger.error("Failed to generate image via DALL·E 3: %s", e)
        raise Exception(f"Failed to generate image via DALL·E 3: {str(e)}")


# TODO: Incorporate dynamic context from user preferences and historical outfit choices.
# TODO: Enhance fallback and error handling if the generated JSON is invalid.
# TODO: Implement an interactive feedback loop to refine outfit suggestions based on user input.