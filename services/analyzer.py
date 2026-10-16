from __future__ import annotations

import re
from typing import Any

from flask import current_app

from models import Analysis, CommentResult, db
from services.classifier import ClassifierService
from services.scraper import ScraperError, scrape_comments
from utils.text_cleaner import clean_comment


class InvalidInstagramUrl(ValueError):
    pass


class NoCommentsError(ValueError):
    pass


INSTAGRAM_HOSTS = {"instagram.com", "www.instagram.com", "m.instagram.com"}
INSTAGRAM_URL_RE = re.compile(r"^https?://([^/]+)/.+", re.IGNORECASE)


def validate_instagram_url(value: str) -> str:
    url = (value or "").strip()
    match = INSTAGRAM_URL_RE.match(url)
    if not match or match.group(1).lower() not in INSTAGRAM_HOSTS:
        raise InvalidInstagramUrl(
            "Enter a valid public Instagram post or reel URL, such as https://www.instagram.com/p/..."
        )
    return url


def _classifier() -> ClassifierService:
    service = current_app.extensions.get("toxicity_classifier")
    if service is None:
        service = ClassifierService(
            current_app.config["MODEL_PATH"],
            batch_size=current_app.config["BATCH_SIZE"],
            max_length=current_app.config["MAX_LENGTH"],
        )
        current_app.extensions["toxicity_classifier"] = service
    return service


def run_analysis(
    source_url: str,
    comments: list[dict[str, Any]],
    *,
    is_demo: bool,
) -> Analysis:
    max_comments = current_app.config["MAX_COMMENTS"]
    total_scraped = len(comments)
    selected = comments[:max_comments]
    prepared: list[dict[str, str]] = []
    for comment in selected:
        cleaned = clean_comment(comment.get("text"))
        if cleaned["cleaned_text"]:
            prepared.append(
                {
                    **cleaned,
                    "username": str(comment.get("username") or ""),
                    "timestamp": str(comment.get("timestamp") or ""),
                }
            )
    if not prepared:
        raise NoCommentsError("No comments were found for this analysis.")

    predictions = _classifier().classify_batch(
        [item["cleaned_text"] for item in prepared], allow_demo_fallback=True
    )
    toxic = sum(1 for result in predictions if result["label"] == "TOXIC")
    total = len(predictions)
    average_confidence = sum(result["confidence"] for result in predictions) / total

    analysis = Analysis(
        source_url=source_url,
        is_demo=is_demo,
        total_scraped=total_scraped,
        comments_analyzed=total,
        total_comments=total,
        toxic_comments=toxic,
        non_toxic_comments=total - toxic,
        toxicity_percentage=(toxic / total * 100) if total else 0,
        average_confidence=average_confidence if total else 0,
    )
    for item, prediction in zip(prepared, predictions):
        analysis.comments.append(
            CommentResult(
                comment_text=item["original_text"],
                cleaned_text=item["cleaned_text"],
                label=prediction["label"],
                confidence=prediction["confidence"],
                username=item["username"],
                timestamp=item["timestamp"],
            )
        )
    db.session.add(analysis)
    db.session.commit()
    return analysis


def analyze_url(url: str, *, is_demo: bool = False) -> Analysis:
    validated = validate_instagram_url(url)
    comments = scrape_comments(
        validated,
        mock_mode=current_app.config["MOCK_SCRAPER"],
        apify_token=current_app.config["APIFY_API_TOKEN"],
        actor_id=current_app.config["APIFY_ACTOR_ID"],
    )
    return run_analysis(validated, comments, is_demo=is_demo)
