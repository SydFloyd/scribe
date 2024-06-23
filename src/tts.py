from pathlib import Path
from openai import OpenAI
import os

try:
  openai_key = open("key.txt", 'r').read()
except:
  try:
    openai_key = os.environ.get("OPENAI_API_KEY")
  except:
    raise ValueError("Couldn't resolve openai api key")

client = OpenAI(
    api_key = openai_key
)

def speak(text, filename, voice='onyx'):

  speech_file_path = Path(__file__).parent.parent / f"{filename}.mp3"
  response = client.audio.speech.create(
    model="tts-1",
    voice="onyx",
    input=text,
  )

  response.stream_to_file(speech_file_path)

  return 0

speak("The quick brown fox jumps over the lazy dog.", 'quick_brown')