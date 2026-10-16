# Instagram Toxic Comment Detection System

A Flask-based web application that analyzes publicly accessible Instagram post and reel comments and classifies them as **Non-Toxic** or **Toxic**. It provides a dashboard for reviewing results, tracking previous analyses, and exporting results to CSV.

## Overview

The application accepts a public Instagram post or reel URL, collects comments using either a sample dataset or an optional Apify integration, preprocesses the text, and runs batch classification through a local Hugging Face sequence-classification model. Analysis results are stored in SQLite and displayed in a dashboard.

> **Model note:** A trained model is not included in this repository by default. If `MODEL_PATH` is not configured, the application uses a clearly labeled demo fallback so the interface can be demonstrated. Demo predictions should not be presented as validated model results. Configure a trained model before evaluating real comments.

## Key Features

- Validate public Instagram post and reel URLs.
- Run the application in demo mode without external credentials.
- Load a local Hugging Face classification model with CPU/CUDA support.
- Classify comments using the configured two-label mapping:
  - `LABEL_0` → `NON TOXIC`
  - `LABEL_1` → `TOXIC`
- Process comments in batches with configurable batch size and maximum sequence length.
- View analysis statistics and a doughnut chart.
- Search, filter, and paginate comment results.
- Save analysis history in SQLite.
- View analysis details and export results as CSV.
- Delete saved analyses and their associated comment results.
- Use a responsive dashboard built with HTML, CSS, JavaScript, and Chart.js.
- Display user-friendly errors without exposing stack traces or secrets.

## Application Workflow

```text
Instagram Post/Reel URL
          |
          v
     Flask Application
          |
          v
       URL Validation
          |
          v
   Comment Collection
 (Demo Dataset / Apify)
          |
          v
     Text Cleaning
          |
          v
  Batch Classification
          |
          v
 Statistics and Results
          |
          v
   SQLite + Dashboard
```

## Technology Stack

| Category | Technologies |
|---|---|
| Backend | Python, Flask |
| Database | SQLite, Flask-SQLAlchemy |
| NLP / Classification | Hugging Face Transformers, PyTorch |
| Data collection | Sample dataset; optional Apify integration |
| Frontend | HTML5, CSS3, JavaScript |
| Visualization | Chart.js |
| Testing | pytest |

## Project Structure

```text
.
├── app.py                  # Flask application and routes
├── config.py               # Environment-based configuration
├── models.py               # Analysis and comment-result database models
├── services/
│   ├── classifier.py       # Local model adapter and demo fallback
│   ├── scraper.py          # Demo scraper and optional Apify adapter
│   └── analyzer.py         # End-to-end analysis pipeline
├── utils/                  # Text cleaning and CSV export utilities
├── templates/              # Jinja HTML templates
├── static/                 # CSS and JavaScript assets
├── tests/                  # Route and text-cleaning tests
├── data/                   # SQLite database, created automatically
├── model/                  # Location for the trained model
├── requirements.txt
└── .env.example            # Example environment configuration
```

## Getting Started

### 1. Prerequisites

- Python 3.10 or a compatible version supported by the dependencies.
- `pip`
- A trained Hugging Face model for meaningful real-world classification. The app can also be run in demo mode without one.

### 2. Clone the repository

```bash
git clone <YOUR_GITHUB_REPOSITORY_URL>
cd <YOUR_REPOSITORY_FOLDER>
```

Replace the placeholders with your repository URL and folder name.

### 3. Create and activate a virtual environment

**Windows**

```bash
python -m venv .venv
.venv\Scripts\activate
```

**Linux / macOS**

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 4. Install dependencies

```bash
python -m pip install -r requirements.txt
```

### 5. Configure environment variables

Use `.env.example` as a reference and configure the values required by your environment. Avoid committing secrets or real API tokens to version control.

Common configuration variables include:

| Variable | Purpose |
|---|---|
| `MODEL_PATH` | Path to the trained Hugging Face model directory |
| `DATABASE_URL` | Database connection URL |
| `MOCK_SCRAPER` | Enables or disables demo comment collection |
| `MAX_COMMENTS` | Maximum number of comments to process |
| `BATCH_SIZE` | Number of comments processed per batch |
| `MAX_LENGTH` | Maximum token sequence length |
| `APIFY_API_TOKEN` | Server-side token for optional Apify integration |
| `APIFY_ACTOR_ID` | Apify actor identifier |
| `SECRET_KEY` | Flask application secret key |

## Model Configuration

Set `MODEL_PATH` to a directory containing a compatible trained Hugging Face sequence-classification model, including its configuration, tokenizer files, and model weights (for example, `model.safetensors`).

The configured model must support the application's two-class label mapping. Confirm that the model's training labels match the expected mapping before interpreting predictions.

The demo fallback is intended for interface demonstration only. It is not a replacement for a trained model, validation, or performance evaluation.

## Comment Collection Configuration

The application supports a sample dataset for demo use and an optional Apify integration for collecting publicly accessible comments.

To configure live collection:

1. Set `MOCK_SCRAPER=false`.
2. Set `APIFY_API_TOKEN` as a server-side environment variable.
3. Set `APIFY_ACTOR_ID` if your Apify actor uses a different identifier.
4. Verify that your account, actor, and intended use are permitted.

Do not attempt to access private accounts or bypass authentication. Collect and analyze only content you are authorized to process, and follow Instagram's terms, Apify's terms, and applicable laws.

## Run the Application

```bash
python app.py
```

Open the local address shown in the terminal. By default, the application uses port `5000`; when a `PORT` environment variable is supplied, it can listen on that port.

For a WSGI deployment, configure the environment and use a production server such as:

```bash
gunicorn app:app
```

Deployment requirements and hosting costs depend on the chosen provider.

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | Homepage |
| `POST` | `/api/analyze` | Collect and analyze comments from a URL |
| `POST` | `/api/demo` | Analyze the included demo comments |
| `GET` | `/analysis/<id>` | View analysis details |
| `GET` | `/history` | View saved analyses |
| `GET` | `/api/history` | Retrieve analysis history as JSON |
| `GET` | `/api/analysis/<id>` | Retrieve a specific analysis as JSON |
| `DELETE` | `/api/analysis/<id>` | Delete an analysis |
| `GET` | `/api/analysis/<id>/export` | Export analysis results as CSV |

## Run Tests

Run the test suite from the project root:

```bash
python -m pytest
```

The included tests cover text cleaning, homepage loading, demo result persistence, history and detail routes, CSV export availability, and invalid URL handling. Model-specific evaluation should be performed separately with a trained model and an appropriately labeled test dataset.

## Data Storage

The application creates its SQLite database and `data/` directory automatically at startup. Each analysis record is associated with its comment-result records. Deleting an analysis also deletes its associated results.

## Limitations

- Toxicity predictions may be incorrect, especially for sarcasm, context-dependent language, spelling variations, and underrepresented languages.
- Results depend on the quality and suitability of the configured model and its training data.
- Confidence scores should not be treated as certainty.
- The demo fallback is not a validated toxicity detection model.
- Multilingual support should not be assumed unless the selected model has been trained and evaluated for the relevant languages.
- Automated classification should support, not replace, appropriate human review in consequential moderation decisions.

## Future Enhancements

- Add user authentication and per-user analysis history.
- Include model evaluation metrics and a labeled review workflow.
- Add background processing for large comment collections.
- Support additional permitted public data providers through modular adapters.
- Improve monitoring, logging, and deployment configuration.

## Responsible Use

This project is intended for educational and research purposes. Use it responsibly, respect platform policies and privacy, and ensure that any collection or analysis of comments is legally and ethically appropriate.
