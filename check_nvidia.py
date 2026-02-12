
import os
import requests
from dotenv import load_dotenv

load_dotenv()

# Placeholder for user to fill
api_key = os.getenv("NVIDIA_API_KEY") 

print(f"Checking NVIDIA API... Key present: {bool(api_key)}")

# Standard NVIDIA NIM endpoint for list models is not always 'v1/models', 
# but let's try standard OpenAI format which they often support.
url = "https://integrate.api.nvidia.com/v1/models" 
# Or sometimes "https://api.nvidia.com/v1/models" depending on the service
# build.nvidia.com usually gives a specific invoke URL per model.
# Let's try to list generic models if possible, or just test a known one.

headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}

try:
    response = requests.get(url, headers=headers, timeout=5)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        print("Models found:", response.json())
    else:
        print("Response:", response.text)
except Exception as e:
    print(f"Error: {e}")
