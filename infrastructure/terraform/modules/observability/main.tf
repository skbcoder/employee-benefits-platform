###############################################################################
# CloudWatch log groups for ECS services
###############################################################################

resource "aws_cloudwatch_log_group" "enrollment" {
  name              = "/ecs/${var.environment}/enrollment"
  retention_in_days = var.retention_days
  tags              = { Service = "enrollment" }
}

resource "aws_cloudwatch_log_group" "processing" {
  name              = "/ecs/${var.environment}/processing"
  retention_in_days = var.retention_days
  tags              = { Service = "processing" }
}

resource "aws_cloudwatch_log_group" "ai_gateway" {
  name              = "/ecs/${var.environment}/ai-gateway"
  retention_in_days = var.retention_days
  tags              = { Service = "ai-gateway" }
}

resource "aws_cloudwatch_log_group" "knowledge_service" {
  name              = "/ecs/${var.environment}/knowledge-service"
  retention_in_days = var.retention_days
  tags              = { Service = "knowledge-service" }
}
