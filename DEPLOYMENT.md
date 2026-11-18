# CMS TECHNOVA deployment configuration

## Cloud database and image storage (Supabase)

The application stores announcements, results, gallery metadata and event passes in Supabase Postgres. Gallery images are stored in the public-read `technova-gallery` Storage bucket. No local SQLite database or Render Persistent Disk is required.

1. Open your Supabase project and go to **SQL Editor**.
2. Open `supabase/schema.sql` from this repository, copy the full contents, paste into a new SQL query and click **Run** once.
3. In Render -> your web service -> **Environment**, set:
   - `SUPABASE_URL`: your project URL, for example `https://YOUR-PROJECT-REF.supabase.co` (not the `/rest/v1/` URL)
   - `SUPABASE_KEY`: the private Supabase secret key. Keep it only in Render; never put it in GitHub, browser JavaScript, or chat.
   - `SUPABASE_STORAGE_BUCKET`: `technova-gallery` (optional; this is the default)
   - `SECRET_KEY`: a long random secret used to sign sessions.
   - `ADMIN_USERNAME`: the administrator username.
   - `ADMIN_PASSWORD_HASH`: a Werkzeug password hash, not the plain-text password.
   - `COOKIE_SECURE=true`: enable secure session cookies on the HTTPS production site.
4. Remove the old `DATABASE_PATH`, `INSTANCE_DIR`, and `UPLOAD_FOLDER` settings if they were added for the old SQLite deployment. They are no longer used.
5. Build command: `pip install -r requirements.txt`
6. Start command: `gunicorn app:app`

The private Supabase key is used only by the Flask server. Row Level Security is enabled on the tables and no anonymous table policies are created. The gallery bucket is public-read so visitors can view images; writes and deletes still go through the authenticated admin server.

## Admin workflow

1. Open `/admin/login` and sign in with the private admin account.
2. Publish announcements and confirmed results.
3. Upload event photos.
4. Create a digital pass only after checking the participant's official registration reference against organiser records.
5. The participant pass URL contains an unguessable token and displays a QR code. Keep the admin dashboard private.

The brochure registration link remains an external form. This website does not claim to receive or verify submissions from that external form automatically; pass issuance remains an organiser-controlled manual verification step.

## Important

The old SQLite file and local upload directory are not automatically imported into Supabase. If the old deployment contains records or photos that must be retained, export them before switching. The website's static TECHNOVA content remains in `data/technova.json`.
