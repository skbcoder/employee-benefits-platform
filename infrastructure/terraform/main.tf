###############################################################################
# Employee Benefits Platform — Root Module
#
# Composes infrastructure from focused modules:
#   networking  — VPC, subnets, NAT, security groups
#   database    — RDS PostgreSQL with pgvector
#   messaging   — EventBridge + SQS for enrollment events
#   observability — CloudWatch log groups
#   ecs         — Fargate cluster, ALB, task definitions, services
###############################################################################

terraform {
  required_version = ">= 1.5"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

data "aws_availability_zones" "available" {
  state = "available"
}

locals {
  name_prefix = "${var.environment}-benefits"
  azs         = slice(data.aws_availability_zones.available.names, 0, 2)
}

# ── Networking ──────────────────────────────────────────────────────

module "networking" {
  source = "./modules/networking"

  name_prefix        = local.name_prefix
  vpc_cidr           = var.vpc_cidr
  availability_zones = local.azs
}

# ── Database ────────────────────────────────────────────────────────

module "database" {
  source = "./modules/database"

  name_prefix       = local.name_prefix
  environment       = var.environment
  subnet_ids        = module.networking.data_subnet_ids
  security_group_id = module.networking.rds_security_group_id
  instance_class    = var.db_instance_class
  multi_az          = var.db_multi_az
  password          = var.db_password
}

# ── Messaging ───────────────────────────────────────────────────────

module "messaging" {
  source = "./modules/messaging"

  name_prefix = local.name_prefix
}

# ── Observability ───────────────────────────────────────────────────

module "observability" {
  source = "./modules/observability"

  name_prefix = local.name_prefix
  environment = var.environment
}

# ── ECS (Fargate) ──────────────────────────────────────────────────

module "ecs" {
  source = "./modules/ecs"

  name_prefix           = local.name_prefix
  environment           = var.environment
  aws_region            = var.aws_region
  vpc_id                = module.networking.vpc_id
  public_subnet_ids     = module.networking.public_subnet_ids
  private_subnet_ids    = module.networking.private_subnet_ids
  alb_security_group_id = module.networking.alb_security_group_id
  ecs_security_group_id = module.networking.ecs_security_group_id
  db_endpoint           = module.database.endpoint
  db_password           = var.db_password
  event_bus_arn         = module.messaging.event_bus_arn
  sqs_queue_arn         = module.messaging.queue_arn

  enrollment_service_image  = var.enrollment_service_image
  processing_service_image  = var.processing_service_image
  enrollment_log_group_name = module.observability.enrollment_log_group_name
  processing_log_group_name = module.observability.processing_log_group_name
}
