from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, List
import logging
from datetime import datetime, timedelta

from .llm_hybrid import parse_event_with_llm, get_parser_status
from .api_simple import add_event_to_calendar, sync_calendar_events
from .db import init_db, store_event, get_events, check_conflicts
from .utils import detect_timezone
from .config import load_config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Smart Calendar Assistant",
    description="LLM-powered personal calendar assistant",
    version="1.0.0"
)

# Request/Response Models
class EventRequest(BaseModel):
    prompt: str
    timezone: Optional[str] = None

class EventResponse(BaseModel):
    success: bool
    message: str
    event_id: Optional[str] = None
    conflicts: Optional[List[dict]] = None

class SyncResponse(BaseModel):
    success: bool
    message: str
    events_synced: int

@app.on_event("startup")
async def startup_event():
    """Initialize database and load configuration on startup."""
    try:
        init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise

@app.get("/")
async def root():
    """Health check endpoint."""
    return {"message": "Smart Calendar Assistant is running", "status": "healthy"}

@app.post("/add-event", response_model=EventResponse)
async def add_event(request: EventRequest):
    """
    Parse natural language prompt and add event to calendar.
    
    Main workflow:
    1. Parse prompt with LLM
    2. Check for conflicts
    3. Add to Google Calendar
    4. Store in local DB
    """
    try:
        # Detect timezone if not provided
        user_timezone = request.timezone or detect_timezone()
        logger.info(f"Processing event request: {request.prompt}")
        
        # Step 1: Parse with LLM
        parsed_event = await parse_event_with_llm(request.prompt, user_timezone)
        if not parsed_event:
            return EventResponse(
                success=False,
                message="Failed to parse event from prompt. Please try rephrasing."
            )
        
        # Step 2: Check for conflicts
        conflicts = check_conflicts(
            parsed_event["start_datetime"], 
            parsed_event["end_datetime"]
        )
        
        if conflicts:
            return EventResponse(
                success=False,
                message=f"Scheduling conflict detected with {len(conflicts)} existing event(s)",
                conflicts=conflicts
            )
        
        # Step 3: Add to Google Calendar
        calendar_event_id = add_event_to_calendar(parsed_event)
        if not calendar_event_id:
            return EventResponse(
                success=False,
                message="Failed to add event to Google Calendar"
            )
        
        # Step 4: Store in local DB
        parsed_event["calendar_event_id"] = calendar_event_id
        store_event(parsed_event)
        
        return EventResponse(
            success=True,
            message="Event added successfully",
            event_id=calendar_event_id
        )
        
    except Exception as e:
        logger.error(f"Error adding event: {e}")
        return EventResponse(
            success=False,
            message=f"Internal error: {str(e)}"
        )

@app.post("/sync-calendar", response_model=SyncResponse)
async def sync_calendar():
    """
    Sync local database with Google Calendar.
    Fetches events from the next 30 days and updates local storage.
    """
    try:
        logger.info("Starting calendar sync...")
        
        # Sync events from Google Calendar
        events_synced = sync_calendar_events()
        
        return SyncResponse(
            success=True,
            message=f"Calendar synced successfully",
            events_synced=events_synced
        )
        
    except Exception as e:
        logger.error(f"Error syncing calendar: {e}")
        return SyncResponse(
            success=False,
            message=f"Sync failed: {str(e)}",
            events_synced=0
        )

@app.get("/events")
async def get_calendar_events(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
):
    """
    Get events from local database.
    Optional date range filtering.
    """
    try:
        # Default to next 7 days if no range specified
        if not start_date:
            start_date = datetime.now().isoformat()
        if not end_date:
            end_date = (datetime.now() + timedelta(days=7)).isoformat()
        
        events = get_events(start_date, end_date)
        
        return {
            "success": True,
            "events": events,
            "count": len(events)
        }
        
    except Exception as e:
        logger.error(f"Error fetching events: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": f"Error fetching events: {str(e)}"}
        )

@app.get("/health")
async def health_check():
    """Detailed health check including database and API connectivity."""
    try:
        # Check database connectivity
        events = get_events(limit=1)
        db_status = "connected"
        
        # TODO: Add Google Calendar API connectivity check
        calendar_status = "not_checked"
        
        # Check parser status
        parser_info = get_parser_status()
        
        return {
            "status": "healthy",
            "database": db_status,
            "calendar_api": calendar_status,
            "parser": parser_info,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
        )

@app.get("/parser-status")
async def get_parsing_status():
    """Get detailed information about available parsing methods."""
    try:
        status = get_parser_status()
        
        return {
            "success": True,
            "parsing_capabilities": status,
            "instructions": {
                "advanced_parsing": "Set HUGGINGFACE_API_TOKEN environment variable",
                "fallback_parsing": "Always available (rule-based)",
                "hybrid_mode": "Automatically tries best available method"
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
        ) 