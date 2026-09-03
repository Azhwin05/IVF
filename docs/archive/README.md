# Archived documentation — historical only, do not onboard from these

Everything in this folder describes **earlier states of the project** and is
kept only for history. None of it is accurate about the system as it stands.

**Current documentation lives at the repo root:**

| File | Purpose |
|---|---|
| `README.md` | Start here — what this is, how to run it |
| `CLAUDE.md` | Working guidance for Claude Code, and the non-negotiable rules |
| `DEVELOPER_HANDOFF.md` | Full architecture and onboarding walkthrough |
| `NEW_FEATURES_GAP_ANALYSIS.md` | Feature-by-feature implementation status |

## Why these were archived

The project began as a **front-end-only visual prototype** — every screen was
wired to hardcoded fixtures and there was no server at all. A FastAPI/Postgres
backend was later built from scratch and the frontend was rewired screen by
screen to call it. That rewiring is complete.

Documents written before or during that transition therefore describe a system
that no longer exists. The most misleading claims still present in them:

- "14 screens" and `npm run dev` on port 3000 as the whole setup
  → there are now 25 screens, and the app needs the Docker backend stack with
  the frontend pinned to **port 3100** (CORS depends on that port)
- "no backend" / "fake login"
  → there is a real backend with JWT auth, RBAC and an audit trail
- "27 modules" / "31 modules"
  → there are now 33 backend modules

## Contents

| File | Written for | Superseded by |
|---|---|---|
| `PROJECT_SUMMARY.md` | Prototype demo | `README.md` |
| `TECHNICAL_ARCHITECTURE.md` | Prototype demo | `DEVELOPER_HANDOFF.md` §3–5 |
| `CLIENT_PRESENTATION_GUIDE.md` | Prototype demo | — (event has passed) |
| `QUICK_START.txt` | Prototype demo | `README.md`, `CLAUDE.md` |
| `DELIVERY_COMPLETE.txt` | Prototype delivery | — |
| `Dr_Archana_..._Prototype_Context.md` | Prototype context | `DEVELOPER_HANDOFF.md` §1 |
| `ARCHITECTURE.md` | Early backend (27 modules) | `DEVELOPER_HANDOFF.md` §4 |
| `IMPLEMENTATION_PLAN.md` | Early backend build-out | `NEW_FEATURES_GAP_ANALYSIS.md` |
| `PROJECT_CONTEXT_PROMPT.md` | Early backend context | `CLAUDE.md` |
