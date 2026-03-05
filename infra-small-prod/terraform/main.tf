terraform {
  required_version = ">= 1.9.0"

  required_providers {
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.35"
    }
    helm = {
      source  = "hashicorp/helm"
      version = "~> 2.17"
    }
  }

  backend "s3" {
    # Configure per environment in environments/{env}/backend.hcl
    # bucket = "sea-retailer-tfstate"
    # key    = "infrastructure/terraform.tfstate"
    # region = "ap-southeast-1"
  }
}

provider "kubernetes" {
  config_path = var.kubeconfig_path
}

provider "helm" {
  kubernetes {
    config_path = var.kubeconfig_path
  }
}

# ClickHouse module
module "clickhouse" {
  source = "./modules/clickhouse"

  namespace       = var.namespace
  storage_size    = var.clickhouse_storage_size
  replicas        = var.clickhouse_replicas
  environment     = var.environment
}

# PostgreSQL module
module "postgres" {
  source = "./modules/postgres"

  namespace       = var.namespace
  storage_size    = var.postgres_storage_size
  db_name         = "sea_retailer"
  db_user         = var.postgres_user
  db_password     = var.postgres_password
  environment     = var.environment
}

# Keycloak module
module "keycloak" {
  source = "./modules/keycloak"

  namespace       = var.namespace
  admin_password  = var.keycloak_admin_password
  postgres_host   = module.postgres.host
  environment     = var.environment
}

# Monitoring stack
module "monitoring" {
  source = "./modules/monitoring"

  namespace   = var.namespace
  environment = var.environment
}

output "clickhouse_endpoint" {
  value = module.clickhouse.endpoint
}

output "postgres_endpoint" {
  value = module.postgres.endpoint
}

output "keycloak_endpoint" {
  value = module.keycloak.endpoint
}
