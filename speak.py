# Import the necessary libraries
from gtts import gTTS
from playsound import playsound
import os

def speak(text_to_speak, language_code):
    """
    A simple function that takes text and a language code,
    and speaks it out loud.
    'te' = Telugu
    'kn' = Kannada
    """
    print(f"Preparing to speak in language '{language_code}'...")
    
    # Create the text-to-speech object
    tts = gTTS(text=text_to_speak, lang=language_code, slow=False)
    
    # Save the audio to a temporary file named 'voice.mp3'
    audio_file = "voice.mp3"
    tts.save(audio_file)
    
    # Play the audio file
    playsound(audio_file)
    
    # Clean up by deleting the temporary audio file
    os.remove(audio_file)


# --- Let's use the function for both languages ---

# 1. Speak in Telugu
telugu_text = "మీకు స్వాగతం"
speak(telugu_text, 'te')


# 2. Speak in Kannada
kannada_text = "ನಿಮಗೆ ಸ್ವಾಗತ"
speak(kannada_text, 'kn')


print("\nFinished speaking both languages.")