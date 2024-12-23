"""
Tests for lambda_function.py
"""

import json
import time
from datetime import timedelta
from unittest.mock import Mock, patch

import pytest
from requests.exceptions import RequestException, Timeout

from src.lambda_function import (
    fetch_articles,
    lambda_handler,
    rate_limit
)


@pytest.fixture(autouse=True)
def set_environment_variables(monkeypatch):
    """Set environment variables for testing."""
    monkeypatch.setenv("SQS_QUEUE_URL", "http://mock-sqs-url.com")
    monkeypatch.setenv("GUARDIAN_API_URL", "https://test.guardianapi.com")
    monkeypatch.setenv("GUARDIAN_API_KEY", "mock-api-key")


@pytest.fixture
def mock_requests_get():
    """Fixture for mocking requests.get."""
    with patch("src.lambda_function.requests.get") as mock_get:
        yield mock_get


@pytest.fixture
def mock_successful_response():
    """Fixture for mocking a successful API response."""
    mock_response = Mock()
    mock_response.json.return_value = {
        "response": {
            "results": [
                {
                    "webPublicationDate": "2024-01-01T10:00:00Z",
                    "webTitle": "Test Article",
                    "webUrl": "http://test.com",
                    "fields": {"bodyText": "Test content"},
                }
            ]
        }
    }
    mock_response.raise_for_status.return_value = None
    return mock_response


@pytest.fixture
def mock_empty_response():
    """Fixture for empty API response."""
    mock_response = Mock()
    mock_response.json.return_value = {"response": {"results": []}}
    mock_response.raise_for_status.return_value = None
    return mock_response


@pytest.fixture
def mock_malformed_response():
    """Fixture for malformed API response."""
    mock_response = Mock()
    mock_response.json.return_value = {"malformed": "response"}
    mock_response.raise_for_status.return_value = None
    return mock_response


@pytest.fixture
def mock_sqs_client():
    """Fixture for mocking SQS client"""
    with patch("boto3.client") as mock_client:
        mock_sqs = Mock()
        mock_client.return_value = mock_sqs
        yield mock_sqs


class TestFetchArticles:
    """Tests for fetch_articles function."""

    @pytest.mark.it("Should fetch articles with all parameters")
    def test_should_fetch_articles_successfully(
        self,
        mock_requests_get,
        mock_successful_response,
        mock_sqs_client
    ):
        """Test successful fetch_articles call."""
        mock_requests_get.return_value = mock_successful_response
        mock_sqs_client.send_message.return_value = {
            "ResponseMetadata": {"HTTPStatusCode": 200}
        }

        articles = fetch_articles("test", "2024-01-01")

        assert len(articles) == 1, "Expected 1 article, got none"
        article = articles[0]
        assert article["webTitle"] == "Test Article"
        assert article["webUrl"] == "http://test.com"
        assert article["webPublicationDate"] == "2024-01-01T10:00:00Z"
        assert article["content_preview"] == "Test content"

    @pytest.mark.it("Should fetch articles without date_from")
    def test_should_fetch_articles_without_date_from(
        self, mock_requests_get, mock_successful_response, mock_sqs_client
    ):
        """Test fetch_articles call without date_from."""
        mock_requests_get.return_value = mock_successful_response
        mock_sqs_client.send_message.return_value = {
            "ResponseMetadata": {"HTTPStatusCode": 200}
        }

        articles = fetch_articles("test")

        assert len(articles) == 1, "Expected 1 article, got none"
        article = articles[0]
        assert article["webTitle"] == "Test Article"
        assert article["webUrl"] == "http://test.com"
        assert article["webPublicationDate"] == "2024-01-01T10:00:00Z"
        assert article["content_preview"] == "Test content"

    @pytest.mark.it("Should raise ValueError if API key is missing")
    def test_should_handle_missing_api_key(self):
        """Test missing API key."""
        with patch(
            "src.lambda_function.os.getenv",
            side_effect=lambda key: None if key == "GUARDIAN_API_KEY"
            else "mock-value",
        ):
            with pytest.raises(ValueError, match="API key is missing"):
                fetch_articles("test")

    @pytest.mark.it("Should raise ValueError if search term is empty")
    def test_should_handle_empty_search_term(self):
        """Test empty search term."""
        with pytest.raises(ValueError, match="Search term cannot be empty"):
            fetch_articles("")

    @pytest.mark.it("Should raise ValueError if SQS queue URL is missing")
    def test_should_handle_missing_sqs_queue_url(self):
        """Test missing SQS queue URL."""
        with patch(
            "src.lambda_function.os.getenv",
            side_effect=lambda key: None if key == "SQS_QUEUE_URL"
            else "mock-value",
        ):
            with pytest.raises(ValueError, match="SQS queue URL is missing"):
                fetch_articles("test")

    @pytest.mark.it("Should handle RequestException")
    def test_should_handle_request_exception(self, mock_requests_get):
        """Test handling RequestException."""
        mock_requests_get.side_effect = RequestException("API Error")
        with pytest.raises(RequestException):
            fetch_articles("test")

    @pytest.mark.it("Should handle Timeout")
    def test_should_handle_timeout(self, mock_requests_get):
        """Test handling Timeout."""
        mock_requests_get.side_effect = Timeout("Request timed out")
        with pytest.raises(Timeout):
            fetch_articles("test")

    @pytest.mark.it("Should handle empty response")
    def test_should_handle_empty_response(
            self,
            mock_requests_get,
            mock_empty_response):
        """Test handling empty response."""
        mock_requests_get.return_value = mock_empty_response
        articles = fetch_articles("test")
        assert articles == []

    @pytest.mark.it("Should handle malformed response")
    def test_should_handle_malformed_response(
            self,
            mock_requests_get,
            mock_malformed_response
    ):
        """Test handling malformed response."""
        mock_requests_get.return_value = mock_malformed_response
        articles = fetch_articles("test")
        assert articles == []

    @pytest.mark.it("Should handle generic exception")
    def test_should_handle_generic_exception(self, mock_requests_get):
        """Test handling generic exception."""
        mock_requests_get.side_effect = Exception("Generic error")
        articles = fetch_articles("test")
        assert articles == []


class TestLambdaHandler:
    """Tests for lambda_handler function."""

    @pytest.mark.it("Should handle successful fetch")
    @patch("src.lambda_function.fetch_articles")
    def test_lambda_handler_success(self, mock_fetch_articles):
        """Test successful lambda_handler call."""
        mock_fetch_articles.return_value = [{"webTitle": "Test Article"}]
        event = {"search_term": "test", "date_from": "2024-01-01"}

        response = lambda_handler(event, None)

        assert response["statusCode"] == 200
        assert json.loads(response["body"]) == [{"webTitle": "Test Article"}]

    @pytest.mark.it("Should return 500 and error message on exception.")
    @patch("src.lambda_function.fetch_articles")
    def test_lambda_handler_error(self, mock_fetch_articles):
        """Test lambda_handler call with exception."""
        mock_fetch_articles.side_effect = Exception("Error fetching articles")
        event = {"search_term": "test", "date_from": "2024-01-01"}

        response = lambda_handler(event, None)

        assert response["statusCode"] == 500
        error_message = json.loads(response["body"])["error"]
        assert "Error fetching articles" in error_message


class TestRateLimit:
    """Tests for rate_limit decorator."""

    @pytest.mark.it("Should allow requests within limit")
    def test_should_allow_requests_within_limit(self):
        """Test rate limit within allowed requests."""

        @rate_limit(max_requests=2, period=timedelta(seconds=1))
        def test_func():
            return True

        assert test_func() is True
        assert test_func() is True

    @pytest.mark.it("Should raise exception when rate limit is exceeded")
    def test_should_raise_exception_when_rate_limit_exceeded(self):
        """Test rate limit exceeding allowed requests."""

        @rate_limit(max_requests=1, period=timedelta(seconds=1))
        def test_func():
            return True

        test_func()
        with pytest.raises(Exception) as exc_info:
            test_func()
        assert "Rate limit exceeded" in str(exc_info.value)

    @pytest.mark.it("Should reset rate limit after period")
    def test_should_reset_rate_limit_after_period(self):
        """Test rate limit reset after period."""

        @rate_limit(max_requests=1, period=timedelta(seconds=1))
        def test_func():
            return True

        assert test_func() is True
        time.sleep(1)
        assert test_func() is True
