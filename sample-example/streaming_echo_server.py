# streaming_echo_server.py (Modifications based on echo_server.py)
# ... (Imports similar to echo_server.py, add AsyncIterable)
import time
import asyncio
import logging
import uvicorn
from typing import AsyncIterable

from common.types import (
    AgentCard, AgentCapabilities, AgentSkill, Task, TaskState, TaskStatus,
    Message, TextPart, SendTaskRequest, SendTaskResponse,
    JSONRPCResponse, JSONRPCError, InternalError, TaskStatusUpdateEvent, SendTaskStreamingRequest,
    SendTaskStreamingResponse
)
from common.server import A2AServer, TaskManager

# Configure basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# --- Agent Definition (Update Capabilities) ---
STREAMING_ECHO_AGENT_CARD = AgentCard(
    name="Streaming Echo Agent",
    description="A simple agent that echoes back user messages",
    url="http://localhost:8002/a2a", # Use a different port
    version="1.0",
    capabilities=AgentCapabilities(
        streaming=True, # <<< Enable streaming capability
        pushNotifications=False,
        stateTransitionHistory=True # Let's include history
    ),
    authentication=None, # No auth for this simple example
    defaultInputModes=["text"],
    defaultOutputModes=["text"],
    skills=[
        AgentSkill(
            id="echo",
            name="Echo",
            description="Echoes back user messages",
            inputModes=["text"],
            outputModes=["text"],
            examples=["'Hello there!' -> 'You said (streamed): Hello there!'"]
        )
    ]
)



# --- Task Management Logic (Implement on_send_task_subscribe) ---
class StreamingEchoTaskManager(TaskManager):
    def __init__(self):
        self.tasks: dict[str, Task] = {} # Store task state
        self.lock = asyncio.Lock()
        # NOTE: The common InMemoryTaskManager in samples handles SSE queueing
        #       If NOT using that base class, you'd need SSE queue management here.
        #       For this example, we'll simulate the async generator directly.

    async def _do_work(self, task_id: str, user_text: str) -> AsyncIterable[SendTaskStreamingResponse]:
        logger.info(f"Task {task_id}: Starting work...")

        # 1. Send 'working' status update
        working_status = TaskStatus(state=TaskState.WORKING)
        yield SendTaskStreamingResponse(
            id=None, # SSE events don't need request ID
            result=TaskStatusUpdateEvent(id=task_id, status=working_status)
        )

        await asyncio.sleep(1) # Simulate work

        # 2. Simulate some progress (optional)
        progress_status = TaskStatus(state=TaskState.WORKING, message=Message(role="agent", parts=[TextPart(text="Thinking...")]))
        yield SendTaskStreamingResponse(
            id=None,
            result=TaskStatusUpdateEvent(id=task_id, status=progress_status)
        )

        await asyncio.sleep(2) # Simulate more work

        # 3. Send 'completed' status update with final message
        agent_response_message = Message(
            role="agent",
            parts=[TextPart(text=f"You said (streamed): {user_text}")]
        )
        completed_status = TaskStatus(
            state=TaskState.COMPLETED,
            message=agent_response_message
        )
        yield SendTaskStreamingResponse(
            id=None,
            result=TaskStatusUpdateEvent(id=task_id, status=completed_status, final=True) # Mark as final
        )

        logger.info(f"Task {task_id}: Work completed.")


    async def on_send_task_subscribe(
        self, request: SendTaskStreamingRequest
    ) -> AsyncIterable[SendTaskStreamingResponse]:
        task_params = request.params
        task_id = task_params.id
        user_message = task_params.message
        logger.info(f"Received streaming task {task_id}")

        # Validate input
        if not user_message.parts or not isinstance(user_message.parts[0], TextPart):
             logger.error(f"Task {task_id}: Invalid input.")
             error = JSONRPCError(code=-32602, message="Invalid input")
             # Cannot yield an error directly in SSE stream start easily with this structure
             # A real server might handle this differently (e.g., immediate error response
             # before starting stream, or an error event in the stream).
             # For simplicity, log and return empty stream or raise
             raise ValueError("Invalid input for streaming task") # Or return empty async iter

        user_text = user_message.parts[0].text

        # Store initial task state (optional but good practice)
        initial_task = Task(
            id=task_id,
            sessionId=task_params.sessionId,
            status=TaskStatus(state=TaskState.SUBMITTED), # Or WORKING immediately
            history=[user_message]
        )
        async with self.lock:
            self.tasks[task_id] = initial_task

        # Return the async generator that yields SSE events
        return self._do_work(task_id, user_text)

    # --- Implement other methods (on_send_task, on_get_task etc.) ---
    async def on_send_task(self, request):
         error = JSONRPCError(code=-32004, message="Use tasks/sendSubscribe for this agent")
         return SendTaskResponse(id=request.id, error=error)

    async def on_get_task(self, request):
        # Basic implementation for retrieving task status
        async with self.lock:
            task = self.tasks.get(request.params.id)
        
        if task:
            return JSONRPCResponse(id=request.id, result=task)
        else:
            error = JSONRPCError(code=-32001, message="Task not found")
            return JSONRPCResponse(id=request.id, error=error)

    async def on_cancel_task(self, request):
        error = JSONRPCError(code=-32004, message="Cancel not supported")
        return JSONRPCResponse(id=request.id, error=error)

    async def on_set_task_push_notification(self, request):
        error = JSONRPCError(code=-32003, message="Push notifications not supported")
        return JSONRPCResponse(id=request.id, error=error)

    async def on_get_task_push_notification(self, request):
        error = JSONRPCError(code=-32003, message="Push notifications not supported")
        return JSONRPCResponse(id=request.id, error=error)

    async def on_resubscribe_to_task(self, request):
        error = JSONRPCError(code=-32004, message="Resubscribe not supported")
        return JSONRPCResponse(id=request.id, error=error)


# --- Server Setup ---
if __name__ == "__main__":
    task_manager = StreamingEchoTaskManager()
    server = A2AServer(
        host="localhost",
        port=8002, # Different port
        endpoint="/a2a",
        agent_card=STREAMING_ECHO_AGENT_CARD,
        task_manager=task_manager
    )
    print("Starting Streaming Echo A2A Server on http://localhost:8002")
    server.start()
