# Mindset Before Skillset — Author Landing Page

## Overview
A single-page static website promoting the book "Mindset Before Skillset" by Oluwasegun Ajibola. It's a self-contained `index.html` file with inline CSS/JS, animated background graphics (SVG + Three.js), and sections for the book, author, updates, and contact/subscribe.

## Project Structure
- `index.html` — the entire site (markup, styles, and scripts inline)
- `server.py` — minimal Python static file server used for local development, serving on `0.0.0.0:5000` with no-cache headers so edits are reflected immediately in the Replit preview

## Tech Stack
- Plain HTML/CSS/JavaScript (no build system, no frontend framework)
- External dependencies loaded via CDN: Google Fonts, Three.js (r128)
- Served in development via Python's built-in `http.server` (wrapped in `server.py`)

## Running the Project
The "Start application" workflow runs `python3 server.py`, which serves the static site on port 5000.

## User Preferences
None recorded yet.
