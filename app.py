from flask import Flask, request, jsonify
import requests
import re

app = Flask(__name__)

API_KEY = "my-secret-key-123"   # same key you will enter in GUVI
GUVI_CALLBACK_URL = "https://hackathon.guvi.in/api/updateHoneyPotFinalResult"

sessions = {}

def detect_scam(text):
    keywords = ["account blocked", "verify", "urgent", "upi", "bank"]
    return any(k in text.lower() for k in keywords)

def extract_intelligence(text, intel):
    upi = re.findall(r"[a-zA-Z0-9.\-_]+@[a-zA-Z]+", text)
    phone = re.findall(r"\+91\d{10}", text)
    link = re.findall(r"https?://\S+", text)

    intel["upiIds"].extend(upi)
    intel["phoneNumbers"].extend(phone)
    intel["phishingLinks"].extend(link)

@app.route("/honeypot", methods=["POST"])
def honeypot():
    if request.headers.get("x-api-key") != API_KEY:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.json
    session_id = data.get("sessionId")
    text = data["message"]["text"]

    if session_id not in sessions:
        sessions[session_id] = {
            "messages": 0,
            "intel": {
                "bankAccounts": [],
                "upiIds": [],
                "phishingLinks": [],
                "phoneNumbers": [],
                "suspiciousKeywords": []
            },
            "scam": False
        }

    session = sessions[session_id]
    session["messages"] += 1

    if detect_scam(text):
        session["scam"] = True
        extract_intelligence(text, session["intel"])

    reply = "I am confused, can you explain this properly?"

    # AUTO FINISH after 6 messages
    if session["messages"] >= 6 and session["scam"]:
        payload = {
            "sessionId": session_id,
            "scamDetected": True,
            "totalMessagesExchanged": session["messages"],
            "extractedIntelligence": session["intel"],
            "agentNotes": "Used urgency and fear tactics"
        }

        try:
            requests.post(GUVI_CALLBACK_URL, json=payload, timeout=5)
        except:
            pass

    return jsonify({
        "status": "success",
        "reply": reply
    })
        import os

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
