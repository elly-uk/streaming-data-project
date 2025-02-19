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
- AWS account with **necessary permissions** (IAM, SQS, Lambda, and CloudWatch)
- AWS CLI configured with your credentials
- Register on the Guardian website to obtain an API key and API URL: https://open-platform.theguardian.com/access/ --> Click "Register Developer Key"

## Setup, Deployment, and Running Application

1. Open a terminal and run the following command to clone the repository
    ```sh
    git clone https://github.com/elly-uk/streaming-data-project
    cd streaming-data-project
    ```

2. Set up Terraform Variables
   - This project requires a `terraform.tfvars` file to configure sensitive variables such as AWS credentials. 
   - Create a `terraform.tfvars` file in the `terraform` directory with the following structure:
     ```hcl
        guardian_api_key = "your-api-key"
        guardian_api_url = "https://content.guardianapis.com/search"
     ```
   - **Important**: Alternatively, you can skip this step. The system will automatically handle these settings in Step 5.
   - **Important**: Do not include this file in version control for security reasons.

3. Set up the virtual environment and install requirements:
    ```sh
    make requirements
    ```
4. Run the application:
    ```sh
    make run
    ```
5. Deploy the application:
    ```sh
    make deploy
    ```
6. Test the Lambda function on AWS:
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

Relevant Link: View Tutorial Video --> https://drive.google.com/file/d/1ZZgfpFZj_Q4KOUuj1UQUeb-wx3FJwijj/view?usp=sharing

## Running Tests
Run test at any point after setting up the environment (after **" make requirements "**)
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
