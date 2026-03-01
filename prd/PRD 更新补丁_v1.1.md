# PRD 文档更新补丁 v1.1

**更新日期**: 2026-03-01
**更新目的**: 修复 PRD 审查中发现的 P0 严重问题
**涉及模块**: 用户与权限、钱包、LMSR 交易、话题、结算、后台

---

## 更新摘要

### P0 问题修复清单

| 问题 ID | 问题描述 | 涉及 PRD | 修复状态 |
|--------|---------|---------|---------|
| WALLET-02 | 充值订单表添加 idempotency_key 字段 | 钱包与充值支付模块_PRD.md | ✅ 已修复 |
| LMSR-01 | 明确 markets 表与 topics 表一对一关系 | LMSR 交易引擎核心模块_PRD.md | ✅ 已修复 |
| LMSR-03 | 统一 LMSR 交易接口路径 | LMSR 交易引擎核心模块_PRD.md | ✅ 已修复 |
| LMSR-04 | 补充 Saga 事务超时处理 | LMSR 交易引擎核心模块_PRD.md | ✅ 已修复 |
| ADMIN-02 | 明确 admins 表与 users 表关系 | 运营后台核心模块_PRD.md | ✅ 已修复 |
| SETTLE-01 | 定义仲裁委员会角色 | 到期结算核心模块_PRD.md | ✅ 已修复 |
| AUTH-03 | 添加刷新 Token 接口 | 用户与权限体系模块_PRD.md | ✅ 已修复 |
| DATA-03 | 统一金额字段精度定义 | 00_架构设计总览.md | ✅ 已修复 |

---

## 1. 钱包与充值支付模块 PRD 修复

### 1.1 修复 WALLET-02：添加幂等性字段

**位置**: 6.1.2 充值订单表 (recharge_orders)

**原定义**:
```markdown
| 字段名 | 类型 | 必填 | 描述 |
|--------|------|------|------|
| id | UUID | 是 | 订单 ID |
| user_id | UUID | 是 | 用户 ID |
| amount_vnd | BIGINT | 是 | 充值金额（VND，整数存储） |
| ... |
```

**修复后**:
```markdown
| 字段名 | 类型 | 必填 | 描述 |
|--------|------|------|------|
| id | UUID | 是 | 订单 ID |
| user_id | UUID | 是 | 用户 ID |
| amount_vnd | BIGINT | 是 | 充值金额（VND，整数存储） |
| amount_tokens | BIGINT | 是 | 获得知识币数量 |
| payment_method | VARCHAR(50) | 是 | 支付方式（momo/zalopay/manual） |
| status | VARCHAR(20) | 是 | 订单状态（pending/success/failed/cancelled） |
| external_order_id | VARCHAR(100) | 否 | 支付网关订单 ID |
| idempotency_key | VARCHAR(100) | 否 | 幂等性键，防止重复提交 |
| daily_limit_used | BIGINT | 是 | 下单时当日已使用额度 |
| monthly_limit_used | BIGINT | 是 | 下单时当月已使用额度 |
| created_at | TIMESTAMP | 是 | 创建时间 |
| updated_at | TIMESTAMP | 是 | 更新时间 |
```

**说明**: `idempotency_key` 由前端生成，每次充值请求使用唯一 UUID，后端通过该键防止重复入账。

---

### 1.2 修复 WALLET-01：统一接口路径

**位置**: 6.2 核心接口清单

**原接口路径**:
```
POST /api/v1/recharge/orders
GET /api/v1/recharge/orders/{order_id}
GET /api/v1/recharge/records
```

**修复后接口路径**:
```
POST /api/v1/wallet/recharge/orders
GET /api/v1/wallet/recharge/orders/{order_id}
GET /api/v1/wallet/recharge/records
GET /api/v1/wallet/transactions
```

---

## 2. LMSR 交易引擎核心模块 PRD 修复

### 2.1 修复 LMSR-01：明确 topics 与 markets 关系

**位置**: 一、模块概述 - 1.3 模块与其他系统模块的关联关系

**新增内容**:
```markdown
### 1.3 模块与其他系统模块的关联关系

- **上游依赖**: 话题与市场管理模块（市场创建）、用户与权限体系模块（用户身份）
- **下游依赖**: 到期结算核心模块（市场到期触发结算）
- **平行依赖**: 钱包与充值支付模块（资金划转）

- **话题与市场的关系**：
  - 一对一映射：一个 topic 创建一个 market，共享相同 UUID
  - topics 表侧重内容管理（标题、描述、分类、审核状态）
  - topic_markets 表侧重交易管理（资金池、流动性、交易状态）
  - 生命周期同步：
    - topic 创建 → market 初始化
    - topic 审核通过 → market 开放交易
    - topic 到期 → market 停止交易，进入结算
```

---

### 2.2 修复 LMSR-03：统一交易接口路径

**位置**: 6.2 核心接口清单

**原接口路径**:
```
POST /api/v1/trading/{topic_id}/buy
POST /api/v1/trading/{topic_id}/sell
GET /api/v1/trading/{topic_id}/quote
```

**修复后接口路径**:
```
# 市场相关
GET    /api/v1/trading/markets              # 获取市场列表
GET    /api/v1/trading/markets/{id}         # 获取市场详情

# 交易相关
POST   /api/v1/trading/{market_id}/quote    # 获取交易报价（买入）
POST   /api/v1/trading/{market_id}/buy      # 执行买入
POST   /api/v1/trading/{market_id}/sell     # 执行卖出
GET    /api/v1/trading/{market_id}/positions # 获取用户持仓
```

---

### 2.3 修复 LMSR-04：补充 Saga 事务超时处理

**位置**: 四、业务流程与逻辑 - 新增 4.2.6 章节

**新增内容**:
```markdown
#### 4.2.6 Saga 事务处理

**交易 Saga 流程**：
1. 验证用户余额和持仓（< 100ms）
2. 预扣款/预冻结持仓（< 100ms）
3. 执行 LMSR 交易计算（< 50ms）
4. 更新持仓记录（< 100ms）
5. 确认扣款/释放冻结（< 100ms）
6. 记录交易流水（< 50ms）

**Saga 状态存储**：
- 表名：`saga_transactions`
- 字段定义：
  - saga_id (UUID): Saga 事务 ID
  - saga_type (VARCHAR): 类型（recharge/trade/settlement/exchange）
  - current_state (VARCHAR): 当前状态（pending/executing/completed/compensating/compensated）
  - current_step (INTEGER): 当前步骤索引
  - timeout_at (TIMESTAMP): 超时时间
  - compensation_log (JSONB): 补偿操作日志
  - business_data (JSONB): 业务数据

**超时处理**：
- 超时时间：5 分钟
- 触发机制：定时任务每分钟扫描超时未完成的 Saga
- 补偿操作：
  1. 撤销预扣款（调用 WalletService.rollback）
  2. 回滚持仓状态（恢复交易前快照）
  3. 更新 Saga 状态为 compensated
  4. 记录补偿日志

**补偿事务伪代码**：
```python
async def compensate_trade_saga(saga_id: UUID):
    saga = await get_saga(saga_id)
    if saga.current_state != 'executing':
        return

    # 执行补偿
    try:
        await WalletService.rollback(saga.business_data['pre_freeze_id'])
        await PositionService.rollback(saga.business_data['position_snapshot'])
        await update_saga_state(saga_id, 'compensated')
        logger.info(f"Trade saga {saga_id} compensated")
    except Exception as e:
        logger.error(f"Compensation failed for saga {saga_id}: {e}")
        # 升级告警，人工介入
```
```

---

### 2.4 修复 DATA-03：统一金额字段精度

**位置**: 6.1 核心数据实体 - 新增说明

**新增内容**:
```markdown
### 6.1.x 金额字段精度统一规范

所有金额和数值字段遵循以下精度规范：

| 字段类型 | 存储类型 | 存储值 | 实际值 | 转换公式 |
|---------|---------|--------|--------|----------|
| 余额 (balance) | BIGINT | 分 | VND | `actual = stored / 100` |
| 充值金额 (amount_vnd) | BIGINT | 分 | VND | `actual = stored / 100` |
| 知识币 (amount_tokens) | BIGINT | 个 | 知识币 | `actual = stored` (整数) |
| 份额 (shares) | BIGINT | 微份额 | 份额 | `actual = stored / 1,000,000` |
| 价格/概率 (price) | BIGINT | 微单位 | 概率 (0-1) | `actual = stored / 1,000,000` |

**示例**：
- 100,000 VND 存储为 `10000000` (分)
- 0.5 概率存储为 `500000` (微单位)
- 100.5 份额存储为 `100500000` (微份额)
```

---

## 3. 用户与权限体系模块 PRD 修复

### 3.1 修复 AUTH-03：添加刷新 Token 接口

**位置**: 6.2 核心接口清单 - 新增接口

**新增内容**:
```markdown
#### 6.2.6 刷新访问 Token
- **URL**: POST /api/v1/auth/refresh
- **认证**: 不需要 JWT Token（使用 Refresh Token）
- **入参**:
  ```json
  {
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
  }
  ```
- **出参**:
  ```json
  {
    "token": "new_jwt_token",
    "refresh_token": "new_refresh_token",
    "expires_in": 7200,
    "token_type": "Bearer"
  }
  ```
- **错误响应**:
  ```json
  {
    "error": {
      "code": "TOKEN_EXPIRED",
      "message": "Refresh Token 已过期，请重新登录"
    }
  }
  ```

**业务逻辑**：
1. 验证 Refresh Token 有效性
2. 检查关联的用户会话是否存在
3. 如果 Refresh Token 使用次数超过阈值（如使用 50 次），强制轮换
4. 生成新的 JWT Token 和 Refresh Token
5. 旧 Refresh Token 加入黑名单

---

#### 6.2.7 用户登出
- **URL**: POST /api/v1/auth/logout
- **认证**: 需要 JWT Token
- **入参**:
  ```json
  {
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
  }
  ```
- **出参**:
  ```json
  {
    "message": "登出成功"
  }
  ```

**业务逻辑**：
1. 将当前 JWT Token 加入黑名单（Redis，过期时间与 Token 有效期一致）
2. 删除 Refresh Token 关联的会话
3. 记录登出日志
```

---

### 3.2 修复 age 字段定义

**位置**: 6.1.1 用户表

**原定义**:
```markdown
| age | INT | 否 | 年龄（计算字段） |
```

**修复后**:
```markdown
| age | INTEGER | 否 | 年龄（数据库生成列，基于 birth_date 自动计算） |
```

**计算公式**:
```sql
age INTEGER GENERATED ALWAYS AS
    (EXTRACT(YEAR FROM AGE(CURRENT_DATE, birth_date))) STORED
```

---

## 4. 话题与市场管理模块 PRD 修复

### 4.1 修复 TOPIC-01：明确与 markets 关系

**位置**: 6.1.1 话题表

**原定义**:
```markdown
| id | UUID | 是 | 话题 ID |
```

**修复后**:
```markdown
| id | UUID | 是 | 话题 ID（与 topic_markets.topic_id 一对一映射，共享相同 UUID） |
```

**新增说明**:
```markdown
**Topic 与 Market 关系说明**：
- topics.id = topic_markets.topic_id
- topics 表存储内容相关字段（title, description, category）
- topic_markets 表存储交易相关字段（total_pool, liquidity, status）
- 一对一映射，生命周期同步
```

---

## 5. 到期结算核心模块 PRD 修复

### 5.1 修复 SETTLE-01：定义仲裁委员会角色

**位置**: 2.1 角色与权限

**原定义**:
```markdown
| 角色 | 权限边界 |
|------|----------|
| 普通用户 | 查看自己持仓的结算状态... |
| 审核人员 | 审核市场结果... |
| 管理员 | 强制结算... |
```

**修复后**:
```markdown
| 角色 | 权限边界 | 角色标识 |
|------|----------|----------|
| 普通用户 | 查看自己持仓的结算状态、提交争议申请 | user |
| 市场创建者 | 提交市场结果建议 | user (creator) |
| 审核人员 | 审核市场结果、处理一级争议 | auditor |
| 仲裁员 | 处理二级争议（MVP 阶段由高级审核人员兼任） | auditor (senior) |
| 管理员 | 强制结算、最终裁决 | admin |

**仲裁委员会说明（Phase2 实现）**：
- 组成：3 名高级审核人员（auditor 角色，信用分 > 90）
- 决策机制：2/3 多数同意
- MVP 简化方案：由 admin 角色直接处理争议
```

---

### 5.2 修复 SETTLE-02：简化 MVP 仲裁流程

**位置**: 4.2.6 争议处理 SOP

**原定义**:
```markdown
- **仲裁机制**：由 3 人仲裁委员会处理，需 2/3 同意才能改变结果
```

**修复后**:
```markdown
#### 4.2.6 争议处理 SOP（MVP 简化版）

- **争议提交**：用户可在结算完成后 7 天内提交争议
- **资金冻结**：争议提交后立即冻结相关用户在该市场的所有资金
- **仲裁机制**：
  - MVP 阶段：由管理员（admin 角色）处理
  - Phase2 规划：实现 3 人仲裁委员会机制，需 2/3 同意
- **处理 SLA**：争议必须在 48 小时内处理完成
- **解冻规则**：争议处理完成后立即解冻资金
```

---

## 6. 运营后台核心模块 PRD 修复

### 6.1 修复 ADMIN-02：明确 admins 与 users 关系

**位置**: 6.1.1 管理员表

**原定义**:
```markdown
#### 6.1.1 管理员表 (admins)
| 字段名 | 类型 | 必填 | 描述 |
|--------|------|------|------|
| id | UUID | 是 | 管理员 ID |
| username | VARCHAR(50) | 是 | 用户名 |
| ... |
```

**修复后**:
```markdown
#### 6.1.1 管理员角色说明

**说明**：管理员不是独立表，而是 users 表的特殊角色，通过 role 字段区分。

管理员角色列表：
| role 值 | 角色名称 | 说明 |
|---------|---------|------|
| super_admin | 超级管理员 | 全系统权限，包括权限分配 |
| admin | 管理员 | 用户管理、内容管理、基础配置 |
| operation | 运营人员 | 数据查询、报表导出、活动配置 |
| auditor | 审核人员 | 内容审核、违规处理 |
| finance | 财务人员 | 资金流水查询、对账报表 |

如需扩展管理员权限，使用 admin_profiles 表：

#### 6.1.1 管理员扩展表 (admin_profiles)
| 字段名 | 类型 | 必填 | 描述 |
|--------|------|------|------|
| id | UUID | 是 | 记录 ID |
| user_id | UUID | 是 | 用户 ID（外键，引用 users.id） |
| permissions | JSONB | 否 | 额外权限列表 |
| approved_by | UUID | 否 | 审批人 ID |
| created_at | TIMESTAMP | 是 | 创建时间 |
```

---

## 7. 跨模块统一规范（新增）

### 7.1 统一 API 接口前缀

所有模块接口统一使用以下格式：

```
/api/v1/{module}/{resource}
```

| 模块 | 接口前缀 |
|------|---------|
| 用户认证 | `/api/v1/auth/` |
| 用户信息 | `/api/v1/users/` |
| 钱包 | `/api/v1/wallet/` |
| 交易 | `/api/v1/trading/` |
| 话题 | `/api/v1/topics/` |
| 结算 | `/api/v1/settlements/` |
| 商城 | `/api/v1/products/` |
| 后台 | `/api/v1/admin/` |
| 风控 | `/api/v1/moderation/` |

### 7.2 统一金额精度

所有金额字段统一使用 BIGINT 存储：

| 字段 | 存储单位 | 示例（存储值 → 实际值） |
|------|---------|----------------------|
| balance | 分 | 10000000 → 100,000 VND |
| amount_vnd | 分 | 50000000 → 500,000 VND |
| shares | 微份额 | 1500000 → 1.5 份额 |
| price | 微单位 | 750000 → 0.75 概率 |

### 7.3 统一角色定义

所有模块统一使用 users.role 字段进行角色识别：

```sql
role ENUM (
    'user',          -- 普通用户
    'super_admin',   -- 超级管理员
    'admin',         -- 管理员
    'operation',     -- 运营人员
    'auditor',       -- 审核人员
    'finance'        -- 财务人员
)
```

---

## 8. 文档更新清单

| 文档名称 | 更新内容 | 版本 |
|---------|---------|------|
| 00_架构设计总览.md | 新建 | v1.0 |
| 用户与权限体系模块_PRD.md | 添加刷新 Token 接口，明确 age 字段 | v1.1 |
| 钱包与充值支付模块_PRD.md | 添加 idempotency_key，统一接口路径 | v1.1 |
| LMSR 交易引擎核心模块_PRD.md | 明确 topic 关系，统一接口，补充 Saga | v1.1 |
| 话题与市场管理模块_PRD.md | 明确与 markets 关系 | v1.1 |
| 到期结算核心模块_PRD.md | 定义仲裁角色，简化 MVP 流程 | v1.1 |
| 运营后台核心模块_PRD.md | 明确 admins 与 users 关系 | v1.1 |

---

## 9. 下一步行动

1. **开发团队**：根据更新后的 PRD 实现代码
2. **测试团队**：根据更新后的接口定义编写测试用例
3. **产品团队**：持续跟踪 PRD 执行情况，收集反馈

---

**补丁版本**: v1.1
**更新日期**: 2026-03-01
**审批状态**: 已批准
