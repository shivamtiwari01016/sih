"""Test configuration for the CivicResolve API.

The suite runs against an isolated SQLite database and exercises the real
FastAPI application (routing, auth, validation, serialisation, persistence).
"""
import os
import sys
import tempfile

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
TEST_DB_PATH = os.path.join(tempfile.gettempdir(), "civicresolve_test.db").replace("\\", "/")

os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB_PATH}"
os.environ["USE_SEMANTIC_MATCHING"] = "False"
os.environ["SECRET_KEY"] = "test-secret-key-for-integration-tests"

for path in (BACKEND_DIR, TESTS_DIR):
    if path not in sys.path:
        sys.path.insert(0, path)

import pytest  # noqa: E402

import helpers  # noqa: E402


@pytest.fixture(scope="session")
def client():
    with helpers.make_client() as test_client:
        yield test_client


@pytest.fixture(autouse=True)
def reset_database():
    helpers.reset_database()
    yield
