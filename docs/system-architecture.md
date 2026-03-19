# System Architecture

This document describes the platform architecture and the target cloud evolution path.

## Overview

The platform accepts employee benefit enrollment requests, persists them in a domain-oriented PostgreSQL data model, and drives downstream processing through a durable outbox/inbox messaging pattern. The current implementation uses a transport-specific publisher adapter for local HTTP delivery, and that boundary is designed to evolve toward EventBridge, SQS, and saga orchestration without breaking the external enrollment API.

An **AI Platform** layer provides natural language access to the enrollment pipeline through an AI chatbot. It uses a local LLM (Ollama), MCP tools wrapping the benefits APIs, and a RAG knowledge base for benefits policy documents. A **Next.js Frontend** serves the enrollment UI and embeds the AI chatbot widget.

## Context Diagram

```mermaid
flowchart LR
    User["User / Browser"] --> Frontend["Next.js Frontend<br/>:3000"]
    Frontend --> EnrollmentApi["Enrollment Service<br/>:8080"]
    Frontend --> ProcessingApi["Processing Service<br/>:8081"]
    Frontend --> AIGateway["AI Gateway<br/>:8200"]

    EnrollmentApi --> EnrollmentDb["PostgreSQL<br/>enrollment schema"]
    EnrollmentApi --> Outbox["PostgreSQL<br/>messaging.outbox_event"]
    Outbox --> Dispatcher["Outbox Dispatcher"]
    Dispatcher --> Publisher["Publisher Adapter"]
    Publisher --> ProcessingApi
    ProcessingApi --> Inbox["PostgreSQL<br/>messaging.inbox_message"]
    ProcessingApi --> ProcessingDb["PostgreSQL<br/>processing schema"]

    AIGateway --> Ollama["Ollama<br/>:11434"]
    AIGateway --> KnowledgeSvc["Knowledge Service<br/>:8300"]
    AIGateway --> EnrollmentApi
    AIGateway --> ProcessingApi
    KnowledgeSvc --> Ollama
    KnowledgeSvc --> KnowledgeDb["PostgreSQL<br/>knowledge schema<br/>(pgvector)"]

    MCPServer["MCP Server<br/>:8100"] --> EnrollmentApi
    MCPServer --> ProcessingApi

    ProcessingApi -. future .-> Saga["PostgreSQL<br/>orchestration schema"]
```

## Runtime Component View

```mermaid
flowchart TB
    subgraph Frontend["Next.js Frontend"]
        UI["Enrollment UI"]
        Chatbot["AI Chatbot Widget"]
        APIRoutes["API Route Handlers<br/>(proxy with 120s timeout)"]
        UI --> APIRoutes
        Chatbot --> APIRoutes
    end

    subgraph Enrollment["Enrollment Service"]
        Submit["REST Controller"]
        App["Application Service"]
        Repo["JPA Repositories"]
        Dispatch["Scheduled Outbox Dispatcher"]
        PublisherAdapter["Enrollment Event Publisher"]
        Submit --> App
        App --> Repo
        Repo --> Dispatch
        Dispatch --> PublisherAdapter
    end

    subgraph Processing["Processing Service"]
        Internal["Internal Event Controller"]
        ProcApp["Processing Application Service"]
        ProcRepo["JPA Repositories"]
        Internal --> ProcApp
        ProcApp --> ProcRepo
    end

    subgraph AIPlatform["AI Platform"]
        subgraph AIGateway["AI Gateway"]
            ChatRoute["Chat Endpoint"]
            AgentLoop["Two-Phase Agent Loop"]
            RAGClient["RAG Client"]
            MCPClient["MCP Client + UUID Stripping"]
            ChatRoute --> AgentLoop
            AgentLoop --> RAGClient
            AgentLoop --> MCPClient
        end

        subgraph MCPServer["MCP Server"]
            ToolDefs["MCP Tool Definitions"]
            BenefitsClient["Benefits API Client"]
            ToolDefs --> BenefitsClient
        end

        subgraph KnowledgeService["Knowledge Service"]
            DocIngest["Document Ingestion"]
            Chunker["Chunker"]
            Embedder["Ollama Embedder"]
            VectorSearch["Semantic Search"]
            DocIngest --> Chunker --> Embedder
        end
    end

    subgraph External["External"]
        OllamaLLM["Ollama (llama3.1:8b + nomic-embed-text)"]
    end

    subgraph Database["PostgreSQL + pgvector"]
        EnrollSchema["enrollment.*"]
        MessagingSchema["messaging.*"]
        ProcessingSchema["processing.*"]
        KnowledgeSchema["knowledge.*"]
        OrchestrationSchema["orchestration.*"]
    end

    APIRoutes --> Submit
    APIRoutes --> ChatRoute
    Repo --> EnrollSchema
    Repo --> MessagingSchema
    Dispatch --> MessagingSchema
    PublisherAdapter --> Internal
    ProcRepo --> MessagingSchema
    ProcRepo --> ProcessingSchema
    AgentLoop --> OllamaLLM
    MCPClient --> Submit
    MCPClient --> Internal
    BenefitsClient --> Submit
    BenefitsClient --> Internal
    RAGClient --> VectorSearch
    Embedder --> OllamaLLM
    VectorSearch --> KnowledgeSchema
    DocIngest --> KnowledgeSchema
    ProcRepo -. future .-> OrchestrationSchema
```

## Runtime Sequence

```mermaid
sequenceDiagram
    participant C as Client
    participant E as Enrollment Service
    participant DB as PostgreSQL
    participant D as Outbox Dispatcher
    participant T as Publisher Adapter
    participant P as Processing Service

    C->>E: POST /api/enrollments
    E->>DB: Save enrollment + selections
    E->>DB: Insert outbox event
    E-->>C: 202 Accepted (SUBMITTED)
    D->>DB: Claim pending outbox rows (SKIP LOCKED)
    D->>T: Publish EnrollmentEvent
    T->>P: POST /internal/enrollment-events
    P->>DB: Save inbox message
    P->>DB: Save processing record
    D->>DB: Mark outbox PUBLISHED
    D->>DB: Mark enrollment PROCESSING
    P->>DB: Mark processing COMPLETED
```

## AI Chat Sequence

```mermaid
sequenceDiagram
    participant U as User
    participant FE as Next.js Frontend
    participant GW as AI Gateway
    participant KS as Knowledge Service
    participant OL as Ollama
    participant BP as Benefits APIs

    U->>FE: Chat message
    FE->>GW: POST /api/ai/chat
    GW->>KS: POST /api/knowledge/search
    KS->>OL: Generate query embedding
    OL-->>KS: vector(768)
    KS-->>GW: Relevant document chunks

    alt Knowledge question (RAG context found, no data keywords)
        GW->>OL: Chat completion (system + RAG context, NO tools)
        OL-->>GW: Direct text response
    else Data question (needs enrollment data)
        GW->>OL: Chat completion (system + context + MCP tools)
        OL-->>GW: tool_call (e.g. list_enrollments_by_status)
        GW->>BP: REST API call
        BP-->>GW: JSON response
        GW->>GW: Strip internal UUIDs
        GW->>OL: Chat completion (+ tool result)
        OL-->>GW: Final response with data
    end

    GW-->>FE: {message, tool_calls_made}
    FE-->>U: Rendered Markdown response
```

## Data Ownership Diagram

```mermaid
flowchart LR
    subgraph EnrollmentSchema["enrollment schema"]
        EnrollmentRecord["enrollment_record"]
        EnrollmentSelection["enrollment_selection"]
    end

    subgraph MessagingSchema["messaging schema"]
        Outbox["outbox_event"]
        Inbox["inbox_message"]
    end

    subgraph ProcessingSchema["processing schema"]
        ProcessingRecord["enrollment_processing_record"]
    end

    subgraph KnowledgeSchema["knowledge schema"]
        Document["document"]
        DocumentChunk["document_chunk<br/>(embedding vector(768))"]
    end

    subgraph OrchestrationSchema["orchestration schema"]
        SagaInstance["saga_instance (future)"]
        SagaStep["saga_step (future)"]
    end

    EnrollmentRecord --> EnrollmentSelection
    EnrollmentRecord --> Outbox
    Outbox --> Inbox
    Inbox --> ProcessingRecord
    Document --> DocumentChunk
    ProcessingRecord -. future compensation/state .-> SagaInstance
    SagaInstance --> SagaStep
```

## State Transitions

```mermaid
stateDiagram-v2
    [*] --> SUBMITTED
    SUBMITTED --> PROCESSING: outbox published
    SUBMITTED --> DISPATCH_FAILED: delivery attempt failed
    DISPATCH_FAILED --> SUBMITTED: retry available
    PROCESSING --> COMPLETED: downstream processing finished
```

## Service Responsibilities

### Next.js Frontend (:3000)

- enrollment submission UI and status dashboard
- AI chatbot floating widget with markdown rendering (react-markdown + remark-gfm)
- API route handlers proxying to AI Gateway with 120s timeout for LLM latency
- rewrites proxying to Enrollment (:8080) and Processing (:8081) services
- graceful degradation when AI Gateway is unavailable

### Enrollment Service (:8080)

- owns enrollment submission and status lookup APIs
- writes `enrollment.enrollment_record` and `enrollment.enrollment_selection`
- writes `messaging.outbox_event`
- runs the outbox dispatcher and retry loop
- chooses a transport-specific publisher adapter from configuration

### Processing Service (:8081)

- accepts internal enrollment events
- enforces idempotency through `messaging.inbox_message`
- writes `processing.enrollment_processing_record`
- performs asynchronous completion updates

### MCP Server (:8100)

- exposes benefits APIs as MCP-compatible tools (8 tools: submit, get, list, check status)
- provides MCP resources and prompt templates for AI clients
- SSE transport for remote MCP clients (Claude Desktop, Claude Code)
- stateless — no database, no LLM calls

### AI Gateway (:8200)

- orchestrates LLM calls (Ollama) with MCP tool execution
- two-phase agent loop: classifies queries as knowledge vs. data, routes accordingly
- RAG augmentation: injects Knowledge Service context into LLM prompts
- tool result post-processing: strips internal UUIDs before LLM sees them
- conversation management with session-based message history
- calls benefits APIs directly (via `_benefits_proxy`) rather than going through MCP SSE transport

### Knowledge Service (:8300)

- document ingestion with chunking (512 tokens, 50 token overlap)
- embedding generation via Ollama (`nomic-embed-text`, 768-dim vectors)
- semantic search with cosine similarity over pgvector
- category-based filtering (policy, plan, faq, compliance, process)
- reads/writes `knowledge.document` and `knowledge.document_chunk`

## Database Boundaries

### `enrollment`

- canonical enrollment request state
- benefit plan selections for each request

### `processing`

- downstream execution state for the enrollment lifecycle

### `messaging`

- outbox rows for durable publish
- inbox rows for idempotent consume
- claim metadata to support multiple dispatcher instances safely

### `knowledge`

- document metadata and content
- document chunks with vector embeddings (pgvector `vector(768)`)
- cosine similarity index (`ivfflat`) for semantic search

### `orchestration`

- reserved for future saga coordinators and compensating steps

## Outbox Hardening

The dispatcher supports safe multi-instance behavior:

- rows are claimed through `FOR UPDATE SKIP LOCKED`
- claims expire after a configured TTL
- delivery attempts are counted
- the last delivery error is stored for debugging
- failed rows are retried after a backoff delay

## Target Cloud Evolution

The current dispatcher publishes through an adapter boundary. The next cloud step is to replace the transport, not the ownership model:

1. Enrollment Service writes the outbox row.
2. An outbox publisher adapter emits to EventBridge.
3. EventBridge routes to SQS.
4. Processing Service consumes from SQS and still writes inbox + processing state.
5. A saga orchestrator can later persist long-running workflow state in the `orchestration` schema.

## Cloud Evolution Diagram

```mermaid
flowchart LR
    Client["UI / API Client"] --> Api["Enrollment Service"]
    Client --> AIGateway["AI Gateway"]
    Api --> Rds["RDS PostgreSQL<br/>+ pgvector"]
    Api --> Outbox["Outbox Publisher"]
    Outbox --> EventBridge["Amazon EventBridge"]
    EventBridge --> Queue["Amazon SQS"]
    Queue --> Consumer["Processing Service Consumer"]
    Consumer --> Rds
    Consumer -. optional long-running flow .-> Orchestrator["Saga Orchestrator"]
    Orchestrator --> Rds
    AIGateway --> LLM["LLM Provider<br/>(Ollama / Bedrock)"]
    AIGateway --> Api
    AIGateway --> Consumer
    AIGateway --> KS["Knowledge Service"]
    KS --> LLM
    KS --> Rds
```

## Port Allocation

| Port | Service |
|------|---------|
| 3000 | Next.js Frontend |
| 8080 | Enrollment Service |
| 8081 | Processing Service |
| 8100 | MCP Server |
| 8200 | AI Gateway |
| 8300 | Knowledge Service |
| 11434 | Ollama |
| 55432 | PostgreSQL + pgvector |
