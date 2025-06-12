import os
import json
import logging
from pathlib import Path
from typing import Optional, Dict

logger = logging.getLogger(__name__)

# Configuration file paths
CONFIG_DIR = Path(__file__).parent.parent / "config"
USER_CONFIG_FILE = CONFIG_DIR / "user_config.json"

def load_config() -> Dict:
    """Load user configuration from file."""
    try:
        if USER_CONFIG_FILE.exists():
            with open(USER_CONFIG_FILE, 'r') as f:
                config = json.load(f)
                logger.info("User configuration loaded successfully")
                return config
        else:
            # Create default config
            default_config = {
                "timezone": "UTC",
                "conflict_gap_minutes": 15,
                "sync_days_ahead": 30,
                "auto_sync": True
            }
            save_config(default_config)
            return default_config
    except Exception as e:
        logger.error(f"Error loading configuration: {e}")
        return {}

def save_config(config: Dict) -> bool:
    """Save user configuration to file."""
    try:
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        with open(USER_CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=2)
        logger.info("User configuration saved successfully")
        return True
    except Exception as e:
        logger.error(f"Error saving configuration: {e}")
        return False

def get_huggingface_token() -> Optional[str]:
    """Get Hugging Face API token from environment."""
    token = os.getenv('HUGGINGFACE_API_TOKEN')
    if not token:
        logger.warning("HUGGINGFACE_API_TOKEN environment variable not set")
    return token

def get_google_credentials_path() -> Optional[str]:
    """Get Google Calendar credentials file path."""
    creds_path = os.getenv('GOOGLE_CREDENTIALS_PATH', 'config/credentials.json')
    
    # Check if file exists
    if not os.path.exists(creds_path):
        logger.warning(f"Google credentials file not found: {creds_path}")
        return None
    
    return creds_path

def get_environment() -> str:
    """Get current environment (development, production, etc.)."""
    return os.getenv('ENVIRONMENT', 'development')

def get_timezone() -> str:
    """Get user's timezone from config or environment."""
    config = load_config()
    return config.get('timezone') or os.getenv('TIMEZONE', 'UTC')

def get_conflict_gap_minutes() -> int:
    """Get conflict detection gap in minutes."""
    config = load_config()
    return config.get('conflict_gap_minutes', 15)

def get_sync_days_ahead() -> int:
    """Get number of days ahead to sync."""
    config = load_config()
    return config.get('sync_days_ahead', 30) 