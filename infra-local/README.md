# infra-local

Local development environment orchestration for the SEA Retailer Top Selling Intelligence platform.

## Quick Start

### Option 1: Stub Data (No Network Required)
```bash
make mvp-stub
```
This runs the full pipeline with pre-built sample data.

### Option 2: Full Docker Stack
```bash
make deps       # Start ClickHouse + Postgres + Keycloak
make mvp-stub   # Run pipeline + matching
make api        # Start API backend
make frontend   # Start web frontend
```

### Option 3: Streamlit Demo
```bash
make mvp-stub   # Run pipeline + matching
make streamlit  # Start Streamlit app on :8501
```

## Services

| Service | Port | Description |
|---------|------|-------------|
| ClickHouse | 8123/9000 | OLAP database (read) |
| PostgreSQL | 5432 | RDBMS (write) |
| Keycloak | 8180 | Identity provider |
| API Backend | 8080 | Spring Boot REST API |
| Web Frontend | 3000 | React dashboard |
| Streamlit | 8501 | Demo app |

## Test Users (Keycloak)

| User | Password | Role |
|------|----------|------|
| viewer | viewer123 | viewer |
| reviewer | reviewer123 | reviewer |
| admin | admin123 | admin |

## Commands

Run `make help` to see all available commands.
