output "namespace" {
  value = var.namespace
}

output "environment" {
  value = var.environment
}

output "monitoring_grafana_url" {
  value = module.monitoring.grafana_url
}
