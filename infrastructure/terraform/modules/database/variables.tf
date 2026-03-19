variable "name_prefix" {
  type = string
}

variable "environment" {
  type = string
}

variable "subnet_ids" {
  description = "Data-tier subnet IDs"
  type        = list(string)
}

variable "security_group_id" {
  description = "RDS security group ID"
  type        = string
}

variable "instance_class" {
  type    = string
  default = "db.t3.medium"
}

variable "multi_az" {
  type    = bool
  default = false
}

variable "password" {
  type      = string
  sensitive = true
}
