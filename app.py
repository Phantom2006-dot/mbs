import os
import re
import sqlite3
from datetime import datetime, timezone

import requests
from flask import Flask, jsonify, request, send_from_directory

app = Flask(__name__, static_folder=".", static_url_path="")

DB_PATH = os.path.join(os.path.dirname(__file__), "waitlist.db")
NOTIFY_EMAIL = "subscribe@mindsetbeforeskillset.com"

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

EMAILJS_SERVICE_ID = os.environ.get("EMAILJS_SERVICE_ID")
EMAILJS_TEMPLATE_ID = os.environ.get("EMAILJS_TEMPLATE_ID")
EMAILJS_PUBLIC_KEY = os.environ.get("EMAILJS_PUBLIC_KEY")
EMAILJS_PRIVATE_KEY = os.environ.get("EMAILJS_PRIVATE_KEY")
EMAILJS_API_URL = "https://api.emailjs.com/api/v1.0/email/send"


def emailjs_configured():
    return all([EMAILJS_SERVICE_ID, EMAILJS_TEMPLATE_ID, EMAILJS_PUBLIC_KEY, EMAILJS_PRIVATE_KEY])


def send_emailjs(to_email, subject, message):
    payload = {
        "service_id": EMAILJS_SERVICE_ID,
        "template_id": EMAILJS_TEMPLATE_ID,
        "user_id": EMAILJS_PUBLIC_KEY,
        "accessToken": EMAILJS_PRIVATE_KEY,
        "template_params": {
            "to_email": to_email,
            "subject": subject,
            "message": message,
        },
    }
    response = requests.post(EMAILJS_API_URL, json=payload, timeout=15)
    if not response.ok:
        raise RuntimeError(f"{response.status_code} {response.text}")
    return response


def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS waitlist (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                email TEXT NOT NULL UNIQUE,
                created_at TEXT NOT NULL
            )
            """
        )
        conn.commit()


init_db()


@app.after_request
def add_no_cache_headers(response):
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response


@app.route("/api/subscribe", methods=["POST"])
def subscribe():
    data = request.get_json(silent=True) or request.form
    name = (data.get("name") or "").strip()
    email = (data.get("email") or "").strip().lower()

    if not email or not EMAIL_RE.match(email):
        return jsonify({"success": False, "message": "Please enter a valid email address."}), 400

    created_at = datetime.now(timezone.utc).isoformat()

    try:
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute(
                "INSERT INTO waitlist (name, email, created_at) VALUES (?, ?, ?)",
                (name, email, created_at),
            )
            conn.commit()
    except sqlite3.IntegrityError:
        return jsonify({"success": True, "message": "You're already on the waitlist!"}), 200

    notify_sent = False
    welcome_sent = False

    if emailjs_configured():
        try:
            send_emailjs(
                to_email=NOTIFY_EMAIL,
                subject="New Waitlist Signup",
                message=(
                    f"New signup for the waitlist:\n\n"
                    f"Name: {name or 'N/A'}\n"
                    f"Email: {email}\n"
                    f"Submitted: {created_at}\n\n"
                    f"{name or 'This person'} has subscribed to the waitlist."
                ),
            )
            notify_sent = True
        except Exception as exc:
            app.logger.error("Failed to send EmailJS notification to %s: %s", NOTIFY_EMAIL, exc)

        try:
            greeting_name = name.split(" ")[0] if name else "there"
            send_emailjs(
                to_email=email,
                subject="Welcome to the Mindset Before Skillset Waitlist",
                message=(
                    f"Hi {greeting_name},\n\n"
                    f"Thank you for joining the waitlist for Mindset Before Skillset "
                    f"by Oluwasegun Ajibola. You're officially on the list!\n\n"
                    f"You'll be among the first to get early access, exclusive insights, "
                    f"and behind-the-scenes content before the official launch.\n\n"
                    f"Talk soon,\nThe Mindset Before Skillset Team"
                ),
            )
            welcome_sent = True
        except Exception as exc:
            app.logger.error("Failed to send EmailJS welcome email to %s: %s", email, exc)
    else:
        app.logger.warning("EmailJS is not fully configured; skipping emails")

    return jsonify(
        {
            "success": True,
            "message": "Thank you for joining the waitlist! Check your inbox for a welcome email.",
            "notify_sent": notify_sent,
            "welcome_sent": welcome_sent,
        }
    )


@app.route("/api/waitlist/count", methods=["GET"])
def waitlist_count():
    with sqlite3.connect(DB_PATH) as conn:
        count = conn.execute("SELECT COUNT(*) FROM waitlist").fetchone()[0]
    return jsonify({"count": count})


@app.route("/")
def index():
    return send_from_directory(".", "index.html")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
