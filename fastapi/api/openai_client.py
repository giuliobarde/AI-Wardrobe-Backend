import os
import re
import json
import logging
from typing import Dict, List, Set, Union, Any
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

from llm.models import ClothingItem
from llm.client import llm_client
from llm.config import ai_config
from llm.occasion import determineOccasions, fallback_determineOccasions
from llm.outfit import generateOutfit
from llm.item import setOccasion
from llm.image import generateImage

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")
if not openai_api_key:
    raise EnvironmentError("OPENAI_API_KEY environment variable not set")


# Keeping the original function definitions but calling the new implementations

def determineOccasions(user_message: str) -> str:
    """
    Determines the target occasion by querying the LLM.
    Now calls the refactored implementation.
    
    Args:
        user_message: The user's input message
        
    Returns:
        A string representing the detected occasion
    """
    from llm.occasion import determineOccasions as new_determineOccasions
    return new_determineOccasions(user_message)


def fallback_determineOccasions(user_message: str) -> str:
    """
    Fallback method to determine the occasion.
    Now calls the refactored implementation.
    
    Args:
        user_message: The user's input message
        
    Returns:
        A string representing the detected occasion, defaulting to "all occasions"
    """
    from llm.occasion import fallback_determineOccasions as new_fallback_determineOccasions
    return new_fallback_determineOccasions(user_message)


def generateOutfit(user_message: str, outside_temp: str, wardrobe_items: List[Dict]) -> Dict:
    """
    Generates an outfit suggestion based on the user's message, outside temperature,
    and wardrobe items.
    Now calls the refactored implementation.
    
    Args:
        user_message: The user's query or request
        outside_temp: The outside temperature description
        wardrobe_items: List of items from the user's wardrobe
        
    Returns:
        A dictionary with occasion, outfit items, and description
    """
    from llm.outfit import generateOutfit as new_generateOutfit
    return new_generateOutfit(user_message, outside_temp, wardrobe_items)


def setOccasion(item: ClothingItem) -> ClothingItem:
    """
    Updates the clothing item with one or more suitable occasion tags.
    Now calls the refactored implementation.
    
    Args:
        item: The clothing item to analyze
        
    Returns:
        The updated clothing item with suitable occasions
    """
    from llm.item import setOccasion as new_setOccasion
    return new_setOccasion(item)


def generateImage(item: ClothingItem) -> bytes:
    """
    Generates an emoji-style illustration of a clothing item using DALL·E 3.
    Now calls the refactored implementation.
    
    Args:
        item: The clothing item to generate an image for
        
    Returns:
        Raw image data as bytes
    """
    from llm.image import generateImage as new_generateImage
    return new_generateImage(item)


# The LLMClient class and AIConfig class are now imported from llm.client and llm.config
# For this compatibility layer, we could create proxy classes that delegate to the refactored ones,
# but it's cleaner to just use the imported classes directly.

# For backwards compatibility:
LLMClient = llm_client.__class__  # This gives you the class definition
AIConfig = ai_config.__class__    # This gives you the class definition

# TODO: Incorporate dynamic context from user preferences and historical outfit choices.
# TODO: Enhance fallback and error handling if the generated JSON is invalid.
# TODO: Implement an interactive feedback loop to refine outfit suggestions based on user input.