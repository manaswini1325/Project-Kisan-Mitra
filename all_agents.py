# all_agents.py
# This file contains all agent classes with the correct async structure.

from api_helpers import call_gemini_api, encode_image_to_base64, get_market_data_from_gov_api, get_weather_from_api
import json
import asyncio

class CropAgent:
    def __init__(self, bridge):
        self.bridge = bridge

    async def diagnose(self, image_path: str, lang: str) -> str:
        """Analyzes a crop image to diagnose diseases."""
        image_base64 = encode_image_to_base64(image_path)
        if not image_base64:
            return "Error: Could not read or encode the image file."

        prompt = f"""
        You are an expert agronomist specializing in crop diseases in India.
        Analyze the provided image of a plant leaf.
        1. Identify the plant if possible (e.g., tomato, rice).
        2. Identify the disease or pest causing the symptoms shown.
        3. Explain the cause of the disease.
        4. Provide a list of actionable steps the farmer should take.
        5. Suggest at least two affordable, locally available remedies (one organic/natural, one chemical).
        
        IMPORTANT: Provide the entire response in the following language: {lang}.
        """
        return await call_gemini_api(prompt, image_base64=image_base64)

class MarketAgent:
    def __init__(self, bridge):
        self.bridge = bridge

    async def get_market_price(self, commodity: str, market: str, lang: str) -> str:
        """Fetches and analyzes market price data."""
        if not commodity or not market:
            return "To get market prices, please tell me the crop and the market name (mandi)."
        
        market_data = get_market_data_from_gov_api(commodity, market)

        if "error" in market_data:
            return f"Sorry, I could not fetch market data. Reason: {market_data['error']}"

        weather_report = self.bridge.request(
            target_agent_name="WeatherAgent",
            task="get_simple_forecast",
            data={"city": market}
        )

        prompt = f"""
        You are a market analyst for Indian farmers. Provide simple, actionable advice.
        Analyze the following real-time market data for '{commodity}' in '{market}'.
        Also consider this weather forecast: {weather_report}

        Market Data:
        {json.dumps(market_data['records'], indent=2)}

        Provide a summary including min, max, and modal price, and a clear recommendation on whether to sell today.
        IMPORTANT: Provide the entire response in the following language: {lang}.
        """
        
        return await call_gemini_api(prompt)

class SchemeAgent:
    def __init__(self, bridge):
        self.bridge = bridge

    async def find_schemes(self, query: str, lang: str) -> str:
        """Finds and explains government schemes."""
        if not query:
            return "Please tell me what kind of scheme or subsidy you are looking for."
            
        prompt = f"""
        You are an expert on Indian government agricultural schemes.
        A farmer has asked for help with: '{query}'.
        Identify the most relevant schemes. For each, explain the benefit, eligibility, and how to apply.
        IMPORTANT: Provide the entire response in the following language: {lang}.
        """
        return await call_gemini_api(prompt)

class WeatherAgent:
    def __init__(self, bridge):
        self.bridge = bridge

    # --- THIS METHOD IS NOW ASYNC AND SMARTER ---
    async def get_weather(self, city: str, lang: str) -> str:
        """Gets a detailed weather report for the user, translated by an LLM."""
        if not city:
            return "Please tell me the city or town for the weather forecast."

        weather_data = get_weather_from_api(city)
        if "error" in weather_data:
             return f"Could not get weather for '{city}'. Reason: {weather_data['error']}"

        main = weather_data['main']
        desc = weather_data['weather'][0]['description']
        
        # Create a simple data structure
        report_data = {
            "city": weather_data['name'],
            "condition": desc.title(),
            "temperature_celsius": main['temp'],
            "humidity_percent": main['humidity']
        }

        # Create a prompt for the LLM to format and translate the data
        prompt = f"""
        You are a weather reporter for an Indian farmer.
        Take the following weather data and present it as a simple, clear report.

        Weather Data:
        {json.dumps(report_data)}

        Example format:
        Weather for [City]:
        - Condition: [Condition]
        - Temperature: [Temperature]°C
        - Humidity: [Humidity]%

        IMPORTANT: Provide the entire response in the following language: {lang}.
        """
        return await call_gemini_api(prompt)

    def handle_request(self, task: str, data: dict) -> str:
        """Handles requests from other agents."""
        if task == "get_simple_forecast":
            city = data.get("city")
            if not city: return "No city provided."
            weather_data = get_weather_from_api(city)
            if "error" in weather_data:
                return "Weather data unavailable."
            desc = weather_data['weather'][0]['description']
            temp = weather_data['main']['temp']
            return f"Forecast for {city}: {desc.title()} with temperatures around {temp}°C."
        return "Unknown task."

class OrganicAgent:
    def __init__(self, bridge):
        self.bridge = bridge

    async def get_tips(self, topic: str, lang: str) -> str:
        """Provides tips on organic farming."""
        if not topic:
            return "Please tell me what organic farming topic you are interested in."

        prompt = f"""
        You are an expert in organic farming in India. A farmer wants to know about '{topic}'.
        Provide a practical, step-by-step guide.
        IMPORTANT: Provide the entire response in the following language: {lang}.
        """
        return await call_gemini_api(prompt)

class SoilAgent:
    def __init__(self, bridge):
        self.bridge = bridge

    async def analyze_soil(self, query: str, lang: str) -> str:
        """Analyzes a farmer's description of their soil."""
        if not query:
            return "Please describe your soil. For example, 'My soil is red and does not hold water well'."

        prompt = f"""
        You are an expert soil scientist for Indian agriculture. A farmer has described their soil: "{query}".
        Provide an analysis: Likely soil type, characteristics, suitable crops, and improvement steps.
        IMPORTANT: Provide the entire response in a clear, easy-to-understand format in the following language: {lang}.
        """
        return await call_gemini_api(prompt)
