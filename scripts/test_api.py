import requests
import os
from dotenv import load_dotenv
import json

load_dotenv()

# Get API key
API_KEY = os.getenv("OPENWEATHER_API_KEY")
print(API_KEY)

# City name
CITY = "London"

# API URL
url = f"https://api.openweathermap.org/data/2.5/weather?q={CITY}&appid={API_KEY}&units=metric"

# Make request
response = requests.get(url)

# Check response
if response.status_code == 200:
    data = response.json()

    print("API call successful!")
    print(json.dumps(data, indent=2))

else:
    print(f"Error: {response.status_code}")
    print(response.text)
