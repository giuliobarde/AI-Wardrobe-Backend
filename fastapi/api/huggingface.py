import os
from dotenv import load_dotenv
from huggingface_hub import InferenceClient
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage

# Load environment variables
load_dotenv()
huggingfacehub_api_token = os.getenv("HUGGINGFACEHUB_API_TOKEN")

# Initialize the Hugging Face Inference Client
client = InferenceClient(model="HuggingFaceH4/zephyr-7b-beta", token=huggingfacehub_api_token)

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
    
    # Construct a strict few-shot prompt with two examples.
    messages = [
        SystemMessage(
            content="""
You are a style assistant that suggests complete outfits based solely on the user's wardrobe and current temperature.
Each outfit suggestion should consist of a cohesive set of garments suitable for the occasion. 
You must only return the items needed for the outfit and a short sentence describing the outfit.
You must not return other items of the user in the response unless they are used in the outfit. 
You must not return the full description of the item at any point in the response.
Your response must strictly adhere to the following format and include only the items for the outfit and one short description:
For -user request- I suggest:
- Item 1
- Item 2
- Item 3
- Item 4
Short description: <One short sentence describing the outfit>

Do not include any additional text, extra items, or a full description of the wardrobe items.
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
            content=f"Now, Occasion: {user_message}. {wardrobe_text} Temperature: {temp}."
        ),
    ]
    
    # Join the messages to form the full prompt.
    input_text = "\n".join(message.content.strip() for message in messages)
    
    response = client.text_generation(
        input_text,
        max_new_tokens=512,
        do_sample=True,
        temperature=0.3,  # Lowered temperature for more deterministic output
        repetition_penalty=1.03,
    )
    
    # Extract generated text if needed.
    if isinstance(response, list) and response and "generated_text" in response[0]:
        generated = response[0]["generated_text"]
    else:
        generated = response  # fallback if response is already a string
    
    return generated
