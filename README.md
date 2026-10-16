# Instagram Toxic Comment Detection System

A Flask-based academic project for collecting publicly accessible Instagram comments, classifying them as **NON TOXIC** or **TOXIC**, and reviewing the results in a saved dashboard.

## Project overview

The application accepts an Instagram post or reel URL, retrieves comments through a mock provider or optional Apify actor, cleans the text, runs batch inference through a local Hugging Face sequence-classification model, and stores each analysis in SQLite.

This repository did not contain a trained model when the application was created. The app therefore keeps the required model interface and uses a clearly labeled lightweight demo classifier only when `MODEL_PATH` is not available. Add the trained model directory before presenting real model results.

## Features

- URL validation for public Instagram post and reel URLs
- Demo mode that works without Instagram, Apify, or an API token
- Local Hugging Face model loading with CPU/CUDA selection
- Fixed label mapping: `LABEL_0 = NON TOXIC`, `LABEL_1 = TOXIC`
- Batch classification with configurable batch size and max length
- Statistics, doughnut chart, search, filters, and pagination
- SQLite analysis history with delete and CSV export
- Responsive HTML/CSS/vanilla JavaScript dashboard
- Friendly error pages and API errors without stack traces or secrets

## Architecture

```text
User → Flask → URL validation → scraper → text cleaner
     → batch classifier → statistics → SQLite → dashboard
```

## Technology stack

Python, Flask, Flask-SQLAlchemy, SQLite, Hugging Face Transformers, PyTorch, requests, optional Apify, HTML5, CSS3, vanilla JavaScript, and Chart.js via CDN.

## Folder structure

```text
app.py                  Flask application and routes
config.py               Environment-backed configuration
models.py               Analysis and CommentResult database models
services/classifier.py  Local model adapter and demo fallback
services/scraper.py     Mock scraper and optional Apify adapter
services/analyzer.py    End-to-end analysis pipeline
utils/                  Text cleaning and CSV export
templates/              Jinja pages
static/                 CSS and vanilla JavaScript
tests/                  Lightweight route and cleaner tests
data/                   SQLite database (created automatically)
model/                  Place the trained Hugging Face model here
```

## Installation

The Replit environment installs Python dependencies for the app. For a local machine:

```bash
python -m pip install -r requirements.txt
```

For a virtual environment:

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# Linux/macOS
source .venv/bin/activate
python -m pip install -r requirements.txt
```

## Model setup

Set `MODEL_PATH` to the directory containing the existing trained model. It should include `config.json`, tokenizer files, and model weights such as `model.safetensors`. The application loads the model once and never reverses the required label mapping.

The model must actually support two labels. The app does not claim multilingual support or create unsupported toxicity categories.

## Apify setup

For live public-comment scraping, set `MOCK_SCRAPER=false`, set `APIFY_API_TOKEN` securely, and configure `APIFY_ACTOR_ID` if your actor uses a different ID. The token is read only on the server and is never put into HTML or JavaScript.

Do not implement private-account access or authentication bypass. Use only content you are authorized to analyze and follow Instagram, Apify, and applicable legal rules.

## Mock and demo modes

`MOCK_SCRAPER=true` uses the included sample comments. The **Try demo** button always uses that dataset and stores the result with a DEMO label. If no trained model is present, the demo uses the transparent local fallback so the interface remains demonstrable; that fallback is not a substitute for model evaluation.

## Running Flask

```bash
python app.py
```

The app listens on `0.0.0.0:$PORT` when `PORT` is supplied, or port 5000 locally.

For production, use a WSGI server only after configuring the environment:

```bash
gunicorn app:app
```

Hosting limits and pricing can change by provider.

## Environment variables

See `.env.example`. Important values are:

- `MODEL_PATH`
- `DATABASE_URL`
- `MOCK_SCRAPER`
- `MAX_COMMENTS`
- `BATCH_SIZE`
- `MAX_LENGTH`
- `APIFY_API_TOKEN`
- `APIFY_ACTOR_ID`
- `SECRET_KEY`

## API endpoints

| Method | Endpoint | Purpose |
| --- | --- | --- |
| GET | `/` | Homepage |
| POST | `/api/analyze` | Scrape and analyze a URL |
| POST | `/api/demo` | Analyze included demo comments |
| GET | `/analysis/<id>` | Detail page |
| GET | `/history` | Saved analyses |
| GET | `/api/history` | History JSON |
| GET | `/api/analysis/<id>` | Analysis JSON |
| DELETE | `/api/analysis/<id>` | Delete analysis |
| GET | `/api/analysis/<id>/export` | Download CSV |

## Testing

```bash
python -m pytest
```

The tests cover text cleaning, homepage loading, demo persistence, history/detail routes, CSV availability, and invalid URL handling. Add the trained model before running model-specific inference checks.

## Database

SQLite and its `data/` directory are created automatically at startup. Each `Analysis` owns many `CommentResult` records. Deleting an analysis deletes its associated results.

## Viva explanation

- **Flask** handles routes, requests, responses, and templates.
- **Tokenizer** converts text into the numbers the Transformer expects.
- **Transformer** generates a representation of the comment.
- **Logits** are the model’s raw class scores.
- **Softmax** turns those scores into probability-like values.
- **Classification** selects the higher probability and maps class 0/class 1 to the two supported labels.
- **SQLite** stores history and individual predictions.
- **Apify** is an optional provider for public comment collection.

## Limitations and ethics

Predictions can be wrong. Sarcasm, context, language variation, and bias in training data affect performance. Confidence is not certainty, and automated classification is not perfect moderation. The app does not implement private-account access or authentication bypass. Users should analyze only authorized public content and respect platform rules and applicable laws.

## Future improvements

- Add authenticated users and per-user history
- Add model evaluation metrics and a labeled review workflow
- Add background jobs for very large comment sets
- Add a provider adapter for additional permitted public data sources