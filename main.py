from huggingface_hub import InferenceClient
from langchain_core.messages import HumanMessage, SystemMessage

# Set your Hugging Face API token
huggingfacehub_api_token = ""

# Initialize the Hugging Face Inference Client
client = InferenceClient(model="HuggingFaceH4/zephyr-7b-beta", token=huggingfacehub_api_token)

# Define the input messages
messages = [
    SystemMessage(content="You're a helpful assistant."),
    HumanMessage(content="What happens when an unstoppable force meets an immovable object?"),
]

# Format the messages into a single string (Zephyr-7B is not a chat model)
input_text = f"{messages[0].content}\n{messages[1].content}"

# Get the model's response
response = client.text_generation(input_text, max_new_tokens=512, do_sample=False, repetition_penalty=1.03)

# Print the output
print(response)
