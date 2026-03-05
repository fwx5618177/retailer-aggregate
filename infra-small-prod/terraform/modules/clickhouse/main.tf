variable "namespace" { type = string }
variable "storage_size" { type = string }
variable "replicas" { type = number }
variable "environment" { type = string }

resource "kubernetes_namespace" "this" {
  metadata {
    name = var.namespace
    labels = {
      environment = var.environment
      app         = "sea-retailer"
    }
  }
}

resource "helm_release" "clickhouse" {
  name       = "clickhouse"
  repository = "https://docs.altinity.com/clickhouse-operator/"
  chart      = "altinity-clickhouse-operator"
  namespace  = var.namespace
  version    = "0.24.0"

  values = [
    yamlencode({
      clickhouse = {
        replicas = var.replicas
        storage = {
          size = var.storage_size
        }
        resources = {
          requests = { cpu = "500m", memory = "1Gi" }
          limits   = { cpu = "2",    memory = "4Gi" }
        }
      }
    })
  ]

  depends_on = [kubernetes_namespace.this]
}

output "endpoint" {
  value = "clickhouse.${var.namespace}.svc.cluster.local:8123"
}
