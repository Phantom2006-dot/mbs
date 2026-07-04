import os
import re
from contextlib import contextmanager
from datetime import datetime, timezone

import psycopg2
import psycopg2.extras
import requests
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS

app = Flask(__name__)

# Allow the cPanel-hosted frontend (a different origin) to call this API.
# Set FRONTEND_ORIGIN to your cPanel site's URL(s), comma-separated, e.g.
#   FRONTEND_ORIGIN=https://mindsetbeforeskillset.com,https://www.mindsetbeforeskillset.com
# Falls back to "*" (any origin) if not set, so it works out of the box.
_frontend_origins = os.environ.get("FRONTEND_ORIGIN", "*")
_origins = [o.strip() for o in _frontend_origins.split(",")] if _frontend_origins != "*" else "*"
CORS(app, resources={r"/api/*": {"origins": _origins}})

DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL environment variable is not set")


@contextmanager
def get_db():
    conn = psycopg2.connect(DATABASE_URL)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
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
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS waitlist (
                    id SERIAL PRIMARY KEY,
                    name TEXT,
                    email TEXT NOT NULL UNIQUE,
                    created_at TIMESTAMPTZ NOT NULL
                )
                """
            )


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
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO waitlist (name, email, created_at) VALUES (%s, %s, %s)",
                    (name, email, created_at),
                )
    except psycopg2.errors.UniqueViolation:
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
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM waitlist")
            count = cur.fetchone()[0]
    return jsonify({"count": count})


@app.route("/")
def index():
    return send_from_directory(".", "index.html")


@app.route("/health")
def health():
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
