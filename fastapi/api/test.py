import requests

BASE_URL = "http://127.0.0.1:8000"

# ✅ Test: Add Clothing Item with Debugging
def test_add_clothing_item():
    url = f"{BASE_URL}/add_clothing_item/"
    data = {
        "user_id": "1",
        "item_type": "jacket",
        "material": "leather",
        "color": "black",
        "formality": "casual",
        "pattern": "solid",
        "fit": "regular",
        "suitable_for_weather": "cold",
        "suitable_for_occasion": "party"
    }

    response = requests.post(url, json=data)

    # Debugging: Print raw response before parsing JSON
    print("Status Code:", response.status_code)
    print("Raw Response Text:", response.text)

    try:
        json_response = response.json()
        print("Parsed JSON Response:", json_response)
    except requests.exceptions.JSONDecodeError as e:
        print("❌ Error parsing JSON:", e)

def get_clothing_item_test():
    url= f"{BASE_URL}/clothing_items/"

    response = requests.get(url)

    # Debugging: Print raw response before parsing JSON
    print("Status Code:", response.status_code)
    print("Raw Response Text:", response.text)

    try:
        json_response = response.json()
        print("Parsed JSON Response:", json_response)
    except requests.exceptions.JSONDecodeError as e:
        print("❌ Error parsing JSON:", e)

# Run the test
test_add_clothing_item()
get_clothing_item_test()
