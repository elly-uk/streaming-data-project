provider "aws" {
    region = var.aws_region
    access_key = var.aws_access_key_id
    secret_key = var.aws_secret_access_key_id
}

resource "aws_iam_role" "lambda_role" {
    name = "lambda-role"

    assume_role_policy = jsonencode({
        Version = "2012-10-17",
        Statement = [
        {
            Action = "sts:AssumeRole",
            Effect = "Allow",
            Principal = {
                Service = "lambda.amazonaws.com",
            },
        },
        ],
    })
}

resource "aws_iam_role_policy" "lambda_policy" {
    name   = "lambda_policy"
    role   = aws_iam_role.lambda_role.id

    policy = jsonencode({
        Version = "2012-10-17",
        Statement = [
        {
            # Allow Lambda to create and manage CloudWatch log groups and streams
            Action = [
                "logs:CreateLogGroup",
                "logs:CreateLogStream",
                "logs:PutLogEvents"
            ]
            Effect   = "Allow"
            Resource = "arn:aws:logs:*:*:*"
        },
        {
            # Allow Lambda to send messages to the specified SQS queue
            Action = "sqs:SendMessage"
            Effect   = "Allow"
            Resource = aws_sqs_queue.guardian_content.arn
        }
        ]
    })
}

# Create an SQS queue named "guardian_content" with a message retention period of 3 days
resource "aws_sqs_queue" "guardian_content" {
    name                      = "guardian_content"
    message_retention_seconds  = 259200  # 3 days
    policy                    = jsonencode({
        Version = "2012-10-17",
        Statement = [
            {
                Effect = "Allow"
                Action = "sqs:SendMessage"
                Principal = "*"
                Resource = "*"
            }
        ]
    })
}


# Create a Lambda function named "guardian_api" with the specified role, handler, and runtime
resource "aws_lambda_function" "guardian_api" {
    function_name = "guardian_api"
    role          = aws_iam_role.lambda_role.arn
    handler       = "lambda_function.lambda_handler"
    runtime       = "python3.8"
    timeout       = 60
    memory_size   = 512

    environment {
    variables = {
        GUARDIAN_API_KEY = var.guardian_api_key
        GUARDIAN_API_URL = var.guardian_api_url
        SQS_QUEUE_URL    = aws_sqs_queue.guardian_content.url
    }
    }

    source_code_hash = filebase64sha256("../lambda_function.zip")
    filename         = "../lambda_function.zip"
}

resource "aws_lambda_permission" "allow_sqs" {
    statement_id  = "AllowExecutionFromSQS"
    action        = "lambda:InvokeFunction"
    function_name = aws_lambda_function.guardian_api.function_name
    principal     = "sqs.amazonaws.com"
    source_arn    = aws_sqs_queue.guardian_content.arn
}
