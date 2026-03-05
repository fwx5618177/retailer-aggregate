variable "namespace" { type = string }
variable "environment" { type = string }

resource "helm_release" "prometheus_stack" {
  name       = "monitoring"
  repository = "https://prometheus-community.github.io/helm-charts"
  chart      = "kube-prometheus-stack"
  namespace  = var.namespace
  version    = "67.0.0"

  values = [
    yamlencode({
      grafana = {
        enabled = true
        adminPassword = "admin"
        dashboardProviders = {
          "dashboardproviders.yaml" = {
            apiVersion = 1
            providers = [{
              name      = "sea-retailer"
              folder    = "SEA Retailer"
              type      = "file"
              options   = { path = "/var/lib/grafana/dashboards/sea-retailer" }
            }]
          }
        }
      }
      prometheus = {
        prometheusSpec = {
          retention = "30d"
          storageSpec = {
            volumeClaimTemplate = {
              spec = {
                resources = { requests = { storage = "20Gi" } }
              }
            }
          }
        }
      }
      alertmanager = {
        enabled = true
      }
    })
  ]
}

output "grafana_url" {
  value = "monitoring-grafana.${var.namespace}.svc.cluster.local:3000"
}
