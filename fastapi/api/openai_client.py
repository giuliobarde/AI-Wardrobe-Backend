import os
import json
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

def generateOutfit(user_message: str, temp: str, wardrobe_items: list[dict]) -> dict:
    """
    Generates an outfit suggestion based on the user's message, current temperature,
    and the items in the user's wardrobe.
    
    Returns a dictionary in the following JSON format:
    {
      "occasion": "<occasion string>",
      "outfit_items": [
         {"id": "<item id>", "sub_type": "<item sub type>", "color": "<item color>"},
         ...
      ],
      "description": "<One short sentence describing the outfit>"
    }
    """
    # Format the wardrobe items.
    formatted_items = []
    for item in wardrobe_items:
        formatted_item = (
            f"Item ID: {item.get('id', 'N/A')}, "
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

    # Construct a strict few-shot prompt with examples and an output delimiter.
    messages = [
        SystemMessage(
            content="""
You are a style assistant that suggests complete outfits based solely on the user's wardrobe and current temperature.
Each outfit suggestion must consist of a cohesive set of garments suitable for the occasion, taking into account the formality of each item.
Your response must be a valid JSON object in the following format:
{
  "occasion": "<occasion string>",
  "outfit_items": [
    {"id": "<item id>", "sub_type": "<item sub type>", "color": "<item color>"},
    ... (up to 4 items)
  ],
  "description": "<One short sentence describing the outfit>"
}
Do not include any extra text.
Below are two examples:
            """
        ),
        HumanMessage(
            content="Example 1 - Occasion: I need an outfit for a wedding. Temperature: 20C. Wardrobe: [Example wardrobe items]."
        ),
        AIMessage(
            content='{"occasion": "wedding", "outfit_items": [{"id": "sbo1823y4ic73es", "sub_type": "White dress shirt", "color": "white"}, {"id": "ae8wciq3byebh2398y", "sub_type": "Navy blue suit pants", "color": "navy"}, {"id": "ab38592018cnwinxuyd", "sub_type": "Black dress shoes", "color": "black"}, {"id": "c1bq82wneyq82wyebq8wi", "sub_type": "Navy blue suit jacket", "color": "navy"}], "description": "This ensemble is classic, elegant, and perfect for a wedding."}'
        ),
        HumanMessage(
            content="Example 2 - Occasion: I need an outfit for a job interview. Temperature: 20C. Wardrobe: [Example wardrobe items]."
        ),
        AIMessage(
            content='{"occasion": "job interview", "outfit_items": [{"id": "w1209e7uqd8ahsjmzx", "sub_type": "Light blue dress shirt", "color": "light blue"}, {"id": "eq0ad8yzhiuhbxq28eu", "sub_type": "Grey slacks", "color": "grey"}, {"id": "12846nqiwuaahjshdaj", "sub_type": "Black leather dress shoes", "color": "black"}, {"id": "2817c2basduhwneiuwq", "sub_type": "Charcoal blazer", "color": "charcoal"}], "description": "This outfit is professional and modern, making a strong impression."}'
        ),
        HumanMessage(
            content=f"Now, Occasion: {user_message}. {wardrobe_text} Temperature: {temp}.\n### Output:"
        ),
    ]
    
    response = llm.invoke(messages)
    generated = response.content
    if "### Output:" in generated:
        generated = generated.split("### Output:")[-1].strip()
    
    try:
        outfit_json = json.loads(generated)
    except Exception as e:
        # Fallback in case parsing fails.
        outfit_json = {
            "occasion": "",
            "outfit_items": [],
            "description": generated
        }
    return outfit_json

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
