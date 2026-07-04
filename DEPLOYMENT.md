# Deployment Guide

This project is split into two independently deployed pieces:

- **Backend (API)** — Flask app (`app.py`) → deployed to **fly.io**
- **Frontend (site)** — `dist/index.html` → uploaded to **cPanel**

They talk to each other over HTTPS: the frontend calls the backend's public URL for `/api/subscribe`.

---

## 1. Deploy the backend to fly.io

### One-time setup
1. Install the fly.io CLI: https://fly.io/docs/flyctl/install/
2. Log in: `fly auth login`

### Files already prepared for you
- `Dockerfile` — builds the Flask app with gunicorn
- `fly.toml` — fly.io app config (app name `mindset-before-skillset-api`, region `iad`, persistent volume for the database, `/health` check)
- `requirements.txt` — Python dependencies (regenerate with `uv export --no-hashes --no-dev --format requirements-txt -o requirements.txt` if you add packages)
- `.dockerignore` — keeps dev-only files out of the image

### First deploy
From the project root:

```bash
fly launch --no-deploy --copy-config --name mindset-before-skillset-api
```
This links the existing `fly.toml` to your fly.io account. If it asks to overwrite `fly.toml`, say no (keep the existing one).

Create the persistent volume for the SQLite database (only once):
```bash
fly volumes create mindset_data --size 1 --region iad
```

Set your secrets (do this once; EmailJS won't send mail without them):
```bash
fly secrets set EMAILJS_SERVICE_ID=service_wkrjxkm
fly secrets set EMAILJS_TEMPLATE_ID=template_gwvclv8
fly secrets set EMAILJS_PUBLIC_KEY=4vtpi89mVXCMesncv
fly secrets set EMAILJS_PRIVATE_KEY=your_private_key_here
```

Restrict CORS to your real domain (recommended once your cPanel site is live):
```bash
fly secrets set FRONTEND_ORIGIN=https://yourdomain.com,https://www.yourdomain.com
```
(If you skip this, the API accepts requests from any origin — fine for testing, less strict for production.)

Deploy:
```bash
fly deploy
```

Your API will be live at `https://mindset-before-skillset-api.fly.dev` (or whatever name you chose — check with `fly status`).

### Every time you update the backend
```bash
fly deploy
```
That's it — push your code, run `fly deploy`, done.

### Verify it's working
```bash
curl https://mindset-before-skillset-api.fly.dev/health
```
Should return `{"status": "ok"}`.

---

## 2. Deploy the frontend to cPanel

The `dist/` folder contains a ready-to-upload `index.html` with `API_BASE` already pointed at
`https://mindset-before-skillset-api.fly.dev`.

**If you used a different fly.io app name**, open `dist/index.html`, find this line near the top of the `<script>` block, and update it to match:
```js
const API_BASE = 'https://mbs-v8bxla.fly.dev';
```

### Upload steps
1. Log in to cPanel → **File Manager**.
2. Navigate to `public_html` (or the subfolder for your domain/subdomain).
3. Upload `dist/index.html` (rename to `index.html` if it isn't already — it already is).
4. That's the entire site — no build step, no dependencies, just the one file.

### Every time you update the frontend
1. Edit `index.html` in the project as usual.
2. Copy it into `dist/index.html`, making sure `API_BASE` still points at your fly.io URL:
   ```bash
   cp index.html dist/index.html
   ```
   Then re-apply the `API_BASE` line change described above (or keep a small diff/script if you prefer).
3. Re-upload `dist/index.html` to cPanel, replacing the old one.

---

## 3. How it fits together

```
 Browser
   |
   |  loads page
   v
cPanel (dist/index.html)  --- fetch('https://mindset-before-skillset-api.fly.dev/api/subscribe') --->  fly.io (Flask API + SQLite volume + EmailJS)
```

- The frontend is static HTML/CSS/JS — cPanel just serves the file, nothing to run.
- The backend on fly.io handles `/api/subscribe`, stores signups in SQLite on a persistent volume (`/data/waitlist.db`), and sends emails via EmailJS.
- CORS on the backend is controlled by the `FRONTEND_ORIGIN` secret so only your cPanel domain(s) can call the API in production.

## Troubleshooting
- **Signups fail / network error in browser console**: check that `API_BASE` in `dist/index.html` exactly matches your fly.io app URL (including `https://`, no trailing slash).
- **CORS errors in browser console**: make sure `FRONTEND_ORIGIN` on fly.io includes the exact domain (with `https://`) the page is served from.
- **Emails not sending**: run `fly secrets list` to confirm all four `EMAILJS_*` secrets are set, then check `fly logs` for errors.
- **Database resets after deploy**: confirm the volume is attached — `fly volumes list` should show `mindset_data` mounted at `/data`.
