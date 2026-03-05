# infra-small-prod

Production-grade infrastructure for the SEA Retailer Top Selling Intelligence platform.

## Components

### Terraform (IaC)
- **ClickHouse**: OLAP database for analytical queries
- **PostgreSQL**: RDBMS for reviews, audit, and mapping
- **Keycloak**: Identity provider (OIDC/JWT)
- **Monitoring**: Prometheus + Grafana stack

### Helm Chart
- API backend deployment with health checks
- Web frontend deployment
- Daily pipeline CronJob
- Daily matching CronJob
- Ingress with TLS
- Secrets management

### CI/CD (GitHub Actions)
- Per-repo CI: lint, test, build, Docker image
- CD staging: auto-deploy on main merge
- CD production: manual gate deployment

### Monitoring
- Grafana dashboards: pipeline metrics, API metrics
- Prometheus alert rules: pipeline failures, DQ failures, API latency, review backlog
- Backup scripts for ClickHouse and PostgreSQL

## Deployment

### Staging
```bash
cd terraform
terraform init
terraform apply -var-file=environments/staging/terraform.tfvars

helm install sea-retailer helm/sea-retailer -f helm/sea-retailer/values.yaml -n sea-retailer-staging
```

### Production
```bash
terraform apply -var-file=environments/prod/terraform.tfvars

helm install sea-retailer helm/sea-retailer -f helm/sea-retailer/values.yaml -f helm/sea-retailer/values-prod.yaml -n sea-retailer-prod
```
