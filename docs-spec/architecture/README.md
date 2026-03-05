# 架构与设计完全指南

> **文档版本**: 1.0.0
> **最后更新**: 2026-02-26
> **面向对象**: 工程师、决策者、未来维护者

## 文档结构

本指南回答三个核心问题，分别对应三个主要文档：

1. **[需求定义](./01-requirements.md)** — 本系统的需求是什么？
2. **[系统架构与实现](./02-architecture-and-implementation.md)** — 核心需求如何实现？架构如何设计？
3. **[设计决策与挑战](./03-design-decisions-and-challenges.md)** — 面临什么问题？为什么这样设计？是否符合业界标准？

## 快速导航

| 问题 | 文档 | 内容 |
|-----|------|------|
| **What?** 这是什么系统 | [需求定义](./01-requirements.md) | MVP 范围、目标平台、成功标准 |
| **How?** 如何实现 | [系统架构与实现](./02-architecture-and-implementation.md) | 6 大模块、技术栈、数据流、部署 |
| **Why?** 为什么这样设计 | [设计决策与挑战](./03-design-decisions-and-challenges.md) | 设计权衡、问题分析、业界对标 |

## 核心事实速览

**系统名称**: SEA Retailer Intelligence Platform
**类型**: 批处理 ETL + 跨平台产品匹配 + REST API + 可视化
**目标市场**: 泰国电商（Shopee Thailand + TikTok Shop Thailand）
**目标品类**: 个人护理商品（沐浴露、洗发水、护肤品）
**更新频率**: 每日批处理（02:00 UTC+7）

**核心指标**:
- TopN 覆盖率：≥95% 的商品被成功采集
- 跨平台匹配率：≥60% 的 Shopee-TikTok 商品对成功匹配
- API 延迟：<2秒（p95）
- 数据新鲜度：数据发布 < 2小时

## 技术栈概览

| 层级 | 技术 | 关键理由 |
|-----|------|--------|
| **采集 + 标准化 + 告警** | Python 3.14 + DuckDB 1.1 | 轻量、敏捷、零配置 |
| **匹配引擎** | Python + RapidFuzz + TF-IDF | 成熟的模糊匹配、易于调试 |
| **API 后端** | Spring Boot 3.4.2 (Java 21) | 类型安全、丰富的安全/审计生态 |
| **Web 前端** | React 19 + Vite 6 + TypeScript 5.7 | 快速开发、现代工具链 |
| **演示 UI** | Streamlit 1.54 | 零构建、快速原型 |
| **认证** | Keycloak 26 + JWT | 标准 OIDC、生产级 RBAC |
| **存储（本地）** | DuckDB 1.1.3 | 零配置、内嵌 SQL |
| **存储（生产计划）** | ClickHouse | 列式、OLAP、分析查询优化 |

## 关键统计

- **代码仓库**: 9 个独立服务
- **代码行数**: ~22,000 行（含测试）
- **测试覆盖**: 100+ 个单元测试，全数通过
- **设计文档**: 12+ 文件（ADR、规范、运维手册）
- **实现完成度**: 148/148 需求项已交付（含 11 项超出 MVP 范围的功能）

## 推荐阅读顺序

### 快速上手（15 分钟）
1. [需求定义](./01-requirements.md) — 快速浏览 MVP 范围、目标和成功标准
2. [系统架构与实现](./02-architecture-and-implementation.md#快速导览) — 查看架构图和模块概述

### 深入理解（1-2 小时）
1. 完整阅读 [系统架构与实现](./02-architecture-and-implementation.md)
2. 了解 [设计决策与挑战](./03-design-decisions-and-challenges.md) 中的核心问题
3. 参考 [需求定义](./01-requirements.md) 中的详细说明

### 架构设计（2-3 小时）
1. 阅读 [系统架构与实现](./02-architecture-and-implementation.md) — 完整的模块设计
2. 学习 [设计决策与挑战](./03-design-decisions-and-challenges.md) — 每个决策的 tradeoff
3. 参考 `docs-spec/design/` 下的详细技术规范：
   - `matching-design.md` — 匹配算法细节
   - `data-model.md` — 数据库 schema
   - `api-design.md` — API 端点规范

## 索引

- **需求文档**: `/docs-spec/scope/mvp-scope.md`
- **设计规范**: `/docs-spec/design/system-design.md`, `/api-design.md`, `/matching-design.md`, `/data-model.md`
- **运维手册**: `/docs-spec/runbooks/`
- **验收标准**: `/docs-spec/acceptance/`
- **架构决策**: `/docs-spec/adr/`
- **源代码**: 9 个服务在 `/sea_retailer_proj/` 下
