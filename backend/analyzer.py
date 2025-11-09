# backend/analyzer.py
import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# Define your model
model = genai.GenerativeModel("gemini-2.5-flash")

def analyze_message_with_gemini(message: str) -> dict:
    """Use Gemini to classify priority and generate a response."""
    prompt = f"""
    You are a Capital One customer service assistant.
    A user said: "{message}"

    Classify the issue as HIGH, MEDIUM, or LOW priority:
    - HIGH: Fraud, suspicious activity, or financial distress
    - MEDIUM: Payments, balance inquiries, or due dates
    - LOW: General info or settings

    Respond with a short message to the user and include a JSON summary like:
    {{
        "priority": "HIGH",
        "response": "Connecting you with a live agent...",
        "confidence": 0.95
    }}
    """

    result = model.generate_content(prompt)
    text = result.text.strip()

    # quick and dirty parse (Gemini outputs structured text)
    import json, re
    try:
        json_text = re.search(r'\{.*\}', text, re.DOTALL).group(0)
        parsed = json.loads(json_text)
        return parsed
    except Exception:
        # fallback if parsing fails
        return {
            "priority": "LOW",
            "response": "This message will be handled by the assistant.",
            "confidence": 0.7,
        }
