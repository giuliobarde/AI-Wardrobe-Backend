import re
import logging
from langchain_core.messages import SystemMessage
from typing import Dict, List

from .client import llm_client
from .config import ai_config

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


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