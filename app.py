from flask import Flask, request, jsonify
import requests
import re
import os

app = Flask(__name__)

# ===== CONFIG =====
API_KEY = "my-secret-key-123"
GUVI_CALLBACK_URL = "https://hackathon.guvi.in/api/updateHoneyPotFinalResult"

# ===== IN-MEMORY SESSION STORE =====
sessions = {}

# ===== SCAM DETECTION =====
def detect_scam(text):
    keywords = ["account blocked", "verify", "urgent", "upi", "bank", "suspended"]
    return any(word in text.lower() for word in keywords)

# ===== INTELLIGENCE EXTRACTION =====
def extract_intelligence(text, intel):
    upi_ids = re.findall(r"[a-zA-Z0-9.\-_]+@[a-zA-Z]+", text)
    phone_numbers = re.findall(r"\+91\d{10}", text)
    links = re.findall(r"https?://\S+", text)

    intel["upiIds"].extend(upi_ids)
    intel["phoneNumbers"].extend(phone_numbers)
    intel["phishingLinks"].extend(links)

# ===== MAIN API ENDPOINT =====
@app.route("/honeypot", methods=["POST"])
def honeypot():
    # API key check
    if request.headers.get("x-api-key") != API_KEY:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json()
    session_id = data.get("sessionId")
    message_text = data["message"]["text"]

    # Initialize session
    if session_id not in sessions:
        sessions[session_id] = {
            "messages": 0,
            "scamDetected": False,
            "intel": {
                "bankAccounts": [],
                "upiIds": [],
                "phishingLinks": [],
                "phoneNumbers": [],
                "suspiciousKeywords": []
            }
        }

    session = sessions[session_id]
    session["messages"] += 1

    # Scam detection & extraction
    if detect_scam(message_text):
        session["scamDetected"] = True
        extract_intelligence(message_text, session["intel"])

    # Human-like reply
    reply = "I am confused, can you please explain this clearly?"

    # ===== FINAL CALLBACK AFTER 6 MESSAGES =====
    if session["messages"] >= 6 and session["scamDetected"]:
        payload = {
            "sessionId": session_id,
            "scamDetected": True,
            "totalMessagesExchanged": session["messages"],
            "extractedIntelligence": session["intel"],
            "agentNotes": "Scammer used urgency and fear tactics"
        }

        try:
            requests.post(GUVI_CALLBACK_URL, json=payload, timeout=5)
        except:
            pass

    return jsonify({
        "status": "success",
        "reply": reply
    })

# ===== RENDER PORT BINDING (VERY IMPORTANT) =====
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
