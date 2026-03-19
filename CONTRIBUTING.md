# Contributing to Employee Benefits Platform

Thank you for your interest in contributing! This guide will help you get started.

## Prerequisites

- **Java 17+** (JDK)
- **Maven 3.9+** (or use the included `./mvnw` wrapper)
- **Docker & Docker Compose** (for PostgreSQL)
- **Python 3.11+** (for AI Platform services)
- **Node.js 20+** (for the frontend)
- **Ollama** (optional — for AI chatbot features)

## Getting Started

1. **Fork & clone**
   ```bash
   git clone https://github.com/skbcoder/employee-benefits-platform.git
   cd employee-benefits-platform
   ```

2. **Run the setup script** (checks prerequisites, installs missing ones, builds everything)
   ```bash
   ./scripts/setup.sh
   ```
   This will:
   - Check for Java 17+, Docker, Python 3.11+, Node.js 20+, Ollama
   - Offer to install anything missing (with your confirmation)
   - Create `.env` from `.env.example`
   - Start PostgreSQL, build Java services, set up Python venvs, install npm dependencies
   - Pull Ollama models for the AI chatbot

   Run `./scripts/setup.sh --check` to see what's installed without changing anything.

3. **Start the platform**
   ```bash
   ./scripts/run-local.sh          # Core services only (enrollment + processing)
   ./scripts/run-local.sh --with-ai  # Core + AI chatbot
   ./scripts/run-local.sh --with-ui  # Core + frontend
   ./scripts/run-local.sh --all      # Everything
   ```

4. **Verify**
   ```bash
   curl http://localhost:8080/actuator/health   # Enrollment Service
   curl http://localhost:8081/actuator/health   # Processing Service
   ```
   Frontend at http://localhost:3000 (if started with `--with-ui` or `--all`).

For the full setup guide with troubleshooting, see [docs/local-setup.md](docs/local-setup.md).

## Development Workflow

1. Create a feature branch from `main`
   ```bash
   git checkout -b feat/your-feature-name
   ```

2. Make your changes with clear, focused commits

3. Run tests before pushing
   ```bash
   ./mvnw test
   ```

4. Push and open a Pull Request against `main`

## Commit Conventions

Use [Conventional Commits](https://www.conventionalcommits.org/):

```
type: short description

Longer explanation if needed.
```

Types: `feat`, `fix`, `refactor`, `test`, `docs`, `chore`

Examples:
- `feat: add vision plan comparison endpoint`
- `fix: resolve null pointer in outbox dispatcher`
- `docs: update local setup guide for AI platform`

## Code Style

### Java (Spring Boot)
- Follow existing Spring Boot conventions in the codebase
- JPA entities use `validate` DDL mode — schema changes go through Flyway migrations
- No `@Autowired` — use constructor injection
- Tests use JUnit 5 + Spring Boot Test

### Python (AI Platform)
- FastAPI with async/await patterns
- Pydantic models for request/response schemas
- Type hints on all public functions

### Frontend (Next.js)
- TypeScript strict mode
- Tailwind CSS for styling
- Components in `src/components/`, pages in `src/app/`

## Testing

- **Bug fixes**: Add a regression test proving the fix
- **New features**: Cover happy path + key edge cases
- **Refactors**: Existing tests must pass

```bash
# Java services
./mvnw test

# Frontend
cd frontend && npm run build
```

## Architecture

Before making significant changes, review:
- [docs/system-architecture.md](docs/system-architecture.md) — full architecture with diagrams
- [docs/persistence.md](docs/persistence.md) — database schema design
- [docs/ai-chatbot-hardening.md](docs/ai-chatbot-hardening.md) — AI security layers
- [docs/ai-loopback-refinement.md](docs/ai-loopback-refinement.md) — RAG refinement mechanism

## Flyway Migrations

Migrations live in `services/shared-model/src/main/resources/db/migration/`. Rules:
- Never modify an existing migration that has been applied
- Use `V{next}__descriptive_name.sql` naming
- Rebuild shared-model after changes: `./mvnw -pl services/shared-model install`

## Reporting Issues

Open an issue on GitHub with:
- Clear description of the problem or feature request
- Steps to reproduce (for bugs)
- Expected vs actual behavior
- Environment details (OS, Java version, Docker version)

## License

By contributing, you agree that your contributions will be licensed under the [Apache License 2.0](LICENSE).
