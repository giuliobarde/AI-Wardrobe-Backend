import os
import logging
import requests
from dotenv import load_dotenv
from openai import OpenAI

from .models import ClothingItem

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")
if not openai_api_key:
    raise EnvironmentError("OPENAI_API_KEY environment variable not set")


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