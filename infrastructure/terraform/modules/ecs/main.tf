###############################################################################
# ECS Fargate cluster, IAM roles, ALB, task definitions, services
###############################################################################

# ── Cluster ─────────────────────────────────────────────────────────

resource "aws_ecs_cluster" "this" {
  name = "${var.name_prefix}-cluster"
}

# ── IAM Roles ───────────────────────────────────────────────────────

resource "aws_iam_role" "execution" {
  name = "${var.name_prefix}-ecs-execution"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action    = "sts:AssumeRole"
      Effect    = "Allow"
      Principal = { Service = "ecs-tasks.amazonaws.com" }
    }]
  })
}

resource "aws_iam_role_policy_attachment" "execution" {
  role       = aws_iam_role.execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

resource "aws_iam_role" "task" {
  name = "${var.name_prefix}-ecs-task"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action    = "sts:AssumeRole"
      Effect    = "Allow"
      Principal = { Service = "ecs-tasks.amazonaws.com" }
    }]
  })
}

resource "aws_iam_role_policy" "eventbridge_publish" {
  name = "eventbridge-publish"
  role = aws_iam_role.task.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = ["events:PutEvents"]
      Resource = var.event_bus_arn
    }]
  })
}

resource "aws_iam_role_policy" "sqs_consume" {
  name = "sqs-consume"
  role = aws_iam_role.task.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = ["sqs:ReceiveMessage", "sqs:DeleteMessage", "sqs:GetQueueAttributes"]
      Resource = var.sqs_queue_arn
    }]
  })
}

# ── ECR Repositories ────────────────────────────────────────────────

resource "aws_ecr_repository" "enrollment" {
  name = "${var.name_prefix}-enrollment-service"
}

resource "aws_ecr_repository" "processing" {
  name = "${var.name_prefix}-processing-service"
}

# ── ALB ─────────────────────────────────────────────────────────────

resource "aws_lb" "this" {
  name               = "${var.name_prefix}-alb"
  load_balancer_type = "application"
  subnets            = var.public_subnet_ids
  security_groups    = [var.alb_security_group_id]
}

resource "aws_lb_listener" "http" {
  load_balancer_arn = aws_lb.this.arn
  port              = 80
  protocol          = "HTTP"
  default_action {
    type = "fixed-response"
    fixed_response {
      content_type = "text/plain"
      message_body = "Not Found"
      status_code  = "404"
    }
  }
}

resource "aws_lb_target_group" "enrollment" {
  name        = "${var.name_prefix}-enroll-tg"
  port        = 8080
  protocol    = "HTTP"
  vpc_id      = var.vpc_id
  target_type = "ip"
  health_check {
    path     = "/actuator/health"
    interval = 30
  }
}

resource "aws_lb_listener_rule" "enrollment" {
  listener_arn = aws_lb_listener.http.arn
  priority     = 10
  condition {
    path_pattern { values = ["/api/enrollments*"] }
  }
  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.enrollment.arn
  }
}

# ── Task Definitions ────────────────────────────────────────────────

resource "aws_ecs_task_definition" "enrollment" {
  family                   = "${var.name_prefix}-enrollment"
  cpu                      = 512
  memory                   = 1024
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  execution_role_arn       = aws_iam_role.execution.arn
  task_role_arn            = aws_iam_role.task.arn

  container_definitions = jsonencode([{
    name         = "enrollment-service"
    image        = var.enrollment_service_image
    portMappings = [{ containerPort = 8080 }]
    environment = [
      { name = "DB_HOST", value = var.db_endpoint },
      { name = "DB_PORT", value = "5432" },
      { name = "DB_NAME", value = "employee_benefits_platform" },
      { name = "DB_USERNAME", value = "benefits_app" },
      { name = "DB_PASSWORD", value = var.db_password },
      { name = "PUBLISHER_TRANSPORT", value = "eventbridge" },
    ]
    logConfiguration = {
      logDriver = "awslogs"
      options = {
        "awslogs-group"         = var.enrollment_log_group_name
        "awslogs-region"        = var.aws_region
        "awslogs-stream-prefix" = "ecs"
      }
    }
  }])
}

resource "aws_ecs_task_definition" "processing" {
  family                   = "${var.name_prefix}-processing"
  cpu                      = 512
  memory                   = 1024
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  execution_role_arn       = aws_iam_role.execution.arn
  task_role_arn            = aws_iam_role.task.arn

  container_definitions = jsonencode([{
    name         = "processing-service"
    image        = var.processing_service_image
    portMappings = [{ containerPort = 8081 }]
    environment = [
      { name = "DB_HOST", value = var.db_endpoint },
      { name = "DB_PORT", value = "5432" },
      { name = "DB_NAME", value = "employee_benefits_platform" },
      { name = "DB_USERNAME", value = "benefits_app" },
      { name = "DB_PASSWORD", value = var.db_password },
      { name = "ENROLLMENT_SERVICE_URL", value = "http://${aws_lb.this.dns_name}" },
    ]
    logConfiguration = {
      logDriver = "awslogs"
      options = {
        "awslogs-group"         = var.processing_log_group_name
        "awslogs-region"        = var.aws_region
        "awslogs-stream-prefix" = "ecs"
      }
    }
  }])
}

# ── ECS Services ────────────────────────────────────────────────────

resource "aws_ecs_service" "enrollment" {
  name            = "enrollment-service"
  cluster         = aws_ecs_cluster.this.id
  task_definition = aws_ecs_task_definition.enrollment.arn
  desired_count   = 1
  launch_type     = "FARGATE"

  network_configuration {
    subnets         = var.private_subnet_ids
    security_groups = [var.ecs_security_group_id]
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.enrollment.arn
    container_name   = "enrollment-service"
    container_port   = 8080
  }
}

resource "aws_ecs_service" "processing" {
  name            = "processing-service"
  cluster         = aws_ecs_cluster.this.id
  task_definition = aws_ecs_task_definition.processing.arn
  desired_count   = 1
  launch_type     = "FARGATE"

  network_configuration {
    subnets         = var.private_subnet_ids
    security_groups = [var.ecs_security_group_id]
  }
}
