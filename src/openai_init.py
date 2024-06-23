from openai import OpenAI
import os

try:
  openai_key = os.environ.get("OPENAI_API_KEY")
  assert openai_key != None
except:
  raise ValueError("Couldn't resolve openai api key")
  
client = OpenAI(
    api_key = openai_key
)