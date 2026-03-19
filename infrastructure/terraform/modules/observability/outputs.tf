output "enrollment_log_group_name" {
  value = aws_cloudwatch_log_group.enrollment.name
}

output "processing_log_group_name" {
  value = aws_cloudwatch_log_group.processing.name
}

output "ai_gateway_log_group_name" {
  value = aws_cloudwatch_log_group.ai_gateway.name
}

output "knowledge_service_log_group_name" {
  value = aws_cloudwatch_log_group.knowledge_service.name
}
