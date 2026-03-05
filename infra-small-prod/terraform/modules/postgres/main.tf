variable "namespace" { type = string }
variable "storage_size" { type = string }
variable "db_name" { type = string }
variable "db_user" { type = string }
variable "db_password" { type = string; sensitive = true }
variable "environment" { type = string }

resource "helm_release" "postgres" {
  name       = "postgres"
  repository = "https://charts.bitnami.com/bitnami"
  chart      = "postgresql"
  namespace  = var.namespace
  version    = "16.4.0"

  set {
    name  = "auth.database"
    value = var.db_name
  }

  set {
    name  = "auth.username"
    value = var.db_user
  }

  set_sensitive {
    name  = "auth.password"
    value = var.db_password
  }

  set {
    name  = "primary.persistence.size"
    value = var.storage_size
  }

  set {
    name  = "primary.resources.requests.cpu"
    value = "250m"
  }

  set {
    name  = "primary.resources.requests.memory"
    value = "512Mi"
  }

  set {
    name  = "metrics.enabled"
    value = "true"
  }
}

output "endpoint" {
  value = "postgres-postgresql.${var.namespace}.svc.cluster.local:5432"
}

output "host" {
  value = "postgres-postgresql.${var.namespace}.svc.cluster.local"
}
