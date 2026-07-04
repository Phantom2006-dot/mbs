---
name: EmailJS server-side sending
description: Gotchas when calling the EmailJS REST API from a backend (Python/Node) instead of the browser SDK.
---

Calling `https://api.emailjs.com/api/v1.0/email/send` directly from a server (not the browser JS SDK) requires:

1. The account owner must enable **"Allow API Request from Non-Browser"** in EmailJS dashboard → Account → Security. Without it, every request returns `403 Forbidden`, even with a valid `accessToken` (private key).
2. The template's **"To Email"** field (in the template's Settings panel) must literally contain a variable like `{{to_email}}`. If it's blank or hardcoded, the API returns `422 The recipients address is empty` even though `template_params.to_email` was sent correctly in the payload — the template setting is what actually controls the recipient, not just the param name.

**Why:** EmailJS is designed primarily for client-side/browser use with origin-based restrictions; server-side usage is an opt-in escape hatch gated by both an account-level toggle and correct template configuration.

**How to apply:** When wiring EmailJS into a backend, walk the user through both settings explicitly — a request with correct keys/IDs will still fail without them, and the errors look like auth or payload bugs rather than dashboard configuration gaps.

One EmailJS "Auto-Reply" (blank) template can be reused for multiple email types (e.g. admin notification + user welcome email) by passing different `to_email`, `subject`, and `message` template params per call — no need for separate templates per email type.
