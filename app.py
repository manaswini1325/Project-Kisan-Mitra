# app.py
# This file creates a web server to run Project Kisan as a local web application.

import os
import sys
import json
import asyncio
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv

# Add the project's root directory to Python's path if it's not already there
# This ensures that Python can find the other .py files
if os.path.dirname(os.path.abspath(__file__)) not in sys.path:
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import your existing agents and bridge
from bridge import AgentBridge
from all_agents import CropAgent, MarketAgent, SchemeAgent, WeatherAgent, OrganicAgent, SoilAgent
from api_helpers import call_gemini_api

# --- Initialization ---
load_dotenv()

# Initialize the Flask app
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)


# Initialize the agent bridge and all agents
bridge = AgentBridge()
agents = {
    "CropAgent": CropAgent(bridge),
    "MarketAgent": MarketAgent(bridge),
    "SchemeAgent": SchemeAgent(bridge),
    "WeatherAgent": WeatherAgent(bridge),
    "OrganicAgent": OrganicAgent(bridge),
    "SoilAgent": SoilAgent(bridge)
}
for name, agent in agents.items():
    print(f"[Bridge] Agent '{name}' has been registered.")
    bridge.register_agent(name, agent)

print("\n✅ Kisan Web App Server is ready and agents are initialized.")

# --- AI Router ---
async def route_query_to_agent(query: str, lang: str):
    """Uses an LLM to analyze the user's query and determine the correct agent."""
    
    print("🧠 AI Router: Analyzing query...")
    
    # --- SOLUTION: Added a smarter prompt for the router ---
    prompt = f"""
    You are an intelligent router for an agricultural AI assistant called Kisan Mitra. Your job is to analyze a farmer's query and determine which expert agent should handle it. You must also extract any necessary information (parameters) from the query.

    The user's query is: "{query}"

    Here are the available agents and the keywords they respond to:
    - "WeatherAgent": For questions about weather, forecast, rain, temperature, humidity.
    - "MarketAgent": For questions about market prices, mandi rates, crop prices.
    - "SchemeAgent": For questions about government schemes, subsidies, PM-KISAN, loans.
    - "SoilAgent": For questions describing soil type (e.g., "my soil is red and sandy", "black and sticky").
    - "OrganicAgent": For questions about organic farming, compost, natural pesticides.
    - "CropAgent": For questions about crop diseases, pests, sick plants (usually triggered by a photo).
    - "General": For polite closings like "thank you", "ok", "bye".

    Your response must be a single, clean JSON object with two keys: "agent" and "parameters".

    Examples:
    - Query: "weather in hyderabad?" -> {{"agent": "WeatherAgent", "parameters": {{"city": "Hyderabad"}}}}
    - Query: "What is the price of potato in Agra?" -> {{"agent": "MarketAgent", "parameters": {{"commodity": "Potato", "market": "Agra"}}}}
    - Query: "Tell me about the PM-KISAN scheme" -> {{"agent": "SchemeAgent", "parameters": {{"query": "PM-KISAN scheme"}}}}
    - Query: "My soil is black and sticky" -> {{"agent": "SoilAgent", "parameters": {{"query": "My soil is black and sticky"}}}}
    - Query: "Hyderabad" -> {{"agent": "WeatherAgent", "parameters": {{"city": "Hyderabad"}}}}
    - Query: "how to make compost" -> {{"agent": "OrganicAgent", "parameters": {{"topic": "how to make compost"}}}}
    - Query: "thank you" -> {{"agent": "General", "parameters": {{"response": "You're welcome! Let me know if you have more questions."}}}}
    """
    
    response_text = await call_gemini_api(prompt)
    try:
        # Clean the response to make sure it's valid JSON
        json_str = response_text.strip().replace("```json", "").replace("```", "")
        parsed_json = json.loads(json_str)
        print(f"🧠 AI Router Output: {json.dumps(parsed_json)}")
        return parsed_json
    except (json.JSONDecodeError, AttributeError) as e:
        print(f"🔴 AI Router failed to parse JSON: {e}")
        return {"agent": "Unclear", "parameters": {}}

# --- Web Routes ---
@app.route('/')
def index():
    """Renders the main chat interface."""
    return render_template('index.html')

@app.route('/ask', methods=['POST'])
async def ask():
    """Handles incoming requests from the user (text or photo)."""
    
    if 'photo' in request.files:
        photo = request.files['photo']
        language = request.form.get('language', 'English')
        filename = os.path.join(app.config['UPLOAD_FOLDER'], photo.filename)
        photo.save(filename)
        
        target_agent = agents["CropAgent"]
        result = await target_agent.diagnose(filename, language)

    else:
        data = request.json
        query = data.get('query')
        language = data.get('language', 'English')
        
        routing_info = await route_query_to_agent(query, language)
        agent_name = routing_info.get("agent")
        params = routing_info.get("parameters", {})
        
        result = "I'm sorry, I'm not sure how to help with that. Could you please rephrase your question?"

        if agent_name == "General":
            result = params.get("response", "You're welcome!")
        elif agent_name in agents:
            target_agent = agents[agent_name]
            try:
                if agent_name == "MarketAgent":
                    result = await target_agent.get_market_price(params.get("commodity"), params.get("market"), language)
                elif agent_name == "SchemeAgent":
                    result = await target_agent.find_schemes(params.get("query"), language)
                elif agent_name == "WeatherAgent":
                    result = await target_agent.get_weather(params.get("city"), language)
                elif agent_name == "OrganicAgent":
                    result = await target_agent.get_tips(params.get("topic"), language)
                elif agent_name == "SoilAgent":
                    result = await target_agent.analyze_soil(params.get("query"), language)
            except Exception as e:
                print(f"🔴 ERROR processing request: {e}")
                result = "Sorry, something went wrong."

    return jsonify({'response': result})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
