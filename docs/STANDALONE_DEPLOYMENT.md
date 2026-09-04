# Standalone deployment (SPA on a different origin than the API)

The docker-compose setup serves the SPA and the API behind one nginx origin, so
the refresh-token cookie was `SameSite=Strict`. When the SPA is hosted
separately from the API — e.g. the frontend on Vercel and the API behind a
tunnel or a different domain — a `Strict` cookie is **never** sent on the
cross-site `POST /api/v1/auth/refresh` call, so every page reload logs the user
out.

## What changed

`backend/app/auth/router.py` — `_set_refresh_cookie` now sets
`SameSite=None; Secure` for any non-`local` `ENVIRONMENT`, and keeps
`SameSite=Strict` for `local`. `Secure` is mandatory with `SameSite=None`, and
the browser only honours a cross-site credentialed request when the API's CORS
response names the exact SPA origin (never `*`) with
`Access-Control-Allow-Credentials: true` — which `main.py` already does from
`settings.CORS_ORIGINS`.

Nothing about same-origin (nginx) deployments changes: keep `ENVIRONMENT=local`
there and the cookie stays `Strict`.

## Deploying the frontend to Vercel + a separately-hosted API

1. **API** — run the compose stack, set on the `api` (and `worker`, `beat`)
   environment:
   - `ENVIRONMENT=staging` (or `production` — then also set a real
     `JWT_SECRET_KEY`, the startup guard enforces it)
   - `CORS_ORIGINS=["https://<your-app>.vercel.app", ...]`
   Expose `:8000` over HTTPS (a reverse proxy, or a tunnel).
2. **Frontend** — Vercel project, root directory `dr-archana-ivf-prototype`,
   framework Next.js. Set `NEXT_PUBLIC_API_URL=https://<api-host>/api/v1`.
   `next.config.js` already emits `output: 'standalone'`; Vercel ignores that and
   builds natively.
3. Deploy, then sign in — the refresh cookie round-trips cross-site and the
   session survives reloads.

Verified live: login as `archana@drarchanaivf.in` / `ChangeMe123!`, the Clinical
Dashboard renders real data (IVF cycle distribution, activity feed, review
queue), and a hard reload keeps the session — the silent refresh succeeds.

## On unifying Archana-IVF into this app

`ClickfieldAI/Archana-IVF` is a deliberately small Day 1–3 slice — Patients (with
couple + documents + a photo capture flow), Appointments, and a permission-code
auth seam. Every capability it contains already exists here, generally with more
depth: this repo's `patients` module has the couple model, `PatientDocument`
with `document_type="photo"` and `Patient.photo_document_id`, Aadhaar/visa
mandatory-document logic, and a full `users`/`roles` RBAC with an audit trail —
a superset of the Archana seam. The real gap for a unified, standalone product
was **deployability as a cross-origin web app**, addressed by the cookie change
above.
