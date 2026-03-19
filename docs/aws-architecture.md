# AWS Architecture

This document describes the target AWS architecture for the Employee Benefits Platform, mapping each local component to its AWS equivalent.

## Local to AWS Mapping

| Local Component | AWS Service | Notes |
|----------------|-------------|-------|
| PostgreSQL 16 (Docker) | Amazon RDS PostgreSQL + pgvector | Multi-AZ, automated backups, private subnet |
| Enrollment Service | ECS Fargate | Auto-scaling, ALB health checks |
| Processing Service | ECS Fargate | Event-driven scaling from SQS |
| HTTP Publisher Adapter | EventBridge Publisher Adapter | Config swap: `PUBLISHER_TRANSPORT=eventbridge` |
| Direct HTTP delivery | EventBridge → SQS → Processing | Decoupled, durable, with DLQ |
| AI Gateway | ECS Fargate + ALB | Behind API Gateway for rate limiting |
| Knowledge Service | ECS Fargate | Uses pgvector on same RDS instance |
| MCP Server | ECS Fargate | SSE transport, internal only |
| Ollama (local LLM) | Amazon Bedrock | Managed LLM, no GPU infrastructure |
| Next.js Frontend | AWS Amplify | CDN-backed, auto-deploy from Git |
| Flyway migrations | Same (runs on ECS task startup) | Connects to RDS |
| audit.log (file) | CloudWatch Logs | Structured JSON via awslogs driver |
| Rate limiter (in-memory) | API Gateway throttling + WAF | Distributed rate limiting |
| Docker Compose | ECS + ECR | Container registry + orchestration |

## VPC Architecture

```mermaid
flowchart TB
    subgraph VPC["VPC (10.0.0.0/16)"]
        subgraph PublicSubnets["Public Subnets"]
            ALB["Application Load Balancer"]
            NAT["NAT Gateway"]
        end

        subgraph PrivateSubnets["Private Subnets (App Tier)"]
            ECSCluster["ECS Cluster (Fargate)"]
            EnrollTask["Enrollment Service<br/>Task Definition"]
            ProcessTask["Processing Service<br/>Task Definition"]
            AIGWTask["AI Gateway<br/>Task Definition"]
            KSTask["Knowledge Service<br/>Task Definition"]
            MCPTask["MCP Server<br/>Task Definition"]
        end

        subgraph DataSubnets["Private Subnets (Data Tier)"]
            RDS["RDS PostgreSQL<br/>+ pgvector<br/>(Multi-AZ)"]
        end
    end

    Internet["Internet"] --> ALB
    ALB --> EnrollTask
    ALB --> AIGWTask
    EnrollTask --> RDS
    ProcessTask --> RDS
    KSTask --> RDS
    AIGWTask --> Bedrock["Amazon Bedrock"]
    AIGWTask --> KSTask
    AIGWTask --> MCPTask
    PrivateSubnets --> NAT --> Internet

    style PublicSubnets fill:#22c55e10,stroke:#22c55e
    style PrivateSubnets fill:#3b82f610,stroke:#3b82f6
    style DataSubnets fill:#f9731610,stroke:#f97316
```

## Event-Driven Flow

```mermaid
flowchart LR
    subgraph EnrollmentService["Enrollment Service (ECS)"]
        API["REST API"]
        Outbox["Outbox Table"]
        Dispatcher["Dispatcher"]
        EBAdapter["EventBridge Adapter"]
    end

    subgraph AWS["AWS Messaging"]
        EB["Amazon EventBridge"]
        SQS["Amazon SQS"]
        DLQ["Dead Letter Queue"]
    end

    subgraph ProcessingService["Processing Service (ECS)"]
        Consumer["SQS Consumer"]
        Inbox["Inbox Table"]
        Worker["Async Worker"]
    end

    API --> Outbox
    Outbox --> Dispatcher
    Dispatcher --> EBAdapter
    EBAdapter --> EB
    EB --> SQS
    SQS --> Consumer
    SQS -->|failures| DLQ
    Consumer --> Inbox
    Inbox --> Worker

    style AWS fill:#f9731610,stroke:#f97316
```

### What Changes from Local

The only code change is a new `EventBridgeEnrollmentEventPublisher` adapter (implementing the existing `EnrollmentEventPublisher` interface) and setting `PUBLISHER_TRANSPORT=eventbridge`. The enrollment API, data model, and processing logic are untouched.

The Processing Service gains an SQS consumer that replaces the HTTP endpoint — receiving events from the SQS queue instead of direct HTTP POST.

## Service Architecture

```mermaid
flowchart TB
    subgraph Frontend["Frontend (Amplify)"]
        Amplify["AWS Amplify<br/>Next.js SSR"]
    end

    subgraph APILayer["API Layer"]
        APIGW["API Gateway<br/>(rate limiting, WAF)"]
    end

    subgraph Compute["ECS Fargate Cluster"]
        EnrollSvc["Enrollment Service"]
        ProcessSvc["Processing Service"]
        AIGateway["AI Gateway"]
        KnowledgeSvc["Knowledge Service"]
        MCPSvc["MCP Server"]
    end

    subgraph Messaging["Messaging"]
        EventBridge["EventBridge"]
        SQSQueue["SQS Queue"]
    end

    subgraph Data["Data Layer"]
        RDS["RDS PostgreSQL<br/>+ pgvector"]
        Bedrock["Amazon Bedrock<br/>(Claude / Llama)"]
    end

    subgraph Observability["Observability"]
        CW["CloudWatch Logs"]
        XRay["X-Ray Tracing"]
    end

    Amplify --> APIGW
    APIGW --> EnrollSvc
    APIGW --> AIGateway
    EnrollSvc --> EventBridge
    EventBridge --> SQSQueue
    SQSQueue --> ProcessSvc
    EnrollSvc --> RDS
    ProcessSvc --> RDS
    KnowledgeSvc --> RDS
    AIGateway --> Bedrock
    AIGateway --> KnowledgeSvc
    AIGateway --> MCPSvc
    MCPSvc --> EnrollSvc
    Compute --> CW
    Compute --> XRay
```

## Infrastructure Components

### Networking
- **VPC** with 2 Availability Zones
- **Public subnets** — ALB, NAT Gateway
- **Private subnets (app)** — ECS Fargate tasks
- **Private subnets (data)** — RDS instance
- **Security groups** — ALB → ECS (8080/8200), ECS → RDS (5432), ECS → ECS (internal)

### Compute (ECS Fargate)
- **Cluster** — single ECS cluster for all services
- **Services** — one ECS service per microservice with desired count and auto-scaling
- **Task definitions** — CPU/memory allocations, environment variables from Parameter Store
- **ECR** — one repository per service for Docker images

### Database (RDS)
- **Engine** — PostgreSQL 16 with pgvector extension
- **Instance** — db.t3.medium (dev), db.r6g.large (prod)
- **Multi-AZ** — for production availability
- **Flyway** — migrations run on ECS task startup

### Messaging
- **EventBridge** — custom event bus for enrollment events
- **SQS** — standard queue with DLQ (maxReceiveCount: 3)
- **EventBridge Rule** — routes `EnrollmentSubmitted` events to SQS

### AI Platform
- **Amazon Bedrock** — replaces Ollama; switch `OLLAMA_BASE_URL` → Bedrock endpoint
- **RDS pgvector** — same database for embedding storage and vector search
- **API Gateway** — WAF + throttling replaces in-memory rate limiter

### Observability
- **CloudWatch Logs** — structured JSON via ECS awslogs driver
- **CloudWatch Metrics** — ECS service metrics, custom enrollment metrics
- **X-Ray** — distributed tracing across services

### Security
- **IAM roles** — least privilege per ECS task
- **Secrets Manager** — database credentials, API keys
- **Parameter Store** — non-secret configuration
- **WAF** — API Gateway protection (rate limiting, geo-blocking)
- **VPC endpoints** — private connectivity to AWS services

## Cost Estimate (Development)

| Component | Monthly Cost (est.) |
|-----------|-------------------|
| RDS db.t3.medium (Multi-AZ) | ~$70 |
| ECS Fargate (5 services, minimal) | ~$50 |
| NAT Gateway | ~$35 |
| ALB | ~$20 |
| SQS + EventBridge | ~$1 |
| ECR | ~$1 |
| Bedrock (Claude Haiku, light usage) | ~$10 |
| **Total** | **~$190/month** |

## Deployment Strategy

1. **CI/CD** — GitHub Actions builds Docker images, pushes to ECR, triggers ECS deployment
2. **Blue/Green** — ECS rolling deployment with health check grace period
3. **Database migrations** — run as one-off ECS task before service deployment
4. **Feature flags** — `PUBLISHER_TRANSPORT` env var controls HTTP vs EventBridge

## Infrastructure as Code

Both CloudFormation and Terraform templates are provided:

- CloudFormation: [infrastructure/cloudformation/template.yaml](../infrastructure/cloudformation/template.yaml)
- Terraform: [infrastructure/terraform/](../infrastructure/terraform/)

These are deployment-ready scaffolds with parameterized values. Customize the parameters for your AWS account and deploy.
