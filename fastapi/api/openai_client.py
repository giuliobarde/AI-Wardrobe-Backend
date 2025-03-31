import os
import re
import json
import logging
from typing import Set
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from pydantic import BaseModel

# Load environment variables
load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")

# Initialize the OpenAI Chat model via LangChain with a default sampling parameter.
llm = ChatOpenAI(
    openai_api_key=openai_api_key,
    temperature=0.5,  # Default generation temperature; will be updated dynamically.
    top_p=1,
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

# Allowed occasions now includes a new "very formal occasion"
ALLOWED_OCCASIONS = [
    "white tie event",
    "black tie event",
    "very formal occasion",
    "job interview",
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

# Dictionary mapping allowed occasions to configuration details.
occasion_config = {
    "white tie event": {
        "items": [
            "Tailcoat",
            "Dress Shirt",
            "Tuxedo Pants",
            "Dress Pants",
            "Patent Leather Oxfords"
        ],
        "rules": "Must adhere to the highest level of formality; only very formal items allowed.",
        "strictness": "Extremely strict",
        "description": "White tie is the most formal dress code, reserved for very special events."
    },
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
    "very formal occasion": {
        "items": [
            "Tailcoat",
            "Tuxedo Jacket",
            "Dress Shirt",
            "Dress Pants",
            "Patent Leather Oxfords",
            "Formal Dress Shoes"
        ],
        "rules": "Only high formal items allowed. Strict dress code; no casual items.",
        "strictness": "Very strict",
        "description": "A very formal occasion demands the utmost elegance and sophistication."
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
    "date night": {
        "items": [
            "Casual Shirt",
            "Jeans",
            "Chinos",
            "Sneakers",
            "Loafers",
            "Blazer"
        ],
        "rules": "Should be stylish yet approachable.",
        "strictness": "Moderate",
        "description": "An outfit that is both attractive and comfortable for a date."
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

def determineOccasions(user_message: str) -> str:
    """
    Determines the target occasion from the user's message using a two-step process:
    
    1. Exact Matching:
       - Converts the input to lowercase and iterates over the allowed occasion phrases
         (from occasion_config) sorted by descending length.
       - Uses regular expressions with word boundaries to ensure that only whole phrases match.
         
    2. Synonyms/Fallback:
       - If no direct match is found, it checks a synonyms mapping for alternate terms or abbreviations.
       - This also handles phrases like "very formal" by mapping them directly to "very formal occasion".
         
    Returns:
        A string representing one of the keys in occasion_config. Defaults to "all occasions" if no match is found.
    """
    lower_msg = user_message.lower()
    
    # Step 1: Exact matching with allowed phrases sorted by length (longest first).
    for occ in sorted(occasion_config.keys(), key=len, reverse=True):
        pattern = r'\b' + re.escape(occ) + r'\b'
        if re.search(pattern, lower_msg):
            return occ

    # Step 2: Synonyms mapping for common alternate phrases.
    synonyms = {
        "very formal": "very formal occasion",
        "black tie": "black tie event",
        "white tie": "white tie event",
        "interview": "job interview",
        "dinner": "dinner party",
        "office": "work",
        "gym": "gym",
        "casual": "casual outing",
        "date": "date night",
        "party": "party",
        "formal": "general formal occasion",
        "informal": "general informal occasion"
    }
    for key, value in synonyms.items():
        pattern = r'\b' + re.escape(key) + r'\b'
        if re.search(pattern, lower_msg):
            return value

    return "all occasions"

def generateOutfit(user_message: str, outside_temp: str, wardrobe_items: list[dict]) -> dict:
    """
    Generates an outfit suggestion based on the user's message, the outside temperature,
    and the items in the user's wardrobe.
    
    This function uses a two-step chain-of-thought process with few-shot prompting.
    For black tie and very formal events, it ensures that the outfit includes the required formal items.
    
    The generation temperature is set dynamically based on the occasion's formality:
      - More formal occasions (e.g., "black tie event", "very formal occasion") use a lower generation temperature (0.1).
      - More informal occasions (e.g., "general informal occasion") use a higher generation temperature (0.7).
    The provided outside_temp (e.g., "20C") is still included in the prompt.
    
    Returns:
        A dictionary in the following JSON format:
        {
          "occasion": "<occasion string>",
          "outfit_items": [
             {"id": "<item id>", "sub_type": "<item sub type>", "color": "<item color>"},
             ... (between 3 and 6 items)
          ],
          "description": "<One short sentence describing the outfit>"
        }
    """
    # Determine target occasion.
    target_occ = determineOccasions(user_message)
    config = occasion_config.get(target_occ, occasion_config["all occasions"])
    
    # Determine generation temperature based on occasion formality.
    occasion_temperature = {
        "white tie event": 0.1,
        "black tie event": 0.1,
        "very formal occasion": 0.2,
        "job interview": 0.2,
        "dinner party": 0.4,
        "work": 0.4,
        "gym": 0.7,
        "all occasions": 0.5,
        "casual outing": 0.7,
        "date night": 0.6,
        "party": 0.6,
        "general formal occasion": 0.3,
        "general informal occasion": 0.7,
    }
    generation_temp = occasion_temperature.get(target_occ, 0.5)
    
    # Update the LLM's generation temperature dynamically.
    llm.temperature = generation_temp

    # Build the rules text.
    rules_text = (
        f"Allowed items: {', '.join(config['items']) if config['items'] else 'Any'}, "
        f"Rules: {config['rules']}, "
        f"Strictness: {config['strictness']}. "
        f"Description: {config['description']}"
    )
    
    # Format the wardrobe items.
    formatted_items = []
    wardrobe_ids: Set[str] = set()
    for item in wardrobe_items:
        item_id = item.get('id', 'N/A')
        wardrobe_ids.add(item_id)
        formatted_item = (
            f"Item ID: {item_id}, "
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

    # -----------------------
    # Step 1: Candidate Generation with Few-Shot Prompting
    # -----------------------
    candidate_messages = [
        SystemMessage(
            content=f"""
Step 1: Candidate Generation.
You are a style assistant that generates outfit suggestions.
Below are four demonstration examples with chain-of-thought reasoning.
IMPORTANT: Only select items that exist in the provided wardrobe (i.e. with matching Item IDs).

Example 1:
User: "I need an outfit for a wedding. Outside Temperature: 20C. Wardrobe: [Example wardrobe items]."
Assistant Reasoning: For a wedding, a formal and elegant outfit is needed. Considering a white dress shirt, navy suit pants, black dress shoes, and a navy suit jacket, this combination creates an elegant, classic look.
Candidate Outfit: 
- Item ID: ex1_1, Sub Type: White Dress Shirt, Color: White
- Item ID: ex1_2, Sub Type: Navy Suit Pants, Color: Navy
- Item ID: ex1_3, Sub Type: Black Dress Shoes, Color: Black
- Item ID: ex1_4, Sub Type: Navy Suit Jacket, Color: Navy

Example 2:
User: "I need an outfit for a dinner party. Outside Temperature: 18C. Wardrobe: [Example wardrobe items]."
Assistant Reasoning: For a dinner party, the outfit should be stylish yet not overly formal. A black dress shirt, dark jeans, brown loafers, and a grey blazer create a modern and sophisticated look.
Candidate Outfit:
- Item ID: ex3_1, Sub Type: Black Dress Shirt, Color: Black
- Item ID: ex3_2, Sub Type: Dark Jeans, Color: Dark Blue
- Item ID: ex3_3, Sub Type: Brown Loafers, Color: Brown
- Item ID: ex3_4, Sub Type: Grey Blazer, Color: Grey

Example 3:
User: "I need an outfit for the gym. Outside Temperature: 22C. Wardrobe: [Example wardrobe items]."
Assistant Reasoning: For the gym, comfort and mobility are most important. An athletic t-shirt, athletic shorts, and running shoes ensure freedom of movement and comfort.
Candidate Outfit:
- Item ID: ex4_1, Sub Type: Athletic T-Shirt, Color: White
- Item ID: ex4_2, Sub Type: Athletic Shorts, Color: Black
- Item ID: ex4_3, Sub Type: Running Shoes, Color: Red

Example 4:
User: "I need an outfit for a job interview. Outside Temperature: 20C. Wardrobe: [Example wardrobe items]."
Assistant Reasoning: For a job interview, professionalism is key. A light blue dress shirt, grey slacks, black leather dress shoes, and a charcoal blazer form a refined and professional ensemble.
Candidate Outfit:
- Item ID: ex2_1, Sub Type: Light Blue Dress Shirt, Color: Light Blue
- Item ID: ex2_2, Sub Type: Grey Slacks, Color: Grey
- Item ID: ex2_3, Sub Type: Black Leather Dress Shoes, Color: Black
- Item ID: ex2_4, Sub Type: Charcoal Blazer, Color: Charcoal

Now, using the following rules:
{rules_text}
and the details provided below:
Occasion: {user_message}
Outside Temperature: {outside_temp}
{wardrobe_text}

Please generate your candidate outfit list with your chain-of-thought reasoning. Do NOT output the final JSON yet.
"""
        ),
        HumanMessage(
            content="Please generate your candidate outfit list with reasoning."
        )
    ]
    
    candidate_response = llm.invoke(candidate_messages)
    candidate_output = candidate_response.content  # Contains reasoning and candidate list.
    
    # -----------------------
    # Step 2: Refinement and Validation with Few-Shot Prompting
    # -----------------------
    refinement_messages = [
        HumanMessage(
            content=f"""
Step 2: Refinement and Validation.
Review the candidate outfit list you generated:
{candidate_output}
Now, ensure that the candidate outfit meets these guardrails:
- Contains between 3 and 6 items.
- Includes exactly one pair of shoes.
- Includes exactly one pair of pants.
- Contains between one and two tops.
- Contains between one and two outerwear pieces (if applicable).
If any rule is violated, adjust the candidate list accordingly.

Below are demonstration examples:

Example 1 (Wedding):
Candidate: [White Dress Shirt, Navy Suit Pants, Black Dress Shoes, Navy Suit Jacket]
Refined Output: {{"occasion": "wedding", "outfit_items": [{{"id": "ex1_1", "sub_type": "White Dress Shirt", "color": "White"}}, {{"id": "ex1_2", "sub_type": "Navy Suit Pants", "color": "Navy"}}, {{"id": "ex1_3", "sub_type": "Black Dress Shoes", "color": "Black"}}, {{"id": "ex1_4", "sub_type": "Navy Suit Jacket", "color": "Navy"}}], "description": "An elegant and classic wedding ensemble."}}

Example 2 (Dinner Party):
Candidate: [Black Dress Shirt, Dark Jeans, Brown Loafers, Grey Blazer]
Refined Output: {{"occasion": "dinner party", "outfit_items": [{{"id": "ex3_1", "sub_type": "Black Dress Shirt", "color": "Black"}}, {{"id": "ex3_2", "sub_type": "Dark Jeans", "color": "Dark Blue"}}, {{"id": "ex3_3", "sub_type": "Brown Loafers", "color": "Brown"}}, {{"id": "ex3_4", "sub_type": "Grey Blazer", "color": "Grey"}}], "description": "A stylish and contemporary outfit perfect for a dinner party."}}

Example 3 (Gym):
Candidate: [Athletic T-Shirt, Athletic Shorts, Running Shoes]
Refined Output: {{"occasion": "gym", "outfit_items": [{{"id": "ex4_1", "sub_type": "Athletic T-Shirt", "color": "White"}}, {{"id": "ex4_2", "sub_type": "Athletic Shorts", "color": "Black"}}, {{"id": "ex4_3", "sub_type": "Running Shoes", "color": "Red"}}], "description": "A comfortable and mobile gym outfit."}}

Example 4 (Job Interview):
Candidate: [Light Blue Dress Shirt, Grey Slacks, Black Leather Dress Shoes, Charcoal Blazer]
Refined Output: {{"occasion": "job interview", "outfit_items": [{{"id": "ex2_1", "sub_type": "Light Blue Dress Shirt", "color": "Light Blue"}}, {{"id": "ex2_2", "sub_type": "Grey Slacks", "color": "Grey"}}, {{"id": "ex2_3", "sub_type": "Black Leather Dress Shoes", "color": "Black"}}, {{"id": "ex2_4", "sub_type": "Charcoal Blazer", "color": "Charcoal"}}], "description": "A refined and professional outfit for a job interview."}}

Now, using your refined reasoning and the guardrails provided above, output the final JSON object (with no extra text) in the following format:
{{
  "occasion": "<occasion string>",
  "outfit_items": [
    {{"id": "<item id>", "sub_type": "<item sub type>", "color": "<item color>"}},
    ... (3 to 6 items)
  ],
  "description": "<One short sentence describing the outfit>"
}}
"""
        )
    ]
    
    final_response = llm.invoke(refinement_messages)
    generated = final_response.content.strip()
    
    # Optionally remove stray chain-of-thought text if present.
    if "### Output:" in generated:
        generated = generated.split("### Output:")[-1].strip()
    
    try:
        outfit_json = json.loads(generated)
    except Exception as e:
        outfit_json = {
            "occasion": target_occ,
            "outfit_items": [],
            "description": generated
        }
    
    # -----------------------
    # Post-Processing: Validate candidate item IDs.
    # -----------------------
    valid_outfit_items = []
    for candidate_item in outfit_json.get("outfit_items", []):
        if candidate_item.get("id") in wardrobe_ids:
            valid_outfit_items.append(candidate_item)
        else:
            logging.warning("Candidate item with id %s not found in wardrobe. Removing item.", candidate_item.get("id"))
    outfit_json["outfit_items"] = valid_outfit_items
    
    # -----------------------
    # Additional Check for Black Tie and Very Formal Events.
    # -----------------------
    if target_occ in ["black tie event", "very formal occasion"]:
        # Check for tuxedo, tailcoat, or dress suit and for dress shoes.
        found_formal_top = any(
            any(keyword in candidate_item.get("sub_type", "").lower() for keyword in ["tuxedo", "tailcoat", "suit"])
            for candidate_item in outfit_json.get("outfit_items", [])
        )
        found_dress_shoes = any(
            "dress shoes" in candidate_item.get("sub_type", "").lower() or "oxford" in candidate_item.get("sub_type", "").lower()
            for candidate_item in outfit_json.get("outfit_items", [])
        )
        
        note = ""
        if not found_formal_top:
            note += "Note: Formal occasions require a tuxedo, tailcoat, or equivalent formal suit. Consider renting one if necessary."
        if not found_dress_shoes:
            note += " Also, ensure you have appropriate dress shoes."
        if note:
            outfit_json["description"] += " " + note
    
    return outfit_json

def setOccasion(item: ClothingItem) -> ClothingItem:
    """
    Updates the clothing item with one or more suitable occasion tags.
    The model is prompted to return a JSON object with a key "occasions" mapping to a list.
    Since the database expects a string, the list will be joined into a comma-separated string.
    """
    prompt = (
        f"Given a clothing item with the following details:\n"
        f"Item type: {item.item_type}\n"
        f"Material: {item.material}\n"
        f"Color: {item.color}\n"
        f"Formality: {item.formality}\n"
        f"Pattern: {item.pattern}\n"
        f"Fit: {item.fit}\n"
        f"Suitable for weather: {item.suitable_for_weather}\n"
        f"Sub-type: {item.sub_type}\n\n"
        "Which occasion(s) is this item most suitable for? Please choose one or more from the following list:\n"
        f"{', '.join(ALLOWED_OCCASIONS)}\n\n"
        "Return your answer as a JSON object with a single key \"occasions\" that maps to a list of occasion strings. "
        "Do not output any extra text."
    )
    messages = [SystemMessage(content=prompt)]
    
    try:
        response = llm.invoke(messages)
        generated = response.content.strip()
        logging.info("setOccasion LLM response: %s", generated)
        # Parse the response as JSON.
        parsed = json.loads(generated)
        occasions = parsed.get("occasions", [])
        # Ensure only allowed options are returned.
        valid_occasions = [opt for opt in occasions if opt in ALLOWED_OCCASIONS]
        if not valid_occasions:
            valid_occasions = ["all occasions"]
    except Exception as e:
        logging.error("Error in setOccasion: %s", e)
        valid_occasions = ["all occasions"]
    
    # Join the list into a comma-separated string.
    item.suitable_for_occasion = ", ".join(valid_occasions)
    return item

# TODO (Step 4): Incorporate dynamic context from user preferences and historical outfit choices.
# TODO (Step 5): Enhance fallback and error handling if the generated JSON is invalid.
# TODO (Step 6): Implement an interactive feedback loop to refine outfit suggestions based on user input.
