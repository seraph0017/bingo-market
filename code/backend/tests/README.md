# Bingo Market 测试指南

## 测试目录结构

```
code/backend/tests/
├── test_health.py          # 健康检查测试
├── test_auth.py            # 用户认证模块测试 (TC-USER-001 ~ TC-USER-031)
├── test_wallet.py          # 钱包模块测试 (TC-WALLET-001 ~ TC-WALLET-021)
├── test_topics.py          # 话题管理模块测试 (TC-TOPIC-001 ~ TC-TOPIC-022)
├── test_trading.py         # LMSR 交易模块测试 (TC-LMSR-001 ~ TC-LMSR-031)
├── test_settlements.py     # 到期结算模块测试 (TC-SETTLE-001 ~ TC-SETTLE-032)
├── test_mall.py            # 知识币商城模块测试 (TC-MALL-001 ~ TC-MALL-031)
├── test_admin.py           # 运营后台模块测试 (TC-ADMIN-001 ~ TC-ADMIN-041)
└── test_moderation.py      # 内容风控模块测试 (TC-RISK-001 ~ TC-RISK-041)
```

## 运行测试

### 前提条件

1. Python 3.11+
2. PostgreSQL 数据库
3. 安装依赖：`pip install -r requirements.txt`

### 运行所有测试

```bash
cd code/backend
python3.11 -m pytest
```

### 运行特定模块测试

```bash
# 认证模块
python3.11 -m pytest tests/test_auth.py -v

# 钱包模块
python3.11 -m pytest tests/test_wallet.py -v

# 话题模块
python3.11 -m pytest tests/test_topics.py -v

# 交易模块
python3.11 -m pytest tests/test_trading.py -v

# 结算模块
python3.11 -m pytest tests/test_settlements.py -v

# 商城模块
python3.11 -m pytest tests/test_mall.py -v

# 管理后台模块
python3.11 -m pytest tests/test_admin.py -v

# 内容风控模块
python3.11 -m pytest tests/test_moderation.py -v
```

### 运行单个测试用例

```bash
python3.11 -m pytest tests/test_auth.py::TestUserRegistration::test_register_with_phone_success -v
```

### 生成测试覆盖率报告

```bash
python3.11 -m pytest --cov=app --cov-report=html
```

## 测试数据库配置

测试使用与开发环境相同的数据库配置。确保 `.env` 文件中配置了正确的数据库连接：

```env
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/bingo_market
```

## 测试数据清理

每次测试运行前后会自动：
- 创建临时表结构
- 测试完成后清理数据

## 手动测试脚本

### 生成测试用户 Token

```bash
cd code/backend/scripts
python3.11 generate_test_token.py
```

### 初始化测试数据

```bash
cd code/backend/scripts
python3.11 seed_data.py
```

## 测试用例覆盖范围

| 模块 | 测试文件 | 测试用例范围 | 状态 |
|------|----------|-------------|------|
| 用户与权限 | test_auth.py | TC-USER-001 ~ TC-USER-031 | ✅ |
| 钱包与充值 | test_wallet.py | TC-WALLET-001 ~ TC-WALLET-021 | ✅ |
| 话题管理 | test_topics.py | TC-TOPIC-001 ~ TC-TOPIC-022 | ✅ |
| LMSR 交易 | test_trading.py | TC-LMSR-001 ~ TC-LMSR-031 | ✅ |
| 到期结算 | test_settlements.py | TC-SETTLE-001 ~ TC-SETTLE-032 | ✅ |
| 知识币商城 | test_mall.py | TC-MALL-001 ~ TC-MALL-031 | ✅ |
| 运营后台 | test_admin.py | TC-ADMIN-001 ~ TC-ADMIN-041 | ✅ |
| 内容风控 | test_moderation.py | TC-RISK-001 ~ TC-RISK-041 | ✅ |

## 前端测试

前端测试用例请参考 [bingo-market-testcases.md](../../test/testcase/bingo-market-testcases.md)

### 手动测试检查清单

#### 用户与权限
- [ ] 用户注册流程（手机号/邮箱）
- [ ] 18+ 实名认证
- [ ] 用户登录（密码/短信验证码）
- [ ] Token 验证和刷新
- [ ] RBAC 权限控制

#### 钱包与充值
- [ ] 钱包余额显示和切换
- [ ] 日限额/月限额显示
- [ ] 充值流程（MoMo/ZaloPay）
- [ ] 充值记录查询
- [ ] 交易流水查询

#### 话题管理
- [ ] 话题浏览和筛选
- [ ] 话题搜索
- [ ] 话题详情展示
- [ ] 话题创建表单验证
- [ ] 创作者资质检查
- [ ] 管理员审核流程

#### LMSR 交易
- [ ] 市场价格查询
- [ ] 买入份额操作
- [ ] 卖出份额操作
- [ ] 持仓管理
- [ ] 交易记录查询

#### 到期结算
- [ ] 到期自动检测
- [ ] 结算结果提交
- [ ] 收益计算
- [ ] 争议处理

#### 知识币商城
- [ ] 商品浏览
- [ ] 商品兑换
- [ ] 库存管理
- [ ] 交付系统
- [ ] 兑换记录

#### 管理后台
- [ ] 仪表盘数据
- [ ] 用户管理
- [ ] 内容审核
- [ ] 数据报表
- [ ] 系统配置

#### 内容风控
- [ ] 敏感词过滤
- [ ] AI 内容审核
- [ ] 违规处理
- [ ] 用户申诉

## 性能测试

使用 `pytest-benchmark` 进行性能测试：

```bash
pip install pytest-benchmark
python3.11 -m pytest --benchmark-only
```

### 性能目标

| 接口类型 | P95 响应时间 | 并发 TPS |
|---------|------------|---------|
| 用户注册 | < 300ms | 100 |
| 用户登录 | < 200ms | 100 |
| 钱包查询 | < 100ms | 100 |
| 充值创建 | < 300ms | 100 |
| 市场列表 | < 200ms | 100 |
| 市场详情 | < 150ms | 100 |
| 交易执行 | < 300ms | 50 |

## 测试问题反馈

发现测试问题时，请提供：
1. 测试用例编号
2. 测试步骤
3. 预期结果 vs 实际结果
4. 错误日志

---

*最后更新：2026-02-28*
*测试文件总数：9*
*覆盖测试用例：130+*
