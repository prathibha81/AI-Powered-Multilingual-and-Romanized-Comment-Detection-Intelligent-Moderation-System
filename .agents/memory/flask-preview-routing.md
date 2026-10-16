---
name: Flask preview routing
description: Replit routing details for a Flask service added to this workspace.
---

Managed artifact service commands execute with the artifact directory as their working directory. A root-level Flask app must be launched with a path such as `python ../../app.py`, and its production command must change directory to the repository root before importing `app`.

**Why:** A plain `python app.py` looked inside `artifacts/api-server` and failed. The existing API service also owned `/api`, so the preview returned 502 for Flask API calls until that overlapping route was removed.

**How to apply:** When exposing this Flask app through the managed artifact, keep the Flask service on `/` and avoid another service claiming `/api`; restart `artifacts/api-server: Flask App` after service metadata or Python dependency changes.