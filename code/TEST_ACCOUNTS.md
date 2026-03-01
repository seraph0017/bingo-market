# 测试账号

## 前端测试账号（Mock）

由于后端数据库未运行，可以在前端本地存储中手动设置测试账号。

### 使用方法

1. 打开浏览器开发者工具（F12）
2. 进入 Application/存储 标签
3. 找到 Local Storage
4. 添加以下项：

```
token: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0LXVzZXItaWQiLCJleHAiOjk5OTk5OTk5OTl9.test
```

5. 刷新页面

---

## 后端测试账号（需要数据库运行）

当数据库运行后，执行以下命令创建测试账号：

```bash
cd /Users/xunan/.openclaw/projects/bingo-market/code/backend
/Users/xunan/miniconda3/envs/bingo/bin/python scripts/seed_data.py
```

### 测试账号列表

| 邮箱/手机 | 密码 | 角色 |
|----------|------|------|
| test@example.com | Test123456 | 普通用户 |
| admin@bingomarket.com | Admin123456 | 管理员 |
| 0901234567 | Phone123456 | 普通用户 |

---

## 手动创建测试账号

如果数据库已运行但种子脚本不可用，可以直接在数据库中插入：

```sql
INSERT INTO users (id, email, password_hash, full_name, status, role)
VALUES (
    'test-user-id',
    'test@example.com',
    '$2b$12$EixUWvLWjGzPZvPJQkTfLeKgCKqS5h.Z1xXvJzQK5vLxLxLxLxLxL',
    'Test User',
    'verified_18plus',
    'user'
);
```

密码 `Test123456` 的 bcrypt hash 需要重新生成。
