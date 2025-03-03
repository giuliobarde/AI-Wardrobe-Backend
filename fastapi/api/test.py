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

def test_sign_up():
    url = f"{BASE_URL}/sign-up/"
    data = {"email": "giuliobarde@gmail.com", "password": "SecurePass123!"}
    response = requests.post(url, json=data)

    # print("Status Code:", response.status_code)
    # print("Raw Response Text:", response.text)

    try:
        json_response = response.json()
        print("Parsed JSON Response:", json_response)
    except requests.exceptions.JSONDecodeError as e:
        print("❌ Error parsing JSON:", e)

import requests

def test_sign_in():
    url = f"{BASE_URL}/sign-in/"
    data = {"email": "giuliobarde@gmail.com", "password": "SecurePass123!"}
    
    # Sign in the user
    response = requests.post(url, json=data)
    # print("\n🔹 Sign-In Status Code:", response.status_code)
    # print("🔹 Raw Response Text:", response.text)

    try:
        json_response = response.json()
        print("✅ Parsed JSON Response:", json_response)

        if "access_token" in json_response:
            access_token = json_response["access_token"]
            # print("\n🟢 User successfully signed in.")

            # Now terminate the session
            test_terminate_session(access_token)

    except requests.exceptions.JSONDecodeError as e:
        print("❌ Error parsing JSON:", e)


def test_terminate_session(access_token):
    url = f"{BASE_URL}/sign-out/"
    headers = {"Authorization": f"Bearer {access_token}"}

    response = requests.post(url, headers=headers)
    print("\n🔹 Sign-Out Status Code:", response.status_code)
    print("🔹 Raw Response Text:", response.text)

    try:
        json_response = response.json()
        print("✅ Parsed JSON Response:", json_response)
    except requests.exceptions.JSONDecodeError as e:
        print("❌ Error parsing JSON:", e)


# Run the test
test_sign_up()


