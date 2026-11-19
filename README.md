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
## Main site areas

- `/` — CMS events and campus discovery homepage
- `/about` — Aliganj Campus I profile and facilities overview
- `/technova`, `/celesta`, `/cmsmun` — event information pages
- `/academic-results`, `/sports`, `/contact` — campus information sections
- `/portal` — interactive role-based concept demonstration for Student, Teacher, Parent and School Admin

## Campus Portal demonstration

The portal is intentionally a prototype. Its attendance figures, timetables, notices, identities and role dashboards are fictional sample content. Module forms create temporary in-page previews only; they do not save records, send messages, publish notices, authenticate school users or connect to a student information system. Do not enter real student or family information.

A production school portal requires school-approved data access, real authentication, server-side role authorization, secure session management, privacy review and operational ownership. The browser-only role selector is not an access-control system.

## Campus Genie and source data

Campus Genie answers using the existing project knowledge and event data. The files in `data/` are treated as read-only source material by the application. Review official event brochures and school communications before publishing any changes to event facts.

## Automated checks

GitHub Actions runs Flask route/chat smoke tests and JavaScript syntax checks on pushes to `main` and the implementation branch, plus pull requests targeting `main`.

Run the Python smoke tests locally with:

    python -m unittest discover -s tests -v

Check browser JavaScript syntax with:

    node --check static/script.js
    node --check static/portal.js
