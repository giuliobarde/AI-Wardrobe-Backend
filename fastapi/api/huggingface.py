import os
import re
from dotenv import load_dotenv
from huggingface_hub import InferenceClient
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from pydantic import BaseModel

# Load environment variables
load_dotenv()
huggingfacehub_api_token = os.getenv("HUGGINGFACEHUB_API_TOKEN")

# Initialize the Hugging Face Inference Client
client = InferenceClient(model="HuggingFaceH4/zephyr-7b-beta", token=huggingfacehub_api_token)

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



def generateOutfit(user_message: str, temp: str, wardrobe_items: list[dict]) -> str:
    """
    Generates an outfit suggestion based on the user's message, current temperature,
    and the items in the user's wardrobe.

    Args:
        user_message (str): The occasion or query from the user.
        temp (str): The current temperature (e.g., "20C").
        wardrobe_items (list[dict]): A list of clothing items in the user's wardrobe,
                                     each containing all attributes.

    Returns:
        str: The AI-generated outfit suggestion following the strict format.
    """
    # Format the wardrobe items.
    formatted_items = []
    for item in wardrobe_items:
        formatted_item = (
            f"Type: {item.get('item_type', 'N/A')}, "
            f"Material: {item.get('material', 'unknown')}, "
            f"Color: {item.get('color', 'unknown')}, "
            f"Formality: {item.get('formality', 'N/A')}, "
            f"Pattern: {item.get('pattern', 'N/A')}, "
            f"Fit: {item.get('fit', 'N/A')}, "
            f"Weather Suitability: {item.get('suitable_for_weather', 'N/A')}, "
            f"Occasion Suitability: {item.get('suitable_for_occasion', 'N/A')}, "
            f"Sub Type: {item.get('sub_type', 'N/A')}"
        )
        formatted_items.append(formatted_item)
    
    wardrobe_text = "The user's wardrobe includes: " + " | ".join(formatted_items) + "."
    
    # Construct a strict few-shot prompt with two examples and a clear output delimiter.
    messages = [
        SystemMessage(
            content="""
You are a style assistant that suggests complete outfits based solely on the user's wardrobe and current temperature.
Each outfit suggestion must consist of a cohesive set of garments suitable for the occasion, keeping in mind the formality described by the user for each item.
Your response must strictly adhere to the following format and include only the outfit items and one short description:

For -user request- I suggest:
- Item 1
- Item 2
- Item 3
- Item 4

Short description: <One short sentence describing the outfit>

Do not include any extra text or repeat any of the instructions. Output only your answer exactly in the above format.

Below are two examples:
            """
        ),
        HumanMessage(
            content="Example 1 - Occasion: I need an outfit for a wedding. Temperature: 20C."
        ),
        AIMessage(
            content="""For a wedding I suggest:

- White dress shirt
- Navy blue suit pants
- Black dress shoes
- Navy blue suit jacket

Short description: This ensemble is classic, elegant, and perfect for a wedding."""
        ),
        HumanMessage(
            content="Example 2 - Occasion: I need an outfit for a job interview. Temperature: 20C."
        ),
        AIMessage(
            content="""For a job interview I suggest:

- Light blue dress shirt
- Grey slacks
- Black leather dress shoes
- Charcoal blazer

Short description: This outfit is professional and modern, making a strong impression."""
        ),
        HumanMessage(
            content=f"Now, Occasion: {user_message}. {wardrobe_text} Temperature: {temp}.\n### Output:"
        ),
    ]
    
    # Join the messages to form the full prompt.
    input_text = "\n".join(message.content.strip() for message in messages)
    
    response = client.text_generation(
        input_text,
        max_new_tokens=512,
        do_sample=True,
        temperature=0.3,
        repetition_penalty=1.03,
    )
    
    # Extract generated text if needed.
    if isinstance(response, list) and response and "generated_text" in response[0]:
        generated = response[0]["generated_text"]
    else:
        generated = response  # fallback if response is already a string
    
    # Optionally, remove any text preceding the delimiter if it still appears.
    if "### Output:" in generated:
        generated = generated.split("### Output:")[-1].strip()
    
    return generated



def setOccasion(item: ClothingItem) -> ClothingItem:
    messages = [
        SystemMessage(
            content=(
        f"Given a clothing item with the following details:\n"
        f"Item type: {item.item_type}\n"
        f"Material: {item.material}\n"
        f"Color: {item.color}\n"
        f"Formality: {item.formality}\n"
        f"Pattern: {item.pattern}\n"
        f"Fit: {item.fit}\n"
        f"Suitable for weather: {item.suitable_for_weather}\n"
        f"Sub-type: {item.sub_type}\n"
        "Which occasion is it most suitable for? "
        "Please choose from one of the following options:\n"
        "white tie eevent, black tie event, job interview, wedding, dinner party, work, gym, "
        "all occasions, casual outing, date night, party, general formal occasion, general informal occasion. "
        "Note: 'black tie event' is reserved exclusively for items that belong to very formal attire categories. " 
        "If the clothing item does not represent that level of formality, do not select this option. Items in this category "
        "include tuxedos and patent leather dress shoes"

        "Below are two output examples:"
    )
        ),
        HumanMessage(
            content="Example 1 - user_id='' item_type='tops' material='cashmere' color='navy' formality='somewhat formal' pattern='solid' fit='regular' suitable_for_weather='cold' suitable_for_occasion='' sub_type='crewneck sweater'"
        ),
        AIMessage(
            content="general formal occasion"
        ),
        HumanMessage(
            content="Example 2 - user_id='' item_type='bottoms' material='synthetic' color='grey' formality='not formal' pattern='solid' fit='baggy' suitable_for_weather='all' suitable_for_occasion='' sub_type='sweatpants'"
        ),
        AIMessage(
            content="gym"
        ),
        HumanMessage(
            content=f"Now, analyze the following item and choose the appropriate occasion from the list: {item.model_dump()}"
        ),
    ]
    
    # Join the messages into one prompt.
    input_text = "\n".join(message.content.strip() for message in messages)
    
    response = client.text_generation(
        input_text,
        max_new_tokens=128,
        do_sample=True,
        temperature=1,
        repetition_penalty=1.03,
    )
    
    # Extract the generated text.
    if isinstance(response, list) and response and "generated_text" in response[0]:
        generated = response[0]["generated_text"].strip()
    else:
        generated = response.strip()

    print(generated)

    allowed_occasions = [
        "white tie event",
        "black tie event",
        "job interview",
        "wedding",
        "dinner party",
        "work",
        "gym",
        "all occasions",
        "casual outing",
        "date night",
        "party",
        "general formal occasion",
        "general informal occasion",
    ]

    response_lower = response.lower()
    
    # Find the first allowed occasion that appears in the response
    chosen = "all occasions"  # default value
    for occasion in allowed_occasions:
        if occasion in response_lower:
            chosen = occasion
            break
    
    # Update the item's suitable_for_occasion field
    item.suitable_for_occasion = chosen
    return item