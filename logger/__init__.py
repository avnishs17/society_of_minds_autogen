from logger.custom_logger import CustomLogger

# Create a single, shared logger instance for the entire application
logger = CustomLogger().get_logger("SoM_Application")
