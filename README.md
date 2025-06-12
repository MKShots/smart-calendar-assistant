# 📅 Smart LLM-Powered Personal Calendar Assistant

A free, always-accessible calendar organizer that uses natural language processing to manage your Google Calendar events intelligently.

## 🚀 Features

- **Natural Language Input**: Add events using plain English like "Schedule dentist appointment tomorrow at 2 PM"
- **Conflict Detection**: Automatically checks for scheduling conflicts with configurable gap times
- **Google Calendar Integration**: Seamlessly syncs with your Google Calendar
- **Local Database**: Maintains an encrypted SQLite database for offline access
- **Daily Sync**: Automatically syncs with Google Calendar daily
- **REST API**: Access from any device via HTTP endpoints
- **Free Tier**: Runs entirely on free services (Hugging Face, Render, Google Calendar)

## 🧱 Tech Stack

| Component | Technology |
|-----------|------------|
| Framework | Python + FastAPI |
| LLM | Hugging Face (Llama-2-7B-Chat) |
| Orchestration | LangChain |
| Database | SQLite |
| Calendar API | Google Calendar API |
| Cloud Host | Render (Free tier) |
| Scheduler | Render Cron Jobs |

## 📂 Project Structure

```
calendar-smart-assistant/
├── app/
│   ├── main.py          # FastAPI application
│   ├── api.py           # Google Calendar API integration
│   ├── llm.py           # LangChain + Hugging Face LLM
│   ├── db.py            # SQLite database handling
│   ├── scheduler.py     # Daily sync job
│   ├── utils.py         # Utility functions
│   └── config.py        # Configuration management
├── config/
│   └── user_config.json # User preferences (auto-generated)
├── data/
│   └── calendar.sqlite  # Local database (auto-generated)
├── requirements.txt     # Python dependencies
├── .gitignore          # Git ignore patterns
└── README.md           # This file
```

## 🔧 Setup Instructions

### 1. Prerequisites

- Python 3.8+
- Google Cloud Console account
- Hugging Face account
- Render account (for deployment)

### 2. Google Calendar API Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable the Google Calendar API
4. Create a Service Account:
   - Go to "IAM & Admin" > "Service Accounts"
   - Click "Create Service Account"
   - Download the JSON credentials file
   - Rename it to `credentials.json` and place in `config/` directory

### 3. Hugging Face API Setup

1. Create account at [huggingface.co](https://huggingface.co)
2. Go to Settings > Access Tokens
3. Generate a new token (read-only is sufficient)
4. Copy the token for environment configuration

### 4. Local Development

```bash
# Clone the repository
git clone <your-repo-url>
cd Smart\ Calendar

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export HUGGINGFACE_API_TOKEN="your_token_here"
export GOOGLE_CREDENTIALS_PATH="config/credentials.json"
export TIMEZONE="America/New_York"  # Optional

# Run the application
uvicorn app.main:app --reload --port 8000
```

### 5. Render Deployment

1. Create a new Web Service on [Render](https://render.com)
2. Connect your GitHub repository
3. Set the following environment variables:
   - `HUGGINGFACE_API_TOKEN`: Your Hugging Face token
   - `GOOGLE_CREDENTIALS_PATH`: `config/credentials.json`
   - `TIMEZONE`: Your timezone (optional)
4. Upload your `credentials.json` file to the Render dashboard
5. Deploy the service

## 📖 API Usage

### Add Event

```bash
curl -X POST "http://localhost:8000/add-event" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Schedule dentist appointment tomorrow at 2 PM for 1 hour",
    "timezone": "America/New_York"
  }'
```

### Get Events

```bash
curl "http://localhost:8000/events?start_date=2024-01-01T00:00:00&end_date=2024-01-07T23:59:59"
```

### Sync Calendar

```bash
curl -X POST "http://localhost:8000/sync-calendar"
```

### Health Check

```bash
curl "http://localhost:8000/health"
```

## 🔄 Daily Sync Setup

The application includes a built-in scheduler for daily synchronization. On Render:

1. Go to your service settings
2. Add a Cron Job with schedule: `0 0 * * *` (daily at midnight)
3. Command: `python -m app.scheduler`

## ⚙️ Configuration

The app creates a `config/user_config.json` file with default settings:

```json
{
  "timezone": "UTC",
  "conflict_gap_minutes": 15,
  "sync_days_ahead": 30,
  "auto_sync": true
}
```

## 🧪 Testing

Test the application with sample prompts:

- "Meeting with John tomorrow at 3 PM"
- "Lunch at Italian restaurant on Friday at noon"
- "Doctor appointment next Monday at 10:30 AM for 45 minutes"
- "Conference call with team on Wednesday from 2 to 3 PM"

## 🐛 Troubleshooting

### Common Issues

1. **LLM not responding**: Check Hugging Face token and rate limits
2. **Calendar sync failing**: Verify Google credentials and permissions
3. **Database errors**: Ensure `data/` directory has write permissions
4. **Timezone issues**: Set `TIMEZONE` environment variable

### Logging

Logs are written to stdout. In production, configure log aggregation through your hosting provider.

## 🎯 Next Steps

After basic setup, consider these enhancements:

- [ ] Add web interface with Streamlit
- [ ] Implement conflict resolution suggestions
- [ ] Add email notifications
- [ ] Support multiple calendars
- [ ] Add recurring event support
- [ ] Implement backup to cloud storage

## 📝 License

This project is open source and available under the [MIT License](LICENSE).

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

---

**Happy scheduling! 📅✨** 