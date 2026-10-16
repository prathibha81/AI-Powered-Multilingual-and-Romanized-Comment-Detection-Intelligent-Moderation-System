# Instagram Toxic Comment Detection System

A Flask dashboard that analyzes public Instagram comments as NON TOXIC or TOXIC, saves the results in SQLite, and provides searchable history and CSV exports.

## Run & Operate

- `python app.py` — run the Flask app locally on port 5000
- The managed preview workflow is `artifacts/api-server: Flask App`
- `python -m pytest -q` — run the Flask/unit test suite
- `python -m compileall -q app.py config.py models.py services utils tests` — syntax check

## Stack

- Python 3.13
- Flask + Flask-SQLAlchemy
- SQLite
- Hugging Face Transformers + PyTorch
- requests + optional Apify actor
- Jinja templates, custom CSS, and vanilla JavaScript

## Where things live

- `app.py` — Flask app factory and HTML/API routes
- `config.py` — environment-backed configuration
- `models.py` — `Analysis` and `CommentResult` SQLAlchemy models
- `services/` — classifier, scraper, and analysis pipeline
- `utils/` — text cleaning and CSV export
- `templates/` — homepage, analysis detail, history, and error pages
- `static/` — responsive styles and dashboard JavaScript
- `tests/` — cleaner and route smoke tests
- `model/` — expected location for the trained Hugging Face model

## Architecture decisions

- SQLite is intentional for this college project. The app ignores the workspace’s injected PostgreSQL URL unless `DATABASE_URL` is explicitly a SQLite URL.
- The classifier loads a local Hugging Face model once and permanently maps class 0 to NON TOXIC and class 1 to TOXIC.
- When the trained model is absent, demo mode uses a clearly labeled lightweight fallback rather than claiming model results.
- The Flask service is registered as the root service of the existing API artifact so `/` and `/api/*` are reachable through the preview router.
- The Apify integration is server-side and optional; mock mode is the default for local demonstration.

## Product

Users can submit a public Instagram URL or run a demo, review summary statistics and a real-data chart, search/filter/paginate comments, save and delete analyses, and export CSV results.

## User preferences

- Use Flask, HTML, CSS, vanilla JavaScript, SQLite, and local ML components.
- Keep the architecture understandable for a college viva.

## Gotchas

- Put a complete trained Hugging Face model in `MODEL_PATH` before presenting real model inference.
- Keep `MOCK_SCRAPER=true` until `APIFY_API_TOKEN` and the actor are configured.
- Do not expose `APIFY_API_TOKEN` in templates or browser JavaScript.
- Artifact workflow commands run from `artifacts/api-server`, so the Flask development command is `python ../../app.py`.

## Pointers

- `README.md` contains setup, API, deployment, viva, and ethics documentation.
- `.env.example` lists safe configuration names and defaults.