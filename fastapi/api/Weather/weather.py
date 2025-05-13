import os
import requests
from dotenv import load_dotenv

load_dotenv()

CITY    = "New York"
BASE    = os.getenv("WEATHER_BASE_URL")
API_KEY = os.getenv("WEATHER_API_KEY")

# Build URL with correct punctuation and parameter names
url = f"{BASE}?key={API_KEY}&q={CITY}"

try:
    response = requests.get(url)
    response.raise_for_status()           # catch HTTP errors
    weather_data = response.json()        # note the parentheses
    print(weather_data)
except requests.RequestException as e:
    print("Error fetching weather:", e)
