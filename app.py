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
CULTURAL_DATA_FILE = BASE_DIR / "data" / "cultural_events.json"
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


def get_cultural_data():
    return json.loads(CULTURAL_DATA_FILE.read_text(encoding="utf-8"))


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
    return render_template("home.html", announcements=announcements, celesta=get_cultural_data())


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
    site_data = get_data()
    return render_template("index.html", data=site_data, announcements=announcements, results=results, gallery=gallery)


@app.get("/celesta")
def celesta_page():
    return render_template("celesta.html", celesta=get_cultural_data())


@app.get("/academic-results")
def academic_results_page():
    return render_template("academic_results.html")


@app.get("/sports")
def sports_page():
    return render_template("sports.html")


@app.get("/cmsmun")
def cmsmun_page():
    return render_template("cmsmun.html")


CAMPUS_INFORMATION_PAGES = {
    "infrastructure": {
        "title": "Infrastructure",
        "eyebrow": "CAMPUS & FACILITIES",
        "intro": "Explore the learning environments and facilities listed by CMS Aliganj Campus I.",
        "sections": [
            {"heading": "Classrooms & academic spaces", "body": "The campus describes spacious classrooms supported by smart panels, creating a technology-enabled setting for lessons, discussion and collaborative work."},
            {"heading": "Science, computing & innovation", "body": "Facilities named by CMS include Physics, Chemistry, Biology, Biotechnology, Computer and Robotics laboratories, along with the Design & Technology Lab, Maker Space and Studio Pod. These spaces support practical exploration, experimentation and project-based learning."},
            {"heading": "Reading, arts & expression", "body": "The campus facilities directory lists a Library, Music Room and Art Room, providing dedicated spaces for reading, creative practice and expression."},
            {"heading": "Sport, health & wellbeing", "body": "Published campus facilities include a swimming pool, children’s splash pool, basketball court, playground and infirmary. Access and availability are subject to school arrangements."}
        ],
        "source": "CMS Aliganj Campus I official website"
    },
    "child-development": {
        "title": "Child Development",
        "eyebrow": "WHOLE-CHILD LEARNING",
        "intro": "CMS describes education as a combination of academic growth, creativity, character, wellbeing and opportunities to contribute.",
        "sections": [
            {"heading": "The 6 Cs", "body": "The campus highlights Critical Thinking, Creativity, Collaboration, Communication, Character and Citizenship as important capabilities for students to develop."},
            {"heading": "Learning beyond lessons", "body": "Sports, music, fine arts, literature, cultural activities and collaborative projects complement classroom learning and give students opportunities to discover interests and build confidence."},
            {"heading": "Service & responsibility", "body": "CMS campus information describes initiatives such as the Junior Youth Empowerment Programme and “Each One–Teach One”, alongside environmental responsibility and community service activities."},
            {"heading": "A supportive environment", "body": "The campus profile presents student development as a shared effort involving teachers, school leaders, counsellors, co-curricular teams and families."}
        ],
        "source": "CMS Aliganj Campus I official website"
    },
    "education-impact": {
        "title": "Education Impact",
        "eyebrow": "VALUES IN ACTION",
        "intro": "CMS connects education with peace, global understanding, universal values and service to the wider community.",
        "sections": [
            {"heading": "Peace education", "body": "CMS places emphasis on peace education, interfaith understanding and human unity. The school reports receiving the UNESCO Prize for Peace Education in 2002."},
            {"heading": "Global citizenship", "body": "The school-wide vision encourages students to understand global issues, respect different perspectives and see themselves as responsible members of a shared world."},
            {"heading": "Community initiatives", "body": "Official campus information describes student participation in social service, peer mentoring, environmental initiatives, water and energy conservation and animal care."},
            {"heading": "Learning through action", "body": "These opportunities connect classroom knowledge with practical responsibility, helping students consider how their choices can contribute to their communities."}
        ],
        "source": "CMS official About Us and Aliganj Campus I pages"
    },
    "our-founders": {
        "title": "Our Founders",
        "eyebrow": "THE FOUNDING VISION",
        "intro": "City Montessori School was founded in Lucknow in 1959 by Dr Jagdish Gandhi and Dr Bharti Gandhi, beginning with five children.",
        "sections": [
            {"heading": "A vision rooted in peace", "body": "Inspired by the ideals of Mahatma Gandhi and Sant Vinoba Bhave, the founders emphasised peace, human unity, values-based education and service to humanity."},
            {"heading": "Jai Jagat", "body": "The CMS motto, “Jai Jagat”, expresses a universal outlook that reaches beyond borders and encourages students to think about the wellbeing of all people."},
            {"heading": "The world is one family", "body": "The idea of “Vasudhaiva Kutumbakam” — the world is one family — is central to the school's stated vision of mutual respect, understanding and shared responsibility."},
            {"heading": "A continuing legacy", "body": "The founding vision continues through CMS's emphasis on peace education, character, global citizenship and preparing young people to contribute thoughtfully to society."}
        ],
        "source": "CMS official About Us and CMS Founders pages"
    },
    "management": {
        "title": "CMS Management",
        "eyebrow": "LEADERSHIP & CAMPUS TEAMS",
        "intro": "CMS's published information describes a school community supported by central leadership, campus principals, teachers and administrative teams.",
        "sections": [
            {"heading": "School leadership", "body": "CMS publishes information about its management and leadership structure, including senior leadership and campus-level responsibilities."},
            {"heading": "Aliganj Campus I leadership", "body": "The official Aliganj Campus I website identifies Mrs Shivani Singh as Principal and Ms Lovey Khan as Vice-Principal."},
            {"heading": "Teaching & student support", "body": "Teaching and support teams work across Pre-Primary, Primary, Junior, Senior and Cambridge sections, helping coordinate academic and co-curricular learning."},
            {"heading": "A connected school community", "body": "Campus councils, teachers, counsellors and administrative staff contribute to the day-to-day environment in which students learn and participate."}
        ],
        "source": "CMS Aliganj Campus I official website"
    }
}


@app.get("/campus/<slug>")
def campus_information_page(slug):
    page = CAMPUS_INFORMATION_PAGES.get(slug)
    if page is None:
        abort(404)
    return render_template("campus_detail.html", page=page)


@app.get("/about")
def about_page():
    return render_template("about.html")


@app.get("/contact")
def contact_page():
    return render_template("contact.html")


@app.get("/portal")
def school_portal():
    return render_template("portal.html")


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
    payload = request.get_json(silent=True) or {}
    message = str(payload.get("message", "")).strip()
    page_context = str(payload.get("page_context", "")).lower().strip()
    if not message:
        return answer("Please enter a question.")
    data = get_data()
    q = " ".join(message.lower().replace("?", " ").replace("!", " ").split())
    # Lightweight query normalisation; the official knowledge files remain read-only.
    typo_aliases = {"schdelue": "schedule", "scheduele": "schedule", "schedual": "schedule", "technovae": "technova", "celestae": "celesta", "kb": "when", "kab": "when", "kahan": "where", "kaha": "where", "kidhar": "where", "kya": "what", "batao": "tell", "btao": "tell", "dikhao": "show"}
    q = " ".join(typo_aliases.get(word, word) for word in q.split())
    # Use the active event page as context only for short, ambiguous follow-ups.
    has_named_event = any(name in q for name in ("technova", "celesta", "nazakat", "cmsmun", "cms mun", "model united nations"))
    if not has_named_event and page_context in ("/technova", "/celesta", "/cmsmun"):
        context_name = {"/technova": "technova", "/celesta": "celesta", "/cmsmun": "cmsmun"}[page_context]
        if re.search(r"\b(what is it|what is this|tell me about it|explain it)\b", q):
            q += " what is " + context_name
        elif any(term in q for term in ("schedule", "date", "when", "venue", "where", "this event", "the event", "timing")) or re.search(r"\b(it|this|that|there)\b", q):
            q += " " + context_name
    events = data.get("events", [])
    teachers = data.get("teachers", [])
    celesta = get_cultural_data()
    celesta_events = celesta.get("events", [])
    # On the TECHNOVA page, a vague venue question should show the source-listed venues
    # rather than guessing which competition the visitor means.
    named_technova_competition = any(e.get("name", "").lower() in q for e in events)
    if page_context == "/technova" and re.search(r"\b(where|venue|location)\b", q) and not named_technova_competition:
        return answer("TECHNOVA competitions use different venues. Which competition are you looking for? Here are the venues listed in the official event data:", ["Competition", "Venue"], [[e["name"], e["venue"]] for e in events])
    # CMS Aliganj Campus I contact directory (details supplied for this site).
    aliganj_contact_terms = ("contact us", "cms contact", "cms contacts", "aliganj contact", "aliganj contacts", "aliganj campus contact", "campus phone", "cms phone", "school phone", "cms mobile", "cms email", "aliganj email", "calling hours", "calling time", "info@cmseducation.org", "aliganj1@cmseducation.org", "96484 29071", "2320897", "phone number", "contact details")
    if any(term in q for term in aliganj_contact_terms) or q in ("contact", "phone", "mobile", "email", "call", "calling hours"):
        return answer("Official contact details listed for CMS Aliganj Campus I:", ["Contact", "Details"], [["Campus", "CMS Aliganj Campus I"], ["Phone", "+91 522 2320897"], ["Mobile", "+91 96484 29071"], ["General email", "info@cmseducation.org"], ["Aliganj campus email", "aliganj1@cmseducation.org"], ["Calling hours", "8:30 AM to 5:00 PM"], ["Contact page", "https://chatbot-19fg.onrender.com/contact"]])
    # Route questions about the homepage's complete event taxonomy.
    if any(term in q for term in ("all events", "list of events", "event list", "show events", "what events", "which events", "events on the portal", "categories", "event categories")):
        return answer("Here are the main sections currently featured on the CMS Events portal:", ["Category", "Events / information"], [["Academic Achievements", "ICSE, ISC, JEE Advanced and AP Examination 2026 results"], ["Academic Events", "CMSMUN 5th Edition · 2026 archive"], ["Sports Events", "SPARDHA 2026 and CONCORD 2026"], ["Cultural Events", "CELESTA International 2026 and its brochure competitions"], ["Technology & Innovation", "TECHNOVA 2026 competitions, schedule, updates and results"]])
    if any(term in q for term in ("academic events", "academic event")):
        return answer("The Academic Events section features CMSMUN 5th Edition, hosted by CMS Aliganj Campus I on 24–25 April 2026. It is a completed 2026 archive with committee agendas and delegate information.", ["Event", "Details"], [["CMSMUN 5th Edition", "24–25 April 2026 · CMS Aliganj Campus I · Completed archive"], ["Page", "Open Academic Events → CMSMUN on the CMS Events homepage"]])
    # CMSMUN 5th Edition — details transcribed from the 24-page Aliganj Campus I brochure.
    mun_terms = ("cmsmun", "cms mun", "model united nations", "mun conference", "mun 2026", "lok sabha", "unga", "un general assembly", "united nations general assembly", "unsc", "security council", "organization of american states", "oas", "house committee", "oversight and government reform", "iaea", "atomic energy agency", "copuos", "peaceful uses of outer space", "international court of justice", "icj", "international press", "peru crisis", "moquegua", "cms aliganj mun")
    if any(term in q for term in mun_terms):
        committees = [
            ["Lok Sabha", "India’s approach to regulation and oversight in hate speech and media trials; reviewing India’s federal structure and state autonomy."],
            ["United Nations General Assembly (UNGA)", "Strengthening and advancing the global framework for arms control, disarmament and non-proliferation treaties."],
            ["United Nations Security Council (UNSC)", "The situation in Central Africa; reviewing regional strategy to combat the Lord’s Resistance Army and the repatriation of former combatants."],
            ["Organization of American States (OAS)", "Strengthening multilateral security cooperation to combat transnational narcotics networks and organised crime in Latin America."],
            ["U.S. House Committee on Oversight and Government Reform", "Legislative reform and intelligence accountability following the 2013 NSA surveillance disclosures."],
            ["International Atomic Energy Agency (IAEA)", "Long-term international safety oversight at the Chernobyl Nuclear Power Plant and the New Safe Confinement."],
            ["Emergency Council of Advisors — Republic of Peru", "A simulated emergency session addressing the aftermath of the Moquegua explosion and escalating geopolitical tension; the brochure gives a freeze date of 3 May 2043."],
            ["Committee on the Peaceful Uses of Outer Space (COPUOS)", "Reviewing and advancing the Space 2030 Agenda for sustainable and equitable use of outer space."],
            ["International Court of Justice (ICJ)", "Jadhav (India v. Pakistan), General List No. 168; freeze date 8 May 2017."],
            ["International Press", "Journalism, photography and caricature, reporting on conference proceedings and debate."]
        ]
        if any(term in q for term in ("committee", "committees", "agenda", "agendas", "topics", "topic", "portfolio", "council", "press", "journalism", "photography", "caricature", "copuos", "iaea", "lok sabha", "unga", "unsc", "oas", "icj", "peru", "moquegua", "chernobyl", "arms control", "central africa", "narcotics", "surveillance", "jadhav", "outer space")):
            aliases_by_committee = {
                "United Nations General Assembly (UNGA)": ("unga", "un general assembly"),
                "United Nations Security Council (UNSC)": ("unsc", "security council"),
                "Organization of American States (OAS)": ("oas", "american states"),
                "U.S. House Committee on Oversight and Government Reform": ("house committee", "oversight", "nsa"),
                "International Atomic Energy Agency (IAEA)": ("iaea", "chernobyl", "atomic energy"),
                "Emergency Council of Advisors — Republic of Peru": ("peru", "moquegua"),
                "Committee on the Peaceful Uses of Outer Space (COPUOS)": ("copuos", "outer space"),
                "International Court of Justice (ICJ)": ("icj", "jadhav"),
                "International Press": ("press", "journalism", "photography", "caricature")
            }
            selected = None
            for row in committees:
                if row[0].lower() in q or any(alias in q for alias in aliases_by_committee.get(row[0], ())):
                    selected = row
                    break
            if selected:
                return answer("CMSMUN brochure agenda:", ["Committee / forum", "Agenda"], [selected])
            return answer("Committees and forums listed in the CMSMUN 5th Edition brochure:", ["Committee / forum", "Agenda"], committees)
        if any(term in q for term in ("date", "when", "venue", "where", "campus", "edition", "fifth", "5th", "about", "what is", "overview", "registration", "register", "fee", "fees", "eligibility", "age", "contact", "email", "phone", "guideline", "guidelines")):
            return answer("CMS Model United Nations 2026 was the 5th Edition, organised by City Montessori School, Aliganj Campus I. The brochure cover lists 24–25 April; the conference is now a past event. Registration and fee information below is historical brochure information, not an active offer.", ["Detail", "Brochure information"], [["Event", "CMS Model United Nations 2026 · 5th Edition"], ["Dates", "24–25 April 2026"], ["Host", "CMS Aliganj Campus I, Sector O, Aliganj, Lucknow, India"], ["Eligibility", "Grades 8–12; brochure states ages 13–19"], ["School delegation", "At least 8 students"], ["Registration fee", "INR 2,700 per participant (Lucknow delegates and outstation delegates not opting for accommodation); INR 3,500 for outstation delegates opting for accommodation"], ["Accommodation", "Brochure says accommodation included all meals on both conference days and dinner at the CISV/KAIZEN Guest House, CMS Kanpur Road"], ["Status", "Completed · 2026 archive"], ["Registration link printed in brochure", "https://linktr.ee/cmsagmun2026 (historical; availability not verified)"], ["Contact email", "mun.aliganj1@cmseducation.org"], ["Conference phone", "+91 522-2320897"]])
        return answer("CMSMUN 2026 was the 5th Edition of the Model United Nations conference hosted by CMS Aliganj Campus I on 24–25 April 2026. Ask me about its committees, agendas, eligibility or brochure details.")
    if any(term in q for term in ("celesta", "nazakat", "cultural event", "cultural competition", "folk dance", "choreography", "orchestra", "choir", "crescendo", "harmonic clash", "mix media", "painting", "timeless frames", "through my lens", "3d collage", "photography", "videography")):
        # Competition aliases make brochure details available for every listed category.
        # Keep generic festival questions ("What is CELESTA?") separate from individual entries.
        competition_aliases = {
            "Art and Painting": ("art and painting", "painting competition", "the world i want to see"),
            "Mix Media Art": ("mix media art", "mixed media art", "mix media", "mixed media", "ways to wonder art"),
            "Choreography": ("choreography", "expressions of life"),
            "Traditional Folk Dance": ("traditional folk dance", "folk dance", "rhythm roots"),
            "Orchestra": ("orchestra", "symphony ensemble"),
            "Choir": ("choir", "from darkness to light"),
            "Harmonic Clash": ("harmonic clash", "jingle making", "jingle competition"),
            "Crescendo (ABRSM)": ("crescendo", "abrsm", "solo singing"),
            "Celesta’s Timeless Frames": ("timeless frames", "photography", "photo competition"),
            "Celesta Through My Lens": ("through my lens", "videography", "video submission", "video competition"),
            "3D Collage": ("3d collage", "3-d collage", "three dimensional collage")
        }
        matched_celesta = None
        for e in celesta_events:
            aliases = competition_aliases.get(e["name"], ())
            if any(alias in q for alias in aliases):
                matched_celesta = e
                break
        if matched_celesta:
            e = matched_celesta
            return answer(f"Brochure details for {e['name']}:", ["Detail", "Information"], [["Topic", e["topic"]], ["Type", e["type"]], ["Duration / deadline", e["duration"]], ["Rules and overview", e["summary"]], ["Evaluation parameters", e["criteria"]]])
        if any(term in q for term in ("date", "when", "schedule", "programme", "program", "timing")):
            return answer("CELESTA International 2026 dates and programme note:", ["Item", "Information"], [["Festival dates on cover", celesta.get("dates", "Not specified")], ["Programme date note", celesta.get("status_note", "")], ["Schedule", "21–25 August 2026; see the brochure programme for day-wise events."]])
        if any(term in q for term in ("what is", "tell me about", "about celesta", "explain", "overview", "describe")) or "celesta" in q or "nazakat" in q:
            return answer(f"{celesta.get('title', 'CELESTA')} is a cultural festival celebrating student creativity and performance. It brings together the competitions listed below. The brochure's competition-specific rules and evaluation details are available by asking about an individual competition.", ["Competition", "Format", "Topic", "Duration / deadline"], [[e["name"], e["type"], e["topic"], e["duration"]] for e in celesta_events])
        rows = [[e["name"], e["type"], e["topic"], e["duration"]] for e in celesta_events]
        return answer(f"{celesta.get('title', 'CELESTA')} cultural competitions from the brochure:", ["Competition", "Format", "Topic", "Duration / deadline"], rows)
    # Individual CMS Academic Achiever lookup — entries shown on the Academic Results page.
    achievers = [
        ("ICSE 2026", "Vaivaswat Narayan Dubey", "Gomti Nagar I", "99.8% · AIR 1"),
        ("ICSE 2026", "Zahra Fatima", "Asharfabad", "99.6% · AIR 2"),
        ("ICSE 2026", "Anay Agarwal", "Gomti Nagar I", "99.6% · AIR 2"),
        ("ICSE 2026", "Afshaan Ahmad", "Gomti Nagar I", "99.4% · AIR 3"),
        ("ICSE 2026", "Divyansh Kushwaha", "Gomti Nagar I", "99.4% · AIR 3"),
        ("ICSE 2026", "Farheen Khan", "Rajajipuram I", "99.4% · AIR 3"),
        ("ICSE 2026", "Prashasti Agrawal", "Gomti Nagar I", "99.2% · AIR 4"),
        ("ICSE 2026", "Divyansh Pandey", "Kanpur Road", "99.2% · AIR 4"),
        ("ICSE 2026", "Muaz Siddiqui", "Mahanagar", "99.2% · AIR 4"),
        ("ICSE 2026", "Yuvraj Singh", "Mahanagar", "99.2% · AIR 4"),
        ("ICSE 2026", "Samarth Tayal", "Rajajipuram I", "99.2% · AIR 4"),
        ("ICSE 2026", "Suyash Tripathi", "Rajajipuram I", "99.2% · AIR 4"),
        ("ICSE 2026", "Peehu Verma", "Aliganj I", "99% · AIR 5"),
        ("ICSE 2026", "Tejas Singh", "Aliganj I", "99% · AIR 5"),
        ("ICSE 2026", "Prakhya Yadav", "Gomti Nagar Ext", "99% · AIR 5"),
        ("ICSE 2026", "Arsh Singhal", "Gomti Nagar I", "99% · AIR 5"),
        ("ICSE 2026", "Kush Sharma", "Gomti Nagar I", "99% · AIR 5"),
        ("ICSE 2026", "Manya Singh", "Gomti Nagar I", "99% · AIR 5"),
        ("ICSE 2026", "Mishti Bisaria", "Gomti Nagar I", "99% · AIR 5"),
        ("ICSE 2026", "Animesh Singh", "Rajajipuram I", "99% · AIR 5"),
        ("ISC 2026", "Zainab Fatima", "Aliganj I", "99.75% · AIR 2"),
        ("ISC 2026", "Sanskriti Chandel", "Gomti Nagar I", "99.75% · AIR 2"),
        ("ISC 2026", "Chhavi Mishra", "Kanpur Road", "99.75% · AIR 2"),
        ("ISC 2026", "Osheen Agarwal", "Mahanagar", "99.75% · AIR 2"),
        ("ISC 2026", "Arya Dwivedi", "Aliganj I", "99.5% · AIR 3"),
        ("ISC 2026", "Bhanu Prakash Verma", "Aliganj I", "99.5% · AIR 3"),
        ("ISC 2026", "Shivpriya Pathak", "Gomti Nagar Ext", "99.5% · AIR 3"),
        ("ISC 2026", "Aditya Tripathi", "Gomti Nagar I", "99.5% · AIR 3"),
        ("ISC 2026", "Advit Dhaon", "Gomti Nagar I", "99.5% · AIR 3"),
        ("ISC 2026", "Aarna Bajpai", "Kanpur Road", "99.5% · AIR 3"),
        ("ISC 2026", "Sonya Arora", "Kanpur Road", "99.5% · AIR 3"),
        ("ISC 2026", "Hansika Jaggi", "Rajajipuram I", "99.5% · AIR 3"),
        ("ISC 2026", "Vailace", "RDSO", "99.5% · AIR 3"),
        ("ISC 2026", "Siddharth Karan", "Aliganj I", "99.25% · AIR 4"),
        ("ISC 2026", "Arikta Singh", "Gomti Nagar I", "99.25% · AIR 4"),
        ("ISC 2026", "Arjun Agarwal", "Gomti Nagar I", "99.25% · AIR 4"),
        ("ISC 2026", "Dhruv Bajpai", "Gomti Nagar I", "99.25% · AIR 4"),
        ("ISC 2026", "Kopal Saxena", "Gomti Nagar I", "99.25% · AIR 4"),
        ("ISC 2026", "Radhika Agrawal", "Gomti Nagar I", "99.25% · AIR 4"),
        ("ISC 2026", "Rishi Raj Shukla", "Gomti Nagar I", "99.25% · AIR 4"),
        ("ISC 2026", "Sandarbh Mishra", "Gomti Nagar I", "99.25% · AIR 4"),
        ("ISC 2026", "Shrot Garg", "Gomti Nagar I", "99.25% · AIR 4"),
        ("ISC 2026", "Utkarsh Singh", "Gomti Nagar I", "99.25% · AIR 4"),
        ("ISC 2026", "Vibhor Srivastava", "Gomti Nagar I", "99.25% · AIR 4"),
        ("ISC 2026", "Pranjal Pandey", "Mahanagar", "99.25% · AIR 4"),
        ("ISC 2026", "Avya Dubey", "Rajajipuram I", "99.25% · AIR 4"),
        ("ISC 2026", "Pranav Upadhyay", "Rajajipuram I", "99.25% · AIR 4"),
        ("ISC 2026", "Shaurya Agarwal", "Station Road", "99.25% · AIR 4"),
        ("ISC 2026", "Kaavya Bisht", "Anand Nagar", "99% · AIR 5"),
        ("ISC 2026", "Aleeya Fatima", "Asharfabad", "99% · AIR 5"),
        ("ISC 2026", "Ashutosh Pratap Singh", "Gomti Nagar I", "99% · AIR 5"),
        ("ISC 2026", "Rishith Raj Raizada", "Gomti Nagar I", "99% · AIR 5"),
        ("ISC 2026", "Utkarsh Singh", "Gomti Nagar I", "99% · AIR 5"),
        ("ISC 2026", "Varalika Yadav", "Gomti Nagar I", "99% · AIR 5"),
        ("ISC 2026", "Vinamra Tandon", "Gomti Nagar I", "99% · AIR 5"),
        ("ISC 2026", "Vallabhi Agnihotri", "Kanpur Road", "99% · AIR 5"),
        ("ISC 2026", "Vidisha Singh", "Mahanagar", "99% · AIR 5"),
        ("ISC 2026", "Vipin Yadav", "Mahanagar", "99% · AIR 5"),
        ("ISC 2026", "Yahvi Mohan", "Mahanagar", "99% · AIR 5"),
        ("ISC 2026", "Shakti Malhotra", "Rajajipuram I", "99% · AIR 5"),
        ("ISC 2026", "Yashraj Rawat", "Rajajipuram I", "99% · AIR 5"),
        ("ISC 2026", "Aadya Yadav", "Rajendra Nagar I", "99% · AIR 5"),
        ("JEE Advanced 2026", "Arjun Agarwal", "Gomti Nagar I", "Open Category Rank 2802"),
        ("JEE Advanced 2026", "Sakshya Vansh", "Rajendra Nagar I", "Open Category Rank 2916"),
        ("JEE Advanced 2026", "Ashutosh Pratap Singh", "Gomti Nagar I", "Open Category Rank 2927"),
        ("JEE Advanced 2026", "Bhanu Prakash Verma", "Aliganj I", "Open Category Rank 2948"),
        ("JEE Advanced 2026", "Nitant Tripathi", "Rajendra Nagar I", "Open Category Rank 4876"),
        ("JEE Advanced 2026", "Aarush Kumar", "Kanpur Road", "Open Rank 5160 · Reserved Rank 1123"),
        ("JEE Advanced 2026", "Rishith Raizada", "Gomti Nagar I", "Open Category Rank 5670"),
        ("JEE Advanced 2026", "Abhyudaya Sarthak", "Aliganj I", "Open Category Rank 6143"),
        ("JEE Advanced 2026", "Abhinav Singh", "Gomti Nagar I", "Open Rank 6146 · Reserved Rank 1375"),
        ("JEE Advanced 2026", "Aditya Singh", "Gomti Nagar I", "Open Category Rank 6698"),
        ("JEE Advanced 2026", "Anuj Jain", "Rajendra Nagar I", "Open Category Rank 6968"),
        ("JEE Advanced 2026", "Tejas Raj", "Kanpur Road", "Open Rank 7093 · Reserved Rank 1610"),
        ("JEE Advanced 2026", "Shikhar Kumar Singh", "Gomti Nagar Extension", "Open Rank 7361 · Reserved Rank 174"),
        ("JEE Advanced 2026", "Divyansh Mahajan", "Gomti Nagar I", "Open Category Rank 7692"),
        ("JEE Advanced 2026", "Pranav Upadhyay", "Rajajipuram I", "Open Category Rank 7854"),
        ("JEE Advanced 2026", "Mohd. Saim Sultan", "Chowk", "Open Rank 8788 · Reserved Rank 2089"),
        ("JEE Advanced 2026", "Siddhima Shukla", "Kanpur Road", "Open Category Rank 8968"),
        ("JEE Advanced 2026", "Arnav Singh", "Gomti Nagar I", "Open Category Rank 9771"),
        ("JEE Advanced 2026", "Deepak Singh", "Kanpur Road", "Reserved Category Rank 283"),
        ("JEE Advanced 2026", "Shaurya Mani Choudhary", "Kanpur Road", "Reserved Category Rank 929"),
        ("JEE Advanced 2026", "Siddhant Singh", "Mahanagar", "Reserved Category Rank 1690"),
        ("JEE Advanced 2026", "Kushagra Singh", "Kanpur Road", "Reserved Category Rank 1890"),
        ("JEE Advanced 2026", "Aryan Azad", "Kanpur Road", "Reserved Category Rank 2252"),
        ("JEE Advanced 2026", "Ayush Verma", "Rajajipuram I", "Reserved Category Rank 2517"),
        ("JEE Advanced 2026", "Aditya Rajput", "Mahanagar", "Reserved Category Rank 3482"),
        ("JEE Advanced 2026", "Aryan Chaudhary", "Mahanagar", "Reserved Category Rank 3552"),
        ("JEE Advanced 2026", "Suyash Gautam", "Rajajipuram I", "Reserved Category Rank 3906"),
        ("JEE Advanced 2026", "Kartikey Dhiman", "Rajendra Nagar I", "Reserved Category Rank 4545"),
        ("JEE Advanced 2026", "Utsav Yadav", "Gomti Nagar Extension", "Reserved Category Rank 4924"),
        ("JEE Advanced 2026", "Yash Yadav", "RDSO", "Reserved Category Rank 5051"),
        ("JEE Advanced 2026", "Abhigyan Chaudhary", "Rajajipuram I", "Reserved Category Rank 6421"),
        ("JEE Advanced 2026", "Aadi Singh", "Mahanagar", "Reserved Category Rank 7165"),
        ("JEE Advanced 2026", "Mohd. Faraz", "Rajajipuram I", "Reserved Category Rank 7938"),
        ("JEE Advanced 2026", "Rohi Sachan", "Kanpur Road", "Reserved Category Rank 7949"),
        ("JEE Advanced 2026", "Amarjot Singh", "RDSO", "Reserved Category Rank 8651"),
        ("AP 2026", "Akshaj Kumar", "Gomti Nagar I", "Computer Science A 5/5 · Physics 1 5/5"),
        ("AP 2026", "Soham Agarwal", "Gomti Nagar I", "Calculus AB 5/5 · Computer Science A 4/5 · Physics C: Mechanics 4/5"),
        ("AP 2026", "Khyati Verma", "Rajajipuram I", "Precalculus 5/5 · World History: Modern 4/5"),
        ("AP 2026", "Arundhati Singh Dagur", "Aliganj I", "Macroeconomics 4/5 · Comparative Government & Politics 4/5 · Human Geography 4/5"),
        ("AP 2026", "Kopal Ali", "Not specified", "5/5 perfect-score achiever"),
        ("AP 2026", "Pranav Mittal", "Not specified", "5/5 perfect-score achiever"),
        ("AP 2026", "Advay Jain", "Not specified", "5/5 perfect-score achiever"),
        ("AP 2026", "Krutika P. Javalkar", "Not specified", "5/5 perfect-score achiever"),
        ("AP 2026", "Rishabh Sukhwani", "Not specified", "5/5 perfect-score achiever"),
        ("AP 2026", "Ananya Sharma", "Not specified", "5/5 perfect-score achiever"),
        ("AP 2026", "Yuvraj Singh", "Not specified", "5/5 perfect-score achiever"),
        ("AP 2026", "Achintya Kushwaha", "Not specified", "5/5 perfect-score achiever"),
        ("AP 2026", "Atharva Sachan", "Not specified", "5/5 perfect-score achiever"),
        ("AP 2026", "Abhigyan Tripathi", "Not specified", "4/5 high-score achiever"),
        ("AP 2026", "Shourya Kaushik", "Not specified", "4/5 high-score achiever"),
        ("AP 2026", "Akshay Mishra", "Not specified", "4/5 high-score achiever"),
        ("AP 2026", "Tejaswi Kanaujia", "Not specified", "4/5 high-score achiever"),
        ("AP 2026", "Aditya Pandey", "Not specified", "4/5 high-score achiever"),
        ("AP 2026", "Neha Rai", "Not specified", "4/5 high-score achiever"),
        ("AP 2026", "Sushant Shukla", "Not specified", "4/5 high-score achiever"),
        ("AP 2026", "Abhijeet Mukherji", "Not specified", "4/5 high-score achiever"),
    ]
    def normalise_person_name(value):
        return " ".join(re.sub(r"[^a-z0-9 ]", " ", value.lower()).split())
    matched_achiever = next((row for row in achievers if normalise_person_name(row[1]) in normalise_person_name(q)), None)
    if matched_achiever:
        exam, student, campus, achievement = matched_achiever
        return answer(f"Yes — {student} is listed among CMS Academic Achievers for {exam}.", ["Detail", "Published information"], [["Student", student], ["Examination", exam], ["Campus", campus], ["Achievement", achievement], ["Source", "Academic Achievements page on CMS Events"]])
    if any(term in q for term in ("academic result", "academic results", "board result", "board results", "icse", "isc", "jee advanced", "jee result", "ap exam", "ap examination", "class 10 result", "class 12 result", "school result", "school results", "exam result", "exam results", "student achievement", "academic achievement", "vaivaswat", "zainab fatima", "akshaj kumar", "soham agarwal", "khyati verma", "arundhati")):
        if "jee" in q:
            return answer("CMS reports 58 qualifiers in JEE (Advanced) 2026. The official announcement publishes Open Category and Reserved Category ranks, not individual marks. The Academic Results page contains the featured rank tables, with the two rank categories kept separate.", ["Item", "Information"], [["Qualifiers", "58 CMS students"], ["Open Category", "Separate rank list"], ["Reserved Category", "Separate rank list"], ["Marks", "Not published in the CMS announcement"], ["Full tables", "Open Academic Results on the CMS Events portal"]])
        if "ap" in q or any(name in q for name in ("akshaj", "soham", "khyati", "arundhati")):
            return answer("CMS AP Examinations 2026: 44 students appeared, earning 184 credits across 15 subjects, with 13 perfect scores of 5/5 and 14 scores of 4/5. Featured achievers: Akshaj Kumar (Computer Science A 5/5; Physics 1 5/5); Soham Agarwal (Calculus AB 5/5; Computer Science A 4/5; Physics C: Mechanics 4/5); Khyati Verma (Precalculus 5/5; World History: Modern 4/5); Arundhati Singh Dagur (three 4/5 scores: Macroeconomics, Comparative Government & Politics, Human Geography). Other named 5/5 achievers: Kopal Ali, Pranav Mittal, Advay Jain, Krutika P. Javalkar, Rishabh Sukhwani, Ananya Sharma, Yuvraj Singh, Achintya Kushwaha and Atharva Sachan. Other named 4/5 achievers: Abhigyan Tripathi, Shourya Kaushik, Akshay Mishra, Tejaswi Kanaujia, Aditya Pandey, Neha Rai, Sushant Shukla and Abhijeet Mukherji.", ["AP 2026", "Published results"], [["Appeared", "44 students"], ["Credits", "184 across 15 subjects"], ["Perfect scores", "13 × 5/5"], ["Other top scores", "14 × 4/5"]])
        return answer("CMS Board Results 2026: ICSE Class 10 featured AIR 1 Vaivaswat Narayan Dubey (99.8%). ISC Class 12 featured four AIR 2 achievers at 99.75%: Zainab Fatima, Sanskriti Chandel, Chhavi Mishra and Osheen Agarwal. The Academic Results page contains the separate ICSE and ISC top-five rank tables with names, campuses, percentages and AIRs.", ["Exam", "Top achievement"], [["ICSE Class 10", "Vaivaswat Narayan Dubey — 99.8%, AIR 1"], ["ISC Class 12", "Zainab Fatima; Sanskriti Chandel; Chhavi Mishra; Osheen Agarwal — 99.75%, AIR 2"], ["Further achievers", "See the separate ICSE and ISC tables on the Academic Results page"]])
    sports_terms = ("spardha", "concord", "sports event", "sports events", "cms sports", "sports at cms", "international sports olympiad", "track and field", "judo", "karate", "badminton", "dance aerobics", "poster making", "football tournament", "sports offered", "what sports", "which sports", "sports list", "sports in cms", "games at cms", "list of sports", "athletics", "roller skating", "table tennis", "basketball", "swimming", "hockey", "cricket", "chess")
    if any(term in q for term in sports_terms):
        if any(term in q for term in ("concord", "football tournament", "international football")):
            return answer("CONCORD 2026 was CMS’s international football tournament, held 2–6 November 2026 at CMS Station Road Campus. It featured boys’ and girls’ matches and is now a completed event.", ["Detail", "Information"], [["Event", "CONCORD 2026"], ["Dates", "2–6 November 2026"], ["Venue", "CMS Station Road Campus"], ["Format", "International football tournament with boys’ and girls’ matches"], ["Status", "Completed · 2026"], ["Official website", "https://cmseducation.org/concord/"]])
        if any(term in q for term in ("spardha", "international sports olympiad", "track and field", "judo", "karate", "dance aerobics", "poster making")):
            return answer("SPARDHA 2026 was CMS’s international sports olympiad, held 24–27 October 2026 at CMS RDSO Campus. The listed programme included sports as well as creative movement and poster-making activities. It is now a completed event.", ["Detail", "Information"], [["Event", "SPARDHA 2026"], ["Dates", "24–27 October 2026"], ["Venue", "CMS RDSO Campus"], ["Listed disciplines", "Track & Field; Judo; Karate; Badminton; Move & Groove – Dance Aerobics; Brush & Beyond – Poster Making"], ["Status", "Completed · 2026"], ["Official website", "https://cmseducation.org/spardha/"]])
        return answer("CMS Sports Events include SPARDHA and CONCORD. SPARDHA 2026 (24–27 October, CMS RDSO Campus) was an international sports olympiad. CONCORD 2026 (2–6 November, CMS Station Road Campus) was an international football tournament. Both are completed. CMS sports offerings listed in the school information include Badminton, Basketball, Cricket, Chess, Swimming, Hockey, Athletics, Football, Roller Skating and Table Tennis.", ["CMS sports offerings", "International event"], [["Badminton", "SPARDHA 2026"], ["Basketball", "Sports offered at CMS"], ["Cricket", "Sports offered at CMS"], ["Chess", "Sports offered at CMS"], ["Swimming", "Sports offered at CMS"], ["Hockey", "Sports offered at CMS"], ["Athletics", "Sports offered at CMS"], ["Football", "CONCORD 2026 and sports offered at CMS"], ["Roller Skating", "Sports offered at CMS"], ["Table Tennis", "Sports offered at CMS"]])
    if q in ("jai jagat", "जय जगत"):
        return answer("Jai Jagat!")
    if q in ("hello", "hi", "hey", "good morning", "good afternoon", "good evening") or q.startswith(("hello ", "hi ", "hey ")):
        return answer("Hi! I’m the CMS Events Chatbot. Feel free to ask me anything about CMS events, competitions, schedules, teachers, and registrations.")
    # TECHNOVA is the current featured event (19–20 November 2026).
    technova_about_terms = ("what is technova", "what's technova", "tell me about technova", "about technova", "explain technova", "technova overview", "ongoing event", "current event", "which event is ongoing", "which event is happening", "event happening now", "is technova happening", "technova status", "technova update")
    if any(term in q for term in technova_about_terms) or q in ("technova", "technova 2026", "current event at cms"):
        return answer(
            "TECHNOVA 2026 is the ongoing Robotics & Artificial Intelligence Championship hosted by City Montessori School, Aliganj-I, on 19–20 November 2026. The event brings together robotics, AI, computing and innovation competitions. The AI & Robotics Quiz Challenge is scheduled for 19 November; the remaining listed competitions are scheduled for 20 November. Registration closed on 16 November. Exact reporting times and individual slots are not listed in the available schedule, so participants should confirm them with the event team.",
            ["Detail", "Current information"],
            [["Event", "TECHNOVA 2026 — Robotics & Artificial Intelligence Championship"], ["Host", "City Montessori School, Aliganj-I"], ["Dates", "19–20 November 2026"], ["Status", "Ongoing · 19 November 2026"], ["Today · 19 November", "AI & Robotics Quiz Challenge — Computer / AI Lab — Ms. Manju Rawat"], ["Tomorrow · 20 November", "Robo Soccer, Line Follower, Obstacle Race, Robo War (Balloon Bust), Boat Race (Senior), AI Model Development, Computer Vision, NLP, Game Development and AI Innovation Showdown"], ["Registration", "Closed · deadline was 16 November 2026"], ["Schedule note", "Individual reporting times and slots are not listed; confirm with the event team"], ["Event page", "https://chatbot-19fg.onrender.com/technova"]]
        )
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
    return answer("Sorry, I could not currently find that information in the CMS Events. Please contact the respective coordinators for the same.")


@app.errorhandler(413)
def too_large(_error):
    return "Upload too large. Maximum file size is 8 MB.", 413


@app.errorhandler(SupabaseError)
def cloud_error(_error):
    return "The cloud data service is temporarily unavailable. Please try again shortly.", 503


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
