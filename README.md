# CMS TECHNOVA 2026 Event Portal

Flask-based event portal with competition listings, schedule, teacher information, search filters and an event chatbot.

## Run locally
```bash
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
python app.py
```
Open http://127.0.0.1:5000

## Deploy on Render
Create a Web Service connected to this repository:
- Runtime: Python
- Build command: `pip install -r requirements.txt`
- Start command: `gunicorn app:app`

Check event details against the official brochure before publishing, especially event-specific rules and unannounced teacher assignments.
