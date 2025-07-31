from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
import uvicorn
from autogen_ext.models.openai import OpenAIChatCompletionClient
from config.constants import API_KEY, MODEL_NAME
from src.som.initializer import create_outer_team_coordination
from logger.custom_logger import CustomLogger
import sys
from custom_exception.custom_exception import SoMApplicationException
from autogen_agentchat.messages import TextMessage, UserInputRequestedEvent
from autogen_agentchat.base import TaskResult

app = FastAPI()
logger = CustomLogger().get_logger(__name__)

@app.get("/")
async def root():
    """Serve the chat interface HTML file."""
    return FileResponse("ui/index.html")

async def send_message(websocket: WebSocket, source: str, content: str, msg_type: str = "TextMessage"):
    """Helper function to send a message to the client."""
    message = {
        "source": source,
        "content": content,
        "type": msg_type,
    }
    await websocket.send_json(message)

@app.websocket("/ws/chat")
async def chat(websocket: WebSocket):
    await websocket.accept()

    # This single function will handle all user input requests, pausing until a message is received.
    async def get_user_input(prompt: str, *args, **kwargs) -> str:
        # The autogen framework sends a UserInputRequestedEvent automatically.
        # We just need to wait for the user's response.
        try:
            data = await websocket.receive_json()
            message = TextMessage.model_validate(data)
            return message.content
        except WebSocketDisconnect:
            logger.info("Client disconnected while waiting for user input.")
            raise

    try:
        # The first message from the user starts the task.
        initial_data = await websocket.receive_json()
        task = initial_data["content"]

        model_client = OpenAIChatCompletionClient(model=MODEL_NAME, api_key=API_KEY)
        
        # Pass the single, correct input function to the team initializer.
        outer_team = create_outer_team_coordination(
            model_client, get_user_input, get_user_input, get_user_input
        )

        # Stream the conversation, sending each message to the client.
        async for message in outer_team.run_stream(task=task):
            if isinstance(message, TaskResult):
                continue
            
            # The message from the framework is already a rich object. We can pass it directly.
            # The frontend will handle rendering based on the message type.
            # Use mode='json' to ensure complex types like datetime are serialized to strings.
            await websocket.send_json(message.model_dump(mode='json'))

        await send_message(websocket, "system", "Task completed.")

    except WebSocketDisconnect:
        logger.info("Client disconnected.")
    except Exception as e:
        app_exc = SoMApplicationException(e, sys)
        logger.error("An error occurred during agent execution", error=str(app_exc))
        await send_message(websocket, "system", f"An error occurred: {app_exc}", msg_type="error")
    finally:
        if websocket.client_state != WebSocketDisconnect:
            await websocket.close()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
