import os
import io
import json
import re
import secrets
import sqlite3
import base64
from functools import wraps
from contextlib import contextmanager
from pathlib import Path
from flask import Flask, jsonify, render_template, request, redirect, url_for, session, flash, abort, send_from_directory
from werkzeug.security import check_password_hash
from werkzeug.utils import secure_filename
from PIL import Image
import qrcode

BASE_DIR = Path(__file__).resolve().parent
INSTANCE_DIR = Path(os.environ.get("INSTANCE_DIR", BASE_DIR / "instance"))
INSTANCE_DIR.mkdir(parents=True, exist_ok=True)
DATABASE = Path(os.environ.get("DATABASE_PATH", INSTANCE_DIR / "technova.sqlite3"))
UPLOAD_DIR = Path(os.environ.get("UPLOAD_FOLDER", INSTANCE_DIR / "uploads"))
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

app = Flask(__name__)
app.config.update(
    SECRET_KEY=os.environ.get("SECRET_KEY") or secrets.token_hex(32),
    MAX_CONTENT_LENGTH=8 * 1024 * 1024,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=os.environ.get("COOKIE_SECURE", "false").lower() == "true",
)
DATA_FILE = BASE_DIR / "data" / "technova.json"
ALLOWED_IMAGE_TYPES = {"JPEG", "PNG", "WEBP"}

def get_data():
    return json.loads(DATA_FILE.read_text(encoding="utf-8"))

@contextmanager
def db():
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row
    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()

def init_db():
    with db() as con:
        con.executescript("""
        CREATE TABLE IF NOT EXISTS announcements (
            id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL,
            body TEXT NOT NULL, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS results (
            id INTEGER PRIMARY KEY AUTOINCREMENT, event TEXT NOT NULL,
            winner TEXT NOT NULL, position TEXT NOT NULL, details TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS gallery (
            id INTEGER PRIMARY KEY AUTOINCREMENT, filename TEXT NOT NULL,
            caption TEXT NOT NULL DEFAULT '', created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS passes (
            id INTEGER PRIMARY KEY AUTOINCREMENT, token TEXT UNIQUE NOT NULL,
            participant TEXT NOT NULL, school TEXT NOT NULL, event TEXT NOT NULL,
            official_ref TEXT NOT NULL, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        """)
if not os.environ.get("SECRET_KEY"):
    app.logger.warning("A temporary SECRET_KEY is active. Set a stable SECRET_KEY in the deployment environment.")
init_db()

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
    with db() as con:
        announcements = con.execute("SELECT * FROM announcements ORDER BY id DESC LIMIT 5").fetchall()
    return render_template("home.html", announcements=announcements)

@app.get("/technova")
def technova():
    with db() as con:
        announcements = con.execute("SELECT * FROM announcements ORDER BY id DESC LIMIT 10").fetchall()
        results = con.execute("SELECT * FROM results ORDER BY id DESC").fetchall()
        gallery = con.execute("SELECT * FROM gallery ORDER BY id DESC").fetchall()
    return render_template("index.html", data=get_data(), announcements=announcements, results=results, gallery=gallery)

@app.get("/media/<path:filename>")
def media(filename):
    return send_from_directory(UPLOAD_DIR, filename)

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
    with db() as con:
        announcements = con.execute("SELECT * FROM announcements ORDER BY id DESC").fetchall()
        results = con.execute("SELECT * FROM results ORDER BY id DESC").fetchall()
        gallery = con.execute("SELECT * FROM gallery ORDER BY id DESC").fetchall()
        passes = con.execute("SELECT * FROM passes ORDER BY id DESC LIMIT 100").fetchall()
    return render_template("admin.html", announcements=announcements, results=results, gallery=gallery, passes=passes)

@app.post("/admin/announcements")
@admin_required
def add_announcement():
    require_csrf()
    title = request.form.get("title", "").strip()[:120]
    body = request.form.get("body", "").strip()[:2000]
    if title and body:
        with db() as con:
            con.execute("INSERT INTO announcements(title, body) VALUES(?, ?)", (title, body))
        flash("Announcement published.", "success")
    else:
        flash("Add both a title and announcement text.", "error")
    return redirect(url_for("admin_dashboard"))

@app.post("/admin/announcements/<int:item_id>/delete")
@admin_required
def delete_announcement(item_id):
    require_csrf()
    with db() as con:
        con.execute("DELETE FROM announcements WHERE id=?", (item_id,))
    return redirect(url_for("admin_dashboard"))

@app.post("/admin/results")
@admin_required
def add_result():
    require_csrf()
    event = request.form.get("event", "").strip()[:120]
    winner = request.form.get("winner", "").strip()[:120]
    position = request.form.get("position", "").strip()[:60]
    details = request.form.get("details", "").strip()[:500]
    if event and winner and position:
        with db() as con:
            con.execute("INSERT INTO results(event,winner,position,details) VALUES(?,?,?,?)", (event,winner,position,details))
        flash("Result published.", "success")
    else:
        flash("Event, participant/team and position are required.", "error")
    return redirect(url_for("admin_dashboard"))

@app.post("/admin/results/<int:item_id>/delete")
@admin_required
def delete_result(item_id):
    require_csrf()
    with db() as con:
        con.execute("DELETE FROM results WHERE id=?", (item_id,))
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
    try:
        image = Image.open(upload.stream)
        if image.format not in ALLOWED_IMAGE_TYPES:
            raise ValueError("Use a JPG, PNG or WEBP image.")
        image.verify()
        upload.stream.seek(0)
        image = Image.open(upload.stream).convert("RGB")
        image.thumbnail((1800, 1800))
        filename = secrets.token_hex(16) + ".webp"
        image.save(UPLOAD_DIR / filename, "WEBP", quality=86, method=6)
        with db() as con:
            con.execute("INSERT INTO gallery(filename,caption) VALUES(?,?)", (filename, caption))
        flash("Gallery image uploaded.", "success")
    except Exception:
        flash("That image could not be processed. Try a JPG, PNG or WEBP file under 8 MB.", "error")
    return redirect(url_for("admin_dashboard"))

@app.post("/admin/gallery/<int:item_id>/delete")
@admin_required
def delete_gallery_image(item_id):
    require_csrf()
    with db() as con:
        item = con.execute("SELECT filename FROM gallery WHERE id=?", (item_id,)).fetchone()
        if item:
            (UPLOAD_DIR / item["filename"]).unlink(missing_ok=True)
            con.execute("DELETE FROM gallery WHERE id=?", (item_id,))
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
    with db() as con:
        con.execute("INSERT INTO passes(token,participant,school,event,official_ref) VALUES(?,?,?,?,?)",
                    (token,participant,school,event,official_ref))
    flash("Verified event pass created.", "success")
    return redirect(url_for("pass_view", token=token))

@app.get("/pass/<token>")
def pass_view(token):
    with db() as con:
        item = con.execute("SELECT participant,school,event,created_at FROM passes WHERE token=?", (token,)).fetchone()
    if not item:
        abort(404)
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
    with db() as con:
        latest = con.execute("SELECT title,body FROM announcements ORDER BY id DESC LIMIT 5").fetchall()
    if "announcement" in q or "update" in q or "notice" in q:
        if latest:
            return answer("Latest published TECHNOVA announcements:", ["Title", "Update"], [[x["title"],x["body"]] for x in latest])
        return answer("There are no official announcements published yet.")
    return answer(data.get("fallback", "I couldn't find that information in the available TECHNOVA 2026 data. Please contact the event team."))

@app.errorhandler(413)
def too_large(_error):
    return "Upload too large. Maximum file size is 8 MB.", 413

if __name__ == "__main__":
    import os
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
