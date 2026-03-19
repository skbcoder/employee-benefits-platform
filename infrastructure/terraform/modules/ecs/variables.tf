variable "name_prefix" {
  type = string
}

variable "environment" {
  type = string
}

variable "aws_region" {
  type = string
}

variable "vpc_id" {
  type = string
}

variable "public_subnet_ids" {
  type = list(string)
}

variable "private_subnet_ids" {
  type = list(string)
}

variable "alb_security_group_id" {
  type = string
}

variable "ecs_security_group_id" {
  type = string
}

variable "db_endpoint" {
  type = string
}

variable "db_password" {
  type      = string
  sensitive = true
}

variable "event_bus_arn" {
  description = "EventBridge bus ARN for publish permissions"
  type        = string
}

variable "sqs_queue_arn" {
  description = "SQS queue ARN for consume permissions"
  type        = string
}

variable "enrollment_service_image" {
  type = string
}

variable "processing_service_image" {
  type = string
}

variable "enrollment_log_group_name" {
  type = string
}

variable "processing_log_group_name" {
  type = string
}
