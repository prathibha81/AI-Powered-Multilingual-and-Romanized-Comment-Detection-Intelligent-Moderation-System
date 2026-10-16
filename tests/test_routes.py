import tempfile
from pathlib import Path

from app import create_app


class TestConfig:
    TESTING = True
    SECRET_KEY = "test"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    MOCK_SCRAPER = True
    MODEL_PATH = str(Path(tempfile.mkdtemp()) / "missing-model")
    DATABASE_URL = f"sqlite:///{Path(tempfile.mkdtemp()) / 'test.db'}"
    BATCH_SIZE = 4
    MAX_LENGTH = 128
    MAX_COMMENTS = 100
    APIFY_API_TOKEN = ""
    APIFY_ACTOR_ID = "apify/instagram-comment-scraper"


def test_homepage_and_demo_flow():
    client = create_app(TestConfig).test_client()
    assert client.get("/").status_code == 200
    response = client.post("/api/demo")
    assert response.status_code == 200
    payload = response.get_json()
    assert payload["success"] is True
    assert payload["total_comments"] == 8
    assert payload["analysis_id"] == 1
    assert client.get("/history").status_code == 200
    assert client.get(f"/analysis/{payload['analysis_id']}").status_code == 200
    assert client.get(f"/api/analysis/{payload['analysis_id']}/export").status_code == 200


def test_invalid_url_is_rejected():
    client = create_app(TestConfig).test_client()
    response = client.post("/api/analyze", json={"url": "https://example.com/post"})
    assert response.status_code == 400
    assert response.get_json()["success"] is False