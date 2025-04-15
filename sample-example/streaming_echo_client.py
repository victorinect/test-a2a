# streaming_echo_client.py (Modifications based on echo_client.py)
import asyncio
import logging
from uuid import uuid4

from common.client import A2AClient
from common.types import Message, TextPart, TaskStatusUpdateEvent, TaskArtifactUpdateEvent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

STREAMING_ECHO_SERVER_URL = "http://localhost:8002/a2a"

async def main():
    client = A2AClient(url=STREAMING_ECHO_SERVER_URL)

    task_id = f"stream-task-{uuid4().hex}"
    user_text = "Testing the streaming client!"

    user_message = Message(role="user", parts=[TextPart(text=user_text)])

    send_params = {
        "id": task_id,
        "message": user_message,
    }

    try:
        logger.info(f"Sending streaming task {task_id} to {STREAMING_ECHO_SERVER_URL}...")

        # Use the client's send_task_streaming method
        async for response in client.send_task_streaming(payload=send_params):
            if response.error:
                # Errors might be sent as part of the stream in some implementations
                logger.error(f"Received error in stream for task {task_id}: {response.error.message}")
                break # Stop processing stream on error

            elif response.result:
                event = response.result
                if isinstance(event, TaskStatusUpdateEvent):
                    logger.info(f"Task {task_id} Status Update: {event.status.state}")
                    if event.status.message and event.status.message.parts:
                         part = event.status.message.parts[0]
                         if isinstance(part, TextPart):
                             logger.info(f"  Agent Message: {part.text}")
                    if event.final:
                        logger.info(f"Task {task_id} reached final state.")
                        break # Exit loop once task is final

                elif isinstance(event, TaskArtifactUpdateEvent):
                     logger.info(f"Task {task_id} Artifact Update: {event.artifact.name}")
                     # Process artifact parts...
                else:
                     logger.warning(f"Received unknown event type in stream: {type(event)}")
            else:
                logger.error(f"Received unexpected empty response in stream for task {task_id}")


    except Exception as e:
        logger.error(f"An error occurred during streaming communication: {e}")

if __name__ == "__main__":
    asyncio.run(main())
