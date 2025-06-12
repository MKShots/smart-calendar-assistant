import json
import logging
import requests
from typing import Dict, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

def parse_event_with_simple_llm(user_input: str, timezone: str = "UTC") -> Optional[Dict]:
    """
    Simplified event parser that creates structured events from natural language.
    This is a placeholder implementation that can be enhanced with actual LLM calls.
    
    Args:
        user_input: Natural language event description
        timezone: User's timezone
        
    Returns:
        Parsed event dictionary or None if parsing fails
    """
    try:
        logger.info(f"Parsing event: {user_input}")
        
        # This is a simple rule-based parser as a fallback
        # In production, this would call the Hugging Face API
        
        # Default event structure
        now = datetime.now()
        
        event = {
            "title": user_input[:50] + "..." if len(user_input) > 50 else user_input,
            "start_datetime": now.replace(minute=0, second=0, microsecond=0).isoformat(),
            "end_datetime": (now.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)).isoformat(),
            "description": f"Created from: {user_input}",
            "location": "",
            "attendees": []
        }
        
        # Simple parsing heuristics
        lower_input = user_input.lower()
        
        # Extract time information
        if "tomorrow" in lower_input:
            tomorrow = now + timedelta(days=1)
            event["start_datetime"] = tomorrow.replace(hour=9, minute=0, second=0, microsecond=0).isoformat()
            event["end_datetime"] = tomorrow.replace(hour=10, minute=0, second=0, microsecond=0).isoformat()
        
        elif "next week" in lower_input:
            next_week = now + timedelta(days=7)
            event["start_datetime"] = next_week.replace(hour=9, minute=0, second=0, microsecond=0).isoformat()
            event["end_datetime"] = next_week.replace(hour=10, minute=0, second=0, microsecond=0).isoformat()
        
        # Extract title (simplified)
        if "meeting" in lower_input:
            event["title"] = "Meeting"
        elif "appointment" in lower_input:
            event["title"] = "Appointment"
        elif "lunch" in lower_input:
            event["title"] = "Lunch"
        elif "call" in lower_input:
            event["title"] = "Call"
        else:
            # Extract the first few words as title
            words = user_input.split()[:3]
            event["title"] = " ".join(words).title()
        
        logger.info(f"Parsed event successfully: {event['title']}")
        return event
        
    except Exception as e:
        logger.error(f"Error parsing event: {e}")
        return None

async def parse_event_with_llm(user_input: str, timezone: str = "UTC") -> Optional[Dict]:
    """
    Async wrapper for the simplified parser.
    This maintains compatibility with the main application.
    """
    return parse_event_with_simple_llm(user_input, timezone)

def call_huggingface_api(prompt: str, model: str = "microsoft/DialoGPT-medium") -> Optional[str]:
    """
    Direct call to Hugging Face Inference API.
    This can be used when LangChain has issues.
    """
    try:
        import os
        api_token = os.getenv('HUGGINGFACE_API_TOKEN')
        if not api_token:
            logger.warning("HUGGINGFACE_API_TOKEN not set")
            return None
        
        headers = {"Authorization": f"Bearer {api_token}"}
        api_url = f"https://api-inference.huggingface.co/models/{model}"
        
        data = {"inputs": prompt}
        
        response = requests.post(api_url, headers=headers, json=data)
        
        if response.status_code == 200:
            result = response.json()
            if isinstance(result, list) and len(result) > 0:
                return result[0].get('generated_text', '')
            return str(result)
        else:
            logger.error(f"Hugging Face API error: {response.status_code}")
            return None
            
    except Exception as e:
        logger.error(f"Error calling Hugging Face API: {e}")
        return None 