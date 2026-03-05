variable "namespace" { type = string }
variable "admin_password" { type = string; sensitive = true }
variable "postgres_host" { type = string }
variable "environment" { type = string }

resource "helm_release" "keycloak" {
  name       = "keycloak"
  repository = "https://charts.bitnami.com/bitnami"
  chart      = "keycloak"
  namespace  = var.namespace
  version    = "24.0.0"

  set {
    name  = "auth.adminUser"
    value = "admin"
  }

  set_sensitive {
    name  = "auth.adminPassword"
    value = var.admin_password
  }

  set {
    name  = "production"
    value = var.environment == "prod" ? "true" : "false"
  }

  set {
    name  = "proxy"
    value = "edge"
  }

  set {
    name  = "resources.requests.cpu"
    value = "250m"
  }

  set {
    name  = "resources.requests.memory"
    value = "512Mi"
  }
}

output "endpoint" {
  value = "keycloak.${var.namespace}.svc.cluster.local:8080"
}
