# Bingo Market 数据库设计文档

## 文档信息

| 项目 | 内容 |
|------|------|
| 文档名称 | Bingo Market 数据库设计 |
| 版本 | v1.0 |
| 创建日期 | 2026-03-07 |
| 数据库 | PostgreSQL 16 |

---

## 1. 数据库概述

### 1.1 数据库特性

| 特性 | 说明 |
|------|------|
| 数据库类型 | PostgreSQL 16 |
| 字符编码 | UTF-8 |
| 时区 | UTC |
| 主键类型 | UUID (String 36) |
| JSON 支持 | JSONB (二进制 JSON，支持索引) |

### 1.2 命名约定

| 对象类型 | 约定 | 示例 |
|---------|------|------|
| 表名 | 小写复数，下划线分隔 | `users`, `user_wallets` |
| 列名 | 小写，下划线分隔 | `created_at`, `user_id` |
| 主键 | `id` | `id` |
| 外键 | `{表名单数}_id` | `user_id`, `topic_id` |
| 索引 | `ix_{表名}_{列名}` | `ix_users_email` |
| 时间戳 | `created_at`, `updated_at` | - |

### 1.3 通用字段

所有表都包含以下字段（大部分表）：

| 字段名 | 类型 | 说明 |
|--------|------|------|
| `id` | VARCHAR(36) | UUID 主键 |
| `created_at` | TIMESTAMP | 创建时间 (UTC) |
| `updated_at` | TIMESTAMP | 更新时间 (UTC) |

---

## 2. ER 图

```
┌─────────────────────────────────────────────────────────────────────┐
│                         用户与认证模块                                │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────┐
│    users    │
├─────────────┤
│ id (PK)     │
│ phone       │
│ email       │
│ password_hash│
│ full_name   │
│ id_number   │
│ birth_date  │
│ status      │
│ role        │
│ created_at  │
│ updated_at  │
│ last_login_ │
│ at          │
└──────┬──────┘
       │
       ├────────────────────────────────────────────────────┐
       │                                                    │
       │ 1                                        1         │
┌──────▼────────┐                          ┌──────▼──────────┐
│ user_wallets  │                          │ creator_profiles │
├───────────────┤                          ├──────────────────┤
│ id (PK)       │                          │ user_id (PK, FK)│
│ user_id (FK)  │                          │ status           │
│ balance       │                          │ topic_count      │
│ daily_recharged│                         │ ...              │
│ ...           │                          └──────────────────┘
└──────┬────────┘
       │
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

┌─────────────────────────────────────────────────────────────────────┐
│                         话题与交易模块                                │
└─────────────────────────────────────────────────────────────────────┘

┌──────────┐
│  topics  │
├──────────┤
│ id (PK)  │
│ title    │
│ category │
│ outcome_ │
│ options  │
│ creator_ │
│ id (FK)  │
│ status   │
│ expires_ │
│ at       │
│ ...      │
└────┬─────┘
     │
     │ 1
     │
     │ N
┌────▼─────┐
│ topic_   │
│ reviews  │
├──────────┤
│ id (PK)  │
│ topic_id │
│ (FK)     │
│ auditor_ │
│ id (FK)  │
│ action   │
│ ...      │
└──────────┘

┌──────────┐
│  topics  │
└────┬─────┘
     │
     │ 1
     │
     │ N
┌────▼──────────────┐
│ market_positions   │
├───────────────────┤
│ id (PK)           │
│ user_id (FK)      │
│ topic_id (FK)     │
│ outcome_index     │
│ shares            │
│ avg_price         │
│ ...               │
└───────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                           结算模块                                    │
└─────────────────────────────────────────────────────────────────────┘

┌──────────┐
│  topics  │
└────┬─────┘
     │
     │ 1
     │
     │ 1
┌────▼──────────────────┐
│ market_settlements    │
├───────────────────────┤
│ id (PK)               │
│ market_id (FK)        │
│ winning_outcome_index │
│ total_pool            │
│ status                │
│ ...                   │
└────┬──────────────────┘
     │
     │ 1
     │
     │ N
┌────▼──────────────┐
│ user_settlements  │
├───────────────────┤
│ id (PK)           │
│ settlement_id (FK)│
│ user_id (FK)      │
│ shares            │
│ payout            │
│ ...               │
└───────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                           商城模块                                    │
└─────────────────────────────────────────────────────────────────────┘

┌──────────────────┐
│ product_         │
│ categories       │
├──────────────────┤
│ id (PK)          │
│ parent_id (FK)   │
│ name             │
│ ...              │
└──────┬───────────┘
       │
       │ 1
       │
       │ N
┌──────▼───────────┐
│    products      │
├──────────────────┤
│ id (PK)          │
│ category_id (FK) │
│ title            │
│ price            │
│ supplier_id (FK) │
│ ...              │
└──────┬───────────┘
       │
       │ 1
       │
       │ N
┌──────▼───────────────┐
│  exchange_orders     │
├──────────────────────┤
│ id (PK)              │
│ user_id (FK)         │
│ product_id (FK)      │
│ quantity             │
│ total_price          │
│ ...                  │
└──────┬───────────────┘
       │
       │ 1
       │
       │ N
┌──────▼───────────────┐
│   user_products      │
├──────────────────────┤
│ id (PK)              │
│ user_id (FK)         │
│ product_id (FK)      │
│ order_id (FK)        │
│ ...                  │
└──────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                         内容风控模块                                  │
└─────────────────────────────────────────────────────────────────────┘

┌──────────────────┐
│  sensitive_words │
├──────────────────┤
│ id (PK)          │
│ word             │
│ category         │
│ language         │
│ ...              │
└──────────────────┘

┌──────────────────┐
│  users           │
└──────┬───────────┘
       │
       │ 1
       │
       │ N
┌──────▼─────────────────┐
│   content_reviews      │
├────────────────────────┤
│ id (PK)                │
│ user_id (FK)           │
│ content_type           │
│ content_id             │
│ ai_result              │
│ manual_result          │
│ ...                    │
└──────┬─────────────────┘
       │
       │
       │
┌──────▼───────────┐
│   violations     │
├──────────────────┤
│ id (PK)          │
│ user_id (FK)     │
│ violation_type   │
│ severity         │
│ ...              │
└──────┬───────────┘
       │
       │ 1
       │
       │ 1
┌──────▼───────────────┐
│ user_risk_levels     │
├──────────────────────┤
│ user_id (PK, FK)     │
│ risk_level           │
│ risk_score           │
│ ...                  │
└──────────────────────┘
```

---

## 3. 表设计详解

### 3.1 用户模块

#### 3.1.1 `users` - 用户表

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| `id` | VARCHAR(36) | PK | 用户 UUID |
| `phone` | VARCHAR(20) | NULL, INDEX | 手机号 (越南格式) |
| `email` | VARCHAR(255) | NULL, INDEX | 邮箱 |
| `password_hash` | VARCHAR(255) | NOT NULL | bcrypt 密码哈希 |
| `full_name` | VARCHAR(100) | NULL | 全名 |
| `id_number` | VARCHAR(50) | NULL | 身份证号 (加密) |
| `birth_date` | TIMESTAMP | NULL | 出生日期 |
| `status` | VARCHAR(20) | NOT NULL | 状态: pending, unverified, verified_18plus, rejected, banned |
| `role` | VARCHAR(20) | NOT NULL | 角色: user, moderator, admin |
| `created_at` | TIMESTAMP | NOT NULL | 创建时间 |
| `updated_at` | TIMESTAMP | NOT NULL | 更新时间 |
| `last_login_at` | TIMESTAMP | NULL | 最后登录时间 |

**索引**:
- `ix_users_phone`: `phone`
- `ix_users_email`: `email`

---

#### 3.1.2 `user_wallets` - 用户钱包表

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| `id` | VARCHAR(36) | PK | 钱包 UUID |
| `user_id` | VARCHAR(36) | FK, UNIQUE, INDEX | 用户 ID |
| `balance` | BIGINT | NOT NULL, CHECK >=0 | 余额 (知识币，1:1 VND) |
| `daily_recharged` | BIGINT | NOT NULL | 今日已充值 |
| `daily_recharged_date` | TIMESTAMP | NULL | 充值日期 |
| `monthly_recharged` | BIGINT | NOT NULL | 本月已充值 |
| `monthly_recharged_month` | INTEGER | NULL | 充值月份 (YYYYMM) |
| `status` | VARCHAR(20) | NOT NULL | 状态: active, frozen |
| `created_at` | TIMESTAMP | NOT NULL | 创建时间 |
| `updated_at` | TIMESTAMP | NOT NULL | 更新时间 |

**约束**:
- `check_balance_non_negative`: `balance >= 0`

**索引**:
- `ix_user_wallets_user_id`: `user_id` (UNIQUE)

**关系**:
- 1:1 with `users`

---

#### 3.1.3 `recharge_orders` - 充值订单表

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| `id` | VARCHAR(36) | PK | 订单 UUID |
| `user_id` | VARCHAR(36) | FK, INDEX | 用户 ID |
| `amount_vnd` | BIGINT | NOT NULL | VND 金额 |
| `amount_tokens` | BIGINT | NOT NULL | 知识币数量 (1:1) |
| `payment_method` | VARCHAR(50) | NOT NULL | 支付方式: momo, zalopay, manual |
| `status` | VARCHAR(20) | NOT NULL | 状态: pending, success, failed, cancelled |
| `external_order_id` | VARCHAR(100) | NULL | 第三方支付订单号 |
| `daily_limit_used` | BIGINT | NOT NULL | 下单时的日限额使用量 |
| `monthly_limit_used` | BIGINT | NOT NULL | 下单时的月限额使用量 |
| `created_at` | TIMESTAMP | NOT NULL | 创建时间 |
| `updated_at` | TIMESTAMP | NOT NULL | 更新时间 |
| `paid_at` | TIMESTAMP | NULL | 支付成功时间 |

**索引**:
- `ix_recharge_orders_user_id`: `user_id`

**关系**:
- N:1 with `users`

---

#### 3.1.4 `wallet_transactions` - 钱包交易流水表

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| `id` | VARCHAR(36) | PK | 交易 UUID |
| `wallet_id` | VARCHAR(36) | FK, INDEX | 钱包 ID |
| `amount` | BIGINT | NOT NULL | 金额 (正为收入，负为支出) |
| `balance_after` | BIGINT | NOT NULL | 交易后余额 |
| `transaction_type` | VARCHAR(50) | NOT NULL | 交易类型: recharge, prediction_purchase, prediction_sale, settlement, purchase |
| `reference_id` | VARCHAR(36) | NULL | 关联实体 ID |
| `reference_type` | VARCHAR(50) | NULL | 关联实体类型 |
| `description` | VARCHAR(255) | NULL | 描述 |
| `created_at` | TIMESTAMP | NOT NULL | 创建时间 |

**索引**:
- `ix_wallet_transactions_wallet_id`: `wallet_id`

**关系**:
- N:1 with `user_wallets`

---

#### 3.1.5 `creator_profiles` - 创作者资料表

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| `user_id` | VARCHAR(36) | PK, FK | 用户 ID |
| `status` | VARCHAR(20) | NOT NULL | 状态: pending, approved, rejected |
| `approved_by` | VARCHAR(36) | NULL | 审核人 ID |
| `approved_at` | TIMESTAMP | NULL | 审核时间 |
| `topic_count` | INTEGER | NOT NULL | 话题总数 |
| `approved_topic_count` | INTEGER | NOT NULL | 已通过话题数 |
| `created_at` | TIMESTAMP | NOT NULL | 创建时间 |

**关系**:
- 1:1 with `users`

---

### 3.2 话题与交易模块

#### 3.2.1 `topics` - 话题/预测市场表

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| `id` | VARCHAR(36) | PK | 话题 UUID |
| `title` | VARCHAR(100) | NOT NULL | 标题 |
| `description` | TEXT | NOT NULL | 描述 |
| `category` | VARCHAR(50) | NOT NULL | 分类: tech, business, culture, academic |
| `outcome_options` | JSONB | NOT NULL | 结果选项数组 |
| `creator_id` | VARCHAR(36) | FK, INDEX | 创建者 ID |
| `status` | VARCHAR(20) | NOT NULL | 状态: draft, pending_review, active, expired, settled, rejected, suspended |
| `expires_at` | TIMESTAMP | NOT NULL | 到期时间 |
| `settled_at` | TIMESTAMP | NULL | 结算时间 |
| `settled_outcome` | INTEGER | NULL | 结算结果索引 |
| `view_count` | INTEGER | NOT NULL | 浏览次数 |
| `participant_count` | INTEGER | NOT NULL | 参与者数 |
| `trade_volume` | INTEGER | NOT NULL | 交易量 |
| `created_at` | TIMESTAMP | NOT NULL | 创建时间 |
| `updated_at` | TIMESTAMP | NOT NULL | 更新时间 |

**索引**:
- `ix_topics_creator_id`: `creator_id`
- `ix_topics_status_category`: `(status, category)`
- `ix_topics_expires_at`: `expires_at`

**关系**:
- N:1 with `users` (creator)

---

#### 3.2.2 `topic_reviews` - 话题审核记录表

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| `id` | VARCHAR(36) | PK | 审核 UUID |
| `topic_id` | VARCHAR(36) | FK, INDEX | 话题 ID |
| `auditor_id` | VARCHAR(36) | FK | 审核人 ID |
| `action` | VARCHAR(20) | NOT NULL | 操作: approved, rejected |
| `reason` | TEXT | NULL | 原因 |
| `created_at` | TIMESTAMP | NOT NULL | 创建时间 |

**索引**:
- `ix_topic_reviews_topic_id`: `topic_id`

**关系**:
- N:1 with `topics`
- N:1 with `users` (auditor)

---

#### 3.2.3 `market_positions` - 用户持仓表

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| `id` | VARCHAR(36) | PK | 持仓 UUID |
| `user_id` | VARCHAR(36) | FK, INDEX | 用户 ID |
| `topic_id` | VARCHAR(36) | FK, INDEX | 话题 ID |
| `outcome_index` | INTEGER | NOT NULL | 结果索引 |
| `shares` | INTEGER | NOT NULL | 股份数 |
| `avg_price` | FLOAT | NOT NULL | 平均买入价 |
| `created_at` | TIMESTAMP | NOT NULL | 创建时间 |
| `updated_at` | TIMESTAMP | NOT NULL | 更新时间 |

**索引**:
- `ix_market_positions_user_id`: `user_id`
- `ix_market_positions_topic_id`: `topic_id`

**关系**:
- N:1 with `users`
- N:1 with `topics`

---

### 3.3 结算模块

#### 3.3.1 `market_settlements` - 市场结算表

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| `id` | VARCHAR(36) | PK | 结算 UUID |
| `market_id` | VARCHAR(36) | FK, UNIQUE | 话题/市场 ID |
| `winning_outcome_index` | INTEGER | NOT NULL | 获胜结果索引 |
| `total_pool` | BIGINT | NOT NULL | 总奖池 |
| `total_shares_winning` | BIGINT | NOT NULL | 获胜股份总数 |
| `status` | VARCHAR(20) | NOT NULL | 状态: pending, settling, settled, disputed |
| `settled_by` | VARCHAR(36) | FK, NULL | 结算人 ID |
| `settled_at` | TIMESTAMP | NULL | 结算时间 |
| `created_at` | TIMESTAMP | NOT NULL | 创建时间 |
| `updated_at` | TIMESTAMP | NOT NULL | 更新时间 |

**关系**:
- 1:1 with `topics`
- N:1 with `users` (settled_by)

---

#### 3.3.2 `user_settlements` - 用户结算表

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| `id` | VARCHAR(36) | PK | 用户结算 UUID |
| `settlement_id` | VARCHAR(36) | FK, INDEX | 结算 ID |
| `user_id` | VARCHAR(36) | FK, INDEX | 用户 ID |
| `outcome_index` | INTEGER | NOT NULL | 用户持有结果索引 |
| `shares` | BIGINT | NOT NULL | 股份数 |
| `payout` | BIGINT | NOT NULL | 赔付金额 (0 表示未中奖) |
| `status` | VARCHAR(20) | NOT NULL | 状态: pending, paid, failed |
| `paid_at` | TIMESTAMP | NULL | 赔付时间 |
| `created_at` | TIMESTAMP | NOT NULL | 创建时间 |

**索引**:
- `ix_user_settlements_settlement_id`: `settlement_id`
- `ix_user_settlements_user_id`: `user_id`

**关系**:
- N:1 with `market_settlements`
- N:1 with `users`

---

#### 3.3.3 `settlement_disputes` - 结算争议表

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| `id` | VARCHAR(36) | PK | 争议 UUID |
| `settlement_id` | VARCHAR(36) | FK, INDEX | 结算 ID |
| `user_id` | VARCHAR(36) | FK | 用户 ID |
| `reason` | TEXT | NOT NULL | 争议原因 |
| `evidence` | JSONB | NULL | 证据 |
| `status` | VARCHAR(20) | NOT NULL | 状态: pending, resolved, rejected |
| `resolved_by` | VARCHAR(36) | FK, NULL | 解决人 ID |
| `resolved_at` | TIMESTAMP | NULL | 解决时间 |
| `resolution` | TEXT | NULL | 解决结果 |
| `created_at` | TIMESTAMP | NOT NULL | 创建时间 |

**索引**:
- `ix_settlement_disputes_settlement_id`: `settlement_id`

**关系**:
- N:1 with `market_settlements`
- N:1 with `users` (user)
- N:1 with `users` (resolved_by)

---

#### 3.3.4 `settlement_announcements` - 结算公告表

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| `id` | VARCHAR(36) | PK | 公告 UUID |
| `settlement_id` | VARCHAR(36) | FK, UNIQUE | 结算 ID |
| `topic_id` | VARCHAR(36) | FK, INDEX | 话题 ID |
| `title` | VARCHAR(200) | NOT NULL | 标题 |
| `content` | TEXT | NOT NULL | 内容 |
| `winning_outcome_index` | INTEGER | NOT NULL | 获胜结果索引 |
| `winning_outcome_text` | VARCHAR(200) | NOT NULL | 获胜结果文本 |
| `total_pool` | BIGINT | NOT NULL | 总奖池 |
| `total_winning_shares` | BIGINT | NOT NULL | 获胜股份总数 |
| `total_participants` | INTEGER | NOT NULL | 参与者总数 |
| `total_payout` | BIGINT | NOT NULL | 总赔付 |
| `is_published` | BOOLEAN | NOT NULL | 是否已发布 |
| `published_at` | TIMESTAMP | NULL | 发布时间 |
| `created_at` | TIMESTAMP | NOT NULL | 创建时间 |
| `updated_at` | TIMESTAMP | NOT NULL | 更新时间 |

**索引**:
- `ix_settlement_announcements_topic_id`: `topic_id`

**关系**:
- 1:1 with `market_settlements`
- N:1 with `topics`

---

### 3.4 商城模块

#### 3.4.1 `product_categories` - 商品分类表

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| `id` | VARCHAR(36) | PK | 分类 UUID |
| `name` | VARCHAR(100) | NOT NULL | 分类名称 |
| `parent_id` | VARCHAR(36) | FK, NULL | 父分类 ID |
| `sort_order` | INTEGER | NOT NULL | 排序 |
| `is_active` | BOOLEAN | NOT NULL | 是否启用 |
| `created_at` | TIMESTAMP | NOT NULL | 创建时间 |

**关系**:
- N:1 with `product_categories` (self-referential)

---

#### 3.4.2 `products` - 商品表

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| `id` | VARCHAR(36) | PK | 商品 UUID |
| `title` | VARCHAR(255) | NOT NULL | 标题 |
| `description` | TEXT | NOT NULL | 描述 |
| `category_id` | VARCHAR(36) | FK, INDEX | 分类 ID |
| `price` | BIGINT | NOT NULL | 价格 (知识币) |
| `inventory_type` | VARCHAR(20) | NOT NULL | 库存类型: limited, unlimited |
| `inventory_count` | BIGINT | NULL | 库存数量 (limited 类型) |
| `sold_count` | INTEGER | NOT NULL | 已售数量 |
| `product_type` | VARCHAR(50) | NOT NULL | 商品类型: digital, service, membership, virtual |
| `delivery_config` | JSONB | NOT NULL | 交付配置 |
| `status` | VARCHAR(20) | NOT NULL | 状态: draft, pending, active, inactive |
| `supplier_id` | VARCHAR(36) | FK, INDEX | 供应商 ID |
| `created_at` | TIMESTAMP | NOT NULL | 创建时间 |
| `updated_at` | TIMESTAMP | NOT NULL | 更新时间 |

**索引**:
- `ix_products_category_id`: `category_id`
- `ix_products_supplier_id`: `supplier_id`

**关系**:
- N:1 with `product_categories`
- N:1 with `users` (supplier)

---

#### 3.4.3 `exchange_orders` - 兑换订单表

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| `id` | VARCHAR(36) | PK | 订单 UUID |
| `user_id` | VARCHAR(36) | FK, INDEX | 用户 ID |
| `product_id` | VARCHAR(36) | FK, INDEX | 商品 ID |
| `quantity` | INTEGER | NOT NULL | 数量 |
| `total_price` | BIGINT | NOT NULL | 总价 |
| `delivery_info` | JSONB | NULL | 交付信息 |
| `status` | VARCHAR(20) | NOT NULL | 状态: processing, delivered, failed, cancelled |
| `created_at` | TIMESTAMP | NOT NULL | 创建时间 |
| `updated_at` | TIMESTAMP | NOT NULL | 更新时间 |

**索引**:
- `ix_exchange_orders_user_id`: `user_id`
- `ix_exchange_orders_product_id`: `product_id`

**关系**:
- N:1 with `users`
- N:1 with `products`

---

#### 3.4.4 `user_products` - 用户商品表

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| `id` | VARCHAR(36) | PK | 用户商品 UUID |
| `user_id` | VARCHAR(36) | FK, INDEX | 用户 ID |
| `product_id` | VARCHAR(36) | FK | 商品 ID |
| `order_id` | VARCHAR(36) | FK | 订单 ID |
| `delivery_code` | VARCHAR(100) | NULL | 兑换码 |
| `access_url` | VARCHAR(500) | NULL | 访问 URL |
| `expires_at` | TIMESTAMP | NULL | 过期时间 |
| `is_used` | BOOLEAN | NOT NULL | 是否已使用 |
| `used_at` | TIMESTAMP | NULL | 使用时间 |
| `created_at` | TIMESTAMP | NOT NULL | 创建时间 |

**索引**:
- `ix_user_products_user_id`: `user_id`

**关系**:
- N:1 with `users`
- N:1 with `products`
- N:1 with `exchange_orders`

---

### 3.5 内容风控模块

#### 3.5.1 `sensitive_words` - 敏感词表

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| `id` | VARCHAR(36) | PK | 敏感词 UUID |
| `word` | VARCHAR(255) | UNIQUE, INDEX | 敏感词 |
| `category` | VARCHAR(50) | NOT NULL | 分类: politics, religion, sports, porn, violence |
| `language` | VARCHAR(10) | NOT NULL | 语言: vi, en |
| `match_type` | VARCHAR(20) | NOT NULL | 匹配类型: exact, fuzzy |
| `is_active` | BOOLEAN | NOT NULL | 是否启用 |
| `created_at` | TIMESTAMP | NOT NULL | 创建时间 |
| `updated_at` | TIMESTAMP | NOT NULL | 更新时间 |

**索引**:
- `ix_sensitive_words_word`: `word` (UNIQUE)

---

#### 3.5.2 `content_reviews` - 内容审核表

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| `id` | VARCHAR(36) | PK | 审核 UUID |
| `content_type` | VARCHAR(50) | NOT NULL | 内容类型: topic, product, comment |
| `content_id` | VARCHAR(36) | INDEX | 内容 ID |
| `user_id` | VARCHAR(36) | FK, INDEX | 用户 ID |
| `content_text` | TEXT | NOT NULL | 内容文本 |
| `ai_result` | VARCHAR(20) | NULL | AI 结果: high_risk, low_risk, error |
| `ai_confidence` | FLOAT | NULL | AI 置信度 |
| `ai_notes` | TEXT | NULL | AI 备注 |
| `manual_result` | VARCHAR(20) | NULL | 人工结果: approved, rejected |
| `reject_reason` | TEXT | NULL | 拒绝原因 |
| `auditor_id` | VARCHAR(36) | FK, NULL | 审核人 ID |
| `status` | VARCHAR(20) | NOT NULL | 状态: pending, ai_review, manual_review, approved, rejected |
| `created_at` | TIMESTAMP | NOT NULL | 创建时间 |
| `updated_at` | TIMESTAMP | NOT NULL | 更新时间 |

**索引**:
- `ix_content_reviews_content_id`: `content_id`
- `ix_content_reviews_user_id`: `user_id`

**关系**:
- N:1 with `users` (user)
- N:1 with `users` (auditor)

---

#### 3.5.3 `violations` - 违规记录表

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| `id` | VARCHAR(36) | PK | 违规 UUID |
| `user_id` | VARCHAR(36) | FK, INDEX | 用户 ID |
| `violation_type` | VARCHAR(50) | NOT NULL | 违规类型: sensitive_content, spam, fraud |
| `severity` | VARCHAR(20) | NOT NULL | 严重程度: light, moderate, severe, critical |
| `content_type` | VARCHAR(50) | NULL | 内容类型 |
| `content_id` | VARCHAR(36) | NULL | 内容 ID |
| `evidence` | JSONB | NULL | 证据 |
| `penalty_type` | VARCHAR(50) | NOT NULL | 处罚类型: warning, restriction, ban |
| `penalty_duration` | INTEGER | NULL | 处罚时长 (天) |
| `status` | VARCHAR(20) | NOT NULL | 状态: pending, appealed, resolved |
| `resolved_by` | VARCHAR(36) | FK, NULL | 解决人 ID |
| `resolved_at` | TIMESTAMP | NULL | 解决时间 |
| `created_at` | TIMESTAMP | NOT NULL | 创建时间 |
| `updated_at` | TIMESTAMP | NOT NULL | 更新时间 |

**索引**:
- `ix_violations_user_id`: `user_id`

**关系**:
- N:1 with `users` (user)
- N:1 with `users` (resolved_by)

---

#### 3.5.4 `user_risk_levels` - 用户风险等级表

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| `user_id` | VARCHAR(36) | PK, FK | 用户 ID |
| `risk_level` | VARCHAR(20) | NOT NULL | 风险等级: low, medium, high, blacklist |
| `risk_score` | INTEGER | NOT NULL | 风险分数 (0-100) |
| `violation_count` | INTEGER | NOT NULL | 违规次数 |
| `last_violation_at` | TIMESTAMP | NULL | 最后违规时间 |
| `next_downgrade_at` | TIMESTAMP | NULL | 下次降级时间 |
| `created_at` | TIMESTAMP | NOT NULL | 创建时间 |
| `updated_at` | TIMESTAMP | NOT NULL | 更新时间 |

**关系**:
- 1:1 with `users`

---

#### 3.5.5 `user_appeals` - 用户申诉表

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| `id` | VARCHAR(36) | PK | 申诉 UUID |
| `user_id` | VARCHAR(36) | FK, INDEX | 用户 ID |
| `violation_id` | VARCHAR(36) | FK, INDEX | 违规 ID |
| `reason` | TEXT | NOT NULL | 申诉原因 |
| `evidence` | JSONB | NULL | 证据 |
| `status` | VARCHAR(20) | NOT NULL | 状态: pending, approved, rejected |
| `reviewer_id` | VARCHAR(36) | FK, NULL | 审核人 ID |
| `review_notes` | TEXT | NULL | 审核备注 |
| `reviewed_at` | TIMESTAMP | NULL | 审核时间 |
| `created_at` | TIMESTAMP | NOT NULL | 创建时间 |
| `updated_at` | TIMESTAMP | NOT NULL | 更新时间 |

**索引**:
- `ix_user_appeals_user_id`: `user_id`
- `ix_user_appeals_violation_id`: `violation_id`

**关系**:
- N:1 with `users` (user)
- N:1 with `violations`
- N:1 with `users` (reviewer)

---

#### 3.5.6 `creator_credit_levels` - 创作者信用等级表

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| `user_id` | VARCHAR(36) | PK, FK | 用户 ID |
| `credit_level` | VARCHAR(10) | NOT NULL | 信用等级: S, A, B, C |
| `credit_score` | INTEGER | NOT NULL | 信用分数 (0-100) |
| `content_count` | INTEGER | NOT NULL | 内容总数 |
| `approved_count` | INTEGER | NOT NULL | 通过数 |
| `rejected_count` | INTEGER | NOT NULL | 拒绝数 |
| `avg_review_time` | FLOAT | NULL | 平均审核时间 (小时) |
| `created_at` | TIMESTAMP | NOT NULL | 创建时间 |
| `updated_at` | TIMESTAMP | NOT NULL | 更新时间 |

**关系**:
- 1:1 with `users`

---

### 3.6 系统模块

#### 3.6.1 `audit_logs` - 审计日志表

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| `id` | VARCHAR(36) | PK | 日志 UUID |
| `user_id` | VARCHAR(36) | FK, INDEX, NULL | 用户 ID |
| `user_agent` | VARCHAR(500) | NULL | User Agent |
| `ip_address` | VARCHAR(45) | NULL | IP 地址 (IPv4/IPv6) |
| `action` | VARCHAR(100) | NOT NULL, INDEX | 操作: LOGIN, LOGOUT, RECHARGE |
| `resource_type` | VARCHAR(50) | NULL | 资源类型: USER, WALLET, TOPIC |
| `resource_id` | VARCHAR(36) | NULL | 资源 ID |
| `method` | VARCHAR(10) | NULL | HTTP 方法 |
| `endpoint` | VARCHAR(255) | NULL | API 端点 |
| `request_body` | TEXT | NULL | 请求体 (已脱敏) |
| `response_status` | INTEGER | NULL | HTTP 状态码 |
| `status` | VARCHAR(20) | NOT NULL | 状态: success, failure, error |
| `error_message` | VARCHAR(500) | NULL | 错误信息 |
| `metadata_json` | VARCHAR(2000) | NULL | 元数据 JSON |
| `created_at` | TIMESTAMP | NOT NULL, INDEX | 创建时间 |

**索引**:
- `ix_audit_logs_user_id`: `user_id`
- `ix_audit_logs_created_at`: `created_at`

**关系**:
- N:1 with `users`

---

#### 3.6.2 `login_devices` - 登录设备表

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| `id` | VARCHAR(36) | PK | 设备 UUID |
| `user_id` | VARCHAR(36) | FK, INDEX | 用户 ID |
| `device_name` | VARCHAR(100) | NULL | 设备名称 (如 "iPhone 14") |
| `device_type` | VARCHAR(50) | NULL | 设备类型: mobile, tablet, desktop |
| `os` | VARCHAR(50) | NULL | 操作系统: iOS, Android, Windows |
| `browser` | VARCHAR(50) | NULL | 浏览器: Chrome, Safari |
| `ip_address` | VARCHAR(45) | NULL | IP 地址 |
| `user_agent` | VARCHAR(500) | NULL | User Agent |
| `device_fingerprint` | VARCHAR(100) | INDEX, NULL | 设备指纹 |
| `is_current` | BOOLEAN | NOT NULL | 是否当前设备 |
| `last_active_at` | TIMESTAMP | NULL | 最后活跃时间 |
| `created_at` | TIMESTAMP | NOT NULL | 创建时间 |

**索引**:
- `ix_login_devices_user_id`: `user_id`
- `ix_login_devices_device_fingerprint`: `device_fingerprint`

**关系**:
- N:1 with `users`

---

#### 3.6.3 `user_terms` - 用户条款表

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| `id` | VARCHAR(36) | PK | 条款 UUID |
| `language` | VARCHAR(10) | NOT NULL, INDEX | 语言: vi, en |
| `title` | VARCHAR(200) | NOT NULL | 标题 |
| `content` | TEXT | NOT NULL | 内容 |
| `version` | VARCHAR(20) | NOT NULL | 版本号 |
| `is_active` | BOOLEAN | NOT NULL | 是否当前版本 |
| `created_at` | TIMESTAMP | NOT NULL | 创建时间 |
| `updated_at` | TIMESTAMP | NOT NULL | 更新时间 |

**索引**:
- `ix_user_terms_language`: `language`

---

#### 3.6.4 `user_notifications` - 用户通知表

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| `id` | VARCHAR(36) | PK | 通知 UUID |
| `user_id` | VARCHAR(36) | FK, INDEX | 用户 ID |
| `notification_type` | VARCHAR(50) | NOT NULL | 通知类型: settlement, system, trade |
| `title` | VARCHAR(200) | NOT NULL | 标题 |
| `content` | TEXT | NOT NULL | 内容 |
| `resource_type` | VARCHAR(50) | NULL | 资源类型 |
| `resource_id` | VARCHAR(36) | NULL | 资源 ID |
| `data` | JSONB | NULL | 额外数据 |
| `is_read` | BOOLEAN | NOT NULL | 是否已读 |
| `is_pushed` | BOOLEAN | NOT NULL | 是否已推送 |
| `created_at` | TIMESTAMP | NOT NULL | 创建时间 |
| `read_at` | TIMESTAMP | NULL | 已读时间 |
| `pushed_at` | TIMESTAMP | NULL | 推送时间 |

**索引**:
- `ix_user_notifications_user_id`: `user_id`

**关系**:
- N:1 with `users`

---

#### 3.6.5 `announcements` - 系统公告表

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| `id` | VARCHAR(36) | PK | 公告 UUID |
| `created_by` | VARCHAR(36) | FK, NULL | 创建人 ID |
| `title` | VARCHAR(200) | NOT NULL | 标题 |
| `content` | TEXT | NOT NULL | 内容 |
| `summary` | VARCHAR(500) | NULL | 摘要 |
| `announcement_type` | VARCHAR(50) | NOT NULL | 类型: system, maintenance, update, event |
| `priority` | VARCHAR(20) | NOT NULL | 优先级: low, normal, high, urgent |
| `is_published` | BOOLEAN | NOT NULL | 是否已发布 |
| `published_at` | TIMESTAMP | NULL | 发布时间 |
| `expires_at` | TIMESTAMP | NULL | 过期时间 |
| `target_audience` | VARCHAR(20) | NOT NULL | 目标受众: all, users, admins, creators |
| `metadata_json` | JSONB | NULL | 元数据 |
| `view_count` | INTEGER | NOT NULL | 浏览次数 |
| `created_at` | TIMESTAMP | NOT NULL | 创建时间 |
| `updated_at` | TIMESTAMP | NOT NULL | 更新时间 |

**关系**:
- N:1 with `users` (created_by)

---

#### 3.6.6 `system_configs` - 系统配置表

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| `id` | VARCHAR(36) | PK | 配置 UUID |
| `config_key` | VARCHAR(100) | UNIQUE, INDEX, NOT NULL | 配置键 |
| `config_value` | TEXT | NOT NULL | 配置值 (JSON 字符串) |
| `value_type` | VARCHAR(20) | NOT NULL | 值类型: string, number, boolean, json |
| `description` | VARCHAR(500) | NULL | 描述 |
| `is_public` | BOOLEAN | NOT NULL | 是否公开 (对用户可见) |
| `is_editable` | BOOLEAN | NOT NULL | 是否可编辑 |
| `created_at` | TIMESTAMP | NOT NULL | 创建时间 |
| `updated_at` | TIMESTAMP | NOT NULL | 更新时间 |

**索引**:
- `ix_system_configs_config_key`: `config_key` (UNIQUE)

---

## 4. 数据库迁移

### 4.1 迁移工具

使用 **Alembic** 进行数据库版本管理。

### 4.2 迁移命令

```bash
# 创建新迁移
alembic revision --autogenerate -m "description"

# 执行迁移
alembic upgrade head

# 回滚迁移
alembic downgrade -1

# 查看迁移历史
alembic history

# 查看当前版本
alembic current
```

### 4.3 初始迁移

初始迁移文件: `alembic/versions/20260307_initial_migration_create_all_tables.py`

---

## 5. 数据库优化建议

### 5.1 索引优化

已创建的索引:
- 所有外键字段
- 常用查询字段 (email, phone, status, category)
- 复合索引 (status + category)
- 时间字段索引 (created_at, expires_at)

### 5.2 分区建议

未来可考虑对以下表进行分区:
- `audit_logs`: 按时间分区 (月/季度)
- `wallet_transactions`: 按时间分区
- `user_notifications`: 按时间分区

### 5.3 归档策略

- 审计日志: 保留 1 年，超过 1 年归档到冷存储
- 交易流水: 保留 2 年
- 通知: 保留 6 个月

---

## 6. 安全与合规

### 6.1 数据加密

| 数据类型 | 加密方式 |
|---------|---------|
| 密码 | bcrypt (工作因子 12) |
| 身份证号 | AES-256 |
| JWT Token | HS256 签名 |

### 6.2 审计追踪

所有关键操作都记录在 `audit_logs` 表中，包括:
- 用户登录/登出
- 充值操作
- 交易操作
- 密码修改
- KYC 认证
- 管理员操作

---

## 附录

### A. 相关文档

- [系统架构设计文档](./ARCHITECTURE.md)
- [Alembic 文档](https://alembic.sqlalchemy.org/)
- [PostgreSQL 16 文档](https://www.postgresql.org/docs/16/)

### B. 变更记录

| 版本 | 日期 | 变更说明 |
|------|------|---------|
| v1.0 | 2026-03-07 | 初始版本 |
