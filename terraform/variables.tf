variable "aws_region" {
  description = "AWS Region"
  type        = string
  default = "eu-west-2"
}

variable "guardian_api_key" {
  description = "Guardian API Key"
  type        = string
}

variable "guardian_api_url" {
  description = "Guardian API URL"
  type        = string
}

variable "aws_access_key_id" {
  description = "AWS Access Key ID"
  type        = string
}

variable "aws_secret_access_key_id" {
  description = "AWS Secret Access Key ID"
  type        = string
}

variable "sqs_queue_url" {
  description = "SQS Queue URL"
  type        = string
}

