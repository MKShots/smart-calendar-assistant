import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import uuid

logger = logging.getLogger(__name__)

def add_event_to_calendar(event_data: Dict) -> Optional[str]:
    """
    Mock function to simulate adding an event to Google Calendar.
    Returns a fake event ID for testing purposes.
    """
    try:
        # Generate a fake Google Calendar event ID
        fake_event_id = f"mock_{uuid.uuid4().hex[:8]}"
        
        logger.info(f"Mock: Added event '{event_data['title']}' with ID: {fake_event_id}")
        
        # In a real implementation, this would call Google Calendar API
        return fake_event_id
        
    except Exception as e:
        logger.error(f"Mock: Error adding event to calendar: {e}")
        return None

def sync_calendar_events(days_ahead: int = 30) -> int:
    """
    Mock function to simulate syncing events from Google Calendar.
    Returns a fake count of synced events.
    """
    try:
        # Simulate syncing some events
        fake_events_count = 3  # Pretend we synced 3 events
        
        logger.info(f"Mock: Synced {fake_events_count} events from Google Calendar")
        
        # In a real implementation, this would:
        # 1. Fetch events from Google Calendar
        # 2. Store them in the local database
        # 3. Return the actual count
        
        return fake_events_count
        
    except Exception as e:
        logger.error(f"Mock: Error syncing calendar events: {e}")
        return 0

def get_calendar_events_in_range(start_date: datetime, end_date: datetime) -> List[Dict]:
    """
    Mock function to simulate fetching events from Google Calendar.
    Returns fake events for testing.
    """
    try:
        # Generate some fake events
        now = datetime.now()
        fake_events = [
            {
                "title": "Mock Meeting",
                "start_datetime": (now + timedelta(hours=1)).isoformat(),
                "end_datetime": (now + timedelta(hours=2)).isoformat(),
                "description": "This is a mock event for testing",
                "location": "Mock Location",
                "attendees": [],
                "calendar_event_id": "mock_12345"
            },
            {
                "title": "Mock Appointment",
                "start_datetime": (now + timedelta(days=1)).isoformat(),
                "end_datetime": (now + timedelta(days=1, hours=1)).isoformat(),
                "description": "Another mock event",
                "location": "",
                "attendees": ["test@example.com"],
                "calendar_event_id": "mock_67890"
            }
        ]
        
        logger.info(f"Mock: Retrieved {len(fake_events)} events from Google Calendar")
        return fake_events
        
    except Exception as e:
        logger.error(f"Mock: Error fetching calendar events: {e}")
        return []

# Additional mock functions for completeness
def update_calendar_event(event_id: str, event_data: Dict) -> bool:
    """Mock function to simulate updating a calendar event."""
    logger.info(f"Mock: Updated event {event_id}")
    return True

def delete_calendar_event(event_id: str) -> bool:
    """Mock function to simulate deleting a calendar event."""
    logger.info(f"Mock: Deleted event {event_id}")
    return True 