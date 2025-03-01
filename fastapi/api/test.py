import requests

url = "http://127.0.0.1:8000/chat"
data = {"user_message": "Going to the museum"}

response = requests.post(url, json=data)
print(response.json())
