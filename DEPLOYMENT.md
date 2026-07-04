# Deployment Guide

This project is split into two independently deployed pieces:

| Piece | What | Where |
|---|---|---|
| **Backend (API)** | `app.py` — Flask + NeonDB + EmailJS | **Fly.io** |
| **Frontend (site)** | `dist/index.html` — static HTML/CSS/JS | **Vercel** or **cPanel** (your choice) |

They talk to each other over HTTPS: the frontend calls the backend's public URL for `/api/subscribe`.

> **Changed from the original guide:** The database is now **NeonDB (PostgreSQL)** — no SQLite volume or `fly volumes` needed.

---

## 1. Build the frontend dist file

Whenever you edit `index.html`, run this before deploying the frontend:

```bash
./build-dist.sh https://mbs-v8bxla.fly.dev
```

This copies `index.html` → `dist/index.html` and injects the correct backend URL.  
Replace `https://mbs-v8bxla.fly.dev` with your actual Fly.io URL if you chose a different app name.

`dist/index.html` is what you upload to cPanel or deploy to Vercel — never deploy the root `index.html` directly to a static host (it has an empty `API_BASE`).

---

## 2. Deploy the backend to Fly.io

### One-time setup

```bash
# Install the Fly CLI (once, on your machine)
# macOS/Linux:
curl -L https://fly.io/install.sh | sh
# Windows: https://fly.io/docs/flyctl/install/

fly auth login
```

### First deploy

```bash
# Link fly.toml to your Fly account — say NO if asked to overwrite fly.toml
fly launch --no-deploy --copy-config --name mbs-v8bxla
```

Set all secrets (once):

```bash
fly secrets set DATABASE_URL="postgresql://neondb_owner:...@....neon.tech/neondb?sslmode=require&channel_binding=require"
fly secrets set EMAILJS_SERVICE_ID=service_wkrjxkm
fly secrets set EMAILJS_TEMPLATE_ID=template_gwvclv8
fly secrets set EMAILJS_PUBLIC_KEY=4vtpi89mVXCMesncv
fly secrets set EMAILJS_PRIVATE_KEY=your_private_key_here
```

Lock CORS to your frontend domain once it's live (swap in your real domain):

```bash
# Vercel:
fly secrets set FRONTEND_ORIGIN=https://your-project.vercel.app,https://yourdomain.com

# cPanel:
fly secrets set FRONTEND_ORIGIN=https://mindsetbeforeskillset.com,https://www.mindsetbeforeskillset.com
```

> Omit `FRONTEND_ORIGIN` (or leave it unset) to accept requests from any origin — fine while testing.

Deploy:

```bash
fly deploy
```

Your API is live at `https://mbs-v8bxla.fly.dev` (confirm with `fly status`).

### Verify

```bash
curl https://mbs-v8bxla.fly.dev/health
# → {"status": "ok"}
```

### Every future backend update

```bash
fly deploy
```

That's it — Fly builds and rolls out the new container automatically.

---

## 3a. Deploy the frontend to Vercel

### One-time setup

1. Push this repo to GitHub (if it isn't there already).
2. Go to [vercel.com](https://vercel.com) → **Add New Project** → import your GitHub repo.
3. Vercel settings:
   - **Framework Preset:** Other
   - **Root Directory:** *(leave blank — root of repo)*
   - **Build Command:** `bash build-dist.sh https://mbs-v8bxla.fly.dev`
   - **Output Directory:** `dist`
4. Click **Deploy**.

Vercel reads `vercel.json` (already in the repo) which tells it to serve from `dist/`.

### Custom domain on Vercel (optional)

In your Vercel project → **Settings → Domains**, add your domain and follow the DNS instructions. Then tighten CORS on Fly:

```bash
fly secrets set FRONTEND_ORIGIN=https://yourdomain.com,https://www.yourdomain.com
```

### Every future frontend update

Push to GitHub → Vercel redeploys automatically (it runs `build-dist.sh` as part of the build).

---

## 3b. Deploy the frontend to cPanel

Use this if you host your domain on cPanel and prefer to upload files manually.

### Build the dist file

```bash
./build-dist.sh https://mbs-v8bxla.fly.dev
```

### Upload

1. Log in to cPanel → **File Manager**.
2. Navigate to `public_html` (or your domain's subdirectory).
3. Upload `dist/index.html` and rename it `index.html` if prompted.
4. That's the entire site — one file, no build dependencies.

### Every future frontend update

1. Edit `index.html` in the project.
2. Run `./build-dist.sh https://mbs-v8bxla.fly.dev`.
3. Re-upload `dist/index.html` to cPanel, replacing the old one.

---

## 4. How it fits together

```
Browser
  │
  │  loads page
  ▼
Vercel or cPanel (dist/index.html)
  │
  │  POST /api/subscribe
  ▼
Fly.io  ──►  NeonDB (PostgreSQL)
             EmailJS (welcome + notify emails)
```

- The frontend is pure static HTML/CSS/JS — no server required.
- The Fly.io backend handles `/api/subscribe` and `/api/waitlist/count`, stores signups in NeonDB, and fires emails via EmailJS.
- CORS on the backend is locked to `FRONTEND_ORIGIN` so only your domain(s) can call the API in production.

---

## 5. Environment variables reference

### Fly.io secrets (`fly secrets set KEY=value`)

| Secret | Value | Required |
|---|---|---|
| `DATABASE_URL` | Your full NeonDB connection string | ✅ Yes |
| `EMAILJS_SERVICE_ID` | `service_wkrjxkm` | For emails |
| `EMAILJS_TEMPLATE_ID` | `template_gwvclv8` | For emails |
| `EMAILJS_PUBLIC_KEY` | `4vtpi89mVXCMesncv` | For emails |
| `EMAILJS_PRIVATE_KEY` | From EmailJS dashboard | For emails |
| `FRONTEND_ORIGIN` | Comma-separated frontend URL(s) | Recommended |

### Vercel environment variables (if using Vercel)

None — the frontend is pure static HTML; all secrets live on Fly.io.

---

## 6. Troubleshooting

| Symptom | Fix |
|---|---|
| `curl /health` returns connection refused | `fly status` — check the machine is running; `fly logs` for errors |
| Signups fail / network error in browser | Check `API_BASE` in `dist/index.html` exactly matches your Fly URL (no trailing slash) |
| CORS error in browser console | Add the exact frontend origin (with `https://`) to `FRONTEND_ORIGIN` secret on Fly |
| Emails not sending | `fly secrets list` — confirm all four `EMAILJS_*` secrets are set; `fly logs` for error details |
| DB errors on Fly | Confirm `DATABASE_URL` secret is set with `fly secrets list`; test the connection string locally first |
| Vercel build fails | Check Vercel build logs — usually a wrong Build Command or Output Directory setting |
