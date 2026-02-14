import google.generativeai as genai
import os

key = "AIzaSyAMxry7kyw7svsZumX6_hu7aGELVHamkm0"

try:
    genai.configure(api_key=key)
    print("Listing available models...")
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(m.name)
            
    # Try a known fallback
    model = genai.GenerativeModel('gemini-pro')
    response = model.generate_content("Hello! Are you working?")
    print(f"SUCCESS with gemini-pro: {response.text}")
except Exception as e:
    print(f"ERROR: {e}")
