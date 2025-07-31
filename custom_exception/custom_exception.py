import sys
import traceback

class SoMApplicationException(Exception):
    """Custom exception for the Society of Mind application"""
    def __init__(self, error_message, error_details: sys):
        _, _, exc_tb = error_details.exc_info()
        self.file_name = exc_tb.tb_frame.f_code.co_filename
        self.lineno = exc_tb.tb_lineno
        self.error_message = str(error_message)
        self.traceback_str = ''.join(traceback.format_exception(*error_details.exc_info()))

    def __str__(self):
        return f"""
        Error in [{self.file_name}] at line [{self.lineno}]
        Message: {self.error_message}
        Traceback:
        {self.traceback_str}
        """

class AgentCreationError(SoMApplicationException):
    """Raised when an agent cannot be created."""
    def __init__(self, agent_name: str, error_details: sys):
        super().__init__(f"Failed to create agent: {agent_name}", error_details)

class TeamCreationError(SoMApplicationException):
    """Raised when a team cannot be created."""
    def __init__(self, team_name: str, error_details: sys):
        super().__init__(f"Failed to create team: {team_name}", error_details)
