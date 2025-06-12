import logging
import asyncio
from datetime import datetime
from .api_simple import sync_calendar_events
from .config import get_sync_days_ahead

logger = logging.getLogger(__name__)

async def daily_sync_job():
    """
    Daily sync job to update local database with Google Calendar events.
    This function is designed to run via cron job or scheduled task.
    """
    try:
        logger.info("Starting daily calendar sync job...")
        
        # Get sync configuration
        days_ahead = get_sync_days_ahead()
        
        # Perform sync
        events_synced = sync_calendar_events(days_ahead)
        
        logger.info(f"Daily sync completed successfully. Synced {events_synced} events.")
        
        return {
            "success": True,
            "events_synced": events_synced,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Daily sync job failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

def run_daily_sync():
    """
    Synchronous wrapper for the daily sync job.
    This can be called directly from cron jobs or scheduled tasks.
    """
    try:
        # Run the async function
        result = asyncio.run(daily_sync_job())
        
        if result["success"]:
            print(f"✅ Daily sync completed: {result['events_synced']} events synced")
        else:
            print(f"❌ Daily sync failed: {result['error']}")
            
        return result
        
    except Exception as e:
        error_msg = f"Failed to run daily sync: {e}"
        logger.error(error_msg)
        print(f"❌ {error_msg}")
        return {
            "success": False,
            "error": error_msg,
            "timestamp": datetime.now().isoformat()
        }

if __name__ == "__main__":
    # Allow running this module directly for testing
    print("Running daily sync job...")
    result = run_daily_sync()
    exit(0 if result["success"] else 1) 