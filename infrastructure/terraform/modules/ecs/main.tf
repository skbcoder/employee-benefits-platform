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

# ── AI Platform IAM ────────────────────────────────────────────────

resource "aws_iam_role" "ai_task_role" {
  name = "${var.name_prefix}-ai-task"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action    = "sts:AssumeRole"
      Effect    = "Allow"
      Principal = { Service = "ecs-tasks.amazonaws.com" }
    }]
  })
}

resource "aws_iam_role_policy" "orchestrator_bedrock" {
  name = "${var.name_prefix}-orchestrator-bedrock"
  role = aws_iam_role.ai_task_role.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = ["bedrock:InvokeModel", "bedrock:InvokeModelWithResponseStream"]
      Resource = ["arn:aws:bedrock:*::foundation-model/anthropic.*"]
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

resource "aws_ecr_repository" "ai_gateway" {
  name = "${var.name_prefix}-ai-gateway"
}

resource "aws_ecr_repository" "orchestrator" {
  name = "${var.name_prefix}-orchestrator"
}

resource "aws_ecr_repository" "knowledge_service" {
  name = "${var.name_prefix}-knowledge-service"
}

resource "aws_ecr_repository" "governance" {
  name = "${var.name_prefix}-governance"
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

# ── AI Platform: Target Groups ────────────────────────────────────

resource "aws_lb_target_group" "ai_gateway" {
  name        = "${var.name_prefix}-ai-gw-tg"
  port        = 8200
  protocol    = "HTTP"
  vpc_id      = var.vpc_id
  target_type = "ip"
  health_check {
    path     = "/health"
    interval = 30
  }
}

resource "aws_lb_target_group" "orchestrator" {
  name        = "${var.name_prefix}-orch-tg"
  port        = 8400
  protocol    = "HTTP"
  vpc_id      = var.vpc_id
  target_type = "ip"
  health_check {
    path     = "/health"
    interval = 30
  }
}

resource "aws_lb_target_group" "knowledge_service" {
  name        = "${var.name_prefix}-ks-tg"
  port        = 8300
  protocol    = "HTTP"
  vpc_id      = var.vpc_id
  target_type = "ip"
  health_check {
    path     = "/health"
    interval = 30
  }
}

resource "aws_lb_target_group" "governance" {
  name        = "${var.name_prefix}-gov-tg"
  port        = 8500
  protocol    = "HTTP"
  vpc_id      = var.vpc_id
  target_type = "ip"
  health_check {
    path     = "/health"
    interval = 30
  }
}

# ── AI Platform: ALB Listener Rules ──────────────────────────────

resource "aws_lb_listener_rule" "ai_gateway" {
  listener_arn = aws_lb_listener.http.arn
  priority     = 20
  condition {
    path_pattern { values = ["/api/chat*", "/api/agents*"] }
  }
  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.ai_gateway.arn
  }
}

resource "aws_lb_listener_rule" "orchestrator" {
  listener_arn = aws_lb_listener.http.arn
  priority     = 30
  condition {
    path_pattern { values = ["/api/orchestrate*"] }
  }
  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.orchestrator.arn
  }
}

resource "aws_lb_listener_rule" "knowledge_service" {
  listener_arn = aws_lb_listener.http.arn
  priority     = 40
  condition {
    path_pattern { values = ["/api/knowledge*", "/api/documents*"] }
  }
  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.knowledge_service.arn
  }
}

resource "aws_lb_listener_rule" "governance" {
  listener_arn = aws_lb_listener.http.arn
  priority     = 50
  condition {
    path_pattern { values = ["/api/governance*"] }
  }
  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.governance.arn
  }
}

# ── AI Platform: Task Definitions ────────────────────────────────

resource "aws_ecs_task_definition" "ai_gateway" {
  family                   = "${var.name_prefix}-ai-gateway"
  cpu                      = 256
  memory                   = 512
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  execution_role_arn       = aws_iam_role.execution.arn
  task_role_arn            = aws_iam_role.ai_task_role.arn

  container_definitions = jsonencode([{
    name         = "ai-gateway"
    image        = var.ai_gateway_image
    portMappings = [{ containerPort = 8200 }]
    environment = [
      { name = "KNOWLEDGE_SERVICE_URL", value = "http://localhost:8300" },
      { name = "ORCHESTRATOR_URL", value = "http://localhost:8400" },
      { name = "MCP_SERVER_URL", value = "http://localhost:8100" },
    ]
    logConfiguration = {
      logDriver = "awslogs"
      options = {
        "awslogs-group"         = var.ai_gateway_log_group_name
        "awslogs-region"        = var.aws_region
        "awslogs-stream-prefix" = "ecs"
      }
    }
  }])
}

resource "aws_ecs_task_definition" "orchestrator" {
  family                   = "${var.name_prefix}-orchestrator"
  cpu                      = 512
  memory                   = 1024
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  execution_role_arn       = aws_iam_role.execution.arn
  task_role_arn            = aws_iam_role.ai_task_role.arn

  container_definitions = jsonencode([{
    name         = "orchestrator"
    image        = var.orchestrator_image
    portMappings = [{ containerPort = 8400 }]
    environment = [
      { name = "KNOWLEDGE_SERVICE_URL", value = "http://localhost:8300" },
      { name = "ENROLLMENT_SERVICE_URL", value = "http://${aws_lb.this.dns_name}" },
      { name = "GOVERNANCE_SERVICE_URL", value = "http://localhost:8500" },
    ]
    logConfiguration = {
      logDriver = "awslogs"
      options = {
        "awslogs-group"         = var.orchestrator_log_group_name
        "awslogs-region"        = var.aws_region
        "awslogs-stream-prefix" = "ecs"
      }
    }
  }])
}

resource "aws_ecs_task_definition" "knowledge_service" {
  family                   = "${var.name_prefix}-knowledge-service"
  cpu                      = 256
  memory                   = 512
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  execution_role_arn       = aws_iam_role.execution.arn
  task_role_arn            = aws_iam_role.ai_task_role.arn

  container_definitions = jsonencode([{
    name         = "knowledge-service"
    image        = var.knowledge_service_image
    portMappings = [{ containerPort = 8300 }]
    environment = [
      { name = "DB_HOST", value = var.db_endpoint },
      { name = "DB_PORT", value = "5432" },
      { name = "DB_NAME", value = "employee_benefits_platform" },
      { name = "DB_USERNAME", value = "benefits_app" },
      { name = "DB_PASSWORD", value = var.db_password },
    ]
    logConfiguration = {
      logDriver = "awslogs"
      options = {
        "awslogs-group"         = var.knowledge_service_log_group_name
        "awslogs-region"        = var.aws_region
        "awslogs-stream-prefix" = "ecs"
      }
    }
  }])
}

resource "aws_ecs_task_definition" "governance" {
  family                   = "${var.name_prefix}-governance"
  cpu                      = 256
  memory                   = 512
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  execution_role_arn       = aws_iam_role.execution.arn
  task_role_arn            = aws_iam_role.ai_task_role.arn

  container_definitions = jsonencode([{
    name         = "governance"
    image        = var.governance_image
    portMappings = [{ containerPort = 8500 }]
    environment = [
      { name = "DB_HOST", value = var.db_endpoint },
      { name = "DB_PORT", value = "5432" },
      { name = "DB_NAME", value = "employee_benefits_platform" },
      { name = "DB_USERNAME", value = "benefits_app" },
      { name = "DB_PASSWORD", value = var.db_password },
    ]
    logConfiguration = {
      logDriver = "awslogs"
      options = {
        "awslogs-group"         = var.governance_log_group_name
        "awslogs-region"        = var.aws_region
        "awslogs-stream-prefix" = "ecs"
      }
    }
  }])
}

# ── AI Platform: ECS Services ────────────────────────────────────

resource "aws_ecs_service" "ai_gateway" {
  name            = "ai-gateway"
  cluster         = aws_ecs_cluster.this.id
  task_definition = aws_ecs_task_definition.ai_gateway.arn
  desired_count   = 1
  launch_type     = "FARGATE"

  network_configuration {
    subnets         = var.private_subnet_ids
    security_groups = [var.ecs_security_group_id]
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.ai_gateway.arn
    container_name   = "ai-gateway"
    container_port   = 8200
  }
}

resource "aws_ecs_service" "orchestrator" {
  name            = "orchestrator"
  cluster         = aws_ecs_cluster.this.id
  task_definition = aws_ecs_task_definition.orchestrator.arn
  desired_count   = 1
  launch_type     = "FARGATE"

  network_configuration {
    subnets         = var.private_subnet_ids
    security_groups = [var.ecs_security_group_id]
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.orchestrator.arn
    container_name   = "orchestrator"
    container_port   = 8400
  }
}

resource "aws_ecs_service" "knowledge_service" {
  name            = "knowledge-service"
  cluster         = aws_ecs_cluster.this.id
  task_definition = aws_ecs_task_definition.knowledge_service.arn
  desired_count   = 1
  launch_type     = "FARGATE"

  network_configuration {
    subnets         = var.private_subnet_ids
    security_groups = [var.ecs_security_group_id]
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.knowledge_service.arn
    container_name   = "knowledge-service"
    container_port   = 8300
  }
}

resource "aws_ecs_service" "governance" {
  name            = "governance"
  cluster         = aws_ecs_cluster.this.id
  task_definition = aws_ecs_task_definition.governance.arn
  desired_count   = 1
  launch_type     = "FARGATE"

  network_configuration {
    subnets         = var.private_subnet_ids
    security_groups = [var.ecs_security_group_id]
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.governance.arn
    container_name   = "governance"
    container_port   = 8500
  }
}
