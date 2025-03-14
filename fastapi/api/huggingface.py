import os
from dotenv import load_dotenv
from huggingface_hub import InferenceClient
from langchain_core.messages import HumanMessage, SystemMessage

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
        str: The AI-generated outfit suggestion.
    """
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

    # Convert wardrobe items into a readable string.
    wardrobe_text = "The user's wardrobe includes: " + " | ".join(formatted_items) + "."

    # Create prompt messages that include wardrobe context.
    messages = [
        SystemMessage(
            content="You're a helpful style assistant that suggests outfits piece by piece based on the user's wardrobe and current temperature."
        ),
        HumanMessage(
            content=f"Occasion: {user_message} {wardrobe_text} It is currently: {temp}."
        ),
    ]
    input_text = f"{messages[0].content}\n{messages[1].content}"

    input_text = f"{messages[0].content}\n{messages[1].content}"
    response = client.text_generation(
        input_text,
        max_new_tokens=512,
        do_sample=True,  # enable sampling for more varied output
        temperature=0.8,
        repetition_penalty=1.03,
    )

    # Extract the generated text if needed.
    if isinstance(response, list) and response and "generated_text" in response[0]:
        generated = response[0]["generated_text"]
    else:
        generated = response  # fallback if response is already a string

    return generated
