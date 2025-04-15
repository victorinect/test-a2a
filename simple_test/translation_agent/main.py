from fastapi import FastAPI, Request
import os

app = FastAPI()

# Use environment variable for host URL or default to localhost
HOST_URL = os.environ.get("HOST_URL", "http://localhost:8002")

# Agent Card for the Translation Agent – advertises a "translate_text" skill.
AGENT_CARD = {
    "name": "TranslatorAgent",
    "description": "An agent that translates English text to Spanish.",
    "url": HOST_URL,  # base URL where this agent is hosted
    "version": "1.0.0",
    "capabilities": {
        "streaming": False,
        "pushNotifications": False,
        "stateTransitionHistory": False
    },
    "defaultInputModes": ["text", "text/plain"],
    "defaultOutputModes": ["text", "text/plain"],
    "skills": [
        {
            "id": "translate_text",
            "name": "English-to-Spanish Translator",
            "description": "Translates English text into Spanish.",
            "tags": ["translation", "language"]
        }
    ]
}

@app.get("/.well-known/agent.json")
async def get_agent_card():
    """Provides this agent's metadata (Agent Card) for discovery."""
    return AGENT_CARD

@app.post("/tasks/send")
async def handle_task(request: Request):
    """Handles incoming translation tasks and returns the Spanish translation."""
    task_request = await request.json()
    task_id = task_request.get("id")
    # Extract the user's text to translate.
    try:
        user_text = task_request["message"]["parts"][0]["text"]
    except Exception:
        return {"error": "Invalid request format"}, 400

    # Determine the portion to translate. 
    text_to_translate = user_text
    # If user text is a phrase like "Translate X to Spanish", strip the directive:
    lower_text = user_text.lower()
    if " to spanish" in lower_text:
        # Remove any trailing " to Spanish" and any leading "translate ".
        text_to_translate = user_text[:lower_text.index(" to spanish")].strip()
        if text_to_translate.lower().startswith("translate"):
            text_to_translate = text_to_translate[len("translate"):].strip().strip(":")
    # For simplicity, use a small static dictionary for translation.
    dictionary = {
        "hello": "hola",
        "world": "mundo",
        "good morning": "buenos días",
        "good night": "buenas noches",
        "thank you": "gracias",
        "goodbye": "adiós"
    }
    translated = []
    # Split into words (very naive approach for demonstration).
    for word in text_to_translate.lower().split():
        translated.append(dictionary.get(word, word))
    translated_text = " ".join(translated)
    # Capitalize translated sentence if original starts with capital.
    if text_to_translate and text_to_translate[0].isupper():
        translated_text = translated_text.capitalize()

    # Formulate the translation result.
    result_text = f"In Spanish: {translated_text}"
    # Build A2A response task with original and translated text.
    response_task = {
        "id": task_id,
        "status": {"state": "completed"},
        "messages": [
            task_request.get("message", {}),   # original user message (for history)
            {
                "role": "agent",
                "parts": [ {"text": result_text} ]  # agent's translated reply
            }
        ]
    }
    return response_task