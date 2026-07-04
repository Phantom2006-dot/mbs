import os
import re
import sqlite3
from datetime import datetime, timezone

import resend
from flask import Flask, jsonify, request, send_from_directory

app = Flask(__name__, static_folder=".", static_url_path="")

DB_PATH = os.path.join(os.path.dirname(__file__), "waitlist.db")
NOTIFY_EMAIL = "subscribe@mindsetbeforeskillset.com"
FROM_EMAIL = os.environ.get("RESEND_FROM_EMAIL", "onboarding@resend.dev")

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

resend.api_key = os.environ.get("RESEND_API_KEY")


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

    email_sent = False
    email_error = None
    if resend.api_key:
        try:
            resend.Emails.send(
                {
                    "from": f"Mindset Before Skillset <{FROM_EMAIL}>",
                    "to": [NOTIFY_EMAIL],
                    "reply_to": email,
                    "subject": "New Waitlist Signup",
                    "html": (
                        f"<p>New signup for the waitlist:</p>"
                        f"<ul>"
                        f"<li><strong>Name:</strong> {name or 'N/A'}</li>"
                        f"<li><strong>Email:</strong> {email}</li>"
                        f"<li><strong>Submitted:</strong> {created_at}</li>"
                        f"</ul>"
                    ),
                }
            )
            email_sent = True
        except Exception as exc:
            email_error = str(exc)
            app.logger.error("Failed to send Resend notification: %s", email_error)
    else:
        email_error = "RESEND_API_KEY not configured"
        app.logger.warning(email_error)

    return jsonify(
        {
            "success": True,
            "message": "Thank you for joining the waitlist!",
            "email_sent": email_sent,
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
