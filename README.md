# CMS TECHNOVA 2026 Event Portal

Flask-based CMS events website with competition listings, schedules, campus information, event updates and a CMS-focused chatbot.

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
## Main site areas

- `/` — CMS events and campus discovery homepage
- `/about` — Aliganj Campus I profile, leadership reference and named facilities directory
- Homepage — live campus announcements when the cloud database is configured, with a clear empty state when none are available
- `/technova`, `/celesta`, `/cmsmun` — event information pages
- `/academic-results`, `/sports`, `/contact` — campus information sections

## Campus Genie and source data

Campus Genie answers using the existing project knowledge and event data. The files in `data/` are treated as read-only source material by the application. Review official event brochures and school communications before publishing any changes to event facts.

## Automated checks

GitHub Actions runs Flask route/chat smoke tests and JavaScript syntax checks on pushes to `main` and the implementation branch, plus pull requests targeting `main`.

Run the Python smoke tests locally with:

    python -m unittest discover -s tests -v

Check browser JavaScript syntax with:

    node --check static/script.js
