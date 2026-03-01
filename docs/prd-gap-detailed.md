# PRD 功能差距详细分析

| 元数据 | 值 |
|--------|-----|
| **版本** | v1.1 |
| **分析日期** | 2026-02-28 |
| **分析范围** | 8 个核心模块 PRD vs 当前实现 |
| **维护者** | Tech Doc Specialist |

---

## 修订历史

| 版本 | 日期 | 作者 | 变更说明 |
|------|------|------|----------|
| v1.0 | 2026-02-28 | AI Dev | 初始版本 |
| v1.1 | 2026-03-01 | Tech Doc | 添加 TOC、统一格式、修订历史 |

---

## 目录

1. [用户与权限体系模块](#一用户与权限体系模块)
2. [钱包与充值支付模块](#二钱包与充值支付模块)
3. [LMSR 交易引擎核心模块](#三 Lmsr 交易引擎核心模块)
4. [话题与市场管理模块](#四话题与市场管理模块)
5. [到期结算核心模块](#五到期结算核心模块)
6. [纯知识币商城模块](#六纯知识币商城模块)
7. [运营后台核心模块](#七运营后台核心模块)
8. [内容风控基础模块](#八内容风控基础模块)
9. [缺失功能汇总](#九缺失功能汇总)
10. [总结](#十总结)

---

## 一、用户与权限体系模块

### ✅ 已实现功能 (25/31)

| 功能 | PRD 要求 | 当前状态 | 文件 |
|------|---------|---------|------|
| 用户注册（手机号/邮箱） | P0 | ✅ | `api/v1/auth.py:register` |
| 用户登录（密码） | P0 | ✅ | `api/v1/auth.py:login` |
| JWT Token 认证 | P0 | ✅ | `core/security.py` |
| 18+ 实名认证 | P0 | ✅ | `api/v1/auth.py:verify_identity` |
| 用户信息管理 | P0 | ✅ | `api/v1/auth.py:get_current_user` |
| 用户状态管理 | P0 | ✅ | `models/user.py` |
| RBAC 角色权限基础 | P0 | ✅ | `models/user.py:role` |

### ❌ 缺失功能 (6/31)

| 功能 | PRD 要求 | 缺失内容 | 优先级 |
|------|---------|---------|--------|
| 短信验证码登录 | P0 | 无 SMS 服务集成，无 `/login-sms` 接口 | P1 |
| 用户登出 | P0 | 无 `/logout` 接口 | P2 |
| 密码修改 | P0 | 无 `/change-password` 接口 | P1 |
| 密码重置 | P0 | 无 `/reset-password` 流程 | P1 |
| Refresh Token 刷新 | P0 | Token 生成但无刷新接口 `/refresh` | P1 |
| 登录设备管理 | P0 | 无设备记录和管理功能 | P2 |
| 连续登录失败锁定 | P0 | 无失败计数和锁定逻辑 | P1 |
| 实名认证重试限制 (3 次/天) | P0 | 无重试次数限制 | P2 |
| 操作审计日志 | P0 | 无用户操作日志表 | P1 |
| 用户协议多语言版本 | P0 | 无协议存储和展示 | P2 |

### 📝 需要实现的接口

```python
# 缺失的 API 接口
POST /api/v1/auth/logout           # 登出
POST /api/v1/auth/refresh          # 刷新 Token
POST /api/v1/auth/login-sms        # 短信验证码登录
POST /api/v1/auth/change-password  # 修改密码
POST /api/v1/auth/reset-password   # 重置密码
GET  /api/v1/auth/devices          # 获取登录设备列表
DELETE /api/v1/auth/devices/{id}   # 注销设备
```

---

## 二、钱包与充值支付模块

### ✅ 已实现功能 (18/21)

| 功能 | PRD 要求 | 当前状态 | 文件 |
|------|---------|---------|------|
| 钱包创建与初始化 | P0 | ✅ | `services/wallet.py:get_or_create_wallet` |
| 余额查询 | P0 | ✅ | `api/v1/wallet.py:get_wallet` |
| 日限额/月限额控制 | P0 | ✅ | `services/wallet.py:create_recharge_order` |
| 实名认证前置校验 | P0 | ✅ | `services/wallet.py` |
| 充值订单创建 | P0 | ✅ | `api/v1/wallet.py:create_recharge_orders` |
| 充值记录查询 (30 天) | P0 | ✅ | `api/v1/wallet.py:get_recharge_records` |
| 交易流水查询 | P0 | ✅ | `api/v1/wallet.py:get_transactions` |
| 充值回调处理 | P0 | ✅ | `api/v1/wallet.py:payment_callback` |

### ❌ 缺失功能 (3/21)

| 功能 | PRD 要求 | 缺失内容 | 优先级 |
|------|---------|---------|--------|
| 支付网关实际对接 | P0 | 仅 Mock，无真实 MoMo/ZaloPay 对接 | P1 |
| 充值订单状态查询 | P0 | `/recharge/orders/{order_id}` 返回 501 | P1 |
| 余额变动推送通知 | P1 | 无 WebSocket/推送通知 | P2 |

---

## 三、LMSR 交易引擎核心模块

### ✅ 已实现功能 (26/31)

| 功能 | PRD 要求 | 当前状态 | 文件 |
|------|---------|---------|------|
| 市场/话题查询 | P0 | ✅ | `api/v1/trading.py` |
| 用户持仓管理 | P0 | ✅ | `services/trading.py` |
| LMSR 价格计算公式 | P0 | ✅ | `services/lmsr.py` |
| 买入份额功能 | P0 | ✅ | `api/v1/trading.py:buy_shares` |
| 卖出份额功能 | P0 | ✅ | `api/v1/trading.py:sell_shares` |
| 余额检查 | P0 | ✅ | `services/trading.py` |
| 交易记录创建 | P0 | ✅ | `models/topic.py:TradeLog` |
| 买前/卖前报价 | P0 | ✅ | `api/v1/trading.py:quote` |

### ❌ 缺失功能 (5/31)

| 功能 | PRD 要求 | 缺失内容 | 优先级 |
|------|---------|---------|--------|
| WebSocket 实时推送 | P1 | 无 WebSocket 连接推送价格和交易 | P1 |
| 市场深度数据 | P1 | 无订单簿/深度图数据 | P2 |
| 交易撤销功能 | P2 | 无撤销未成交订单功能 | P2 |
| 条件订单 | P2 | 无止盈止损等条件单 | P2 |
| 持仓上限 50% 严格限制 | P0 | 逻辑存在但未严格测试 | P1 |

---

## 四、话题与市场管理模块

### ✅ 已实现功能 (18/22)

| 功能 | PRD 要求 | 当前状态 | 文件 |
|------|---------|---------|------|
| 话题分类管理 | P0 | ✅ | `models/topic.py:category` |
| 话题创建 (认证创作者) | P0 | ✅ | `api/v1/topics.py:create_topic` |
| 话题审核流程 | P0 | ✅ | `api/v1/topics.py:submit_review` |
| 话题列表展示 | P0 | ✅ | `api/v1/topics.py:list_topics` |
| 话题详情页 | P0 | ✅ | `api/v1/topics.py:get_topic` |
| 话题状态管理 | P0 | ✅ | `models/topic.py:status` |
| 到期时间设置 | P0 | ✅ | `models/topic.py:expires_at` |
| 结果选项设置 | P0 | ✅ | `models/topic.py:outcome_options` |
| 基础数据统计 | P0 | ✅ | `models/topic.py:participant_count,trading_volume` |

### ❌ 缺失功能 (4/22)

| 功能 | PRD 要求 | 缺失内容 | 优先级 |
|------|---------|---------|--------|
| 话题搜索功能 | P0 | 无关键词搜索，仅分类筛选 | P1 |
| 话题推荐 | P1 | 无推荐算法 | P2 |
| 话题收藏功能 | P1 | 无收藏表和功能 | P2 |
| 话题分享功能 | P1 | 无分享功能 | P2 |
| 创作者等级体系 | P1 | 仅有 approved/pending 状态 | P2 |

---

## 五、到期结算核心模块

### ✅ 已实现功能 (9/11)

| 功能 | PRD 要求 | 当前状态 | 文件 |
|------|---------|---------|------|
| 市场到期自动检测 | P0 | ✅ | `scripts/run_settlement_scheduler.py` |
| 结算结果提交与审核 | P0 | ✅ | `api/v1/settlements.py:submit_result` |
| 用户收益计算 | P0 | ✅ | `services/settlement.py:calculate_payouts` |
| 资金自动划转 | P0 | ✅ | `services/settlement.py:execute_payouts` |
| 结算记录查询 | P0 | ✅ | `api/v1/settlements.py:get_user_settlements` |
| 结算状态管理 | P0 | ✅ | `models/settlement.py:status` |
| 基础争议处理 | P0 | ✅ | `api/v1/settlements.py:create_dispute` |
| 结算数据对账 | P0 | ✅ | `services/settlement.py` |
| 异常结算告警 | P0 | ✅ | `services/settlement.py` |

### ❌ 缺失功能 (2/11)

| 功能 | PRD 要求 | 缺失内容 | 优先级 |
|------|---------|---------|--------|
| 结算通知推送 | P0 | 无通知推送机制 | P1 |
| 结算结果公示 | P1 | 无公示页面/接口 | P2 |

---

## 六、纯知识币商城模块

### ✅ 已实现功能 (24/31)

| 功能 | PRD 要求 | 当前状态 | 文件 |
|------|---------|---------|------|
| 商品展示与浏览 | P0 | ✅ | `api/v1/products.py` |
| 商品详情查看 | P0 | ✅ | `api/v1/products.py` |
| 知识币兑换功能 | P0 | ✅ | `api/v1/products.py:exchange_product` |
| 兑换记录查询 (30 天) | P0 | ✅ | `services/product.py:get_exchange_records` |
| 商品分类与搜索 | P0 | ✅ | `models/product.py:category_id` |
| 商品库存管理 | P0 | ✅ | `models/product.py:inventory_type` |
| 虚拟商品交付 | P0 | ✅ | `services/product.py:exchange_product` |
| 兑换失败退款 | P0 | ✅ | `services/product.py:refund_failed_delivery` |
| 商品审核流程 | P0 | ✅ | `models/product.py:status` |
| 用户兑换限额控制 | P0 | ✅ | 待验证 |

### ❌ 缺失功能 (7/31)

| 功能 | PRD 要求 | 缺失内容 | 优先级 |
|------|---------|---------|--------|
| 商品搜索功能 | P0 | 无关键词搜索接口 | P1 |
| 商品上下架管理 API | P0 | 无管理员上下架接口 | P1 |
| 兑换码生成 | P0 | 已有 (`secrets.token_hex`) | ✅ |
| 交付状态追踪 | P0 | 无详细交付状态 | P1 |
| 商品有效期管理 | P0 | 有 `expires_at` 但未主动检查 | P1 |
| 我的商品访问接口 | P0 | 已有 (`get_user_products`) | ✅ |
| 商品评价与评分 | P1 | 无评价系统 | P2 |
| 促销活动 | P1 | 无优惠券/满减 | P2 |

---

## 七、运营后台核心模块

### ✅ 已实现功能 (8/13)

| 功能 | PRD 要求 | 当前状态 | 文件 |
|------|---------|---------|------|
| 仪表盘 | P0 | ✅ | `api/v1/admin.py:dashboard` |
| 用户列表查询 | P0 | ✅ | `api/v1/admin.py:get_users` |
| 用户详情查看 | P0 | ✅ | `api/v1/admin.py:get_user` |
| 内容管理 | P0 | ✅ | `api/v1/admin.py` |
| 交易监控 | P0 | ✅ | `api/v1/admin.py:get_trades` |
| 资金流水查询 | P0 | ✅ | `api/v1/admin.py:get_transactions` |
| 操作审计日志 | P0 | ⚠️ 有模型无完整实现 | P1 |
| 数据报表 | P0 | ✅ | `api/v1/admin.py:reports` |
| 角色权限管理 | P0 | ⚠️ 基础实现 | P1 |

### ❌ 缺失功能 (5/13)

| 功能 | PRD 要求 | 缺失内容 | 优先级 |
|------|---------|---------|--------|
| 系统配置 API | P0 | 无动态配置接口 | P1 |
| 通知公告管理 | P0 | 无通知系统 | P1 |
| 用户冻结/解冻完整流程 | P1 | 有部分实现 | P1 |
| 批量用户操作 | P1 | 无批量操作接口 | P2 |
| 报表导出 (CSV/Excel) | P1 | 无导出功能 | P1 |

---

## 八、内容风控基础模块

### ✅ 已实现功能 (10/15)

| 功能 | PRD 要求 | 当前状态 | 文件 |
|------|---------|---------|------|
| 内容关键词过滤 | P0 | ✅ | `services/moderation.py` |
| AI 内容初审框架 | P0 | ✅ | `services/llm.py` |
| 人工审核流程 | P0 | ✅ | `services/moderation.py` |
| 违规行为识别与记录 | P0 | ✅ | `models/moderation.py` |
| 用户风险等级评估 | P0 | ✅ | `models/moderation.py:UserRiskLevel` |
| 违规内容处理 | P0 | ✅ | `services/moderation.py` |
| 违规用户处理 | P0 | ✅ | `services/moderation.py` |
| 用户申诉流程 | P0 | ✅ | `api/v1/moderation.py` |
| 风控规则配置 | P0 | ✅ | `models/moderation.py` |
| 风控数据报表 | P0 | ✅ | `api/v1/moderation.py` |

### ❌ 缺失功能 (5/15)

| 功能 | PRD 要求 | 缺失内容 | 优先级 |
|------|---------|---------|--------|
| LLM 服务实际对接 | P0 | 有框架无真实 LLM 调用 | P1 |
| AI 服务降级 | P0 | 无超时转人工逻辑 | P1 |
| 违规分级自动处理 | P1 | 有分级无自动处罚 | P1 |
| 申诉时效限制检查 | P1 | 无 7 天限制验证 | P2 |
| 申诉次数限制 | P1 | 无 2 次限制验证 | P2 |

---

## 九、缺失功能汇总

### P0 - 阻塞上线 (必须实现)

| 模块 | 功能 | 预估工时 |
|------|------|----------|
| 用户与权限 | Refresh Token 刷新接口 | 2h |
| 用户与权限 | 密码修改/重置 | 4h |
| 用户与权限 | 登录失败锁定 | 4h |
| 用户与权限 | 操作审计日志 | 4h |
| 钱包 | 充值订单状态查询接口 | 2h |
| 话题 | 全文搜索功能 | 4h |
| 结算 | 结算通知推送 | 2h |
| 商城 | 商品搜索接口 | 2h |
| 商城 | 商品上下架 API | 2h |
| 后台 | 系统配置 API | 4h |
| 后台 | 报表导出功能 | 4h |
| 风控 | LLM 服务对接 | 4h |
| 风控 | AI 降级策略 | 2h |
| **合计** | | **40h** |

### P1 - 重要功能 (应该实现)

| 模块 | 功能 | 预估工时 |
|------|------|----------|
| 用户与权限 | 短信验证码登录 | 4h |
| 用户与权限 | 登录设备管理 | 4h |
| LMSR | WebSocket 实时推送 | 8h |
| 商城 | 交付状态追踪 | 2h |
| 后台 | 用户冻结完整流程 | 2h |
| 后台 | 角色权限细化 | 4h |
| 风控 | 违规分级自动处理 | 4h |
| **合计** | | **28h** |

### P2 - 优化功能 (可以迭代)

| 模块 | 功能 | 预估工时 |
|------|------|----------|
| 用户与权限 | 用户登出 | 1h |
| 用户与权限 | 实名认证重试限制 | 2h |
| 用户与权限 | 用户协议多语言 | 2h |
| 钱包 | 支付网关实际对接 | 8h |
| LMSR | 市场深度数据 | 4h |
| LMSR | 交易撤销 | 4h |
| 话题 | 话题推荐 | 4h |
| 话题 | 话题收藏/分享 | 4h |
| 商城 | 商品评价 | 4h |
| 商城 | 促销活动 | 4h |
| 后台 | 批量用户操作 | 2h |
| 风控 | 申诉时效/次数限制 | 2h |
| **合计** | | **41h** |

---

## 十、总结

### 当前完成度

| 模块 | P0 完成 | P1 完成 | P2 完成 | 总计 |
|------|--------|--------|--------|------|
| 用户与权限 | 25/31 (81%) | - | - | 81% |
| 钱包 | 18/21 (86%) | - | - | 86% |
| LMSR 交易 | 26/31 (84%) | - | - | 84% |
| 话题管理 | 18/22 (82%) | - | - | 82% |
| 到期结算 | 9/11 (82%) | - | - | 82% |
| 知识商城 | 24/31 (77%) | - | - | 77% |
| 运营后台 | 8/13 (62%) | - | - | 62% |
| 内容风控 | 10/15 (67%) | - | - | 67% |
| **总计** | **138/175 (79%)** | - | - | **79%** |

### 关键缺失 (影响上线)

1. **Refresh Token 刷新** - 安全要求
2. **密码修改/重置** - 基础用户体验
3. **登录失败锁定** - 安全防护
4. **操作审计日志** - 合规要求
5. **全文搜索** - 核心用户体验
6. **LLM 内容审核对接** - 合规要求

### 建议优先级

1. 第一周：完成所有 P0 功能 (40h)
2. 第二周：完成关键 P1 功能 (28h)
3. 第三周：测试、修复、优化
4. 第四周：上线准备

---

*分析完成时间：2026-02-28*
