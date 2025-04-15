## Agent-to-Agent (A2A) Protocol Demo app

This demo showcases Google's Agent-to-Agent (A2A) protocol with a simple Python prototype. We create three agents (services) that register themselves, discover each other's capabilities, exchange messages, and coordinate to complete tasks. The prototype uses FastAPI for HTTP endpoints (for easy deployment) and includes clear inline comments explaining each step of the A2A interactions.

## Overview
	•	Orchestrator Agent: Acts as a client agent and coordinator. It receives user tasks and delegates them to the appropriate remote agent after discovering their capabilities (via Agent Cards).
	•	Math Agent: A remote agent that can perform basic arithmetic calculations. It advertises a calculator skill in its Agent Card and implements the A2A tasks/send endpoint to handle calculation tasks.
	•	Translation Agent: A remote agent that translates English text to Spanish. It advertises a translation skill in its Agent Card and handles translation tasks.

Each agent provides an Agent Card (at /.well-known/agent.json) for capability discovery and a tasks/send endpoint for message exchange. The Orchestrator uses these to route tasks to the correct agent.

### Orchestrator Agent (Client & Coordinator)

The Orchestrator is an A2A server that also acts as an A2A client to the other agents. It exposes a tasks/send endpoint for incoming user tasks, discovers remote agents' capabilities by fetching their Agent Cards, and delegates execution to the appropriate agent. It then returns the result to the original caller, demonstrating agent registration, capability discovery, and message exchange.


How it works: When a user (or another client) sends a task to the Orchestrator's /tasks/send, the Orchestrator will:
	1.	Discover capabilities: Identify which agent is needed (using the keywords or by looking at registered skills from Agent Cards). In our code, we loaded each remote agent's Agent Card at startup to "register" their skills. For example, the Math Agent's card might list a skill with ID "calculate", and the Translator lists "translate_text".
	2.	Forward the task: The Orchestrator creates a new sub-task request and sends it to the remote agent's tasks/send endpoint. This shows agent-to-agent message exchange: the Orchestrator acts as an A2A client calling another agent's service.
	3.	Collect the result: It waits for the remote agent's response (which includes the agent's reply and a completed status). The Orchestrator then extracts the answer text and incorporates it into its own response message.
	4.	Respond to the original caller: Finally, the Orchestrator returns an A2A-formatted JSON response containing the original user message and the answer (as if the Orchestrator itself were the answering agent). The task is marked "completed".

### Math Agent (Arithmetic Service)

The Math Agent is a simple A2A-compliant service that can evaluate basic arithmetic expressions. It registers an Agent Card advertising a calculation capability, and its tasks/send endpoint processes incoming tasks by computing the result of the expression.


What's happening: When a request comes to Math Agent's /tasks/send:
	•	It reads the task JSON and gets the user's query text, e.g., "Calculate 2+2".
	•	The agent executes the task by evaluating the expression (after some basic cleaning and replacing words like "plus" with +). This demonstrates the execution capability of the agent.
	•	The result is formatted into a friendly reply string (e.g., "The result is 4.").
	•	The agent returns a JSON response following the A2A schema, including the original message and the agent's answer as separate messages. The task status is set to "completed" to indicate no further action is needed.

### Translation Agent (Language Service)

The Translation Agent provides English-to-Spanish translation. It registers a translation skill and its tasks/send endpoint responds to translation requests. This agent's implementation will be simple (using a small dictionary for demonstration), but it illustrates the interaction pattern and how an agent's unique capability can be exposed via A2A.

What's happening: On receiving a task, the Translation Agent:
	•	Extracts the input text (e.g., "Translate Hello to Spanish"). It strips out the directive ("Translate ... to Spanish") to isolate the phrase needing translation.
	•	It then executes the translation (here, using a simple lookup dictionary). In a real scenario, this could involve an ML model or external API, but the principle is the same.
	•	The result (Spanish text) is packaged into the A2A response format, echoing the original user message and the translated text as the agent's answer, with the task marked completed.



## Testing

With all three agents running, you can send tasks to the Orchestrator (which serves as the entry point). For example, using curl or any HTTP client:
	•	Calculation Task:

curl -X POST http://localhost:8000/tasks/send \
     -H "Content-Type: application/json" \
     -d '{"id": "task1", "message": {"role": "user", "parts": [{"text": "Calculate 5+7"}]}}'

The Orchestrator will recognize the calculation request and delegate to MathAgent. The JSON response will look like:

{
  "id": "task1",
  "status": { "state": "completed" },
  "messages": [
    { "role": "user", "parts": [ {"text": "Calculate 5+7"} ] },
    { "role": "agent", "parts": [ {"text": "The result is 12."} ] }
  ]
}

Here, the agent's reply "The result is 12." came from MathAgent via the Orchestrator.

	•	Translation Task:

curl -X POST http://localhost:8000/tasks/send \
     -H "Content-Type: application/json" \
     -d '{"id": "task2", "message": {"role": "user", "parts": [{"text": "Translate Hello World to Spanish"}]}}'

The Orchestrator delegates this to TranslatorAgent. The response might be:

{
  "id": "task2",
  "status": { "state": "completed" },
  "messages": [
    { "role": "user", "parts": [ {"text": "Translate Hello World to Spanish"} ] },
    { "role": "agent", "parts": [ {"text": "In Spanish: Hola mundo"} ] }
  ]
}

## Running with Docker Compose

This project includes Docker Compose configuration for easy deployment of all three agents:

1. Build and start the containers:
   ```bash
   docker-compose up -d
   ```

2. Once all containers are running, you can send tasks to the Orchestrator as shown in the Testing section above:

   ```bash
   # Example calculation task
   curl -X POST http://localhost:9000/tasks/send \
        -H "Content-Type: application/json" \
        -d '{"id": "task1", "message": {"role": "user", "parts": [{"text": "Calculate 5+7"}]}}'

   # Example translation task
   curl -X POST http://localhost:9000/tasks/send \
        -H "Content-Type: application/json" \
        -d '{"id": "task2", "message": {"role": "user", "parts": [{"text": "Translate Hello World to Spanish"}]}}'
   ```

3. To shut down the services:
   ```bash
   docker-compose down
   ```

The Docker Compose setup automatically configures the network connections between agents, so they can discover each other and exchange messages according to the A2A protocol.

