variable "environment" {
  description = "Deployment environment (staging/prod)"
  type        = string
  default     = "staging"
}

variable "namespace" {
  description = "Kubernetes namespace"
  type        = string
  default     = "sea-retailer"
}

variable "kubeconfig_path" {
  description = "Path to kubeconfig file"
  type        = string
  default     = "~/.kube/config"
}

# ClickHouse
variable "clickhouse_storage_size" {
  description = "ClickHouse storage size"
  type        = string
  default     = "50Gi"
}

variable "clickhouse_replicas" {
  description = "Number of ClickHouse replicas"
  type        = number
  default     = 1
}

# PostgreSQL
variable "postgres_storage_size" {
  description = "PostgreSQL storage size"
  type        = string
  default     = "10Gi"
}

variable "postgres_user" {
  description = "PostgreSQL username"
  type        = string
  default     = "sea_retailer"
  sensitive   = true
}

variable "postgres_password" {
  description = "PostgreSQL password"
  type        = string
  sensitive   = true
}

# Keycloak
variable "keycloak_admin_password" {
  description = "Keycloak admin password"
  type        = string
  sensitive   = true
}
