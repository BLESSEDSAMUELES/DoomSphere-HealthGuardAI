
import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("GROQ_API_KEY")
if not api_key:
    print("Error: GROQ_API_KEY not found in .env")
    exit(1)

url = "https://api.groq.com/openai/v1/models"
headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}

try:
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        models = response.json()['data']
        with open("models_list.txt", "w", encoding="utf-8") as f:
            f.write(f"Found {len(models)} models.\n")
            f.write("-" * 40 + "\n")
            for model in models:
                f.write(model['id'] + "\n")
        print("Models written to models_list.txt")
    else:
        print(f"Error fetching models: {response.status_code} - {response.text}")
except Exception as e:
    print(f"Exception: {e}")
