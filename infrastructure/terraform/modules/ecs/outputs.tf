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
