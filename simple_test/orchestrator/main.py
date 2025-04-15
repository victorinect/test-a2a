from fastapi import FastAPI, Request
import requests
import uuid
import os

app = FastAPI()

# Get remote agent URLs from environment variables or use defaults
MATH_AGENT_URL = os.environ.get("MATH_AGENT_URL", "http://localhost:8001")
TRANSLATOR_AGENT_URL = os.environ.get("TRANSLATOR_AGENT_URL", "http://localhost:8002")

# Also update the URL in the agent card to use the host from environment or default
HOST_URL = os.environ.get("HOST_URL", "http://localhost:8000")

# Fetch and store remote agents' Agent Cards for capability discovery.
remote_agents = {}  # Map skill ID -> agent info
for agent_url in [MATH_AGENT_URL, TRANSLATOR_AGENT_URL]:
    try:
        card_url = f"{agent_url}/.well-known/agent.json"
        card = requests.get(card_url).json()
        # Store agent info by skill id (each agent in this demo has one primary skill)
        for skill in card.get("skills", []):
            skill_id = skill.get("id")
            remote_agents[skill_id] = {
                "name": card.get("name"),
                "base_url": card.get("url") or agent_url,
                "description": skill.get("description")
            }
            # Log discovered capabilities for clarity
            print(f"Registered remote agent '{card.get('name')}' with skill '{skill_id}'")
    except Exception as e:
        print(f"Failed to register agent at {agent_url}: {e}")

# Define this agent's Agent Card (advertises a coordination skill).
AGENT_CARD = {
    "name": "OrchestratorAgent",
    "description": "Coordinates tasks by delegating to other agents",
    "url": HOST_URL,  # base URL of this orchestrator service
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
            "id": "delegate_task",
            "name": "Task Delegation",
            "description": "Delegates tasks to the appropriate specialized agent"
        }
    ]
}

@app.get("/.well-known/agent.json")
async def get_agent_card():
    """Expose this agent's capabilities for discovery (Agent Card)."""
    return AGENT_CARD  # FastAPI will serialize this dict to JSON

@app.post("/tasks/send")
async def handle_task(request: Request):
    """Handle incoming tasks by forwarding them to the appropriate remote agent."""
    task_request = await request.json()          # parse incoming JSON task request
    task_id = task_request.get("id", str(uuid.uuid4()))  # use provided ID or generate one
    # Extract the user's message text (assumes first part is text as per A2A spec).
    try:
        user_text = task_request["message"]["parts"][0]["text"]
    except Exception:
        # If the request format is invalid, return an error response
        return {"error": "Invalid A2A request format"}, 400

    # Determine which skill/agent should handle this task (simple keyword-based routing).
    target_agent_url = None
    if "translate" in user_text.lower() or "spanish" in user_text.lower():
        target_agent_url = TRANSLATOR_AGENT_URL
        skill_used = "translate_text"
    elif any(word in user_text.lower() for word in ["calculate", "calc", "+", "-", "*", "/"]):
        target_agent_url = MATH_AGENT_URL
        skill_used = "calculate"
    else:
        # If no known skill is detected, respond that the request cannot be handled.
        result_text = "Sorry, I cannot handle this request."
        # Formulate a completed task response with a failure message.
        response_task = {
            "id": task_id,
            "status": {"state": "completed"},
            "messages": [
                task_request.get("message", {}),          # echo original user message
                {"role": "agent", "parts": [{"text": result_text}]}  # agent's reply
            ]
        }
        return response_task

    # Forward the task to the chosen remote agent via its A2A `tasks/send` endpoint.
    new_task_id = str(uuid.uuid4())  # unique ID for the sub-task to the remote agent
    forward_payload = {
        "id": new_task_id,
        "message": {
            "role": "user",
            "parts": [ {"text": user_text} ]  # forward the same user query text
        }
    }
    try:
        # Send the task to the remote agent (synchronous call using HTTP POST).
        resp = requests.post(f"{target_agent_url}/tasks/send", json=forward_payload)
    except Exception as e:
        return {"error": f"Failed to reach agent: {e}"}, 500

    if resp.status_code != 200:
        return {"error": f"Remote agent error: {resp.text}"}, resp.status_code

    remote_task = resp.json()  # The remote agent's task response (JSON)
    # Extract the remote agent's answer from the task response.
    agent_reply_text = ""
    # The last message in remote_task["messages"] should be the agent's answer.
    messages = remote_task.get("messages", [])
    if messages:
        last_message = messages[-1]
        # Concatenate all text parts of the agent's last message (if any).
        for part in last_message.get("parts", []):
            if "text" in part:
                agent_reply_text += part["text"]

    # Formulate the orchestrator's response task, marking it as completed.
    final_response = {
        "id": task_id, 
        "status": {"state": "completed"},
        "messages": [
            task_request.get("message", {}),             # original user message
            {"role": "agent", "parts": [ {"text": agent_reply_text} ]}  # reply from orchestrator (delegated answer)
        ]
    }
    return final_response