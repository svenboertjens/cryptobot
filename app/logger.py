import logging
from logging.handlers import RotatingFileHandler

# Configure logger
logger = logging.getLogger('my_logger')
logger.setLevel(logging.DEBUG)

# Configure rotating file handler
handler = RotatingFileHandler('app.log', maxBytes=10*1024*1024, backupCount=5)  # Max 10 MB per file, keep 5 backup files
handler.setLevel(logging.DEBUG)

# Set log format
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)

# Add handler to logger
logger.addHandler(handler)

# All logging levels
_levels = [
    "info",
    "error",
    "debug",
    "warning",
    "critical"
]

# Function to handle logs
def log(message: str, level: str = "info", *args):
    if level in _levels:
        return getattr(logger, level)(message, *args)
    
    logger.debug(f"Message of invalid level '{level}': {message}")
    
    raise ValueError(f"Invalid level '{level}'")
    
    