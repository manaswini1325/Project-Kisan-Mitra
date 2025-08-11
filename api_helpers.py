# api_helpers.py
# This file centralizes all the logic for making external API calls.
# This version uses the fast and efficient gemini-2.0-flash model.

import os
import requests
import base64
import json

async def call_gemini_api(prompt, image_base64=None):
    """
    Calls the Gemini API for either text or vision models.
    This version uses the fast gemini-2.0-flash model.
    """
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("🔴 ERROR: GOOGLE_API_KEY not found in .env file.")
        return "Error: GOOGLE_API_KEY not found in .env file. Please get a key from Google AI Studio."

    headers = {'Content-Type': 'application/json'}
    parts = [{"text": prompt}]
    
    # --- SOLUTION: Switch to the simple, faster model ---
    # This model handles both text and images with a single endpoint.
    api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"
    if image_base64:
        # Add the image part if it exists
        parts.append({"inlineData": {"mimeType": "image/jpeg", "data": image_base64}})
    # --- END OF SOLUTION ---

    payload = {"contents": [{"role": "user", "parts": parts}]}

    try:
        print(f"➡️ Sending request to Gemini API (flash model)...")
        response = requests.post(api_url, headers=headers, json=payload)
        
        response.raise_for_status() 
        
        result = response.json()

        if result.get('candidates'):
            print("✅ Successfully received response from Gemini API.")
            return result['candidates'][0]['content']['parts'][0]['text']
        else:
            print(f"🟡 WARNING: Gemini API responded but with no candidates. Full response: {response.text}")
            return "The AI model responded, but the content may have been blocked for safety reasons."
            
    except requests.exceptions.RequestException as e:
        if e.response is not None:
            print(f"🔴 Server Response: {e.response.text}")
        return f"API Request Error: Could not connect to Google AI. Please check your API key and ensure the API is enabled in your Google Cloud project."
    except Exception as e:
        print(f"🔴 ERROR: An unexpected error occurred: {e}")
        return f"An unexpected error occurred during the API call."

# The rest of the functions remain the same
def get_market_data_from_gov_api(commodity: str, market: str) -> dict:
    """Fetches real-time market price data from India's data.gov.in API."""
    api_key = os.getenv("DATA_GOV_IN_API_KEY") 
    if not api_key:
        return {"error": "DATA_GOV_IN_API_KEY not found."}
    base_url = "https://api.data.gov.in/resource/9ef84268-d588-465a-a308-a864a43d0070"
    params = {
        "api-key": api_key, "format": "json", "offset": "0", "limit": "10",
        "filters[commodity]": commodity, "filters[market]": market
    }
    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}

def get_weather_from_api(city: str) -> dict:
    """Fetches weather data from OpenWeatherMap API."""
    api_key = os.getenv("OPENWEATHER_API_KEY")
    if not api_key:
        return {"error": "OPENWEATHER_API_KEY not found."}
    base_url = "http://api.openweathermap.org/data/2.5/weather"
    params = {"q": city, "appid": api_key, "units": "metric"}
    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}

def encode_image_to_base64(image_path):
    """Encodes an image file to a base64 string."""
    try:
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    except FileNotFoundError:
        return None
