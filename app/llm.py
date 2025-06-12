import json
import logging
from typing import Dict, Optional
from datetime import datetime, timedelta
import pytz
from langchain_community.llms import HuggingFaceHub
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from .config import get_huggingface_token

logger = logging.getLogger(__name__)

# Event parsing prompt template
EVENT_PARSING_PROMPT = """
You are a calendar assistant. Parse the following natural language request into a structured event.

Current date and time: {current_datetime}
User timezone: {timezone}

Request: "{user_input}"

Extract the following information and respond ONLY with valid JSON in this exact format:
{{
    "title": "Event title",
    "start_datetime": "YYYY-MM-DDTHH:MM:SS",
    "end_datetime": "YYYY-MM-DDTHH:MM:SS", 
    "description": "Event description or empty string",
    "location": "Event location or empty string",
    "attendees": []
}}

Rules:
1. If no end time is specified, assume 1 hour duration
2. If no date is specified, assume today
3. If time is specified without AM/PM, use 24-hour format context
4. Convert all times to the user's timezone
5. Use ISO format for datetime (YYYY-MM-DDTHH:MM:SS)
6. Keep attendees array empty unless email addresses are explicitly mentioned
7. Make reasonable assumptions for missing information
8. Respond with ONLY the JSON object, no other text

JSON:
"""

class LLMEventParser:
    def __init__(self):
        self.llm = None
        self.chain = None
        self._initialize_llm()
    
    def _initialize_llm(self):
        """Initialize the Hugging Face LLM and chain."""
        try:
            hf_token = get_huggingface_token()
            if not hf_token:
                raise ValueError("Hugging Face token not found in configuration")
            
            # Initialize Hugging Face Hub LLM
            self.llm = HuggingFaceHub(
                repo_id="microsoft/DialoGPT-medium",  # Fallback model for testing
                model_kwargs={
                    "temperature": 0.1,
                    "max_length": 512,
                    "return_full_text": False
                },
                huggingfacehub_api_token=hf_token
            )
            
            # Create prompt template
            prompt_template = PromptTemplate(
                input_variables=["current_datetime", "timezone", "user_input"],
                template=EVENT_PARSING_PROMPT
            )
            
            # Create LLM chain
            self.chain = LLMChain(
                llm=self.llm,
                prompt=prompt_template
            )
            
            logger.info("LLM initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize LLM: {e}")
            raise
    
    def parse_event(self, user_input: str, timezone: str = "UTC") -> Optional[Dict]:
        """
        Parse natural language input into structured event data.
        
        Args:
            user_input: Natural language event description
            timezone: User's timezone (default: UTC)
            
        Returns:
            Parsed event dictionary or None if parsing fails
        """
        try:
            # Get current datetime in user's timezone
            tz = pytz.timezone(timezone)
            current_dt = datetime.now(tz)
            
            # Run the LLM chain
            result = self.chain.run(
                current_datetime=current_dt.strftime("%Y-%m-%d %H:%M:%S %Z"),
                timezone=timezone,
                user_input=user_input
            )
            
            # Clean up the result and extract JSON
            json_str = self._extract_json_from_response(result)
            if not json_str:
                logger.error("No valid JSON found in LLM response")
                return None
            
            # Parse JSON
            event_data = json.loads(json_str)
            
            # Validate required fields
            required_fields = ["title", "start_datetime", "end_datetime"]
            if not all(field in event_data for field in required_fields):
                logger.error(f"Missing required fields in parsed event: {event_data}")
                return None
            
            # Validate datetime format
            try:
                datetime.fromisoformat(event_data["start_datetime"])
                datetime.fromisoformat(event_data["end_datetime"])
            except ValueError as e:
                logger.error(f"Invalid datetime format: {e}")
                return None
            
            logger.info(f"Successfully parsed event: {event_data['title']}")
            return event_data
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON from LLM response: {e}")
            return None
        except Exception as e:
            logger.error(f"Error parsing event with LLM: {e}")
            return None
    
    def _extract_json_from_response(self, response: str) -> Optional[str]:
        """Extract JSON from LLM response, handling various formats."""
        try:
            # Try to find JSON object in response
            response = response.strip()
            
            # Look for JSON object markers
            start_idx = response.find('{')
            end_idx = response.rfind('}')
            
            if start_idx != -1 and end_idx != -1:
                json_str = response[start_idx:end_idx + 1]
                # Test if it's valid JSON
                json.loads(json_str)
                return json_str
            
            return None
            
        except Exception as e:
            logger.error(f"Error extracting JSON: {e}")
            return None

# Global parser instance
_parser = None

def get_parser() -> LLMEventParser:
    """Get or create global parser instance."""
    global _parser
    if _parser is None:
        _parser = LLMEventParser()
    return _parser

async def parse_event_with_llm(user_input: str, timezone: str = "UTC") -> Optional[Dict]:
    """
    Async wrapper for parsing events with LLM.
    
    Args:
        user_input: Natural language event description
        timezone: User's timezone
        
    Returns:
        Parsed event dictionary or None if parsing fails
    """
    try:
        parser = get_parser()
        return parser.parse_event(user_input, timezone)
    except Exception as e:
        logger.error(f"Error in async event parsing: {e}")
        return None

def parse_event_fallback(user_input: str, timezone: str = "UTC") -> Optional[Dict]:
    """
    Fallback parser using simple heuristics when LLM fails.
    This is a basic implementation for when the LLM is unavailable.
    """
    try:
        # This is a very basic fallback - in production you might want more sophisticated parsing
        logger.warning("Using fallback parser - limited functionality")
        
        # Default event structure
        event = {
            "title": user_input[:50] + "..." if len(user_input) > 50 else user_input,
            "start_datetime": datetime.now().replace(minute=0, second=0, microsecond=0).isoformat(),
            "end_datetime": (datetime.now().replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)).isoformat(),
            "description": f"Parsed from: {user_input}",
            "location": "",
            "attendees": []
        }
        
        return event
        
    except Exception as e:
        logger.error(f"Error in fallback parser: {e}")
        return None 