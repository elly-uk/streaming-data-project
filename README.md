# Streaming Data Project

## Overview

This project is designed to fetch articles from the Guardian API and send them to an AWS SQS queue. The project includes a Lambda function that handles the fetching and publishing of articles, as well as a set of Terraform scripts to set up the necessary AWS infrastructure.

## Features

- Fetch articles from the Guardian API
- Publish articles to an AWS SQS queue
- Terraform scripts to set up AWS infrastructure
- Unit tests for the Lambda function and message broker
- Rate limiting to comply with API usage policies

## Prerequisites

- Python 3.8 or higher
- AWS account with necessary permissions
- AWS CLI configured with your credentials

## Setup, Deployment, and Running Application

1. Clone the repository
    ```sh
    git clone https://github.com/elly-uk/streaming-data-project
    cd streaming-data-project
    ```
2. Set up the virtual environment and install requirements:
    ```sh
    make requirements
    ```
3. Run the application:
    ```sh
    make run
    ```
4. Deploy the application:
    ```sh
    make deploy
    ```
5. Test the Lambda function on AWS:
   - Go to AWS > Lambda > Functions > `guardian_api`
   - Click "Test" and paste the following event:
    ```json
    {
        "search_term": "machine learning",
        "date_from": "2023-01-01"
    }
    ```
    or
    ```json
    {
        "search_term": "machine learning",
        "date_from": ""
    }
    ```
   - Click the "Test" button
   - Go to AWS > SQS > Queues > `guardian_content` > "Send and receive messages"
   - Click "Poll for messages"

Relevant Link: View Tutorial Video --> https://drive.google.com/file/d/1BJFynIqiK5t4NuONdwr_20SqdByfsbNj/view?usp=sharing

## Running Tests

- To run tests:
    ```sh
    make test
    ```
- To run tests with coverage:
    ```sh
    make coverage
    ```
- To check code style (PEP-8 compliance):
    ```sh
    make lint
    ```
- To run security checks:
    ```sh
    make security
    ```

Relevant Link: View Tutorial Video --> https://drive.google.com/file/d/1k2hx8YcPGiFQ9Q6K6wyKfzXJnCEGQ1ek/view?usp=sharing

## Destroying the Deployment and Cleaning Up

- To destroy the application on AWS:
    ```sh
    make destroy
    ```
- To clean up the environment and remove generated files:
    ```sh
    make clean
    ```

## Help

- To display available commands:
    ```sh
    make help
    ```