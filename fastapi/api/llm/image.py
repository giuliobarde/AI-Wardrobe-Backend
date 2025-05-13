import os
import logging
import requests
import time
from typing import Optional, Dict, Any
from dotenv import load_dotenv
from openai import OpenAI, APIError, RateLimitError

from .models import ClothingItem

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")
if not openai_api_key:
    raise EnvironmentError("OPENAI_API_KEY environment variable not set")

# Configuration constants
MAX_RETRIES = 3
RETRY_DELAY = 2  # seconds
REQUEST_TIMEOUT = 30  # seconds
DEFAULT_IMAGE_SIZE = "1024x1024"
DEFAULT_IMAGE_QUALITY = "hd"


# For backward compatibility
def generateImage(item: ClothingItem) -> bytes:
    """
    Backward compatible function for generating an emoji-style illustration of a clothing item.
    
    Args:
        item: The clothing item to generate an image for
        
    Returns:
        Raw image data as bytes
    """
    return generate_image(item)


def generate_image(
    item: ClothingItem, 
    size: str = DEFAULT_IMAGE_SIZE,
    quality: str = DEFAULT_IMAGE_QUALITY,
    style: str = "natural",
    background: str = "pure white"
) -> bytes:
    """
    Generates an emoji-style illustration of a clothing item using DALL·E 3.
    
    Args:
        item: The clothing item to generate an image for
        size: Image size (e.g., "1024x1024", "1792x1024", "1024x1792")
        quality: Image quality ("standard" or "hd")
        style: Generation style ("natural" or "vivid")
        background: Background description
        
    Returns:
        Raw image data as bytes
    """
    # Build a detailed prompt that avoids logo generation and focuses on quality
    base_description = f"{item.color} {item.material} {item.sub_type}"
    if item.pattern and item.pattern.lower() != "none" and item.pattern.lower() != "solid":
        base_description += f" with a {item.pattern} pattern"
    
    prompt = (
        f"Create a minimalist emoji-style illustration of a {base_description}. "
        f"The illustration should be simple, glossy, and vector-like, centered on a {background} background. "
        f"The clothing item should be well-lit with subtle shadows to define its shape. "
        f"Use clean lines and vibrant, solid colors in a modern emoji aesthetic. "
        f"IMPORTANT: "
        f"- Do not include any logos, text, watermarks, decorations, or brand identifiers of any kind. "
        f"- The image should only show the clothing item itself with absolutely no Apple logo or any other symbol. "
        f"- Do not add any human figures, mannequins, or additional objects. "
        f"- Create a straight-on view of the item as if photographed for a product catalog, unless it is a piece of footware. "
        f"- If it is a piece of footware crate the image at a slight angle. . "
        f"- The style should be highly simplified, appropriate for small emoji display. "
    )
    
    logger.info(f"Generating image for {base_description}")
    
    # Initialize the OpenAI client
    client = OpenAI(api_key=openai_api_key)
    
    # Implement retry logic for resilience
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            # Call DALL·E 3 via OpenAI's API with configurable parameters
            response = client.images.generate(
                model="dall-e-3",
                prompt=prompt,
                n=1,
                size=size,
                quality=quality,
                response_format="url",
                style=style
            )
            
            # Log the revised prompt that DALL-E actually used
            if hasattr(response.data[0], 'revised_prompt'):
                logger.debug(f"DALL-E revised prompt: {response.data[0].revised_prompt}")
            
            # Retrieve the URL of the generated image
            image_url = response.data[0].url
            
            # Download the image data from the URL with timeout
            r = requests.get(image_url, timeout=REQUEST_TIMEOUT)
            r.raise_for_status()
            
            logger.info(f"Successfully generated image for {base_description}")
            return r.content
            
        except RateLimitError as e:
            if attempt < MAX_RETRIES:
                wait_time = RETRY_DELAY * (2 ** (attempt - 1))  # Exponential backoff
                logger.warning(f"Rate limit exceeded. Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
            else:
                logger.error("Rate limit exceeded after multiple retries")
                raise Exception("Failed to generate image: Rate limit exceeded") from e
                
        except APIError as e:
            logger.error(f"OpenAI API error: {str(e)}")
            if "content_policy_violation" in str(e).lower():
                # Content policy issues - try modifying the prompt
                logger.warning("Content policy violation. Using alternative prompt approach.")
                return _generate_with_alternative_prompt(client, item, size, quality, style, background)
            elif attempt < MAX_RETRIES:
                wait_time = RETRY_DELAY * (2 ** (attempt - 1))
                logger.warning(f"API error. Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
            else:
                raise Exception(f"Failed to generate image via DALL·E 3: {str(e)}") from e
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to download the generated image: {str(e)}")
            if attempt < MAX_RETRIES:
                wait_time = RETRY_DELAY * (2 ** (attempt - 1))
                logger.warning(f"Download error. Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
            else:
                raise Exception(f"Failed to download the generated image after {MAX_RETRIES} attempts") from e
                
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            raise Exception(f"Failed to generate image: {str(e)}") from e


def _generate_with_alternative_prompt(
    client: OpenAI,
    item: ClothingItem,
    size: str,
    quality: str,
    style: str,
    background: str
) -> bytes:
    """
    Fallback method with an alternative prompt approach if the first one fails.
    
    This method uses a more generic description that focuses on shapes and colors
    rather than specific clothing terminology that might trigger content filters.
    """
    try:
        alternative_prompt = (
            f"Create a simple, minimalist vector illustration showing the shape of a {item.color} "
            f"{item.sub_type} on a {background} background. Use flat colors with minimal details, "
            f"in a clean clipart style. No text, no logos, no patterns, just the basic silhouette "
            f"with solid color fill. The image should be extremely simple like an app icon."
        )
        
        response = client.images.generate(
            model="dall-e-3",
            prompt=alternative_prompt,
            n=1,
            size=size,
            quality=quality,
            response_format="url",
            style=style
        )
        
        image_url = response.data[0].url
        r = requests.get(image_url, timeout=REQUEST_TIMEOUT)
        r.raise_for_status()
        
        logger.info(f"Successfully generated image using alternative prompt")
        return r.content
    except Exception as e:
        logger.error(f"Alternative prompt also failed: {str(e)}")
        raise Exception("Failed to generate image with alternative prompt") from e


def batch_generate_images(items: list[ClothingItem], **kwargs) -> Dict[str, Optional[bytes]]:
    """
    Generate images for multiple clothing items with error handling.
    
    Args:
        items: List of clothing items to generate images for
        **kwargs: Additional parameters to pass to generate_image
        
    Returns:
        Dictionary mapping item IDs to image data (or None if generation failed)
    """
    results = {}
    
    for item in items:
        try:
            results[item.id] = generate_image(item, **kwargs)
        except Exception as e:
            logger.error(f"Failed to generate image for item {item.id}: {e}")
            results[item.id] = None
    
    return results