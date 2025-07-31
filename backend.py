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

@app.websocket("/ws/chat")
async def chat(websocket: WebSocket):
    await websocket.accept()

    # A single, simple input function that only waits for the next message from the client.
    async def get_user_input(prompt: str, *args, **kwargs) -> str:
        try:
            data = await websocket.receive_json()
            message = TextMessage.model_validate(data)
            return message.content
        except WebSocketDisconnect:
            logger.info("Client disconnected while waiting for user input.")
            raise

    try:
        initial_data = await websocket.receive_json()
        task = initial_data["content"]

        model_client = OpenAIChatCompletionClient(model=MODEL_NAME, api_key=API_KEY)
        
        # Pass the single, correct input function to all user proxy agents.
        outer_team = create_outer_team_coordination(
            model_client, get_user_input, get_user_input, get_user_input
        )

        async for message in outer_team.run_stream(task=task):
            if isinstance(message, TaskResult):
                continue

            # ** THE FIX **
            # Intercept the UserInputRequestedEvent and replace its generic content
            # with the specific, instructional prompt needed by the UI.
            if isinstance(message, UserInputRequestedEvent):
                source_name = message.source.name if hasattr(message.source, 'name') else str(message.source)
                if source_name == 'Human_ContentOverseer':
                    message.content = """
==================================================
 HUMAN INPUT - Content Team
==================================================
Options:
1. Type 'APPROVE' to approve
2. Provide feedback for improvements
--------------------------------------------------
"""
                elif source_name == 'Human_QualityOverseer':
                    message.content = """
==================================================
 HUMAN INPUT - Quality Team
==================================================
Options:
1. Type 'QUALITY_APPROVED' to approve
2. Provide quality feedback
--------------------------------------------------
"""
                elif source_name == 'Human_ProjectOverseer':
                    message.content = """
============================================================
 HUMAN INPUT - Outer Team Coordination
============================================================
Options:
1. Type 'FINAL_APPROVAL' for final approval
2. Type 'REJECT_OUTPUT' to reject and rework
3. Provide coordination feedback
------------------------------------------------------------
"""
            
            # Now, send the (potentially modified) message to the client.
            await websocket.send_json(message.model_dump(mode='json'))

        await websocket.send_json({
            "source": "system",
            "content": "Task completed.",
            "type": "TextMessage"
        })

    except WebSocketDisconnect:
        logger.info("Client disconnected.")
    except Exception as e:
        app_exc = SoMApplicationException(e, sys)
        logger.error("An error occurred during agent execution", error=str(app_exc))
        await websocket.send_json({
            "source": "system",
            "content": f"An error occurred: {app_exc}",
            "type": "error"
        })
    finally:
        if websocket.client_state != WebSocketDisconnect:
            await websocket.close()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
