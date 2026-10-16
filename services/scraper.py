from __future__ import annotations

from typing import Any

import requests


DEMO_COMMENTS = [
    {"id": "demo-1", "text": "Beautiful post!", "username": "maya", "timestamp": ""},
    {"id": "demo-2", "text": "I really like this.", "username": "arjun", "timestamp": ""},
    {"id": "demo-3", "text": "This is terrible.", "username": "rhea", "timestamp": ""},
    {"id": "demo-4", "text": "You are an idiot.", "username": "sam", "timestamp": ""},
    {"id": "demo-5", "text": "The content is amazing.", "username": "noah", "timestamp": ""},
    {"id": "demo-6", "text": "Not my favorite, but keep creating.", "username": "zoe", "timestamp": ""},
    {"id": "demo-7", "text": "What a thoughtful idea ✨", "username": "lina", "timestamp": ""},
    {"id": "demo-8", "text": "This is dumb and pointless.", "username": "dev", "timestamp": ""},
    {"id": "demo-9", "text": "Where was nkr 😒", "username": "emma", "timestamp": ""},
    {"id": "demo-10", "text": "nuvvu oka vedhava", "username": "liam", "timestamp": ""},
    {"id": "demo-11", "text": "bullshit", "username": "olivia", "timestamp": ""},
    {"id": "demo-12", "text": "lanjakodaka", "username": "lucas", "timestamp": ""},
    {"id": "demo-13", "text": "great job🔥", "username": "sophia", "timestamp": ""},
]


class ScraperError(RuntimeError):
    pass


def _first_value(item: dict[str, Any], *keys: str) -> Any:
    """Return the first non-empty value from a list of possible API field names."""
    for key in keys:
        value = item.get(key)
        if value is not None and value != "":
            return value
    return ""


def normalize_comment(item: Any, index: int) -> dict[str, str]:
    """Normalize one Apify comment/reply into the application's format."""
    if isinstance(item, str):
        return {
            "id": str(index),
            "text": item,
            "username": "",
            "timestamp": "",
        }

    if not isinstance(item, dict):
        return {
            "id": str(index),
            "text": "",
            "username": "",
            "timestamp": "",
        }

    # The official Apify Instagram Comment Scraper uses fields such as
    # pk, username, text and created_at. Other Instagram actors use id,
    # ownerUsername and timestamp, so support both.
    comment_id = _first_value(
        item,
        "pk",
        "id",
        "commentId",
        "comment_id",
        "shortcode",
    )

    text = _first_value(
        item,
        "text",
        "comment",
        "commentText",
        "body",
        "caption",
    )

    username = _first_value(
        item,
        "username",
        "ownerUsername",
        "owner_username",
        "userName",
    )

    timestamp = _first_value(
        item,
        "created_at",
        "createdAt",
        "timestamp",
        "takenAt",
    )

    # Some actors put the author inside a nested user/owner object.
    if not username:
        user = item.get("user") or item.get("owner")
        if isinstance(user, dict):
            username = _first_value(
                user,
                "username",
                "userName",
                "name",
            )

    return {
        "id": str(comment_id or index),
        "text": str(text or ""),
        "username": str(username or ""),
        "timestamp": str(timestamp or ""),
    }


def _extract_comment_items(payload: Any) -> list[Any]:
    """
    Extract comment records from several common Apify response shapes.

    Normally the Dataset API returns a list where each item is one comment.
    Some actors instead wrap records in comments/items/data/results.
    """
    if isinstance(payload, list):
        return payload

    if isinstance(payload, dict):
        for key in ("items", "comments", "results", "data"):
            value = payload.get(key)
            if isinstance(value, list):
                return value

        # A single comment object.
        if any(
            key in payload
            for key in (
                "text",
                "comment",
                "commentText",
                "pk",
                "commentId",
            )
        ):
            return [payload]

    return []


def _flatten_comments(items: list[Any]) -> list[dict[str, str]]:
    """
    Flatten top-level comments and nested replies.

    Different Apify actors expose replies under different names, including
    replies, comments, childComments and nestedComments.
    """
    flattened: list[dict[str, str]] = []

    def visit(item: Any, fallback_index: int) -> None:
        if not isinstance(item, dict):
            normalized = normalize_comment(item, fallback_index)
            if normalized["text"].strip():
                flattened.append(normalized)
            return

        normalized = normalize_comment(item, fallback_index)

        # Add the parent/top-level comment first.
        if normalized["text"].strip():
            flattened.append(normalized)

        # Then add nested replies as separate comments.
        for key in (
            "replies",
            "comments",
            "childComments",
            "nestedComments",
            "repliesData",
        ):
            children = item.get(key)
            if isinstance(children, list):
                for child_index, child in enumerate(children):
                    visit(child, f"{fallback_index}-reply-{child_index}")

    for index, item in enumerate(items):
        visit(item, index)

    return flattened


def _deduplicate_comments(
    comments: list[dict[str, str]],
) -> list[dict[str, str]]:
    """Remove duplicate records while preserving the order returned by Apify."""
    result: list[dict[str, str]] = []
    seen_ids: set[str] = set()
    seen_fallbacks: set[tuple[str, str, str]] = set()

    for comment in comments:
        comment_id = comment.get("id", "").strip()
        text = comment.get("text", "").strip()
        username = comment.get("username", "").strip()
        timestamp = comment.get("timestamp", "").strip()

        if not text:
            continue

        if comment_id:
            if comment_id in seen_ids:
                continue
            seen_ids.add(comment_id)
        else:
            fallback = (text, username, timestamp)
            if fallback in seen_fallbacks:
                continue
            seen_fallbacks.add(fallback)

        result.append(comment)

    return result


def scrape_comments(
    instagram_url: str,
    *,
    mock_mode: bool,
    apify_token: str = "",
    actor_id: str = "apify/instagram-comment-scraper",
) -> list[dict[str, str]]:
    """
    Scrape comments from an Instagram post/reel.

    The application expects a list containing one dictionary per comment.
    The Apify actor is asked for up to 1,000 comments and replies are
    flattened into the same list so the classifier can process them all.
    """
    if mock_mode:
        return DEMO_COMMENTS.copy()

    if not apify_token:
        raise ScraperError(
            "Apify is not configured. Set APIFY_API_TOKEN "
            "or enable MOCK_SCRAPER for demo data."
        )

    # Apify's official Instagram Comment Scraper accepts directUrls and
    # resultsLimit. Replies can be returned as separate results when
    # includeNestedComments is enabled.
    endpoint = (
        f"https://api.apify.com/v2/acts/"
        f"{actor_id.replace('/', '~')}/runs"
        f"?token={apify_token}&waitForFinish=120"
    )

    run_input = {
        "directUrls": [instagram_url],
        "resultsLimit": 1000,
        "includeNestedComments": True,
    }

    try:
        response = requests.post(
            endpoint,
            json=run_input,
            timeout=135,
        )
        response.raise_for_status()

        run_data = response.json().get("data", {})
        dataset_id = run_data.get("defaultDatasetId")

        if not dataset_id:
            raise ScraperError(
                "Apify completed without returning a comment dataset."
            )

        # Request a large page and explicitly sort/clean the dataset response.
        # The Dataset API returns one dataset item per comment for the official
        # Instagram Comment Scraper.
        dataset_response = requests.get(
            f"https://api.apify.com/v2/datasets/{dataset_id}/items",
            params={
                "token": apify_token,
                "clean": "true",
                "format": "json",
                "limit": 1000,
            },
            timeout=60,
        )
        dataset_response.raise_for_status()

        payload = dataset_response.json()
        raw_items = _extract_comment_items(payload)

        if not raw_items:
            raise ScraperError(
                "Apify completed successfully, but returned no comment records."
            )

        comments = _flatten_comments(raw_items)
        comments = _deduplicate_comments(comments)

        if not comments:
            raise ScraperError(
                "Apify returned records, but no comment text could be extracted."
            )

        print(f"Scraper: received {len(comments)} comments from Apify.")
        return comments

    except requests.RequestException as exc:
        raise ScraperError(
            "Apify could not be reached or rejected the request."
        ) from exc
    except ValueError as exc:
        raise ScraperError(
            "Apify returned invalid JSON data."
        ) from exc
