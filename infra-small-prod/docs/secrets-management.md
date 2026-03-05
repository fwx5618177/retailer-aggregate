# 密钥管理规范

> SEA Retailer Top Selling Intelligence Platform
> 最后更新: 2026-02-26

---

## 目录

1. [密钥分类与清单](#1-密钥分类与清单)
2. [本地开发环境](#2-本地开发环境)
3. [Staging/生产环境 -- Sealed Secrets](#3-staging生产环境----sealed-secrets)
4. [密钥轮换流程](#4-密钥轮换流程)
5. [紧急密钥撤销](#5-紧急密钥撤销)
6. [审计追踪](#6-审计追踪)

---

## 1. 密钥分类与清单

### 1.1 密钥清单

| 密钥名称 | 类型 | 使用组件 | 轮换周期 | 敏感等级 |
|----------|------|---------|---------|---------|
| `postgres-password` | 数据库密码 | api-backend, data-pipeline | 90 天 | 高 |
| `clickhouse-password` | 数据库密码 | api-backend, data-pipeline, matching-engine | 90 天 | 高 |
| `keycloak-admin-password` | 管理员密码 | Keycloak 管理控制台 | 90 天 | 极高 |
| `jwt-signing-key` | JWT 签名密钥 | api-backend (Spring Security) | 180 天 | 极高 |
| `s3-access-key-id` | API 密钥 | data-pipeline, backup CronJob | 180 天 | 高 |
| `s3-secret-access-key` | API 密钥 | data-pipeline, backup CronJob | 180 天 | 高 |
| `tls-cert` | TLS 证书 | Ingress Controller | 365 天 (自动续期) | 高 |
| `tls-key` | TLS 私钥 | Ingress Controller | 365 天 (自动续期) | 极高 |
| `slack-webhook-url` | Webhook URL | 监控告警通知 | 按需 | 中 |
| `ghcr-pull-secret` | 容器镜像拉取凭证 | Kubernetes Pod | 365 天 | 中 |

### 1.2 敏感等级定义

| 等级 | 说明 | 泄漏影响 |
|------|------|---------|
| **极高** | 泄漏可导致全系统被接管 | 立即启动紧急撤销流程 |
| **高** | 泄漏可导致数据泄露或服务中断 | 24 小时内轮换 |
| **中** | 泄漏可导致部分功能受影响 | 72 小时内轮换 |

---

## 2. 本地开发环境

### 2.1 `.env.local` 文件

本地开发使用 `.env.local` 文件管理密钥, 该文件 **绝不可提交至版本控制**。

**文件位置**: `infra-local/.env.local`

```bash
# ============================================
# SEA Retailer 本地开发密钥配置
# 警告: 此文件不可提交至 Git!
# ============================================

# PostgreSQL
POSTGRES_USER=sea_retailer
POSTGRES_PASSWORD=local_dev_pg_password_change_me
POSTGRES_DB=sea_retailer

# ClickHouse
CH_USER=default
CH_PASSWORD=local_dev_ch_password_change_me

# Keycloak
KEYCLOAK_ADMIN=admin
KEYCLOAK_ADMIN_PASSWORD=local_dev_kc_password_change_me

# JWT
JWT_SIGNING_KEY=local-dev-jwt-key-32-chars-min!!

# S3 (LocalStack 模拟)
AWS_ACCESS_KEY_ID=test
AWS_SECRET_ACCESS_KEY=test
AWS_ENDPOINT_URL=http://localhost:4566
```

### 2.2 `.gitignore` 配置

确保以下条目存在于 `.gitignore` 中:

```gitignore
# 密钥文件 - 绝不可提交
.env.local
.env.*.local
*.key
*.pem
credentials.json
```

### 2.3 Docker Secrets (Compose)

`infra-local/docker-compose.yml` 中通过 Docker Secrets 传递敏感信息:

```yaml
secrets:
  postgres_password:
    file: ./.secrets/postgres_password.txt
  clickhouse_password:
    file: ./.secrets/clickhouse_password.txt

services:
  postgres:
    secrets:
      - postgres_password
    environment:
      POSTGRES_PASSWORD_FILE: /run/secrets/postgres_password
```

---

## 3. Staging/生产环境 -- Sealed Secrets

### 3.1 架构概述

Staging 和生产环境使用 [Bitnami Sealed Secrets](https://github.com/bitnami-labs/sealed-secrets) 管理密钥:

```
开发者本地                          Kubernetes 集群
┌───────────────┐                 ┌──────────────────────┐
│               │                 │                      │
│  明文 Secret  │ ── kubeseal ──→ │  SealedSecret (加密) │
│  (不可提交)   │   (公钥加密)    │  (可安全提交至 Git)   │
│               │                 │        │              │
└───────────────┘                 │        ↓              │
                                  │  Sealed Secrets      │
                                  │  Controller (解密)   │
                                  │        │              │
                                  │        ↓              │
                                  │  Kubernetes Secret   │
                                  │  (集群内明文)         │
                                  └──────────────────────┘
```

**核心优势**: SealedSecret 资源可安全存储在 Git 仓库中, 只有集群内的 Sealed Secrets Controller 才能解密。

### 3.2 安装 Sealed Secrets Controller

```bash
# 安装 Controller 到集群
helm repo add sealed-secrets https://bitnami-labs.github.io/sealed-secrets
helm repo update

helm install sealed-secrets sealed-secrets/sealed-secrets \
  --namespace kube-system \
  --set-string fullnameOverride=sealed-secrets-controller
```

### 3.3 安装 kubeseal CLI

```bash
# macOS
brew install kubeseal

# Linux
KUBESEAL_VERSION=$(curl -s https://api.github.com/repos/bitnami-labs/sealed-secrets/releases/latest | jq -r .tag_name | cut -c2-)
wget "https://github.com/bitnami-labs/sealed-secrets/releases/download/v${KUBESEAL_VERSION}/kubeseal-${KUBESEAL_VERSION}-linux-amd64.tar.gz"
tar -xvzf kubeseal-*.tar.gz kubeseal
sudo install -m 755 kubeseal /usr/local/bin/kubeseal
```

### 3.4 创建 SealedSecret

**步骤 1**: 创建明文 Secret YAML (仅用于加密, 不提交至 Git):

```bash
kubectl create secret generic sea-retailer-secrets \
  --namespace sea-retailer \
  --from-literal=postgres-password='YOUR_STRONG_PG_PASSWORD' \
  --from-literal=clickhouse-password='YOUR_STRONG_CH_PASSWORD' \
  --from-literal=keycloak-admin-password='YOUR_STRONG_KC_PASSWORD' \
  --from-literal=jwt-signing-key='YOUR_JWT_KEY_AT_LEAST_32_CHARS!!' \
  --dry-run=client \
  -o yaml > /tmp/secret-plain.yaml
```

**步骤 2**: 使用 kubeseal 加密:

```bash
kubeseal \
  --controller-name=sealed-secrets-controller \
  --controller-namespace=kube-system \
  --format yaml \
  < /tmp/secret-plain.yaml \
  > infra-small-prod/helm/sea-retailer/templates/sealed-secrets.yaml
```

**步骤 3**: 清理明文文件:

```bash
# 安全删除明文 Secret 文件
shred -u /tmp/secret-plain.yaml 2>/dev/null || rm -f /tmp/secret-plain.yaml
```

**步骤 4**: 验证 SealedSecret:

```bash
# 应用 SealedSecret 到集群
kubectl apply -f infra-small-prod/helm/sea-retailer/templates/sealed-secrets.yaml

# 确认 Controller 已解密并生成对应的 Secret
kubectl get secret sea-retailer-secrets -n sea-retailer
kubectl get secret sea-retailer-secrets -n sea-retailer -o jsonpath='{.data}' | jq .
```

### 3.5 更新单个密钥值

无需重新创建整个 SealedSecret, 可逐个更新:

```bash
# 仅加密单个值
echo -n "NEW_POSTGRES_PASSWORD" | \
  kubeseal \
    --controller-name=sealed-secrets-controller \
    --controller-namespace=kube-system \
    --raw \
    --namespace sea-retailer \
    --name sea-retailer-secrets \
    --from-file=/dev/stdin

# 将输出的加密字符串替换到 sealed-secrets.yaml 对应字段
```

---

## 4. 密钥轮换流程

### 4.1 定期轮换计划

| 密钥 | 轮换周期 | 下次轮换日期 | 负责人 |
|------|---------|-------------|--------|
| `postgres-password` | 90 天 | 待定 | DBA |
| `clickhouse-password` | 90 天 | 待定 | DBA |
| `keycloak-admin-password` | 90 天 | 待定 | 安全负责人 |
| `jwt-signing-key` | 180 天 | 待定 | 后端负责人 |
| TLS 证书 | 365 天 | 自动 (cert-manager) | 自动化 |

### 4.2 PostgreSQL 密码轮换流程

```bash
# 步骤 1: 生成新密码
NEW_PG_PASSWORD=$(openssl rand -base64 32)
echo "新密码已生成 (请勿在日志中记录明文)"

# 步骤 2: 在 PostgreSQL 中更新密码
psql -h $POSTGRES_HOST -U postgres \
  -c "ALTER USER sea_retailer PASSWORD '${NEW_PG_PASSWORD}';"

# 步骤 3: 更新 SealedSecret
echo -n "${NEW_PG_PASSWORD}" | \
  kubeseal \
    --controller-name=sealed-secrets-controller \
    --controller-namespace=kube-system \
    --raw \
    --namespace sea-retailer \
    --name sea-retailer-secrets

# 步骤 4: 更新 sealed-secrets.yaml 中的加密值并 apply
kubectl apply -f infra-small-prod/helm/sea-retailer/templates/sealed-secrets.yaml

# 步骤 5: 滚动重启依赖该密码的服务
kubectl rollout restart deployment sea-retailer-api -n sea-retailer

# 步骤 6: 验证服务正常
kubectl rollout status deployment sea-retailer-api -n sea-retailer --timeout=300s
curl -s https://sea-retailer.example.com/actuator/health | jq .
```

### 4.3 JWT 签名密钥轮换流程

JWT 密钥轮换需要特别注意, 因为旧 token 在密钥更换后将失效:

```bash
# 步骤 1: 选择低峰期执行 (建议 UTC 时间 22:00-02:00)

# 步骤 2: 生成新的 JWT 签名密钥
NEW_JWT_KEY=$(openssl rand -base64 48)

# 步骤 3: 更新 SealedSecret 并 apply
# (同上述流程)

# 步骤 4: 滚动重启 API 服务
kubectl rollout restart deployment sea-retailer-api -n sea-retailer

# 步骤 5: 通知用户可能需要重新登录
# (所有持有旧 JWT 的用户 session 将失效)
```

### 4.4 ClickHouse 密码轮换流程

```bash
# 步骤 1: 生成新密码
NEW_CH_PASSWORD=$(openssl rand -base64 32)

# 步骤 2: 在 ClickHouse 中更新密码
clickhouse-client --host $CH_HOST --user default --password $CH_PASSWORD \
  --query "ALTER USER default IDENTIFIED BY '${NEW_CH_PASSWORD}'"

# 步骤 3: 更新 SealedSecret 并 apply
# (同上述流程)

# 步骤 4: 滚动重启依赖该密码的服务
kubectl rollout restart deployment sea-retailer-api -n sea-retailer
```

---

## 5. 紧急密钥撤销

当发现或怀疑密钥泄漏时, 必须立即执行紧急撤销流程。

### 5.1 响应流程

```
┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐
│ 1. 发现   │ ──→ │ 2. 评估   │ ──→ │ 3. 隔离   │ ──→ │ 4. 轮换   │
│ 密钥泄漏  │     │ 影响范围  │     │ 受影响    │     │ 所有受影  │
│          │     │          │     │ 服务      │     │ 响密钥    │
└──────────┘     └──────────┘     └──────────┘     └──────────┘
                                                         │
┌──────────┐     ┌──────────┐     ┌──────────┐          │
│ 7. 事后   │ ←── │ 6. 审计   │ ←── │ 5. 恢复   │ ←────────┘
│ 总结      │     │ 日志检查  │     │ 服务      │
└──────────┘     └──────────┘     └──────────┘
```

### 5.2 紧急操作命令

```bash
# ===== 极高敏感密钥泄漏: 立即执行 =====

# 1. 通报 (在 #ops-alerts 和 #security 频道)
echo "紧急: 检测到密钥泄漏, 正在执行紧急轮换" | slack-notify '#security'

# 2. 如果是 JWT 密钥泄漏 -- 立即使所有 token 失效
kubectl rollout restart deployment sea-retailer-api -n sea-retailer

# 3. 如果是数据库密码泄漏 -- 立即修改密码
# PostgreSQL
psql -h $POSTGRES_HOST -U postgres \
  -c "ALTER USER sea_retailer PASSWORD '$(openssl rand -base64 32)';"

# ClickHouse
clickhouse-client --host $CH_HOST --user default --password $CH_PASSWORD \
  --query "ALTER USER default IDENTIFIED BY '$(openssl rand -base64 32)'"

# 4. 如果是 Keycloak 管理密码泄漏 -- 同时禁用管理端口外部访问
kubectl patch service keycloak -n sea-retailer \
  -p '{"spec":{"type":"ClusterIP"}}'

# 5. 如果是 S3 密钥泄漏 -- 立即在 AWS IAM 中停用旧密钥
aws iam update-access-key \
  --access-key-id AKIAXXXXXXXXXXXXXXXX \
  --status Inactive \
  --user-name sea-retailer-pipeline

# 6. 生成新密钥并更新 SealedSecret
# (按第 4 节流程操作)
```

### 5.3 泄漏排查清单

- [ ] 检查 Git 历史记录中是否有明文密钥被提交
- [ ] 检查 CI/CD 日志中是否有密钥被打印
- [ ] 检查容器日志中是否有密钥泄漏
- [ ] 检查 S3 访问日志中是否有异常访问
- [ ] 检查数据库审计日志中是否有异常查询
- [ ] 检查 Kubernetes 事件中是否有异常 Secret 访问

---

## 6. 审计追踪

### 6.1 Kubernetes Secret 访问审计

启用 Kubernetes 审计日志, 记录所有对 Secret 资源的访问:

```yaml
# audit-policy.yaml
apiVersion: audit.k8s.io/v1
kind: Policy
rules:
  # 记录所有对 Secret 的操作
  - level: Metadata
    resources:
      - group: ""
        resources: ["secrets"]
    namespaces: ["sea-retailer"]
  # 记录 SealedSecret 的操作
  - level: Metadata
    resources:
      - group: "bitnami.com"
        resources: ["sealedsecrets"]
    namespaces: ["sea-retailer"]
```

### 6.2 审计日志查询

```bash
# 查询最近 24 小时内对 Secret 的所有操作
kubectl logs -n kube-system -l component=kube-apiserver --since=24h | \
  jq 'select(.objectRef.resource == "secrets" and .objectRef.namespace == "sea-retailer")'

# 查询特定 Secret 的访问记录
kubectl logs -n kube-system -l component=kube-apiserver --since=24h | \
  jq 'select(.objectRef.name == "sea-retailer-secrets")'
```

### 6.3 密钥操作记录表

所有密钥操作 (创建、轮换、撤销) 必须记录在运维操作日志中:

```markdown
## 密钥操作记录

| 日期 | 操作人 | 操作类型 | 密钥名称 | 原因 | 影响服务 | 状态 |
|------|--------|---------|----------|------|---------|------|
| 2026-02-26 | 张三 | 创建 | sea-retailer-secrets | 初始部署 | 全部 | 完成 |
| 2026-MM-DD | (操作人) | 轮换 | postgres-password | 定期轮换 | api-backend | (状态) |
```

### 6.4 合规要求

- 所有密钥轮换操作需至少两人知晓 (执行人 + 审核人)
- 明文密钥严禁出现在以下位置:
  - Git 仓库 (包括历史记录)
  - CI/CD 日志输出
  - 应用程序日志
  - Slack 消息
  - 邮件
- 密钥轮换后, 旧密钥的明文必须安全销毁
- 每季度进行一次密钥管理合规审查
