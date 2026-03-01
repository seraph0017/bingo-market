# Bingo Market - Claude Code 项目指南

**完整文档**: 参见 [docs/CLAUDE.md](./docs/CLAUDE.md)

---

## 快速开始

### 开发环境设置

**Conda Python**: `/Users/xunan/miniconda3/envs/bingo/bin/python`

```bash
# 启动 PostgreSQL
brew services start postgresql@16

# 启动 Redis
brew services start redis

# 启动后端
cd code/backend
/Users/xunan/miniconda3/envs/bingo/bin/python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 启动前端
cd code/frontend
npm run dev
```

---

## 项目结构

```
bingo-market/
├── docs/                       # 项目文档（完整文档在此）
│   ├── README.md               # 文档索引
│   ├── CLAUDE.md               # 完整项目指南
│   ├── PROJECT_STRUCTURE.md    # 目录结构
│   └── ...
├── code/
│   ├── backend/                # Python FastAPI 后端
│   └── frontend/               # Vue 3 前端
├── prd/                        # 产品需求文档
└── design/                     # UI/UX 设计文档
```

---

## 技术栈

| 层级 | 技术 |
|------|------|
| Backend | Python FastAPI |
| Frontend | Vue 3 (H5 移动优先) + Element Plus |
| Database | PostgreSQL 16 (with JSONB) |
| Cache | Redis 7 |

---

## 文档导航

- **完整项目指南**: [docs/CLAUDE.md](./docs/CLAUDE.md)
- **项目目录结构**: [docs/PROJECT_STRUCTURE.md](./docs/PROJECT_STRUCTURE.md)
- **文档索引**: [docs/README.md](./docs/README.md)
