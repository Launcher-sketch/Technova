from flask import Flask, jsonify, render_template, request
import json
from pathlib import Path

app = Flask(__name__)
DATA_FILE = Path(__file__).parent / "data" / "technova.json"

def get_data():
    return json.loads(DATA_FILE.read_text(encoding="utf-8"))

def answer(reply, headers=None, rows=None):
    result = {"reply": reply}
    if headers is not None and rows is not None:
        result["table"] = {"headers": headers, "rows": rows}
    return jsonify(result)

@app.get("/")
def home():
    return render_template("home.html")

@app.get("/technova")
def technova():
    return render_template("index.html", data=get_data())

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

    greetings = ("hello", "hi", "hey", "good morning", "good afternoon", "good evening")
    if q in greetings or q.startswith(("hello ", "hi ", "hey ")):
        return answer("Hi! I’m the CMS Events Chatbot. Feel free to ask me anything about CMS events, competitions, schedules, teachers, and registrations.")

    # Show complete event directory in a readable table.
    if any(term in q for term in ("all events", "list of events", "event list", "competitions", "competition list", "show events", "what events", "which events")):
        rows = [[e["name"], e["category"], e["date"], e["teacher"], e["venue"]] for e in events]
        return answer(f"Here are all {len(events)} TECHNOVA 2026 competitions listed in the available data:", ["Event", "Category", "Date", "Teacher in-charge", "Venue"], rows)

    # Teacher directory.
    if any(term in q for term in ("all teachers", "teacher list", "teachers", "who is in charge", "in charge list", "event incharge", "event in-charge")):
        rows = [[t["name"], t["event"]] for t in teachers]
        return answer("TECHNOVA 2026 teachers and their listed event responsibilities:", ["Teacher", "Event responsibility"], rows)

    if any(term in q for term in ("schedule", "date wise", "date-wise", "what happens on", "events on", "which day")):
        rows = []
        for e in events:
            rows.append([e["date"], e["name"], e["venue"], e["teacher"]])
        rows.sort(key=lambda row: row[0])
        return answer(f"TECHNOVA 2026 runs on {data['dates']}. Here is the event-wise schedule available in the data. Individual reporting times are not listed:", ["Date", "Event", "Venue", "Teacher in-charge"], rows)

    if any(term in q for term in ("registration", "register", "registration form", "last date", "deadline")):
        return answer("TECHNOVA 2026 registration details:", ["Item", "Details"], [
            ["Registration deadline", data["registration_deadline"]],
            ["Registration form", data["registration_url"]]
        ])

    if any(term in q for term in ("contact", "phone", "help desk", "coordinator", "call", "email")):
        return answer("Official contact information listed for TECHNOVA 2026:", ["Role", "Contact details"], [
            ["Help Desk", "Mr. Shubham Asthana"],
            ["Technical Coordinator", "Ms. Swaranjali Rawat — 8090365217"],
            ["Technical Coordinator", "Mr. Abhishek Sharma — 9670050600"]
        ])

    # Find a specific event by its full name or brochure keywords.
    matched_event = None
    for event in events:
        name = event["name"].lower()
        keywords = [str(k).lower() for k in event.get("keywords", [])]
        if name in q or any(k and k in q for k in keywords):
            matched_event = event
            break
    if matched_event:
        e = matched_event
        return answer(f"Here are the available details for {e['name']}:", ["Detail", "Information"], [
            ["Category", e["category"]],
            ["Date", e["date"]],
            ["Teacher in-charge", e["teacher"]],
            ["Venue", e["venue"]],
            ["About", e["summary"]]
        ])

    # A teacher-name query returns the teacher's listed responsibilities.
    matched_teacher = next((t for t in teachers if t["name"].lower() in q), None)
    if matched_teacher:
        return answer(f"Responsibilities listed for {matched_teacher['name']}:", ["Teacher", "Event"], [[matched_teacher["name"], matched_teacher["event"]]])

    if any(word in q for word in ("date", "when", "timing", "how many days")):
        return answer("TECHNOVA 2026 event dates:", ["Item", "Information"], [
            ["Dates", data["dates"]],
            ["19 November", "AI & Robotics Quiz Challenge"],
            ["20 November", "Other listed competitions"],
            ["Timing note", data["schedule_note"]]
        ])

    if any(word in q for word in ("school", "cms", "admission", "academics", "principal", "facility", "facilities", "club", "sports", "history", "address", "location")):
        return answer("I currently have verified information from the TECHNOVA 2026 event data, but not the complete official CMS school information for this question. I won't guess. Please contact the school office for confirmation.")

    return answer(data.get("fallback", "I couldn't find that information in the available TECHNOVA 2026 data. Please contact the event team."))

if __name__ == "__main__":
    import os
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
