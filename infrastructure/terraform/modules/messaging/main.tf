###############################################################################
# EventBridge custom bus + SQS queue with DLQ for enrollment events
###############################################################################

resource "aws_cloudwatch_event_bus" "this" {
  name = "${var.name_prefix}-enrollment-events"
}

resource "aws_sqs_queue" "dlq" {
  name                      = "${var.name_prefix}-enrollment-dlq"
  message_retention_seconds = 1209600 # 14 days
}

resource "aws_sqs_queue" "this" {
  name                       = "${var.name_prefix}-enrollment-processing"
  visibility_timeout_seconds = 60
  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.dlq.arn
    maxReceiveCount     = 3
  })
}

resource "aws_cloudwatch_event_rule" "enrollment_submitted" {
  name           = "${var.name_prefix}-enrollment-submitted"
  event_bus_name = aws_cloudwatch_event_bus.this.name
  event_pattern = jsonencode({
    detail-type = ["EnrollmentSubmitted"]
  })
}

resource "aws_cloudwatch_event_target" "sqs" {
  rule           = aws_cloudwatch_event_rule.enrollment_submitted.name
  event_bus_name = aws_cloudwatch_event_bus.this.name
  target_id      = "processing-queue"
  arn            = aws_sqs_queue.this.arn
}

resource "aws_sqs_queue_policy" "allow_eventbridge" {
  queue_url = aws_sqs_queue.this.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "events.amazonaws.com" }
      Action    = "sqs:SendMessage"
      Resource  = aws_sqs_queue.this.arn
      Condition = {
        ArnEquals = {
          "aws:SourceArn" = aws_cloudwatch_event_rule.enrollment_submitted.arn
        }
      }
    }]
  })
}
