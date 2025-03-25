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

# Dictionary mapping allowed occasions to configuration details.
occasion_config = {
    "black tie event": {
        "items": [
            "Tuxedo Jacket",
            "Tuxedo Vest",
            "Tuxedo Pants",
            "Tuxedo Shirt",
            "Dress Shirt",
            "Patent Leather Oxfords",
            "Leather Oxfords",
            "Patent Leather Derbies",
            "Opera Pumps",
            "Ribbon Pumps"
        ],
        "rules": "Only if strictly required; must not use any lower-formality items.",
        "strictness": "Extremely strict",
        "description": "Black tie is an extremely high level of formality, and it should only be worn on special occasions, typically after 6pm."
    },
    "job interview": {
        "items": [
            "Dress Shirt",
            "Slacks",
            "Suit Pants",
            "Oxfords",
            "Derbies",
            "Blazer",
            "Suit Jacket",
            "Dress Shoes",
            "Tie",
            "Belt"
        ],
        "rules": "Maintain professionalism; ideally suggest a full suit.",
        "strictness": "Strict",
        "description": "This outfit should be professional, clean, and conservative."
    },
    "dinner party": {
        "items": [
            "Blazer",
            "Dress Shirt",
            "Chinos",
            "Dress Pants",
            "Loafers",
            "Derbies",
            "Oxfords",
            "Dress Boots",
            "Sweater",
            "Polo Shirt"
        ],
        "rules": "Should be sophisticated but not overly formal; avoid overly casual items.",
        "strictness": "Moderate",
        "description": "An outfit for a dinner party should be stylish and sophisticated without being overly formal."
    },
    "work": {
        "items": [
            "Dress Shirt",
            "Suit Pants",
            "Chinos",
            "Dress Shoes",
            "Blazer",
            "Sweater",
            "Loafers",
            "Derbies",
            "Oxfords",
            "Tie"
        ],
        "rules": "Professional business casual or formal, depending on the work environment; avoid overly casual items.",
        "strictness": "Moderate",
        "description": "Work attire should be business casual or formal, appropriate for a professional environment."
    },
    "gym": {
        "items": [
            "T-Shirt",
            "Athletic Shorts",
            "Joggers",
            "Sweatpants",
            "Tank Top",
            "Sneakers",
            "Running Shoes",
            "Sports Socks",
            "Athletic Jacket",
            "Sweatshirt"
        ],
        "rules": "Must prioritize comfort, breathability, and mobility; avoid restrictive or formal items.",
        "strictness": "Low",
        "description": "Gym attire should be comfortable, breathable, and suitable for physical exercise."
    },
    "all occasions": {
        "items": [
            "T-Shirt",
            "Jeans",
            "Chinos",
            "Sneakers",
            "Casual Shoes",
            "Sweater",
            "Jacket",
            "Polo Shirt"
        ],
        "rules": "Items should be versatile, comfortable, and acceptable in most casual to semi-formal settings.",
        "strictness": "Moderate",
        "description": "A versatile outfit that works in many settings."
    },
    "casual outing": {
        "items": [
            "T-Shirt",
            "Jeans",
            "Shorts",
            "Sneakers",
            "Casual Shoes",
            "Sweatshirt",
            "Hoodie",
            "Casual Jacket"
        ],
        "rules": "Focus on comfort and relaxed style; no formal clothing required.",
        "strictness": "Low",
        "description": "For casual outings, choose relaxed and comfortable clothing."
    },
    "party": {
        "items": [
            "Casual Shirt",
            "Jeans",
            "Chinos",
            "Sneakers",
            "Loafers",
            "Casual Boots",
            "Blazer",
            "Bomber Jacket"
        ],
        "rules": "Fashionable and fun without being overly casual or inappropriate.",
        "strictness": "Moderate",
        "description": "Party outfits should be trendy and fun while still being appropriate."
    },
    "general formal occasion": {
        "items": [
            "Suit Jacket",
            "Blazer",
            "Dress Shirt",
            "Dress Pants",
            "Tie",
            "Leather Dress Shoes",
            "Oxfords",
            "Derbies"
        ],
        "rules": "Must be neat, formal, and appropriate for high-level events; avoid casual wear.",
        "strictness": "Strict",
        "description": "A formal outfit suitable for most formal events."
    },
    "general informal occasion": {
        "items": [
            "T-Shirt",
            "Casual Shirt",
            "Jeans",
            "Chinos",
            "Shorts",
            "Sneakers",
            "Casual Shoes",
            "Sweatshirt",
            "Hoodie"
        ],
        "rules": "Comfortable and casual; suitable for relaxed environments.",
        "strictness": "Low",
        "description": "An informal outfit that is comfortable and casual."
    }
}

def determine_occasions(user_message: str) -> str:
    """
    Determines the target occasion from the user's message using simple keyword matching.
    Returns one of the keys in occasion_config or defaults to "all occasions".
    """
    lower_msg = user_message.lower()
    for occ in occasion_config.keys():
        if occ in lower_msg:
            return occ
    return "all occasions"

def generateOutfit(user_message: str, temp: str, wardrobe_items: list[dict]) -> dict:
    """
    Generates an outfit suggestion based on the user's message, current temperature,
    and the items in the user's wardrobe.
    
    Returns a dictionary in the following JSON format:
    {
      "occasion": "<occasion string>",
      "outfit_items": [
         {"id": "<item id>", "sub_type": "<item sub type>", "color": "<item color>"},
         ... (between 3 and 6 items, following guardrails)
      ],
      "description": "<One short sentence describing the outfit>"
    }
    """
    # Determine target occasion from the user message.
    target_occ = determine_occasions(user_message)
    config = occasion_config.get(target_occ, occasion_config["all occasions"])
    
    # Build the rules text from the configuration.
    rules_text = (
        f"Allowed items: {', '.join(config['items']) if config['items'] else 'Any'}, "
        f"Rules: {config['rules']}, "
        f"Strictness: {config['strictness']}. "
        f"Description: {config['description']}"
    )

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

    # Construct a strict few-shot prompt including the occasion configuration and guardrails.
    messages = [
        SystemMessage(
            content=f"""
You are a style assistant that suggests complete outfits based solely on the user's wardrobe, current temperature, and a given occasion configuration.
Rules for target occasion ({target_occ}):
{rules_text}

Additional guardrails:
- The outfit may contain between 3 and 6 items.
- It must include exactly one pair of shoes.
- It must include exactly one pair of pants.
- It must include between one and two tops.
- It must include between one and two outerwear pieces (if applicable).

For each outfit item, include only the item id, sub type, and color.
Your response must be a valid JSON object in the following format:
{{
  "occasion": "<occasion string>",
  "outfit_items": [
    {{"id": "<item id>", "sub_type": "<item sub type>", "color": "<item color>"}},
    ... (between 3 and 6 items following the guardrails)
  ],
  "description": "<One short sentence describing the outfit>"
}}
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
                "white tie event, black tie event, job interview, dinner party, work, gym, "
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
        "dinner party",
        "work",
        "gym",
        "all occasions",
        "casual outing",
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
