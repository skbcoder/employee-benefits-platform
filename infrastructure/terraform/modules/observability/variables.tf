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
