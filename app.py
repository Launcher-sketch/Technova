import os
import io
import json
import re
import secrets
import base64
import logging
from functools import wraps
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen

from flask import Flask, jsonify, render_template, request, redirect, url_for, session, flash, abort
from werkzeug.security import check_password_hash
from PIL import Image
import qrcode

BASE_DIR = Path(__file__).resolve().parent
DATA_FILE = BASE_DIR / "data" / "technova.json"
ALLOWED_IMAGE_TYPES = {"JPEG", "PNG", "WEBP"}
STORAGE_BUCKET = os.environ.get("SUPABASE_STORAGE_BUCKET", "technova-gallery")

app = Flask(__name__)
app.config.update(
    SECRET_KEY=os.environ.get("SECRET_KEY") or secrets.token_hex(32),
    MAX_CONTENT_LENGTH=8 * 1024 * 1024,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=os.environ.get("COOKIE_SECURE", "false").lower() == "true",
)

SUPABASE_URL = os.environ.get("SUPABASE_URL", "").rstrip("/")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY") or os.environ.get("SUPABASE_SECRET_KEY", "")


class SupabaseError(RuntimeError):
    pass


def require_supabase():
    if not SUPABASE_URL or not SUPABASE_KEY:
        raise SupabaseError("Cloud database is not configured. Set SUPABASE_URL and SUPABASE_KEY in Render.")
    return SUPABASE_URL, SUPABASE_KEY


def supabase_request(path, method="GET", payload=None, params=None, content_type="application/json", extra_headers=None):
    base_url, key = require_supabase()
    url = f"{base_url}{path}"
    if params:
        url += "?" + urlencode(params, safe="*,().")
    body = None
    if payload is not None:
        body = payload if isinstance(payload, bytes) else json.dumps(payload).encode("utf-8")
    headers = {
        "apikey": key,
        "Authorization": f"Bearer {key}",
        "Accept": "application/json",
    }
    if body is not None:
        headers["Content-Type"] = content_type
    if extra_headers:
        headers.update(extra_headers)
    req = Request(url, data=body, headers=headers, method=method)
    try:
        with urlopen(req, timeout=25) as response:
            raw = response.read()
            if not raw:
                return None
            if "application/json" in response.headers.get("Content-Type", ""):
                return json.loads(raw.decode("utf-8"))
            return raw
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        app.logger.error("Supabase request failed (%s): %s", exc.code, detail[:1000])
        raise SupabaseError(f"Cloud database request failed ({exc.code}). Check the Supabase setup.") from exc
    except (URLError, TimeoutError) as exc:
        app.logger.error("Supabase connection failed: %s", exc)
        raise SupabaseError("Could not connect to Supabase. Check the project URL and network.") from exc


def select_rows(table, order="id.desc", limit=None, filters=None, columns="*"):
    params = {"select": columns}
    if order:
        params["order"] = order
    if limit is not None:
        params["limit"] = str(limit)
    if filters:
        params.update(filters)
    rows = supabase_request(f"/rest/v1/{table}", params=params)
    return rows or []


def insert_row(table, values):
    rows = supabase_request(
        f"/rest/v1/{table}",
        method="POST",
        payload=values,
        extra_headers={"Prefer": "return=representation"},
    )
    if not rows:
        raise SupabaseError("Supabase did not confirm the new record.")
    return rows[0]


def delete_row(table, item_id):
    supabase_request(
        f"/rest/v1/{table}",
        method="DELETE",
        params={"id": f"eq.{int(item_id)}"},
        extra_headers={"Prefer": "return=minimal"},
    )


def storage_public_url(filename):
    return f"{SUPABASE_URL}/storage/v1/object/public/{quote(STORAGE_BUCKET)}/{quote(filename)}"


def upload_gallery_file(filename, image_bytes):
    supabase_request(
        f"/storage/v1/object/{quote(STORAGE_BUCKET)}/{quote(filename)}",
        method="POST",
        payload=image_bytes,
        content_type="image/webp",
        extra_headers={"Cache-Control": "max-age=31536000", "x-upsert": "false"},
    )


def delete_gallery_file(filename):
    supabase_request(
        f"/storage/v1/object/{quote(STORAGE_BUCKET)}",
        method="DELETE",
        payload={"prefixes": [filename]},
    )


def get_data():
    return json.loads(DATA_FILE.read_text(encoding="utf-8"))


if not os.environ.get("SECRET_KEY"):
    app.logger.warning("A temporary SECRET_KEY is active. Set a stable SECRET_KEY in the deployment environment.")
if not SUPABASE_URL or not SUPABASE_KEY:
    app.logger.warning("Supabase is not configured. Set SUPABASE_URL and SUPABASE_KEY in Render.")


def csrf_token():
    if "_csrf" not in session:
        session["_csrf"] = secrets.token_urlsafe(32)
    return session["_csrf"]


@app.context_processor
def inject_csrf():
    return {"csrf_token": csrf_token}


def require_csrf():
    supplied = request.form.get("_csrf", "")
    expected = session.get("_csrf", "")
    if not expected or not secrets.compare_digest(supplied, expected):
        abort(400, "Invalid or expired form token. Refresh and try again.")


def admin_required(fn):
    @wraps(fn)
    def wrapped(*args, **kwargs):
        if not session.get("admin_authenticated"):
            return redirect(url_for("admin_login", next=request.path))
        return fn(*args, **kwargs)
    return wrapped


def answer(reply, headers=None, rows=None):
    result = {"reply": reply}
    if headers is not None and rows is not None:
        result["table"] = {"headers": headers, "rows": rows}
    return jsonify(result)


@app.get("/")
def home():
    try:
        announcements = select_rows("announcements", limit=5)
    except SupabaseError:
        app.logger.exception("Could not load homepage announcements")
        announcements = []
    return render_template("home.html", announcements=announcements)


@app.get("/technova")
def technova():
    try:
        announcements = select_rows("announcements", limit=10)
        results = select_rows("results")
        gallery = select_rows("gallery")
    except SupabaseError:
        app.logger.exception("Could not load TECHNOVA content")
        announcements, results, gallery = [], [], []
        flash("Live updates are temporarily unavailable. Please try again later.", "error")
    return render_template("index.html", data=get_data(), announcements=announcements, results=results, gallery=gallery)


@app.get("/media/<path:filename>")
def media(filename):
    # Gallery files are served from the public Supabase Storage bucket, not local disk.
    return redirect(storage_public_url(filename), code=302)


@app.get("/admin/login")
def admin_login():
    if session.get("admin_authenticated"):
        return redirect(url_for("admin_dashboard"))
    return render_template("admin_login.html", setup_ready=bool(os.environ.get("ADMIN_USERNAME") and os.environ.get("ADMIN_PASSWORD_HASH")))


@app.post("/admin/login")
def admin_login_post():
    require_csrf()
    username = request.form.get("username", "")
    password = request.form.get("password", "")
    expected_user = os.environ.get("ADMIN_USERNAME", "")
    password_hash = os.environ.get("ADMIN_PASSWORD_HASH", "")
    if not expected_user or not password_hash:
        flash("Admin login is not configured yet. Set ADMIN_USERNAME and ADMIN_PASSWORD_HASH in the hosting environment.", "error")
        return redirect(url_for("admin_login"))
    if secrets.compare_digest(username, expected_user) and check_password_hash(password_hash, password):
        session.clear()
        session["admin_authenticated"] = True
        session["admin_user"] = expected_user
        csrf_token()
        return redirect(url_for("admin_dashboard"))
    flash("Login details were not recognised.", "error")
    return redirect(url_for("admin_login"))


@app.post("/admin/logout")
@admin_required
def admin_logout():
    require_csrf()
    session.clear()
    return redirect(url_for("admin_login"))


@app.get("/admin")
@admin_required
def admin_dashboard():
    try:
        announcements = select_rows("announcements")
        results = select_rows("results")
        gallery = select_rows("gallery")
        passes = select_rows("passes", limit=100)
    except SupabaseError:
        app.logger.exception("Could not load admin dashboard")
        flash("Cloud database is unavailable. Check the Supabase setup.", "error")
        announcements, results, gallery, passes = [], [], [], []
    return render_template("admin.html", announcements=announcements, results=results, gallery=gallery, passes=passes)


@app.post("/admin/announcements")
@admin_required
def add_announcement():
    require_csrf()
    title = request.form.get("title", "").strip()[:120]
    body = request.form.get("body", "").strip()[:2000]
    if not (title and body):
        flash("Add both a title and announcement text.", "error")
    else:
        try:
            insert_row("announcements", {"title": title, "body": body})
            flash("Announcement published.", "success")
        except SupabaseError:
            app.logger.exception("Announcement insert failed")
            flash("Could not publish the announcement. Check the Supabase setup.", "error")
    return redirect(url_for("admin_dashboard"))


@app.post("/admin/announcements/<int:item_id>/delete")
@admin_required
def delete_announcement(item_id):
    require_csrf()
    try:
        delete_row("announcements", item_id)
    except SupabaseError:
        app.logger.exception("Announcement delete failed")
        flash("Could not delete that announcement.", "error")
    return redirect(url_for("admin_dashboard"))


@app.post("/admin/results")
@admin_required
def add_result():
    require_csrf()
    event = request.form.get("event", "").strip()[:120]
    winner = request.form.get("winner", "").strip()[:120]
    position = request.form.get("position", "").strip()[:60]
    details = request.form.get("details", "").strip()[:500]
    if not (event and winner and position):
        flash("Event, participant/team and position are required.", "error")
    else:
        try:
            insert_row("results", {"event": event, "winner": winner, "position": position, "details": details})
            flash("Result published.", "success")
        except SupabaseError:
            app.logger.exception("Result insert failed")
            flash("Could not publish the result. Check the Supabase setup.", "error")
    return redirect(url_for("admin_dashboard"))


@app.post("/admin/results/<int:item_id>/delete")
@admin_required
def delete_result(item_id):
    require_csrf()
    try:
        delete_row("results", item_id)
    except SupabaseError:
        app.logger.exception("Result delete failed")
        flash("Could not delete that result.", "error")
    return redirect(url_for("admin_dashboard"))


@app.post("/admin/gallery")
@admin_required
def add_gallery_image():
    require_csrf()
    upload = request.files.get("photo")
    caption = request.form.get("caption", "").strip()[:160]
    if not upload or not upload.filename:
        flash("Choose an image first.", "error")
        return redirect(url_for("admin_dashboard"))
    filename = secrets.token_hex(16) + ".webp"
    try:
        image = Image.open(upload.stream)
        if image.format not in ALLOWED_IMAGE_TYPES:
            raise ValueError("Unsupported image type")
        image.verify()
        upload.stream.seek(0)
        image = Image.open(upload.stream).convert("RGB")
        image.thumbnail((1800, 1800))
        output = io.BytesIO()
        image.save(output, "WEBP", quality=86, method=6)
        image_bytes = output.getvalue()
        upload_gallery_file(filename, image_bytes)
        try:
            insert_row("gallery", {"filename": filename, "caption": caption})
        except Exception:
            delete_gallery_file(filename)
            raise
        flash("Gallery image uploaded.", "success")
    except Exception:
        app.logger.exception("Gallery upload failed")
        flash("That image could not be uploaded. Check the Supabase Storage bucket and try a JPG, PNG or WEBP under 8 MB.", "error")
    return redirect(url_for("admin_dashboard"))


@app.post("/admin/gallery/<int:item_id>/delete")
@admin_required
def delete_gallery_image(item_id):
    require_csrf()
    try:
        rows = select_rows("gallery", filters={"id": f"eq.{int(item_id)}"}, limit=1)
        if rows:
            delete_gallery_file(rows[0]["filename"])
            delete_row("gallery", item_id)
    except SupabaseError:
        app.logger.exception("Gallery delete failed")
        flash("Could not delete that gallery image.", "error")
    return redirect(url_for("admin_dashboard"))


@app.post("/admin/passes")
@admin_required
def create_pass():
    require_csrf()
    participant = request.form.get("participant", "").strip()[:120]
    school = request.form.get("school", "").strip()[:120]
    event = request.form.get("event", "").strip()[:120]
    official_ref = request.form.get("official_ref", "").strip()[:100]
    confirmed = request.form.get("confirmed") == "yes"
    if not all((participant, school, event, official_ref)) or not confirmed:
        flash("Enter the official registration reference and confirm it against the organiser's records before issuing a pass.", "error")
        return redirect(url_for("admin_dashboard"))
    token = secrets.token_urlsafe(32)
    try:
        insert_row("passes", {
            "token": token,
            "participant": participant,
            "school": school,
            "event": event,
            "official_ref": official_ref,
        })
        flash("Verified event pass created.", "success")
        return redirect(url_for("pass_view", token=token))
    except SupabaseError:
        app.logger.exception("Pass creation failed")
        flash("Could not create the pass. Check the Supabase setup.", "error")
        return redirect(url_for("admin_dashboard"))


@app.get("/pass/<token>")
def pass_view(token):
    try:
        rows = select_rows(
            "passes",
            columns="participant,school,event,created_at",
            filters={"token": f"eq.{token}"},
            limit=1,
        )
    except SupabaseError:
        app.logger.exception("Pass lookup failed")
        abort(503, "Pass verification is temporarily unavailable.")
    if not rows:
        abort(404)
    item = rows[0]
    pass_url = url_for("pass_view", token=token, _external=True)
    qr = qrcode.make(pass_url)
    output = io.BytesIO()
    qr.save(output, format="PNG")
    qr_data = "data:image/png;base64," + base64.b64encode(output.getvalue()).decode("ascii")
    return render_template("pass.html", item=item, qr_data=qr_data)


@app.get("/api/data")
def api_data():
    return jsonify(get_data())


@app.post("/api/chat")
def chat():
    message = (request.get_json(silent=True) or {}).get("message", "").strip()
    if not message:
        return answer("Please enter a question.")
    data = get_data()
    q = " ".join(message.lower().replace("?", " ").replace("!", " ").split())
    events = data.get("events", [])
    teachers = data.get("teachers", [])
    if q in ("hello", "hi", "hey", "good morning", "good afternoon", "good evening") or q.startswith(("hello ", "hi ", "hey ")):
        return answer("Hi! I’m the CMS Events Chatbot. Feel free to ask me anything about CMS events, competitions, schedules, teachers, and registrations.")
    if any(term in q for term in ("all events", "list of events", "event list", "competitions", "competition list", "show events", "what events", "which events")):
        rows = [[e["name"], e["category"], e["date"], e["teacher"], e["venue"]] for e in events]
        return answer(f"Here are all {len(events)} TECHNOVA 2026 competitions listed in the available data:", ["Event", "Category", "Date", "Teacher in-charge", "Venue"], rows)
    if any(term in q for term in ("all teachers", "teacher list", "teachers", "who is in charge", "in charge list", "event incharge", "event in-charge")):
        rows = [[t["name"], t["event"]] for t in teachers]
        return answer("TECHNOVA 2026 teachers and their listed event responsibilities:", ["Teacher", "Event responsibility"], rows)
    if any(term in q for term in ("schedule", "date wise", "date-wise", "what happens on", "events on", "which day")):
        rows = sorted([[e["date"], e["name"], e["venue"], e["teacher"]] for e in events], key=lambda row: row[0])
        return answer(f"TECHNOVA 2026 runs on {data['dates']}. Individual reporting times are not listed:", ["Date", "Event", "Venue", "Teacher in-charge"], rows)
    if any(term in q for term in ("registration", "register", "registration form", "last date", "deadline")):
        return answer("TECHNOVA 2026 registration details:", ["Item", "Details"], [["Registration deadline", data["registration_deadline"]], ["Registration form", data["registration_url"]]])
    if any(term in q for term in ("contact", "phone", "help desk", "coordinator", "call", "email")):
        return answer("Official contact information listed for TECHNOVA 2026:", ["Role", "Contact details"], [["Help Desk", "Mr. Shubham Asthana"], ["Technical Coordinator", "Ms. Swaranjali Rawat — 8090365217"], ["Technical Coordinator", "Mr. Abhishek Sharma — 9670050600"]])
    matched_event = next((e for e in events if e["name"].lower() in q or any(str(k).lower() in q for k in e.get("keywords", []))), None)
    if matched_event:
        e = matched_event
        return answer(f"Here are the available details for {e['name']}:", ["Detail", "Information"], [["Category",e["category"]],["Date",e["date"]],["Teacher in-charge",e["teacher"]],["Venue",e["venue"]],["About",e["summary"]]])
    matched_teacher = next((t for t in teachers if t["name"].lower() in q), None)
    if matched_teacher:
        return answer(f"Responsibilities listed for {matched_teacher['name']}:", ["Teacher", "Event"], [[matched_teacher["name"], matched_teacher["event"]]])
    if any(word in q for word in ("date", "when", "timing", "how many days")):
        return answer("TECHNOVA 2026 event dates:", ["Item", "Information"], [["Dates",data["dates"]],["19 November","AI & Robotics Quiz Challenge"],["20 November","Other listed competitions"],["Timing note",data["schedule_note"]]])
    if any(word in q for word in ("school", "cms", "admission", "academics", "principal", "facility", "facilities", "club", "sports", "history", "address", "location")):
        return answer("I have verified TECHNOVA 2026 information, but not the complete official CMS school information for this question. I won't guess. Please contact the school office.")
    try:
        latest = select_rows("announcements", columns="title,body", limit=5)
    except SupabaseError:
        latest = []
    if "announcement" in q or "update" in q or "notice" in q:
        if latest:
            return answer("Latest published TECHNOVA announcements:", ["Title", "Update"], [[x["title"],x["body"]] for x in latest])
        return answer("There are no official announcements published yet.")
    return answer(data.get("fallback", "I couldn't find that information in the available TECHNOVA 2026 data. Please contact the event team."))


@app.errorhandler(413)
def too_large(_error):
    return "Upload too large. Maximum file size is 8 MB.", 413


@app.errorhandler(SupabaseError)
def cloud_error(_error):
    return "The cloud data service is temporarily unavailable. Please try again shortly.", 503


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
