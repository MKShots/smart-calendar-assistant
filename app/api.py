import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from .config import get_google_credentials_path
from .db import store_event, get_all_events

logger = logging.getLogger(__name__)

class GoogleCalendarAPI:
    def __init__(self):
        self.service = None
        self.calendar_id = 'primary'  # Use primary calendar
        self._initialize_service()
    
    def _initialize_service(self):
        """Initialize Google Calendar API service."""
        try:
            credentials_path = get_google_credentials_path()
            if not credentials_path:
                raise ValueError("Google credentials path not configured")
            
            # Define the scopes
            SCOPES = ['https://www.googleapis.com/auth/calendar']
            
            # Load service account credentials
            credentials = service_account.Credentials.from_service_account_file(
                credentials_path, scopes=SCOPES
            )
            
            # Build the service
            self.service = build('calendar', 'v3', credentials=credentials)
            
            logger.info("Google Calendar API service initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Google Calendar API: {e}")
            raise
    
    def add_event(self, event_data: Dict) -> Optional[str]:
        """
        Add an event to Google Calendar.
        
        Args:
            event_data: Event dictionary with title, start_datetime, etc.
            
        Returns:
            Google Calendar event ID or None if failed
        """
        try:
            # Convert event data to Google Calendar format
            calendar_event = self._convert_to_calendar_event(event_data)
            
            # Insert event
            event = self.service.events().insert(
                calendarId=self.calendar_id,
                body=calendar_event
            ).execute()
            
            event_id = event.get('id')
            logger.info(f"Event created successfully: {event_id}")
            return event_id
            
        except HttpError as e:
            logger.error(f"HTTP error adding event to calendar: {e}")
            return None
        except Exception as e:
            logger.error(f"Error adding event to calendar: {e}")
            return None
    
    def get_events(self, start_date: datetime, end_date: datetime) -> List[Dict]:
        """
        Fetch events from Google Calendar within date range.
        
        Args:
            start_date: Start datetime for event range
            end_date: End datetime for event range
            
        Returns:
            List of event dictionaries
        """
        try:
            # Format datetime for Google Calendar API
            time_min = start_date.isoformat() + 'Z'
            time_max = end_date.isoformat() + 'Z'
            
            # Call the Calendar API
            events_result = self.service.events().list(
                calendarId=self.calendar_id,
                timeMin=time_min,
                timeMax=time_max,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            
            # Convert to our event format
            converted_events = []
            for event in events:
                converted_event = self._convert_from_calendar_event(event)
                if converted_event:
                    converted_events.append(converted_event)
            
            logger.info(f"Fetched {len(converted_events)} events from Google Calendar")
            return converted_events
            
        except HttpError as e:
            logger.error(f"HTTP error fetching events: {e}")
            return []
        except Exception as e:
            logger.error(f"Error fetching events from calendar: {e}")
            return []
    
    def update_event(self, event_id: str, event_data: Dict) -> bool:
        """
        Update an existing event in Google Calendar.
        
        Args:
            event_id: Google Calendar event ID
            event_data: Updated event data
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Convert event data to Google Calendar format
            calendar_event = self._convert_to_calendar_event(event_data)
            
            # Update event
            self.service.events().update(
                calendarId=self.calendar_id,
                eventId=event_id,
                body=calendar_event
            ).execute()
            
            logger.info(f"Event updated successfully: {event_id}")
            return True
            
        except HttpError as e:
            logger.error(f"HTTP error updating event: {e}")
            return False
        except Exception as e:
            logger.error(f"Error updating event: {e}")
            return False
    
    def delete_event(self, event_id: str) -> bool:
        """
        Delete an event from Google Calendar.
        
        Args:
            event_id: Google Calendar event ID
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.service.events().delete(
                calendarId=self.calendar_id,
                eventId=event_id
            ).execute()
            
            logger.info(f"Event deleted successfully: {event_id}")
            return True
            
        except HttpError as e:
            logger.error(f"HTTP error deleting event: {e}")
            return False
        except Exception as e:
            logger.error(f"Error deleting event: {e}")
            return False
    
    def _convert_to_calendar_event(self, event_data: Dict) -> Dict:
        """Convert our event format to Google Calendar event format."""
        calendar_event = {
            'summary': event_data.get('title', 'Untitled Event'),
            'description': event_data.get('description', ''),
            'start': {
                'dateTime': event_data['start_datetime'],
                'timeZone': 'UTC',  # TODO: Use user's timezone
            },
            'end': {
                'dateTime': event_data['end_datetime'],
                'timeZone': 'UTC',  # TODO: Use user's timezone
            },
        }
        
        # Add location if provided
        if event_data.get('location'):
            calendar_event['location'] = event_data['location']
        
        # Add attendees if provided
        if event_data.get('attendees'):
            calendar_event['attendees'] = [
                {'email': email} for email in event_data['attendees']
            ]
        
        return calendar_event
    
    def _convert_from_calendar_event(self, calendar_event: Dict) -> Optional[Dict]:
        """Convert Google Calendar event to our event format."""
        try:
            # Extract start and end times
            start = calendar_event.get('start', {})
            end = calendar_event.get('end', {})
            
            # Handle both dateTime and date formats
            start_datetime = start.get('dateTime') or start.get('date')
            end_datetime = end.get('dateTime') or end.get('date')
            
            if not start_datetime or not end_datetime:
                logger.warning(f"Missing datetime in event: {calendar_event.get('id')}")
                return None
            
            # Extract attendees
            attendees = []
            for attendee in calendar_event.get('attendees', []):
                if attendee.get('email'):
                    attendees.append(attendee['email'])
            
            event_data = {
                'title': calendar_event.get('summary', 'Untitled Event'),
                'start_datetime': start_datetime,
                'end_datetime': end_datetime,
                'description': calendar_event.get('description', ''),
                'location': calendar_event.get('location', ''),
                'attendees': attendees,
                'calendar_event_id': calendar_event.get('id'),
                'created': calendar_event.get('created'),
                'updated': calendar_event.get('updated')
            }
            
            return event_data
            
        except Exception as e:
            logger.error(f"Error converting calendar event: {e}")
            return None

# Global API instance
_calendar_api = None

def get_calendar_api() -> GoogleCalendarAPI:
    """Get or create global calendar API instance."""
    global _calendar_api
    if _calendar_api is None:
        _calendar_api = GoogleCalendarAPI()
    return _calendar_api

def add_event_to_calendar(event_data: Dict) -> Optional[str]:
    """
    Add event to Google Calendar.
    
    Args:
        event_data: Event dictionary
        
    Returns:
        Calendar event ID or None if failed
    """
    try:
        api = get_calendar_api()
        return api.add_event(event_data)
    except Exception as e:
        logger.error(f"Error adding event to calendar: {e}")
        return None

def sync_calendar_events(days_ahead: int = 30) -> int:
    """
    Sync events from Google Calendar to local database.
    
    Args:
        days_ahead: Number of days ahead to sync
        
    Returns:
        Number of events synced
    """
    try:
        api = get_calendar_api()
        
        # Define date range
        start_date = datetime.now()
        end_date = start_date + timedelta(days=days_ahead)
        
        # Fetch events from Google Calendar
        calendar_events = api.get_events(start_date, end_date)
        
        events_synced = 0
        for event in calendar_events:
            try:
                # Store/update event in local database
                store_event(event, sync=True)
                events_synced += 1
            except Exception as e:
                logger.error(f"Error storing synced event: {e}")
                continue
        
        logger.info(f"Synced {events_synced} events from Google Calendar")
        return events_synced
        
    except Exception as e:
        logger.error(f"Error syncing calendar events: {e}")
        return 0

def get_calendar_events_in_range(start_date: datetime, end_date: datetime) -> List[Dict]:
    """
    Get events from Google Calendar within date range.
    
    Returns:
        List of events
    """
    try:
        api = get_calendar_api()
        return api.get_events(start_date, end_date)
    except Exception as e:
        logger.error(f"Error fetching calendar events: {e}")
        return [] 