# Mindset Before Skillset — Author Landing Page

## Overview
A landing page and waitlist app for the book "Mindset Before Skillset" by Oluwasegun Ajibola. It consists of a Flask backend (`app.py`) serving a waitlist API backed by SQLite, and a large single-file frontend (`index.html`) with animated SVG/Three.js backgrounds, served as a static file.

## Project Structure
- `app.py` — Flask backend: `/api/subscribe` (POST), `/api/waitlist/count` (GET), serves `index.html` at `/`
- `index.html` — entire frontend (HTML/CSS/JS inline, ~2.7MB)
- `dist/index.html` — alternate/backup build of the frontend
- `waitlist.db` — SQLite database storing waitlist signups
- `requirements.txt` / `pyproject.toml` — Python dependencies (Flask, flask-cors, requests, gunicorn)
- `fly.toml` / `Dockerfile` — Fly.io deployment config (previous host)

## Tech Stack
- **Backend:** Python / Flask / SQLite
- **Frontend:** Plain HTML/CSS/JavaScript, Three.js (CDN), Google Fonts (CDN)
- **Email:** EmailJS REST API (server-side) for waitlist notification and welcome emails

## Running the Project
The "Start application" workflow runs `python3 app.py`, serving on port 5000.

## Environment Variables
Set in `.replit` `[userenv.shared]` (already configured):
- `EMAILJS_SERVICE_ID` — EmailJS service ID
- `EMAILJS_TEMPLATE_ID` — EmailJS template ID
- `EMAILJS_PUBLIC_KEY` — EmailJS public key

Still needed as a Replit Secret:
- `EMAILJS_PRIVATE_KEY` — EmailJS private/access token (required for server-side sending)

Without `EMAILJS_PRIVATE_KEY`, the app still works — signups are saved to the DB but emails are skipped with a warning.

## User Preferences
None recorded yet.
