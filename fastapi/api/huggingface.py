import os
from dotenv import load_dotenv
from huggingface_hub import InferenceClient
from langchain_core.messages import HumanMessage, SystemMessage

# Load environment variables
load_dotenv()
huggingfacehub_api_token = os.getenv("HUGGINGFACEHUB_API_TOKEN")

# Initialize the Hugging Face Inference Client
client = InferenceClient(model="HuggingFaceH4/zephyr-7b-beta", token=huggingfacehub_api_token)

def generateOutfit(user_message: str, temp: str, wardrobe_items: list[str]) -> str:
    """
    Generates an outfit suggestion based on the user's message, current temperature,
    and the items in the user's wardrobe.

    Args:
        user_message (str): The occasion or query from the user.
        temp (str): The current temperature (e.g., "20C").
        wardrobe_items (list[str]): A list of clothing items in the user's wardrobe.

    Returns:
        str: The AI-generated outfit suggestion.
    """
    # Convert wardrobe items into a readable string.
    wardrobe_text = "The user's wardrobe includes: " + ", ".join(wardrobe_items) + "."

    # Create prompt messages that include wardrobe context.
    messages = [
        SystemMessage(
            content="You're a helpful style assistant that suggests outfits piece by piece based on the user's wardrobe and current temperature."
        ),
        HumanMessage(
            content=f"{user_message} {wardrobe_text} It is currently {temp}."
        ),
    ]
    input_text = f"{messages[0].content}\n{messages[1].content}"

    response = client.text_generation(
        input_text,
        max_new_tokens=512,
        do_sample=False,
        repetition_penalty=1.03,
    )

    return response
