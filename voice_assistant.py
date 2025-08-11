# voice_assistant.py
# This script runs a voice-controlled assistant using the offline pyttsx3 library.

import os
import asyncio
import json
import re
import speech_recognition as sr
import pyttsx3  # Using the offline pyttsx3 library
from dotenv import load_dotenv

# Import all the existing logic from your project
from bridge import AgentBridge
from all_agents import CropAgent, MarketAgent, SchemeAgent, WeatherAgent, OrganicAgent, SoilAgent
from api_helpers import call_gemini_api

# --- Initialization ---
load_dotenv()

# Initialize the offline TTS engine
try:
    engine = pyttsx3.init()
except Exception as e:
    print(f"🔴 CRITICAL ERROR: Could not initialize pyttsx3 engine: {e}")
    print("Please ensure your OS has a working speech synthesis engine (like SAPI5, NSSpeech, or eSpeak).")
    exit()

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
    bridge.register_agent(name, agent)

# --- A more robust function to clean text for speech ---
def clean_text_for_speech(text):
    """A more aggressive function to remove markdown and non-language characters."""
    if not isinstance(text, str):
        return ""
    
    text = re.sub(r'\s*\([^)]*\)', '', text)
    text = re.sub(r'[\*_`#]', '', text)
    text = re.sub(r'^\s*[\d\.\-\*]+\s*', '', text, flags=re.MULTILINE)
    text = text.replace('₹', 'rupees')
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text

# --- Voice Functions (using offline pyttsx3) ---

def speak(text, voice_id=None):
    """Converts text to speech using the offline pyttsx3 engine."""
    try:
        clean_text = clean_text_for_speech(text)
        
        if not clean_text:
            print("WARNING: No text left to speak after cleaning.")
            return

        print(f"🤖 Kisan Mitra says: {text}")

        # Set the voice if a specific ID is provided
        if voice_id:
            engine.setProperty('voice', voice_id)

        engine.say(clean_text)
        engine.runAndWait() # Blocks while speaking

    except Exception as e:
        print(f"Sorry, I couldn't speak. Error: {e}")

def listen(lang_code='en-US'):
    """Listens for voice input from the user and converts it to text."""
    r = sr.Recognizer()
    with sr.Microphone() as source:
        print("\n🎤 Listening... Please speak your question.")
        r.pause_threshold = 1
        r.adjust_for_ambient_noise(source)
        audio = r.listen(source)

    try:
        print("🔍 Recognizing...")
        query = r.recognize_google(audio, language=lang_code)
        print(f"👤 You said: {query}\n")
        return query
    except sr.UnknownValueError:
        speak("Sorry, I did not understand that.")
        return None
    except sr.RequestError as e:
        speak(f"Could not request results from the speech recognition service; {e}")
        return None
    except Exception as e:
        print(f"An error occurred: {e}")
        return None

def discover_voices():
    """Discovers and maps available voices on the system."""
    print("🔊 Discovering available voices on your system...")
    available_voices = {}
    voices = engine.getProperty('voices')
    for voice in voices:
        try:
            # The lang attribute can be a list, so we take the first one
            lang_code = voice.languages[0] if voice.languages else 'en_US'
            # Normalize the language code format (e.g., en_US -> en-US)
            lang_code_normalized = lang_code.replace('_', '-')
            if lang_code_normalized not in available_voices:
                available_voices[lang_code_normalized] = {
                    "id": voice.id,
                    "name": voice.name
                }
        except Exception:
            continue # Skip voices with malformed data
    print(f"Found {len(available_voices)} unique language voices.")
    return available_voices

# --- AI Router ---
async def route_query_to_agent(query: str, lang: str):
    """Uses an LLM to analyze the user's query and determine the correct agent."""
    prompt = f"""
    You are an intelligent router for an agricultural AI assistant. Your job is to analyze a farmer's query, identify the correct agent, and extract all necessary parameters.
    The user's query is: "{query}"
    Your response must be a JSON object.
    Examples:
    - Query: "weather in hyderabad" -> {{"agent": "WeatherAgent", "parameters": {{"city": "Hyderabad"}}}}
    - Query: "What is the price of potato in Agra?" -> {{"agent": "MarketAgent", "parameters": {{"commodity": "Potato", "market": "Agra"}}}}
    """
    response_text = await call_gemini_api(prompt)
    try:
        json_str = response_text.strip().replace("```json", "").replace("```", "")
        return json.loads(json_str)
    except (json.JSONDecodeError, AttributeError):
        return {"agent": "Unclear", "parameters": {}}

# --- Main Application Logic ---
async def main():
    """The main function to run the voice assistant."""
    
    system_voices = discover_voices()
    
    # Dynamically build the language menu based on available system voices
    language_map = {}
    display_map = {}
    # Define the languages we are interested in
    desired_languages = {
        "en-US": "English", "hi-IN": "हिन्दी", "kn-IN": "ಕನ್ನಡ",
        "te-IN": "తెలుగు", "ta-IN": "தமிழ்"
    }

    menu_index = 1
    for code, name in desired_languages.items():
        if code in system_voices:
            display_map[str(menu_index)] = {"name": name, "rec_code": code, "voice_id": system_voices[code]['id']}
            menu_index += 1

    if not display_map:
        print("\n🔴 No supported voices found on your system. Please install OS language packs.")
        print("Defaulting to the first available English voice.")
        eng_voice = next((v for k, v in system_voices.items() if k.startswith('en')), None)
        if eng_voice:
             display_map["1"] = {"name": "Default English", "rec_code": "en-US", "voice_id": eng_voice['id']}
        else:
            print("🔴 No English voice found either. The application cannot speak. Exiting.")
            exit()


    print("\nPlease select an available language:")
    for key, lang in display_map.items():
        print(f"{key}. {lang['name']}")
    
    choice = input("Enter the number for your language: ")
    selected_lang = display_map.get(choice, display_map["1"])
    
    lang_name = selected_lang["name"]
    rec_code = selected_lang["rec_code"]
    voice_id = selected_lang["voice_id"]

    welcome_message = "Welcome! I am your Kisan Mitra. How can I assist you?"
    speak(welcome_message, voice_id=voice_id)

    while True:
        user_query = listen(lang_code=rec_code)

        if user_query:
            if any(word in user_query.lower() for word in ["exit", "quit", "stop"]):
                speak("Goodbye!", voice_id=voice_id)
                break

            routing_info = await route_query_to_agent(user_query, lang_name)
            agent_name = routing_info.get("agent")
            params = routing_info.get("parameters", {})
            
            result = ""
            if agent_name in agents:
                # Agent logic remains the same
                target_agent = agents[agent_name]
                if agent_name == "CropAgent":
                    speak("Please tell me the full path to the crop image on your computer.", voice_id=voice_id)
                    image_path = input("Enter image path here: ")
                    if os.path.exists(image_path):
                        result = await target_agent.diagnose(image_path, lang_name)
                    else:
                        result = "Sorry, I could not find that file."
                else: # Simplified handling for other agents
                    # This part needs to be expanded based on your actual agent methods
                    result = f"Routing to {agent_name} with parameters {params}" # Placeholder
            else:
                result = "I'm sorry, I'm not sure how to help with that. Could you please rephrase your question?"
            
            speak(result, voice_id=voice_id)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nExiting application.")