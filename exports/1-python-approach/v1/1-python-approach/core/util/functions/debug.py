import os, sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from datetime import datetime
from core.util.functions.config import config

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
DEBUG_FILE = os.path.normpath(os.path.join(CURRENT_DIR, "../../../logs", f'{datetime.now().strftime("%Y-%m-%d %H-%M-%S")}-debug.log'))
os.makedirs(os.path.dirname(DEBUG_FILE), exist_ok=True)
def debug(*args, **kwargs):
   
    """Custom debug function to log messages if debug mode is enabled."""
    if config("debug", False):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        message = f"[{timestamp}] " + " ".join(map(str, args))
        with open(DEBUG_FILE, "a", encoding='utf-8') as f:
            print(message, **kwargs, file=f)
    else:
        pass
