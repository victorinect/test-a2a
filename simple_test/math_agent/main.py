from fastapi import FastAPI, Request
import re
import os

app = FastAPI()

# Use environment variable for host URL or default to localhost
HOST_URL = os.environ.get("HOST_URL", "http://localhost:8001")

# Agent Card for the Math Agent – advertises a "calculate" skill.
AGENT_CARD = {
    "name": "MathAgent",
    "description": "An agent that performs simple arithmetic calculations.",
    "url": HOST_URL,  # base URL where this agent is hosted
    "version": "1.0.0",
    "capabilities": {
        "streaming": False,          # no streaming responses
        "pushNotifications": False,  # no push notifications
        "stateTransitionHistory": False
    },
    "defaultInputModes": ["text", "text/plain"],
    "defaultOutputModes": ["text", "text/plain"],
    "skills": [
        {
            "id": "calculate",
            "name": "Calculator",
            "description": "Performs basic arithmetic (addition, subtraction, multiplication, division).",
            "tags": ["math", "arithmetic"]
        }
    ]
}

@app.get("/.well-known/agent.json")
async def get_agent_card():
    """Provides this agent's metadata (Agent Card) for discovery."""
    return AGENT_CARD

@app.post("/tasks/send")
async def handle_task(request: Request):
    """Handles incoming calculation tasks and returns the result."""
    task_request = await request.json()
    task_id = task_request.get("id")
    # Extract the user's query from the task request.
    try:
        user_text = task_request["message"]["parts"][0]["text"]
    except Exception:
        return {"error": "Invalid request format"}, 400

    # Simple parsing: replace words with symbols and remove invalid characters.
    expr = user_text.lower()
    # Replace common words with arithmetic symbols (e.g., "plus" -> "+").
    replacements = {
        "plus": "+", "add": "+", 
        "minus": "-", "subtract": "-", 
        "times": "*", "multiply": "*", "multiplied by": "*", "x": "*",
        "divide": "/", "divided by": "/"
    }
    for word, sym in replacements.items():
        expr = expr.replace(word, sym)
    # Remove any character that is not a digit, operator or whitespace.
    expr = re.sub(r"[^0-9+\-*/().\s]", "", expr)
    expr = expr.strip()
    result_text = ""
    if expr:
        try:
            # **Execution:** Evaluate the arithmetic expression.
            result_value = eval(expr)  # caution: using eval for simplicity; in real usage, use a safe parser
            result_text = f"The result is {result_value}."
        except Exception as e:
            result_text = "I'm sorry, I couldn't calculate that."
    else:
        result_text = "I'm sorry, I could not understand the calculation."

    # Form the A2A response task with the result.
    response_task = {
        "id": task_id,
        "status": {"state": "completed"},      # mark task as completed
        "messages": [
            task_request.get("message", {}),   # include the original user message
            {   # Agent's response message with the calculation result
                "role": "agent",
                "parts": [ {"text": result_text} ]
            }
        ]
    }
    return response_task