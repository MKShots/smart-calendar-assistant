import json
import logging
from typing import Dict, Optional
from datetime import datetime, timedelta
import os

logger = logging.getLogger(__name__)

# Import simple parser as fallback
from .llm_simple import parse_event_with_simple_llm

class HybridEventParser:
    def __init__(self):
        self.langchain_available = False
        self.langchain_parser = None
        self._initialize_langchain()
    
    def _initialize_langchain(self):
        """Try to initialize LangChain, fall back gracefully if it fails."""
        try:
            # Check if we have required environment variables
            hf_token = os.getenv('HUGGINGFACE_API_TOKEN')
            if not hf_token:
                logger.info("HUGGINGFACE_API_TOKEN not found - will use simple parser only")
                return
            
            # Try to import LangChain components
            from langchain_community.llms import HuggingFaceHub
            from langchain.prompts import PromptTemplate
            from langchain.chains import LLMChain
            
            # Initialize the LLM
            llm = HuggingFaceHub(
                repo_id="microsoft/DialoGPT-medium",
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
                template=self._get_event_parsing_prompt()
            )
            
            # Create LLM chain
            self.langchain_parser = LLMChain(
                llm=llm,
                prompt=prompt_template
            )
            
            self.langchain_available = True
            logger.info("✅ LangChain initialized successfully - advanced parsing enabled")
            
        except ImportError as e:
            logger.warning(f"LangChain not available: {e} - using simple parser only")
        except Exception as e:
            logger.warning(f"Failed to initialize LangChain: {e} - using simple parser only")
    
    def _get_event_parsing_prompt(self) -> str:
        """Get the prompt template for LangChain event parsing."""
        return """
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
    
    def parse_with_langchain(self, user_input: str, timezone: str = "UTC") -> Optional[Dict]:
        """Try to parse using LangChain."""
        try:
            if not self.langchain_available or not self.langchain_parser:
                return None
            
            # Get current datetime in user's timezone
            import pytz
            tz = pytz.timezone(timezone)
            current_dt = datetime.now(tz)
            
            # Run the LLM chain
            result = self.langchain_parser.run(
                current_datetime=current_dt.strftime("%Y-%m-%d %H:%M:%S %Z"),
                timezone=timezone,
                user_input=user_input
            )
            
            # Extract and parse JSON from response
            json_str = self._extract_json_from_response(result)
            if not json_str:
                logger.warning("No valid JSON found in LangChain response")
                return None
            
            event_data = json.loads(json_str)
            
            # Validate required fields
            required_fields = ["title", "start_datetime", "end_datetime"]
            if not all(field in event_data for field in required_fields):
                logger.warning(f"Missing required fields in LangChain response: {event_data}")
                return None
            
            # Validate datetime format
            try:
                datetime.fromisoformat(event_data["start_datetime"])
                datetime.fromisoformat(event_data["end_datetime"])
            except ValueError as e:
                logger.warning(f"Invalid datetime format from LangChain: {e}")
                return None
            
            logger.info(f"✅ LangChain successfully parsed: {event_data['title']}")
            return event_data
            
        except Exception as e:
            logger.warning(f"LangChain parsing failed: {e}")
            return None
    
    def _extract_json_from_response(self, response: str) -> Optional[str]:
        """Extract JSON from LLM response."""
        try:
            response = response.strip()
            start_idx = response.find('{')
            end_idx = response.rfind('}')
            
            if start_idx != -1 and end_idx != -1:
                json_str = response[start_idx:end_idx + 1]
                # Test if it's valid JSON
                json.loads(json_str)
                return json_str
            
            return None
            
        except Exception:
            return None
    
    def parse_event(self, user_input: str, timezone: str = "UTC") -> Optional[Dict]:
        """
        Hybrid parsing: Try LangChain first, fall back to simple parser.
        
        Args:
            user_input: Natural language event description
            timezone: User's timezone
            
        Returns:
            Parsed event dictionary or None if both methods fail
        """
        logger.info(f"🔄 Parsing event with hybrid approach: {user_input}")
        
        # Method 1: Try LangChain first
        if self.langchain_available:
            logger.debug("Attempting LangChain parsing...")
            result = self.parse_with_langchain(user_input, timezone)
            if result:
                logger.info("✅ Successfully parsed with LangChain")
                return result
            else:
                logger.info("⚠️ LangChain parsing failed, falling back to simple parser")
        else:
            logger.debug("LangChain not available, using simple parser")
        
        # Method 2: Fallback to simple parser
        logger.debug("Attempting simple parsing...")
        result = parse_event_with_simple_llm(user_input, timezone)
        if result:
            logger.info("✅ Successfully parsed with simple parser")
            # Add a note that this was parsed with fallback method
            result["parsing_method"] = "simple_fallback"
            return result
        
        # Both methods failed
        logger.error("❌ Both LangChain and simple parsing failed")
        return None

# Global hybrid parser instance
_hybrid_parser = None

def get_hybrid_parser() -> HybridEventParser:
    """Get or create global hybrid parser instance."""
    global _hybrid_parser
    if _hybrid_parser is None:
        _hybrid_parser = HybridEventParser()
    return _hybrid_parser

async def parse_event_with_llm(user_input: str, timezone: str = "UTC") -> Optional[Dict]:
    """
    Main parsing function with hybrid approach.
    
    This function:
    1. Tries LangChain + Hugging Face API (if token available)
    2. Falls back to simple rule-based parsing
    3. Returns the best available result
    
    Args:
        user_input: Natural language event description
        timezone: User's timezone
        
    Returns:
        Parsed event dictionary or None if parsing fails
    """
    try:
        parser = get_hybrid_parser()
        return parser.parse_event(user_input, timezone)
    except Exception as e:
        logger.error(f"Error in hybrid event parsing: {e}")
        return None

def get_parser_status() -> Dict:
    """Get status of available parsing methods."""
    parser = get_hybrid_parser()
    return {
        "langchain_available": parser.langchain_available,
        "huggingface_token_set": bool(os.getenv('HUGGINGFACE_API_TOKEN')),
        "fallback_available": True,  # Simple parser is always available
        "recommended_action": (
            "Advanced parsing active" if parser.langchain_available 
            else "Set HUGGINGFACE_API_TOKEN for advanced parsing"
        )
    } 