# SEA Retailer API Backend

Java Spring Boot REST API for the SEA Retailer Top Selling Intelligence platform. Provides cross-platform top-selling item analysis, matching, alerts, and review workflows.

## Tech Stack

- **Java 21** (LTS, Eclipse Temurin)
- **Spring Boot 3.4.2**
- **ClickHouse** JDBC for OLAP reads (top items, price history, matches, alerts)
- **PostgreSQL** + JPA/Hibernate for writes (review decisions, our mapping, audit log)
- **Flyway** for database migrations
- **Spring Security** OAuth2 Resource Server (JWT/OIDC)
- **springdoc-openapi** for Swagger UI and API documentation
- **Micrometer + Prometheus** for metrics

## Prerequisites

- Java 21+
- PostgreSQL 15+
- ClickHouse (for read queries)
- OIDC provider (Keycloak) for production JWT auth

## Quick Start

### Local Development (no external dependencies)

```bash
# Build the project
make build

# Run with local profile (H2 in-memory, security disabled)
make run
```

The API will start at http://localhost:8080

- Swagger UI: http://localhost:8080/swagger-ui.html
- Health check: http://localhost:8080/healthz
- H2 Console: http://localhost:8080/h2-console

### With Docker

```bash
make docker-build
make docker-run
```

### Running Tests

```bash
make test
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/healthz` | Health check |
| GET | `/api/v1/overview` | Dashboard overview KPIs |
| GET | `/api/v1/top-items` | Paginated top-selling items |
| GET | `/api/v1/items/{platform}/{itemId}` | Item detail with history and matches |
| GET | `/api/v1/alerts` | Paginated alerts |
| GET | `/api/v1/review-queue` | Items pending human review |
| POST | `/api/v1/review/{tiktokItemId}/{shopeeItemId}/decision` | Submit review decision |
| GET | `/api/v1/our-mapping/{platform}/{itemId}` | Get internal mapping |
| POST | `/api/v1/our-mapping/{platform}/{itemId}` | Update internal mapping |

## Configuration

Configuration is via `application.yaml` and environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `POSTGRES_USER` | `sea_retailer` | PostgreSQL username |
| `POSTGRES_PASSWORD` | `changeme` | PostgreSQL password |
| `CH_URL` | `jdbc:ch://localhost:8123/sea_retailer` | ClickHouse JDBC URL |
| `CH_USER` | `default` | ClickHouse username |
| `CH_PASSWORD` | (empty) | ClickHouse password |
| `OIDC_ISSUER` | `http://localhost:8180/realms/sea-retailer` | OIDC issuer URI |

## Security

- Production: JWT-based RBAC with roles `VIEWER`, `REVIEWER`, `ADMIN`
- Local profile (`-Dspring-boot.run.profiles=local`): all security disabled

## Maven Wrapper

To initialize the Maven wrapper (if `mvnw` is not present):

```bash
mvn wrapper:wrapper -Dmaven=3.9.9
```

## Project Structure

```
src/main/java/com/searetailer/api/
  config/         Security, CORS, ClickHouse configuration
  controller/     REST controllers
  service/        Business logic
  repository/
    clickhouse/   ClickHouse JdbcTemplate repositories
    postgres/     JPA repositories
  model/
    entity/       JPA entities (ReviewDecision, OurMapping, AuditLog)
    dto/          Request/response DTOs
    enums/        Shared enumerations
  exception/      Global exception handling
  filter/         Servlet filters (RequestId)
  util/           Utilities (pagination)
```
