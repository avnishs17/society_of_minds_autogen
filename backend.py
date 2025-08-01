import asyncio
import json
import logging
import os
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from autogen_agentchat.messages import TextMessage
from src.som.team_setup import create_outer_team_coordination
from autogen_ext.models.openai import OpenAIChatCompletionClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
api_key = os.getenv('GOOGLE_API_KEY')

# Initialize logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def read_root():
    """Serve the main HTML file."""
    return FileResponse('ui/index.html')

@app.websocket("/ws/chat")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    logger.info("WebSocket connection accepted.")

    async def human_input_function(prompt: str, cancellation_token=None):
        """Function to get human input from the WebSocket."""
        logger.info(f"Requesting human input for prompt: {prompt}")

        # Determine which team is asking for input based on the prompt
        if "ContentTeam" in prompt:
            team_name = "Content Creation Team"
            instructions = "Enter 'APPROVE' to approve the content, or provide feedback for revision."
        elif "QualityTeam" in prompt:
            team_name = "Quality Assurance Team"
            instructions = "Enter 'APPROVE' to approve the quality, or provide feedback."
        else:
            team_name = "Project Overseer"
            instructions = "Enter 'FINAL_APPROVAL' to approve the project, or provide feedback."

        await websocket.send_json({
            "type": "human_input_request",
            "content": f"--- {team_name} ---\n{instructions}"
        })
        data = await websocket.receive_json()
        return data["content"]

    try:
        # Initialize the model client
        model_client = OpenAIChatCompletionClient(model='gemini-1.5-flash', api_key=api_key)
        
        # Create the teams
        outer_team, _, _ = await create_outer_team_coordination(model_client, human_input_function)

        # Wait for the initial message from the user
        initial_data = await websocket.receive_json()
        task = initial_data.get("content")
        logger.info(f"Received initial task: {task}")

        # Stream the conversation
        async for message in outer_team.run_stream(task=task):
            if isinstance(message, TextMessage):
                source = message.source if hasattr(message, 'source') and message.source else "System"
                content = message.content.strip()
                if content:
                    logger.info(f"Sending message from {source}: {content}")
                    await websocket.send_json({"type": "message", "source": source, "content": content})

    except WebSocketDisconnect:
        logger.info("Client disconnected.")
    except Exception as e:
        logger.error(f"An error occurred: {e}", exc_info=True)
        await websocket.send_json({
            "type": "error",
            "content": str(e)
        })
    finally:
        try:
            await websocket.close()
            logger.info("WebSocket connection closed.")
        except RuntimeError:
            pass # Connection already closed

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting server...")
    uvicorn.run(app, host="0.0.0.0", port=8000)
