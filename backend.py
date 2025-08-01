import sys
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from autogen_agentchat.messages import TextMessage
from src.som.team_setup import create_outer_team_coordination
from autogen_ext.models.openai import OpenAIChatCompletionClient
from logger import logger
from custom_exception.custom_exception import SoMApplicationException
from config.constants import MODEL_NAME, API_KEY


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

    async def human_input_function(agent_name: str, prompt: str, cancellation_token=None):
        """Function to get human input from the WebSocket."""
        logger.info(f"Requesting human input from {agent_name}: {prompt}")

        if agent_name == "Human_ContentOverseer":
            team_name = "Content Creation Team"
            instructions = "Enter 'APPROVE' to approve the content, or provide feedback for revision."
        elif agent_name == "Human_QualityOverseer":
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
        model_client = OpenAIChatCompletionClient(model=MODEL_NAME, api_key=API_KEY)
        
        # Create the teams
        outer_team, _, _ = await create_outer_team_coordination(model_client, human_input_function)

        # Wait for the initial message from the user
        initial_data = await websocket.receive_json()
        task = initial_data.get("content")
        logger.info(f"Received initial task: {task}")

        # Stream the conversation
        is_first_message = True
        async for message in outer_team.run_stream(task=task):
            if is_first_message:
                is_first_message = False
                continue  # Skip sending the initial task back to the client

            if isinstance(message, TextMessage):
                source = message.source if hasattr(message, 'source') and message.source else "System"
                content = message.content.strip()

                # Don't send back the human's input, as it's already displayed on the frontend
                if source in ["Human_ContentOverseer", "Human_ProjectOverseer"]:
                    continue

                if content:
                    logger.info(f"Sending message from {source}: {content}")
                    await websocket.send_json({"type": "message", "source": source, "content": content})
        
        logger.info("Conversation ended successfully.")
        await websocket.send_json({
            "type": "message", 
            "source": "System", 
            "content": "Conversation ended."
        })

    except WebSocketDisconnect:
        logger.info("client_disconnected")
    except Exception as e:
        som_exception = SoMApplicationException(e, sys)
        logger.error("error_occurred", error=str(som_exception))
        await websocket.send_json({
            "type": "error",
            "content": str(som_exception)
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
