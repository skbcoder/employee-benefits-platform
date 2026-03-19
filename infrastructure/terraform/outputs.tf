output "alb_dns_name" {
  description = "Application Load Balancer DNS name"
  value       = module.ecs.alb_dns_name
}

output "rds_endpoint" {
  description = "RDS PostgreSQL endpoint"
  value       = module.database.endpoint
}

output "enrollment_queue_url" {
  description = "SQS queue URL for enrollment events"
  value       = module.messaging.queue_url
}

output "event_bus_arn" {
  description = "EventBridge bus ARN for enrollment events"
  value       = module.messaging.event_bus_arn
}

output "enrollment_ecr_url" {
  description = "ECR repository URL for enrollment service"
  value       = module.ecs.enrollment_ecr_url
}

output "processing_ecr_url" {
  description = "ECR repository URL for processing service"
  value       = module.ecs.processing_ecr_url
}
