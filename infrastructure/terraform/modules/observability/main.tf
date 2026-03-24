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

resource "aws_cloudwatch_log_group" "orchestrator" {
  name              = "/ecs/${var.environment}/orchestrator"
  retention_in_days = var.retention_days
  tags              = { Service = "orchestrator" }
}

resource "aws_cloudwatch_log_group" "governance" {
  name              = "/ecs/${var.environment}/governance"
  retention_in_days = var.retention_days
  tags              = { Service = "governance" }
}

# ── CloudWatch Dashboard ──────────────────────────────────────────

resource "aws_cloudwatch_dashboard" "main" {
  dashboard_name = "${var.name_prefix}-${var.environment}"
  dashboard_body = jsonencode({
    widgets = [
      {
        type = "metric"
        properties = {
          title  = "ECS Service Health"
          metrics = [
            ["AWS/ECS", "CPUUtilization", "ClusterName", var.ecs_cluster_name],
            ["AWS/ECS", "MemoryUtilization", "ClusterName", var.ecs_cluster_name],
          ]
          period = 300
          stat   = "Average"
        }
      },
      {
        type = "metric"
        properties = {
          title   = "RDS Performance"
          metrics = [
            ["AWS/RDS", "DatabaseConnections", "DBInstanceIdentifier", var.db_instance_id],
            ["AWS/RDS", "ReadLatency", "DBInstanceIdentifier", var.db_instance_id],
            ["AWS/RDS", "WriteLatency", "DBInstanceIdentifier", var.db_instance_id],
          ]
          period = 300
          stat   = "Average"
        }
      },
      {
        type = "metric"
        properties = {
          title   = "SQS Queue Depth"
          metrics = [
            ["AWS/SQS", "ApproximateNumberOfMessagesVisible", "QueueName", var.sqs_queue_name],
            ["AWS/SQS", "ApproximateAgeOfOldestMessage", "QueueName", var.sqs_queue_name],
          ]
          period = 60
          stat   = "Maximum"
        }
      }
    ]
  })
}

# ── CloudWatch Alarms ─────────────────────────────────────────────

resource "aws_cloudwatch_metric_alarm" "rds_cpu" {
  alarm_name          = "${var.name_prefix}-${var.environment}-rds-high-cpu"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "CPUUtilization"
  namespace           = "AWS/RDS"
  period              = 300
  statistic           = "Average"
  threshold           = 80
  alarm_description   = "RDS CPU > 80% for 10 minutes"
  dimensions = { DBInstanceIdentifier = var.db_instance_id }
}

resource "aws_cloudwatch_metric_alarm" "sqs_dlq" {
  alarm_name          = "${var.name_prefix}-${var.environment}-sqs-dlq-messages"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "ApproximateNumberOfMessagesVisible"
  namespace           = "AWS/SQS"
  period              = 60
  statistic           = "Sum"
  threshold           = 0
  alarm_description   = "Messages in DLQ — failed event processing"
  dimensions = { QueueName = var.dlq_queue_name }
}
