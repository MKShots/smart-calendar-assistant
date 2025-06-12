import sqlite3
import logging
import json
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from pathlib import Path

logger = logging.getLogger(__name__)

# Database file path
DB_PATH = Path(__file__).parent.parent / "data" / "calendar.sqlite"

def init_db():
    """Initialize the database with required tables."""
    try:
        # Ensure data directory exists
        data_dir = Path(DB_PATH).parent
        data_dir.mkdir(parents=True, exist_ok=True)
        
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            
            # Create events table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    start_datetime TEXT NOT NULL,
                    end_datetime TEXT NOT NULL,
                    description TEXT DEFAULT '',
                    location TEXT DEFAULT '',
                    attendees TEXT DEFAULT '[]',
                    calendar_event_id TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    synced_at TEXT,
                    is_deleted INTEGER DEFAULT 0
                )
            ''')
            
            # Create indexes
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_events_datetime 
                ON events(start_datetime, end_datetime)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_events_calendar_id 
                ON events(calendar_event_id)
            ''')
            
            conn.commit()
            logger.info("Database initialized successfully")
            
    except sqlite3.Error as e:
        logger.error(f"Database initialization error: {e}")
        raise

def store_event(event_data: Dict, sync: bool = False) -> Optional[int]:
    """Store an event in the database."""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            
            current_time = datetime.now().isoformat()
            attendees_json = json.dumps(event_data.get('attendees', []))
            
            if sync and event_data.get('calendar_event_id'):
                # Check if event already exists
                cursor.execute(
                    'SELECT id FROM events WHERE calendar_event_id = ?',
                    (event_data['calendar_event_id'],)
                )
                existing = cursor.fetchone()
                
                if existing:
                    # Update existing event
                    cursor.execute('''
                        UPDATE events SET
                            title = ?, start_datetime = ?, end_datetime = ?,
                            description = ?, location = ?, attendees = ?,
                            updated_at = ?, synced_at = ?
                        WHERE calendar_event_id = ?
                    ''', (
                        event_data['title'],
                        event_data['start_datetime'],
                        event_data['end_datetime'],
                        event_data.get('description', ''),
                        event_data.get('location', ''),
                        attendees_json,
                        current_time,
                        current_time,
                        event_data['calendar_event_id']
                    ))
                    conn.commit()
                    return existing[0]
            
            # Insert new event
            cursor.execute('''
                INSERT INTO events (
                    title, start_datetime, end_datetime, description,
                    location, attendees, calendar_event_id, created_at,
                    updated_at, synced_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                event_data['title'],
                event_data['start_datetime'],
                event_data['end_datetime'],
                event_data.get('description', ''),
                event_data.get('location', ''),
                attendees_json,
                event_data.get('calendar_event_id'),
                current_time,
                current_time,
                current_time if sync else None
            ))
            
            conn.commit()
            event_id = cursor.lastrowid
            logger.info(f"Event stored successfully: {event_id}")
            return event_id
            
    except sqlite3.Error as e:
        logger.error(f"Database error storing event: {e}")
        return None

def get_events(start_date: Optional[str] = None, 
               end_date: Optional[str] = None, limit: Optional[int] = None) -> List[Dict]:
    """Get events from database with optional filtering."""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            
            query = '''
                SELECT id, title, start_datetime, end_datetime, description,
                       location, attendees, calendar_event_id, created_at,
                       updated_at, synced_at
                FROM events 
                WHERE is_deleted = 0
            '''
            params = []
            
            if start_date:
                query += ' AND start_datetime >= ?'
                params.append(start_date)
            
            if end_date:
                query += ' AND end_datetime <= ?'
                params.append(end_date)
            
            query += ' ORDER BY start_datetime ASC'
            
            if limit:
                query += ' LIMIT ?'
                params.append(limit)
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            events = []
            for row in rows:
                event = {
                    'id': row[0],
                    'title': row[1],
                    'start_datetime': row[2],
                    'end_datetime': row[3],
                    'description': row[4],
                    'location': row[5],
                    'attendees': json.loads(row[6]) if row[6] else [],
                    'calendar_event_id': row[7],
                    'created_at': row[8],
                    'updated_at': row[9],
                    'synced_at': row[10]
                }
                events.append(event)
            
            return events
            
    except sqlite3.Error as e:
        logger.error(f"Database error fetching events: {e}")
        return []

def check_conflicts(start_datetime: str, end_datetime: str, 
                   gap_minutes: int = 15) -> List[Dict]:
    """Check for scheduling conflicts with existing events."""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            
            # Calculate buffer times
            start_time = datetime.fromisoformat(start_datetime)
            end_time = datetime.fromisoformat(end_datetime)
            buffer_start = (start_time - timedelta(minutes=gap_minutes)).isoformat()
            buffer_end = (end_time + timedelta(minutes=gap_minutes)).isoformat()
            
            cursor.execute('''
                SELECT id, title, start_datetime, end_datetime
                FROM events 
                WHERE is_deleted = 0
                AND (
                    (start_datetime < ? AND end_datetime > ?) OR
                    (start_datetime < ? AND end_datetime > ?)
                )
            ''', [buffer_end, buffer_start, end_datetime, start_datetime])
            
            rows = cursor.fetchall()
            
            conflicts = []
            for row in rows:
                conflict = {
                    'id': row[0],
                    'title': row[1],
                    'start_datetime': row[2],
                    'end_datetime': row[3]
                }
                conflicts.append(conflict)
            
            return conflicts
            
    except sqlite3.Error as e:
        logger.error(f"Database error checking conflicts: {e}")
        return []

def get_all_events() -> List[Dict]:
    """Get all events from database."""
    return get_events() 