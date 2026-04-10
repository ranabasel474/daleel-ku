import sys
import os
import pytest
from unittest import mock
from dotenv import load_dotenv

# Put backend/ on sys.path so "from app import create_app" resolves correctly.
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Load backend/.env so config.py finds its required env vars when imported.
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"))

# routes/chat.py calls build_index() at module level (line 25).
# This patch must be started before create_app() triggers that import so
# no PDF files are read and no OpenAI embedding calls are made.
_build_index_patcher = mock.patch(
    "rag.ingest.build_index", return_value=mock.MagicMock()
)
_build_index_patcher.start()


@pytest.fixture(scope="session")
def app():
    from app import create_app

    flask_app = create_app()
    flask_app.config["TESTING"] = True
    return flask_app


@pytest.fixture
def client(app):
    return app.test_client()
