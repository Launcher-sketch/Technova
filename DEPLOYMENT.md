# CMS TECHNOVA deployment configuration

## Required environment variables
Set these in the hosting provider's private environment settings. Never commit real values to GitHub or send passwords in chat.
- SECRET_KEY: a long random secret used to sign sessions.
- ADMIN_USERNAME: the administrator username chosen by the event/site owner.
- ADMIN_PASSWORD_HASH: a Werkzeug password hash, not the plain-text password.
- COOKIE_SECURE=true: enable secure session cookies on the HTTPS production site.
- DATABASE_PATH=/var/data/technova.sqlite3: database location on a persistent disk.
- INSTANCE_DIR=/var/data: persistent app data directory.
- UPLOAD_FOLDER=/var/data/uploads: persistent gallery image directory.

Generate a password hash locally in a trusted terminal after installing the requirements:
```bash
python -c "from werkzeug.security import generate_password_hash; print(generate_password_hash(input('Admin password: ')))"
```

Generate a strong session key locally:
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

Use the generated outputs as private environment-variable values. Have the school/event owner or responsible adult create and control the admin credentials. Do not put them in source files.

## Persistent storage on Render
Attach a persistent disk to the web service and mount it at /var/data. Set the three path variables above. Without a persistent disk, SQLite records and uploaded gallery images may be lost when the service is redeployed or its instance is replaced.

Build command: pip install -r requirements.txt
Start command: gunicorn app:app

## Admin workflow
1. Open /admin/login and sign in with the private admin account.
2. Publish announcements and confirmed results.
3. Upload event photos.
4. Create a digital pass only after checking the participant's official registration reference against organiser records.
5. The participant pass URL contains an unguessable token and displays a QR code. Keep the admin dashboard private.

The current TECHNOVA brochure registration link remains an external form. This website does not claim to receive or verify submissions from that external form automatically; pass issuance is an organiser-controlled manual verification step.