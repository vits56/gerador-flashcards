import os
import google.generativeai as genai

def test():
    print("Testing Gemini Engine...")
    api_key = "AQ.Ab8RN6KIDvWwQreNBrDW5IbNS02lJrkchwLN6ddOI6vDb51VvQ"
    genai.configure(api_key=api_key)
    
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(m.name)

if __name__ == "__main__":
    test()
