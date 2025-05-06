import pytest
from fastapi.testclient import TestClient
from typing import Generator
from app.main import app
from app.config import get_settings, Settings
from app.core.logging import setup_logger

@pytest.fixture
def test_settings() -> Settings:
    """Override settings for testing."""
    settings = get_settings()
    settings.ENV = "test"
    settings.DEBUG = True
    settings.HUGGINGFACE_API_KEY = "test_key"
    return settings

@pytest.fixture
def client(test_settings) -> Generator:
    """Create a test client."""
    with TestClient(app) as c:
        yield c

@pytest.fixture
def test_logger():
    """Create a test logger."""
    return setup_logger("test")