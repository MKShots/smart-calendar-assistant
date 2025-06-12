# 🔧 Smart Calendar Assistant - Setup Guide

This guide will help you set up your own instance of the Smart Calendar Assistant.

## 🚀 Quick Start (Mock Mode)

The project comes with mock implementations so you can test it immediately:

```bash
# 1. Clone the repository
git clone <your-repo-url>
cd Smart-Calendar

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run the application
uvicorn app.main:app --reload --port 8000

# 4. Test it works
curl -X POST "http://localhost:8000/add-event" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Meeting tomorrow at 2 PM"}'
```

**The app runs in mock mode by default** - no API keys required for initial testing!

## 🔑 Production Setup (Real APIs)

### Step 1: Get API Credentials

#### Google Calendar API
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create new project → Enable Google Calendar API
3. Create Service Account → Download credentials JSON
4. Place as `config/credentials.json`

#### Hugging Face API
1. Create account at [huggingface.co](https://huggingface.co)
2. Settings → Access Tokens → Generate new token
3. Copy token for environment setup

### Step 2: Switch to Production Mode

Edit `app/main.py` to use real APIs:

```python
# Change these two imports:
from .api_simple import → from .api import
from .llm_simple import → from .llm import
```

### Step 3: Environment Setup

```bash
# Set environment variables
export HUGGINGFACE_API_TOKEN="your_hf_token_here"
export GOOGLE_CREDENTIALS_PATH="config/credentials.json"
export TIMEZONE="Your/Timezone"  # e.g., "America/New_York"

# Run with real APIs
uvicorn app.main:app --reload --port 8000
```

## 🌐 Cloud Deployment (Render)

1. Push your code to GitHub
2. Create account at [Render.com](https://render.com)
3. Create new Web Service → Connect GitHub repo
4. Set environment variables in Render dashboard
5. Upload `credentials.json` file to Render
6. Deploy!

## 🎯 Configuration

Customize `config/user_config.json`:

```json
{
  "timezone": "America/New_York",
  "conflict_gap_minutes": 15,
  "sync_days_ahead": 30,
  "auto_sync": true
}
```

## 🔒 Security Notes

- **Never commit `credentials.json`** (already in .gitignore)
- **Use environment variables** for all secrets
- **Keep your personal deployment private**
- **Use service accounts** for Google Calendar access

## 📞 Support

- Check the main README.md for API documentation
- Review the code comments for implementation details
- Open issues for bugs or feature requests

---

**Ready to build your own smart calendar? Let's go! 🚀** 