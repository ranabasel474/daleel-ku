import sys
import os
import pytest
from unittest import mock
from dotenv import load_dotenv

#Add backend/ to the import path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

#Load backend/.env before importing app code
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"))

#Mock build_index before app import so tests do not parse files or call embeddings
_build_index_patcher = mock.patch(
    "rag.ingest.build_index", return_value=mock.MagicMock()
)
_build_index_patcher.start()

@pytest.fixture(scope="session")
def app():
    #Create one Flask app instance for the full test session
    from app import create_app

    flask_app = create_app()
    flask_app.config["TESTING"] = True
    return flask_app

@pytest.fixture
def client(app):
    #Return a test client for making requests in tests
    return app.test_client()
