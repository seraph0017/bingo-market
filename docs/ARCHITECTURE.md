# Bingo Market 系统架构设计文档

## 文档信息

| 项目 | 内容 |
|------|------|
| 文档名称 | Bingo Market 系统架构设计 |
| 版本 | v1.0 |
| 创建日期 | 2026-03-07 |
| 项目阶段 | Phase 1 MVP |

---

## 1. 系统概述

### 1.1 项目定位

Bingo Market 是面向东南亚市场的合规预测平台，首发越南市场，聚焦科技、商业、文化和学术知识领域。

### 1.2 核心特性

- 合规的预测市场平台（禁止体育、政治、宗教话题）
- LMSR (Logarithmic Market Scoring Rule) 交易引擎
- 18+ 实名认证 (KYC)
- 日/月充值限额控制
- 单向充值（不支持提现）
- 知识币商城系统
- 完整的内容风控体系

### 1.3 设计原则

- **合规优先**: 所有功能设计以越南市场合规为前提
- **移动优先**: H5 移动端优先设计
- **异步优先**: 核心业务逻辑使用异步处理
- **分层架构**: 清晰的 API → Service → Model 分层
- **安全审计**: 所有关键操作都有审计日志

---

## 2. 技术架构

### 2.1 技术栈

| 层级 | 技术选型 | 版本 | 说明 |
|------|---------|------|------|
| **后端框架** | FastAPI | 0.109+ | 高性能异步 Web 框架 |
| **数据库** | PostgreSQL | 16 | 关系型数据库，支持 JSONB |
| **ORM** | SQLAlchemy | 2.0 | 异步 ORM |
| **数据库迁移** | Alembic | 1.13+ | 数据库版本管理 |
| **缓存** | Redis | 7 | 缓存、会话、限流 |
| **认证** | JWT | - | 无状态认证 |
| **密码加密** | bcrypt | - | 密码哈希 |
| **任务队列** | Celery | 5.3+ | 异步任务处理 |
| **前端框架** | Vue 3 | 3.4+ | 渐进式 JavaScript 框架 |
| **前端构建** | Vite | 5+ | 下一代前端构建工具 |
| **UI 组件库** | Element Plus | 2.4+ | Vue 3 组件库 |
| **状态管理** | Pinia | 2+ | Vue 3 官方状态管理 |
| **国际化** | Vue I18n | 9+ | 多语言支持 |
| **HTTP 客户端** | Axios | 1.6+ | HTTP 请求库 |

### 2.2 系统架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                         用户层 (Users)                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐        │
│  │   Mobile H5  │  │   Desktop    │  │   Admin UI   │        │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘        │
└─────────┼───────────────────┼───────────────────┼───────────────┘
          │                   │                   │
          └───────────────────┴───────────────────┘
                              │
                              ▼ HTTPS/WebSocket
┌─────────────────────────────────────────────────────────────────┐
│                        接入层 (Gateway)                         │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              Nginx / API Gateway (可选)                   │  │
│  │  - 静态资源服务                                           │  │
│  │  - SSL 终止                                               │  │
│  │  - 负载均衡                                               │  │
│  └───────────────────────────┬──────────────────────────────┘  │
└───────────────────────────────┼──────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                        应用层 (Application)                      │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                    FastAPI Application                     │  │
│  │  ┌────────────────────────────────────────────────────┐  │  │
│  │  │                API Routes (16 modules)             │  │  │
│  │  │  - /api/v1/auth          (认证)                    │  │  │
│  │  │  - /api/v1/wallet        (钱包)                    │  │  │
│  │  │  - /api/v1/topics        (话题)                    │  │  │
│  │  │  - /api/v1/trading       (交易)                    │  │  │
│  │  │  - /api/v1/settlements   (结算)                    │  │  │
│  │  │  - /api/v1/products      (商品)                    │  │  │
│  │  │  - /api/v1/admin         (管理后台)                │  │  │
│  │  │  - /api/v1/moderation    (内容风控)                │  │  │
│  │  │  ...                                                    │  │  │
│  │  └───────────────────────┬────────────────────────────┘  │  │
│  │                          │                                  │  │
│  │  ┌───────────────────────▼────────────────────────────┐  │  │
│  │  │            Business Services (20+ services)         │  │  │
│  │  │  - AuthService            (认证服务)                │  │  │
│  │  │  - WalletService          (钱包服务)                │  │  │
│  │  │  - LMSREngine             (LMSR 交易引擎)          │  │  │
│  │  │  - TradingService         (交易服务)                │  │  │
│  │  │  - TopicService           (话题服务)                │  │  │
│  │  │  - SettlementService      (结算服务)                │  │  │
│  │  │  - ProductService         (商品服务)                │  │  │
│  │  │  - ModerationService      (风控服务)                │  │  │
│  │  │  - SMSService             (短信服务)                │  │  │
│  │  │  - PaymentGatewayService  (支付网关)                │  │  │
│  │  │  ...                                                    │  │  │
│  │  └───────────────────────┬────────────────────────────┘  │  │
│  └───────────────────────────┼──────────────────────────────┘  │
└───────────────────────────────┼──────────────────────────────────┘
                                │
            ┌───────────────────┼───────────────────┐
            │                   │                   │
            ▼                   ▼                   ▼
┌───────────────────┐  ┌───────────────────┐  ┌───────────────────┐
│   PostgreSQL 16   │  │     Redis 7       │  │   Celery Worker   │
│   (主数据库)       │  │   (缓存/会话)      │  │   (异步任务)       │
│  - 用户表         │  │  - JWT 黑名单     │  │  - 到期结算       │
│  - 钱包表         │  │  - 登录限流       │  │  - 通知推送       │
│  - 话题表         │  │  - 会话存储       │  │  - 异步审计       │
│  - 交易表         │  │  - 实时数据       │  │                   │
│  - 结算表         │  └───────────────────┘  └───────────────────┘
│  - 商品表         │
│  - ...            │
└───────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                        外部服务集成层                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐        │
│  │   MoMo Pay   │  │  ZaloPay     │  │   SMS Gate   │        │
│  │   (支付)      │  │   (支付)      │  │   (短信)      │        │
│  └──────────────┘  └──────────────┘  └──────────────┘        │
│  ┌──────────────┐  ┌──────────────┐                            │
│  │  Anthropic   │  │   OpenAI     │                            │
│  │   (LLM)      │  │   (LLM)      │                            │
│  └──────────────┘  └──────────────┘                            │
└─────────────────────────────────────────────────────────────────┘
```

---

## 3. 后端架构

### 3.1 目录结构

```
code/backend/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI 应用入口
│   ├── api/
│   │   └── v1/                 # API v1 路由
│   │       ├── __init__.py
│   │       ├── router.py        # 路由聚合
│   │       ├── auth.py          # 认证 API
│   │       ├── wallet.py        # 钱包 API
│   │       ├── topics.py        # 话题 API
│   │       ├── trading.py       # 交易 API
│   │       ├── settlements.py   # 结算 API
│   │       ├── products.py      # 商品 API
│   │       ├── admin.py         # 管理后台 API
│   │       ├── moderation.py    # 内容风控 API
│   │       ├── audit.py         # 审计日志 API
│   │       ├── devices.py       # 设备管理 API
│   │       ├── terms.py         # 条款 API
│   │       ├── notifications.py # 通知 API
│   │       ├── announcements.py # 公告 API
│   │       └── ...
│   ├── core/                    # 核心配置
│   │   ├── __init__.py
│   │   ├── config.py            # 应用配置
│   │   ├── database.py          # 数据库连接
│   │   ├── security.py          # 安全工具 (JWT, 密码)
│   │   ├── redis.py             # Redis 连接
│   │   └── exceptions.py        # 自定义异常
│   ├── models/                  # SQLAlchemy 模型
│   │   ├── __init__.py
│   │   ├── user.py              # 用户模型
│   │   ├── wallet.py            # 钱包模型
│   │   ├── topic.py             # 话题模型
│   │   ├── trading.py           # 交易模型
│   │   ├── settlement.py        # 结算模型
│   │   ├── product.py           # 商品模型
│   │   ├── moderation.py        # 风控模型
│   │   ├── audit.py             # 审计模型
│   │   ├── device.py            # 设备模型
│   │   ├── notification.py      # 通知模型
│   │   ├── announcement.py      # 公告模型
│   │   ├── terms.py             # 条款模型
│   │   └── system_config.py     # 系统配置模型
│   ├── schemas/                 # Pydantic 模型
│   │   ├── __init__.py
│   │   ├── auth.py              # 认证 Schema
│   │   ├── wallet.py            # 钱包 Schema
│   │   ├── topic.py             # 话题 Schema
│   │   ├── product.py           # 商品 Schema
│   │   └── moderation.py        # 风控 Schema
│   ├── services/                # 业务逻辑层
│   │   ├── __init__.py
│   │   ├── auth.py              # 认证服务
│   │   ├── wallet.py            # 钱包服务
│   │   ├── lmsr.py              # LMSR 交易引擎
│   │   ├── trading.py           # 交易服务
│   │   ├── topic.py             # 话题服务
│   │   ├── settlement.py        # 结算服务
│   │   ├── product.py           # 商品服务
│   │   ├── moderation.py        # 风控服务
│   │   ├── audit.py             # 审计服务
│   │   ├── sms.py               # 短信服务
│   │   ├── payment_gateway.py   # 支付网关服务
│   │   └── ...
│   └── utils/                   # 工具函数
├── alembic/                     # Alembic 数据库迁移
│   ├── versions/                # 迁移脚本
│   ├── env.py
│   └── script.py.mako
├── tests/                       # 测试文件
│   ├── conftest.py              # pytest 配置
│   ├── test_auth.py             # 认证测试
│   ├── test_wallet.py           # 钱包测试
│   ├── test_trading.py          # 交易测试
│   ├── test_topics.py           # 话题测试
│   ├── test_settlements.py      # 结算测试
│   ├── test_mall.py             # 商城测试
│   ├── test_admin.py            # 管理后台测试
│   └── test_moderation.py       # 内容风控测试
├── scripts/                     # 脚本工具
│   ├── seed_data.py            # 数据填充
│   ├── generate_test_token.py  # 测试 Token 生成
│   └── ...
├── requirements.txt             # Python 依赖
├── pyproject.toml              # 项目配置 (black, ruff, mypy)
├── pytest.ini                  # pytest 配置
├── alembic.ini                 # Alembic 配置
├── .env.example                # 环境变量示例
└── Dockerfile                  # Docker 镜像
```

### 3.2 分层架构

```
┌─────────────────────────────────────────────────────────┐
│                    API Layer (路由层)                    │
│  - 请求验证 (Pydantic)                                  │
│  - 响应格式化                                           │
│  - 异常处理                                             │
└──────────────────────┬──────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────┐
│                 Service Layer (服务层)                   │
│  - 业务逻辑                                             │
│  - 事务管理                                             │
│  - 外部服务调用 (支付、短信、LLM)                      │
└──────────────────────┬──────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────┐
│                  Model Layer (模型层)                    │
│  - 数据访问 (SQLAlchemy)                               │
│  - 数据验证                                             │
│  - 关系映射                                             │
└──────────────────────┬──────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────┐
│                Database Layer (数据库层)                  │
│  - PostgreSQL 16                                        │
│  - Redis 7                                              │
└─────────────────────────────────────────────────────────┘
```

### 3.3 核心模块说明

#### 3.3.1 LMSR 交易引擎

**文件位置**: `app/services/lmsr.py`

LMSR (Logarithmic Market Scoring Rule) 是预测市场的核心算法：

```python
# 成本函数
C(q) = b * ln(sum(exp(q_i / b)))

# 价格计算
p_i = exp(q_i / b) / sum(exp(q_j / b))

# 其中:
# - q_i: 每个结果的股份数
# - b: 流动性参数 (liquidity parameter)
```

**核心类**:
- `LMSRState`: 市场状态数据类
- `LMSREngine`: LMSR 引擎主类

**主要方法**:
- `calculate_price()`: 计算当前价格
- `buy()`: 买入操作
- `sell()`: 卖出操作
- `calculate_roi()`: 计算 ROI

#### 3.3.2 认证与授权

**认证方式**: JWT (JSON Web Token)

**Token 类型**:
- Access Token: 有效期 2 小时
- Refresh Token: 有效期 7 天

**安全机制**:
- bcrypt 密码哈希
- 登录失败限流 (Redis)
- 账户锁定 (5 次失败锁定 30 分钟)
- 设备指纹追踪

#### 3.3.3 钱包与限额

**限额配置** (越南市场):
- 日充值限额: 500,000 VND
- 月充值限额: 5,000,000 VND
- 最低充值: 10,000 VND

**余额约束**:
- 余额非负约束 (数据库 Check Constraint)
- 交易前余额校验

---

## 4. 前端架构

### 4.1 目录结构

```
code/frontend/
├── src/
│   ├── main.ts                  # 应用入口
│   ├── App.vue                  # 根组件
│   ├── router.ts                # 路由配置
│   ├── i18n.ts                  # 国际化配置
│   ├── stores/                  # Pinia 状态管理
│   │   └── auth.ts             # 认证状态
│   ├── views/                   # 页面组件
│   │   ├── Home.vue            # 首页
│   │   ├── Login.vue           # 登录页
│   │   ├── Register.vue        # 注册页
│   │   ├── Wallet.vue          # 钱包页
│   │   ├── Topics.vue          # 话题列表
│   │   ├── TopicDetail.vue     # 话题详情/交易
│   │   ├── Mall.vue            # 商城页
│   │   ├── kyc/
│   │   │   └── Verify.vue      # KYC 认证
│   │   ├── profile/
│   │   │   └── Index.vue       # 个人资料
│   │   ├── settlement/
│   │   │   ├── List.vue        # 结算列表
│   │   │   └── Detail.vue      # 结算详情
│   │   ├── trading/
│   │   │   └── Positions.vue   # 持仓列表
│   │   └── admin/
│   │       └── Dashboard.vue   # 管理后台
│   ├── components/              # 可复用组件
│   │   ├── Navbar.vue          # 导航栏
│   │   └── LanguageSwitcher.vue # 语言切换
│   ├── utils/
│   │   └── api.ts              # API 客户端
│   ├── styles/
│   │   └── index.scss          # 全局样式
│   └── assets/                 # 静态资源
├── package.json                 # Node 依赖
├── vite.config.ts              # Vite 配置
├── tsconfig.json               # TypeScript 配置
├── .env.example                # 环境变量示例
└── Dockerfile                  # Docker 镜像
```

### 4.2 页面路由

| 路径 | 页面 | 认证要求 |
|------|------|---------|
| `/` | 首页 | 否 |
| `/login` | 登录页 | 否 |
| `/register` | 注册页 | 否 |
| `/wallet` | 钱包页 | 是 |
| `/topics` | 话题列表 | 否 |
| `/topics/:id` | 话题详情 | 否 |
| `/mall` | 商城 | 否 |
| `/settlements` | 结算列表 | 是 |
| `/settlements/:id` | 结算详情 | 是 |
| `/profile` | 个人资料 | 是 |
| `/kyc/verify` | KYC 认证 | 是 |
| `/trading/positions` | 持仓列表 | 是 |
| `/admin` | 管理后台 | 是 + 管理员 |

### 4.3 国际化

**支持语言**:
- 越南语 (vi) - 默认
- 英语 (en)
- 中文 (zh-CN)

---

## 5. 数据架构

### 5.1 数据库 ER 图

```
┌─────────────┐
│    users    │
├─────────────┤
│ id (PK)     │
│ phone       │
│ email       │
│ password    │
│ full_name   │
│ id_number   │
│ birth_date  │
│ status      │
│ role        │
│ created_at  │
│ updated_at  │
└──────┬──────┘
       │ 1
       │
       │ N
       ├──────────────────────────────────────────────┐
       │                                              │
       │ N                                            │ N
┌──────▼────────┐                         ┌──────────▼──────────┐
│ user_wallets  │                         │  creator_profiles    │
├───────────────┤                         ├─────────────────────┤
│ id (PK)       │                         │ user_id (PK, FK)    │
│ user_id (FK)  │                         │ status               │
│ balance       │                         │ topic_count          │
│ daily_recharged│                        │ approved_topic_count │
│ ...           │                         │ ...                  │
└──────┬────────┘                         └─────────────────────┘
       │ 1
       │
       │ N
┌──────▼──────────┐
│ recharge_orders │
├─────────────────┤
│ id (PK)         │
│ user_id (FK)    │
│ amount_vnd      │
│ amount_tokens   │
│ payment_method  │
│ status          │
│ ...             │
└──────┬──────────┘
       │
       │
       │
┌──────▼──────────────┐
│ wallet_transactions  │
├─────────────────────┤
│ id (PK)              │
│ wallet_id (FK)       │
│ amount               │
│ balance_after        │
│ transaction_type     │
│ ...                  │
└─────────────────────┘


┌─────────────────────────────────────────────────────────┐
│                    话题与交易                             │
└─────────────────────────────────────────────────────────┘

┌──────────┐
│  topics  │
├──────────┤
│ id (PK)  │
│ title    │
│ category │
│ creator  │
│  (FK)    ├───┐
│ status   │   │
│ ...      │   │
└────┬─────┘   │
     │ 1       │
     │         │
     │ N       │
┌────▼─────┐  │
│ topic_   │  │
│ reviews  │  │
└──────────┘  │
              │
              │ N
              │
     ┌────────▼─────────┐
     │ market_positions  │
     ├──────────────────┤
     │ id (PK)          │
     │ user_id (FK)     │
     │ topic_id (FK)    │
     │ outcome_index    │
     │ shares           │
     │ avg_price        │
     └──────────────────┘

┌─────────────────────────────────────────────────────────┐
│                      结算                                 │
└─────────────────────────────────────────────────────────┘

┌─────────────────────┐
│ market_settlements  │
├─────────────────────┤
│ id (PK)             │
│ market_id (FK)      │
│ winning_outcome     │
│ total_pool          │
│ status              │
└──────────┬──────────┘
           │ 1
           │
           │ N
┌──────────▼──────────┐
│  user_settlements   │
├─────────────────────┤
│ id (PK)             │
│ settlement_id (FK)  │
│ user_id (FK)        │
│ shares              │
│ payout              │
└─────────────────────┘

┌─────────────────────────────────────────────────────────┐
│                      商城                                 │
└─────────────────────────────────────────────────────────┘

┌──────────────────┐        ┌───────────────┐
│ product_         │        │   products    │
│ categories       │        ├───────────────┤
├──────────────────┤        │ id (PK)       │
│ id (PK)          │   ┌────│ category_id   │
│ parent_id (FK)   │   │    │ (FK)          │
│ name             │   │    │ title         │
│ ...              │   │    │ price         │
└──────────────────┘   │    │ ...           │
                       │    └───────┬───────┘
                       │            │ N
                       │            │
                       │            │
                       │ N          │
            ┌──────────▼──────────┐ │
            │   exchange_orders    │ │
            ├──────────────────────┤ │
            │ id (PK)              │ │
            │ user_id (FK)         │ │
            │ product_id (FK)      │─┘
            │ quantity             │
            │ total_price          │
            └──────────┬───────────┘
                       │ 1
                       │
                       │ N
            ┌──────────▼──────────┐
            │    user_products     │
            ├──────────────────────┤
            │ id (PK)              │
            │ user_id (FK)         │
            │ product_id (FK)      │
            │ order_id (FK)        │
            │ ...                  │
            └──────────────────────┘

┌─────────────────────────────────────────────────────────┐
│                    内容风控                               │
└─────────────────────────────────────────────────────────┘

┌──────────────────┐     ┌──────────────────┐
│  sensitive_words │     │  content_reviews │
├──────────────────┤     ├──────────────────┤
│ id (PK)          │     │ id (PK)          │
│ word             │     │ content_type     │
│ category         │     │ content_id       │
│ language         │     │ user_id (FK)     │
│ ...              │     │ ai_result        │
└──────────────────┘     │ manual_result    │
                         │ ...              │
                         └────────┬─────────┘
                                  │
                                  │
                         ┌────────▼─────────┐
                         │    violations     │
                         ├──────────────────┤
                         │ id (PK)          │
                         │ user_id (FK)     │
                         │ violation_type   │
                         │ severity         │
                         │ ...              │
                         └────────┬─────────┘
                                  │
                                  │
                         ┌────────▼─────────┐
                         │  user_risk_levels │
                         ├──────────────────┤
                         │ user_id (PK, FK) │
                         │ risk_level       │
                         │ risk_score       │
                         │ ...              │
                         └──────────────────┘
```

### 5.2 核心数据表

详细的数据库设计文档请参考 [DATABASE_DESIGN.md](./DATABASE_DESIGN.md)。

---

## 6. 安全架构

### 6.1 认证安全

| 安全措施 | 实现方式 |
|---------|---------|
| 密码存储 | bcrypt 哈希 (工作因子 12) |
| Token | JWT + HS256 签名 |
| Token 过期 | Access Token 2 小时，Refresh Token 7 天 |
| 登录限流 | Redis + 滑动窗口 |
| 账户锁定 | 5 次失败锁定 30 分钟 |

### 6.2 数据安全

| 安全措施 | 说明 |
|---------|------|
| 传输加密 | HTTPS/TLS 1.3 |
| SQL 注入防护 | SQLAlchemy ORM 参数化查询 |
| XSS 防护 | 前端输入转义 + 内容审核 |
| 敏感数据 | 身份证号等敏感字段加密存储 |
| 审计日志 | 所有关键操作记录审计日志 |

### 6.3 合规控制

| 合规要求 | 实现方式 |
|---------|---------|
| 18+ 认证 | KYC 流程 + 年龄校验 |
| 日限额 | 钱包表 `daily_recharged` 字段 |
| 月限额 | 钱包表 `monthly_recharged` 字段 |
| 单向充值 | 无提现/转账功能 |
| 内容风控 | 敏感词过滤 + LLM 审核 |
| 审计追踪 | 所有关键操作审计日志 |

---

## 7. 部署架构

### 7.1 生产环境部署

```
                    ┌─────────────┐
                    │   Cloudflare │
                    │   (CDN/WAF)  │
                    └──────┬──────┘
                           │
              ┌────────────┼────────────┐
              │            │            │
         ┌────▼────┐  ┌───▼────┐  ┌───▼────┐
         │ Nginx 1 │  │ Nginx 2│  │ Nginx 3│
         └────┬────┘  └───┬────┘  └───┬────┘
              │            │            │
              └────────────┼────────────┘
                           │
              ┌────────────┼────────────┐
              │            │            │
         ┌────▼────┐  ┌───▼────┐  ┌───▼────┐
         │ App 1   │  │ App 2  │  │ App 3  │
         │(Worker) │  │(Worker)│  │(Worker)│
         └────┬────┘  └───┬────┘  └───┬────┘
              │            │            │
              └────────────┼────────────┘
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
   ┌────▼────┐      ┌─────▼─────┐    ┌─────▼─────┐
   │PostgreSQL│      │   Redis   │    │  Celery   │
   │ (Primary)│      │ (Cluster) │    │  Workers  │
   └────┬────┘      └─────┬─────┘    └───────────┘
        │                  │
   ┌────▼────┐             │
   │PostgreSQL│             │
   │ (Replica)│             │
   └─────────┘             │
                           │
                    ┌──────▼──────┐
                    │   External   │
                    │   Services   │
                    └──────────────┘
```

### 7.2 Docker 容器化

**后端 Dockerfile**:
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**前端 Dockerfile**:
```dockerfile
FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/nginx.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

---

## 8. 监控与运维

### 8.1 日志架构

```
应用日志 → 文件/标准输出 → Filebeat → Elasticsearch → Kibana
```

**日志级别**:
- ERROR: 错误需要立即处理
- WARNING: 警告需要关注
- INFO: 重要业务流程
- DEBUG: 调试信息

### 8.2 监控指标

| 指标类型 | 具体指标 |
|---------|---------|
| **应用指标** | 请求量、响应时间、错误率、APDEX |
| **业务指标** | 注册用户数、充值金额、交易量、话题数 |
| **系统指标** | CPU、内存、磁盘、网络 |
| **数据库指标** | 连接数、慢查询、QPS、复制延迟 |
| **缓存指标** | 命中率、内存使用率、连接数 |

### 8.3 告警规则

| 告警项 | 触发条件 | 级别 |
|-------|---------|------|
| 应用错误率 | > 5% 持续 5 分钟 | P0 |
| 响应时间 | P95 > 2s 持续 5 分钟 | P1 |
| 数据库连接数 | > 80% 持续 5 分钟 | P1 |
| 缓存命中率 | < 80% 持续 10 分钟 | P2 |
| 磁盘使用率 | > 85% | P2 |

---

## 9. 扩展架构

### 9.1 水平扩展

- **无状态应用**: FastAPI 应用水平扩展
- **数据库读写分离**: 主从复制，读操作走从库
- **缓存集群**: Redis Cluster 分片

### 9.2 未来扩展

- **微服务拆分**: 按业务域拆分为独立服务
- **事件驱动**: Kafka/RabbitMQ 事件总线
- **实时功能**: WebSocket 实时价格更新
- **数据分析**: OLAP 数据库 + BI 报表

---

## 10. 总结

Bingo Market 采用现代化的技术栈和清晰的分层架构，确保了系统的可扩展性、可维护性和安全性。核心设计亮点包括：

1. **合规优先**: 所有功能设计以合规为前提
2. **异步架构**: 核心业务采用异步处理
3. **清晰分层**: API → Service → Model 分层清晰
4. **安全审计**: 完整的审计日志和安全机制
5. **容器化部署**: Docker + Kubernetes 就绪

---

## 附录

### A. 相关文档

- [数据库设计文档](./DATABASE_DESIGN.md)
- [API 文档](../code/backend/README.md) (Swagger/OpenAPI)
- [部署指南](./DEPLOYMENT.md)
- [开发指南](./DEVELOPMENT.md)

### B. 参考资料

- [FastAPI 官方文档](https://fastapi.tiangolo.com/)
- [LMSR 算法说明](https://en.wikipedia.org/wiki/Logarithmic_market_scoring_rule)
- [PostgreSQL 文档](https://www.postgresql.org/docs/)
- [Vue 3 文档](https://vuejs.org/)
