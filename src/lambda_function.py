"""
    Fetch articles from the Guardian API and send them to an SQS queue.
"""

import json
import logging
import os
from datetime import datetime, timedelta
from functools import wraps
from typing import Callable

import boto3
import requests
from requests.exceptions import RequestException, Timeout

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()


def rate_limit(
    max_requests: int = 50, period: timedelta = timedelta(days=1)
) -> Callable:
    """
    Rate limit decorator.
    """
    message_requests = []

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            now = datetime.now()

            nonlocal message_requests
            message_requests[:] = [
                req_time for req_time in message_requests
                if now - req_time < period
            ]

            if len(message_requests) >= max_requests:
                raise Exception(
                    f"Rate limit exceeded. Maximum {max_requests} "
                    f"message requests per {period.days} days."
                )

            message_requests.append(now)
            return func(*args, **kwargs)

        return wrapper

    return decorator


@rate_limit()
def fetch_articles(search_term, date_from=None):
    """
    Fetch articles from the Guardian API and send them to an SQS queue.
    """
    GUARDIAN_API_URL = os.getenv("GUARDIAN_API_URL")
    GUARDIAN_API_KEY = os.getenv("GUARDIAN_API_KEY")
    SQS_QUEUE_URL = os.getenv("SQS_QUEUE_URL")

    if not GUARDIAN_API_KEY:
        raise ValueError(
            "API key is missing. Please set the GUARDIAN_API_KEY environment "
            "variable."
        )

    if not search_term or not search_term.strip():
        raise ValueError("Search term cannot be empty")

    if not SQS_QUEUE_URL:
        raise ValueError(
            "SQS queue URL is missing. Please set the SQS_QUEUE_URL "
            "environment variable."
        )

    params = {
        "q": f'"{search_term}"',
        "api-key": GUARDIAN_API_KEY,
        "page-size": 10,
        "order-by": "newest",
        "show-fields": "bodyText",
    }

    if date_from:
        params["from-date"] = date_from

    try:
        response = requests.get(GUARDIAN_API_URL, params=params, timeout=30)
        response.raise_for_status()
        articles = response.json().get("response", {}).get("results", [])
        transformed_articles = [
            {
                "webPublicationDate": article["webPublicationDate"],
                "webTitle": article["webTitle"],
                "webUrl": article["webUrl"],
                "content_preview": article.get("fields", {})
                .get("bodyText", "")[:1000],
            }
            for article in articles
            if all(
                field in article
                for field in ["webPublicationDate", "webTitle", "webUrl"]
            )
        ]

        sqs = boto3.client("sqs", region_name="eu-west-2")
        for article in transformed_articles:
            sqs.send_message(
                QueueUrl=SQS_QUEUE_URL,
                MessageBody=json.dumps(article)
            )

        return transformed_articles

    except (RequestException, Timeout) as e:
        logger.error(f"Error fetching articles: {e}")
        raise e
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return []


def lambda_handler(event, context):
    """
    Lambda function handler to fetch articles from the Guardian API.
    """
    search_term = event.get("search_term", "machine learning")
    date_from = event.get("date_from", None)

    try:
        articles = fetch_articles(search_term, date_from)
        return {"statusCode": 200, "body": json.dumps(articles)}
    except Exception as e:
        logger.error(f"Error in lambda_handler: {e}")
        return {"statusCode": 500, "body": json.dumps({"error": str(e)})}