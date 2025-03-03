import os
from dotenv import load_dotenv
from huggingface_hub import InferenceClient
from langchain_core.messages import HumanMessage, SystemMessage

# Load environment variables
load_dotenv()
huggingfacehub_api_token = os.getenv("HUGGINGFACEHUB_API_TOKEN")

# Initialize the Hugging Face Inference Client
client = InferenceClient(model="HuggingFaceH4/zephyr-7b-beta", token=huggingfacehub_api_token)

def generateOutfit(user_message: str, temp: str) -> str:
    """
    Function to generate a response using Hugging Face API.
    
    Args:
        user_message (str): The message input from the user.

    Returns:
        str: The AI-generated response.
    """
    messages = [
        SystemMessage(content="You're a helpful style assystant that suggests outfits piece by piece based on the temperature."),
        HumanMessage(content=user_message + "It is currently " + temp),
    ]
    input_text = f"{messages[0].content}\n{messages[1].content}"

    response = client.text_generation(input_text, max_new_tokens=512, do_sample=False, repetition_penalty=1.03)

    return response
