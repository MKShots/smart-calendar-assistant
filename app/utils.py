import logging
import requests
from typing import Optional
from datetime import datetime
import pytz

logger = logging.getLogger(__name__)

def detect_timezone() -> str:
    """
    Detect user's timezone based on IP address.
    Falls back to UTC if detection fails.
    """
    try:
        # Try to get timezone from IP-based service
        response = requests.get('http://ip-api.com/json/', timeout=5)
        if response.status_code == 200:
            data = response.json()
            timezone = data.get('timezone')
            if timezone:
                # Validate timezone
                try:
                    pytz.timezone(timezone)
                    logger.info(f"Detected timezone: {timezone}")
                    return timezone
                except pytz.exceptions.UnknownTimeZoneError:
                    logger.warning(f"Invalid timezone detected: {timezone}")
        
    except Exception as e:
        logger.warning(f"Failed to detect timezone: {e}")
    
    # Fallback to UTC
    logger.info("Using UTC as fallback timezone")
    return "UTC"

def format_datetime_for_user(dt_string: str, target_timezone: str = "UTC") -> str:
    """
    Format datetime string for user display in their timezone.
    
    Args:
        dt_string: ISO format datetime string
        target_timezone: Target timezone for display
        
    Returns:
        Formatted datetime string
    """
    try:
        # Parse the datetime
        dt = datetime.fromisoformat(dt_string.replace('Z', '+00:00'))
        
        # Convert to target timezone
        target_tz = pytz.timezone(target_timezone)
        if dt.tzinfo is None:
            dt = pytz.UTC.localize(dt)
        
        local_dt = dt.astimezone(target_tz)
        
        # Format for display
        return local_dt.strftime("%Y-%m-%d %H:%M %Z")
        
    except Exception as e:
        logger.error(f"Error formatting datetime: {e}")
        return dt_string

def validate_datetime_format(dt_string: str) -> bool:
    """
    Validate if a string is in valid ISO datetime format.
    
    Args:
        dt_string: Datetime string to validate
        
    Returns:
        True if valid, False otherwise
    """
    try:
        datetime.fromisoformat(dt_string.replace('Z', '+00:00'))
        return True
    except ValueError:
        return False

def convert_to_utc(dt_string: str, from_timezone: str = "UTC") -> str:
    """
    Convert datetime string from given timezone to UTC.
    
    Args:
        dt_string: Datetime string to convert
        from_timezone: Source timezone
        
    Returns:
        UTC datetime string
    """
    try:
        # Parse datetime
        dt = datetime.fromisoformat(dt_string)
        
        # Add timezone info if not present
        if dt.tzinfo is None:
            source_tz = pytz.timezone(from_timezone)
            dt = source_tz.localize(dt)
        
        # Convert to UTC
        utc_dt = dt.astimezone(pytz.UTC)
        
        return utc_dt.strftime("%Y-%m-%dT%H:%M:%S")
        
    except Exception as e:
        logger.error(f"Error converting to UTC: {e}")
        return dt_string

def calculate_duration_minutes(start_datetime: str, end_datetime: str) -> int:
    """
    Calculate duration between two datetime strings in minutes.
    
    Args:
        start_datetime: Start datetime string
        end_datetime: End datetime string
        
    Returns:
        Duration in minutes
    """
    try:
        start = datetime.fromisoformat(start_datetime)
        end = datetime.fromisoformat(end_datetime)
        
        duration = end - start
        return int(duration.total_seconds() / 60)
        
    except Exception as e:
        logger.error(f"Error calculating duration: {e}")
        return 0

def format_conflict_message(conflicts: list) -> str:
    """
    Format conflict list into a readable message.
    
    Args:
        conflicts: List of conflicting events
        
    Returns:
        Formatted conflict message
    """
    if not conflicts:
        return "No conflicts detected."
    
    if len(conflicts) == 1:
        conflict = conflicts[0]
        return f"Conflict with '{conflict['title']}' ({conflict['start_datetime']} - {conflict['end_datetime']})"
    
    conflict_titles = [c['title'] for c in conflicts]
    return f"Conflicts with {len(conflicts)} events: {', '.join(conflict_titles)}" 