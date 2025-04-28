import json
import logging
from langchain_core.messages import SystemMessage

from .models import ClothingItem
from .client import llm_client
from .config import ai_config

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


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