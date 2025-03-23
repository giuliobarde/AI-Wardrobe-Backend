import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from pydantic import BaseModel

# Load environment variables
load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")

# Initialize the OpenAI Chat model via LangChain
llm = ChatOpenAI(
    openai_api_key=openai_api_key,
    temperature=0.3,
    model_name="gpt-3.5-turbo"
)

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

    # Construct a strict few-shot prompt with two examples and an output delimiter.
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
    
    # Call the OpenAI model with the list of messages using the invoke method.
    response = llm.invoke(messages)
    generated = response.content
    # Remove any text preceding the output delimiter.
    if "### Output:" in generated:
        generated = generated.split("### Output:")[-1].strip()
    return generated

def setOccasion(item: ClothingItem) -> ClothingItem:
    """
    Analyzes an item and sets the suitable_for_occasion field based on the item's details.
    """
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
                "white tie event, black tie event, job interview, wedding, dinner party, work, gym, "
                "all occasions, casual outing, date night, party, general formal occasion, general informal occasion.\n"
                "Note: 'black tie event' is reserved exclusively for items that belong to very formal attire categories. "
                "If the clothing item does not represent that level of formality, do not select this option. Items in this category "
                "include tuxedos and patent leather dress shoes.\n"
                "Below are two output examples:"
            )
        ),
        HumanMessage(
            content="Example 1 - Item: tuxedo, a formal black tuxedo with a bow tie and cummerbund."
        ),
        AIMessage(
            content="black tie event"
        ),
        HumanMessage(
            content="Example 2 - Item: business suit, a tailored navy business suit with a white shirt and conservative tie."
        ),
        AIMessage(
            content="job interview"
        ),
        HumanMessage(
            content=f"Now, analyze the following item and choose the appropriate occasion from the list: {item.model_dump()}"
        ),
    ]
    
    response = llm.invoke(messages)
    generated = response.content.strip()
    print(generated)

    allowed_occasions = [
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
    
    response_lower = generated.lower()
    chosen = "all occasions"  # default value
    for option in allowed_occasions:
        if option in response_lower:
            chosen = option
            break
    
    item.suitable_for_occasion = chosen
    return item
