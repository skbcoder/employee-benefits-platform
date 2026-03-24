output "cluster_id" {
  value = aws_ecs_cluster.this.id
}

output "alb_dns_name" {
  value = aws_lb.this.dns_name
}

output "enrollment_ecr_url" {
  value = aws_ecr_repository.enrollment.repository_url
}

output "processing_ecr_url" {
  value = aws_ecr_repository.processing.repository_url
}

output "ai_gateway_ecr_url" {
  value = aws_ecr_repository.ai_gateway.repository_url
}

output "orchestrator_ecr_url" {
  value = aws_ecr_repository.orchestrator.repository_url
}

output "knowledge_service_ecr_url" {
  value = aws_ecr_repository.knowledge_service.repository_url
}

output "governance_ecr_url" {
  value = aws_ecr_repository.governance.repository_url
}

output "cluster_name" {
  value = aws_ecs_cluster.this.name
}
