import re
from typing import Any


WHITESPACE_RE = re.compile(r"\s+")


def clean_comment(value: Any) -> dict[str, str]:
    """Keep expressive punctuation and emoji while normalizing whitespace."""
    original = "" if value is None else str(value)
    cleaned = WHITESPACE_RE.sub(" ", original.strip())
    return {"original_text": original, "cleaned_text": cleaned}


def clean_comments(values: list[Any]) -> list[dict[str, str]]:
    return [
        cleaned
        for cleaned in (clean_comment(value) for value in values)
        if cleaned["cleaned_text"]
    ]
