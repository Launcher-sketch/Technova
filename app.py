from flask import Flask, jsonify, render_template, request
import json
from pathlib import Path

app = Flask(__name__)
DATA_FILE = Path(__file__).parent / "data" / "technova.json"

def get_data():
    return json.loads(DATA_FILE.read_text(encoding="utf-8"))

@app.get("/")
def index():
    return render_template("index.html", data=get_data())

@app.get("/api/data")
def api_data():
    return jsonify(get_data())

@app.post("/api/chat")
def chat():
    message = (request.get_json(silent=True) or {}).get("message", "").strip()
    if not message:
        return jsonify(reply="Please enter a question.")
    data = get_data()
    q = message.lower()
    if any(word in q for word in ("hello", "hi", "hey", "good morning", "good afternoon")):
        return jsonify(reply="Hello! I am the CMS Event Manager Chatbot. How can I help you with TECHNOVA 2026?")
    if "all teacher" in q or "teacher list" in q or "teachers" in q:
        lines = ["Teachers and event responsibilities:"]
        for item in data["teachers"]:
            lines.append(f"• {item['name']} — {item['event']}")
        lines.append("Technical Coordinators: Ms. Swaranjali Rawat and Mr. Abhishek Sharma.")
        return jsonify(reply="\n".join(lines))
    if any(word in q for word in ("date", "when", "schedule", "timing")):
        return jsonify(reply=f"TECHNOVA 2026 takes place on {data['dates']}. {data['schedule_note']}")
    if any(word in q for word in ("register", "registration", "form")):
        return jsonify(reply=f"Registration deadline: {data['registration_deadline']}. Registration form: {data['registration_url']}")
    if any(word in q for word in ("contact", "phone", "help desk", "coordinator")):
        return jsonify(reply=data["contact"])
    for event in data["events"]:
        if event["name"].lower() in q or event["keywords"] and any(k in q for k in event["keywords"]):
            return jsonify(reply=f"{event['name']}\nDate: {event['date']}\nCategory: {event['category']}\nTeacher in charge: {event['teacher']}\nVenue: {event['venue']}\n{event['summary']}")
    return jsonify(reply=data["fallback"])

if __name__ == "__main__":
    import os
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
