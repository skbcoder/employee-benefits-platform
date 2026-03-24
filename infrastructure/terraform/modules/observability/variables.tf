variable "name_prefix" {
  type = string
}

variable "environment" {
  type = string
}

variable "retention_days" {
  description = "CloudWatch log retention in days"
  type        = number
  default     = 30
}

variable "ecs_cluster_name" {
  description = "ECS cluster name for dashboard metrics"
  type        = string
  default     = ""
}

variable "db_instance_id" {
  description = "RDS instance identifier for dashboard metrics"
  type        = string
  default     = ""
}

variable "sqs_queue_name" {
  description = "SQS queue name for dashboard metrics"
  type        = string
  default     = ""
}

variable "dlq_queue_name" {
  description = "SQS dead-letter queue name for alarms"
  type        = string
  default     = ""
}
