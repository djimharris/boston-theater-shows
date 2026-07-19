"""Shared test fixtures and utilities."""

import os
import pytest


FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")


@pytest.fixture
def fixture_path():
    """Returns a function to get the path to a fixture file."""
    def _get_path(filename):
        return os.path.join(FIXTURES_DIR, filename)
    return _get_path


@pytest.fixture
def load_fixture():
    """Returns a function that loads and returns fixture HTML content."""
    def _load(filename):
        path = os.path.join(FIXTURES_DIR, filename)
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    return _load


@pytest.fixture
def mock_session():
    """Creates a mock requests session that returns fixture HTML."""
    import responses

    @responses.activate
    def _setup(url, fixture_filename):
        html = _load_fixture(fixture_filename)
        responses.add(responses.GET, url, body=html, status=200)
        return responses

    return _setup


def _load_fixture(filename):
    path = os.path.join(FIXTURES_DIR, filename)
    with open(path, "r", encoding="utf-8") as f:
        return f.read()
