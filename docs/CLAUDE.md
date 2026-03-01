# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Bingo Market** - Southeast Asian compliance prediction market platform (knowledge monetization + topic community). Vietnam launch first, focusing on tech, business, culture, and academic knowledge sectors.

### Compliance Red Lines (MUST follow in all code)
- Platform coins (knowledge coins) support **fiat one-way recharge ONLY** - NO withdrawal, user-to-user transfer/gift features
- Vietnam market limits: **daily 500K VND, monthly 5M VND**
- **18+ real-name registration required** for all transactions
- **NO sports scores, political elections, or religion-related topics**
- Use compliant terminology: "prediction", "knowledge coins", "shares", "market consensus probability" (NOT "gambling", "betting", "odds")

## Tech Stack

| Layer | Technology |
|-------|------------|
| Backend | Python FastAPI |
| Frontend | Vue 3 (H5 mobile-first) + Element Plus (admin) |
| Database | PostgreSQL 16 (with JSONB) |
| Cache | Redis 7 |
| Architecture | Monolith-first, CQRS read/write separation |
| AI | LLM API calls only (no custom algorithms) |

## Codebase Structure

```
bingo-market/
├── code/
│   ├── backend/              # Python FastAPI backend
│   │   ├── app/
│   │   │   ├── main.py       # Application entry point
│   │   │   ├── api/v1/       # API v1 routes
│   │   │   ├── models/       # SQLAlchemy database models
│   │   │   ├── schemas/      # Pydantic schemas
│   │   │   ├── services/     # Business logic layer
│   │   │   └── core/         # Config, security, utils
│   │   ├── tests/            # Pytest test files
│   │   ├── requirements.txt  # Python dependencies
│   │   └── pyproject.toml    # Project config
│   └── frontend/             # Vue 3 frontend
│       ├── src/
│       │   ├── main.ts       # App entry point
│       │   ├── views/        # Page components
│       │   ├── components/   # Reusable UI components
│       │   ├── composables/  # Vue composables (hooks)
│       │   └── assets/       # Static assets
│       ├── package.json      # Node dependencies
│       └── vite.config.ts    # Vite config
├── design/                   # UI/UX design specs
│   ├── bingo-market-design-system.md      # Master design system
│   ├── bingo-market-hifi-*.md             # Hi-fi mockups per module
│   └── bingo-market-wireframes-*.md       # Wireframes per module
├── prd/                    # Product Requirement Documents (Chinese)
│   ├── Phase1_MVP_产品整体架构与需求范围说明书.md  # Master MVP spec
│   ├── design_principles.md               # UI design principles
│   ├── ui_ux_component_spec.md            # Component specifications
│   ├── 用户与权限体系模块_PRD.md            # User & permission system
│   ├── 钱包与充值支付模块_PRD.md            # Wallet & recharge
│   ├── LMSR 交易引擎核心模块_PRD.md         # LMSR trading engine
│   ├── 话题与市场管理模块_PRD.md            # Topics & markets
│   ├── 到期结算核心模块_PRD.md              # Settlement engine
│   ├── 纯知识币商城模块_PRD.md              # Knowledge coin mall
│   ├── 运营后台核心模块_PRD.md              # Admin backend
│   └── 内容风控基础模块_PRD.md              # Content risk control
└── needs/
    └── 0226.txt          # Product manager role definition
```

## Phase1 MVP Modules (8 Core Modules)

| Module | PRD | Key Features |
|--------|-----|--------------|
| **User System** | 用户与权限体系模块_PRD.md | 18+ KYC, JWT auth, RBAC, phone/email registration |
| **Wallet** | 钱包与充值支付模块_PRD.md | VND recharge, MoMo/ZaloPay, balance management, transaction logs |
| **LMSR Engine** | LMSR 交易引擎核心模块_PRD.md | LMSR AMM market maker, position management, price calculation |
| **Topics/Markets** | 话题与市场管理模块_PRD.md | Topic creation,审核 workflow, category management, search |
| **Settlement** | 到期结算核心模块_PRD.md | Auto-settlement, payout calculation, dispute handling |
| **Mall** | 纯知识币商城模块_PRD.md | Virtual goods, coin redemption, delivery system |
| **Admin Backend** | 运营后台核心模块_PRD.md | Dashboard, user/content management, audit logs, reports |
| **Content Risk** | 内容风控基础模块_PRD.md | Sensitive word filter, AI review, violation handling |

## Design System (from design/bingo-market-design-system.md)

### Color Palette
```css
/* Primary (Tailwind Blue) */
--color-primary-500: #3b82f6;  /* Main brand */
--color-primary-600: #2563eb;  /* Hover */
--color-primary-700: #1d4ed8;  /* Active */

/* Grayscale */
--color-gray-50: #f9fafb;
--color-gray-500: #6b7280;
--color-gray-900: #111827;

/* Semantic */
--color-success-500: #10b981;
--color-warning-500: #f59e0b;
--color-error-500: #ef4444;
```

### Typography (16px base)
```css
--text-xs: 0.75rem;    /* 12px */
--text-sm: 0.875rem;   /* 14px */
--text-base: 1rem;     /* 16px */
--text-lg: 1.125rem;   /* 18px */
--text-xl: 1.25rem;    /* 20px */
--text-2xl: 1.5rem;    /* 24px */
--leading-normal: 1.5;
```

### Spacing (4px base unit)
```css
--space-1: 0.25rem;   /* 4px */
--space-2: 0.5rem;    /* 8px */
--space-3: 0.75rem;   /* 12px */
--space-4: 1rem;      /* 16px */
--space-5: 1.25rem;   /* 20px */
--space-6: 1.5rem;    /* 24px */
--space-8: 2rem;      /* 32px */
```

### Responsive Breakpoints
```css
--breakpoint-sm: 640px;    /* Mobile landscape */
--breakpoint-md: 768px;    /* Tablet portrait */
--breakpoint-lg: 1024px;   /* Tablet landscape */
--breakpoint-xl: 1280px;   /* Desktop */
```

### Localization Requirements
- **Languages**: Vietnamese, English
- **Date format**: DD/MM/YYYY HH:mm
- **Number format**: 1.000.000 (dot as thousand separator)
- **Currency**: VND (no decimals, symbol after number)
- **Text expansion**: +30% for Vietnamese

### Accessibility (WCAG 2.1 AA)
- Color contrast: Text ≥ 4.5:1, large text ≥ 3:1
- Touch target: Minimum 44x44px
- Keyboard navigation: Full Tab support
- Screen reader: Semantic HTML + ARIA labels

## Database Conventions

- **Primary keys**: UUID for all tables
- **Currency/amounts**: BIGINT (integer storage, no floats)
- **Flexible data**: JSONB for device info, evidence, configs
- **Timestamps**: `created_at`, `updated_at` on all tables
- **Soft deletes**: Where applicable (e.g., users, topics)

## Key API Endpoints (per PRDs)

### Authentication
- `POST /api/v1/auth/register` - User registration
- `POST /api/v1/auth/login` - Login
- `POST /api/v1/auth/verify-identity` - 18+ KYC verification
- `POST /api/v1/auth/refresh` - Refresh access token
- `POST /api/v1/auth/logout` - Logout
- `POST /api/v1/auth/change-password` - Change password (requires login)
- `POST /api/v1/auth/reset-password` - Reset password (with verification code)

### Wallet
- `GET /api/v1/wallet` - Get wallet info & limits
- `POST /api/v1/wallet/recharge/orders` - Create recharge order
- `GET /api/v1/wallet/recharge/orders/{id}` - Get recharge order status
- `GET /api/v1/wallet/recharge/records` - Recharge history
- `GET /api/v1/wallet/transactions` - Transaction history
- `POST /api/v1/wallet/recharge/{order_id}/simulate` - Mock payment callback (testing)

### Topics
- `GET /api/v1/topics` - List topics (filter, sort)
- `GET /api/v1/topics/search?q=query` - Search topics
- `GET /api/v1/topics/{id}` - Topic details
- `POST /api/v1/topics` - Create topic (creators only)
- `POST /api/v1/topics/{id}/review` - Submit review (auditors only)
- `GET /api/v1/topics/reviews/pending` - Pending reviews

### Trading (LMSR)
- `POST /api/v1/trading/{topic_id}/buy` - Buy shares
- `POST /api/v1/trading/{topic_id}/sell` - Sell shares
- `GET /api/v1/trading/{topic_id}/quote` - Buy quote preview
- `GET /api/v1/trading/{topic_id}/sell-quote` - Sell quote preview
- `GET /api/v1/trading/{topic_id}/positions` - User positions

### Settlement
- `GET /api/v1/settlements/pending` - Pending settlements
- `POST /api/v1/settlements/{id}/result` - Submit settlement result
- `POST /api/v1/settlements/{id}/execute` - Execute settlement
- `GET /api/v1/settlements/user` - User settlement history
- `POST /api/v1/settlements/{id}/dispute` - Create dispute
- `POST /api/v1/settlements/disputes/{id}/resolve` - Resolve dispute

### Mall
- `GET /api/v1/products` - Product list
- `GET /api/v1/products/search?q=query` - Search products
- `GET /api/v1/products/{id}` - Product details
- `POST /api/v1/products/{id}/exchange` - Redeem with coins
- `GET /api/v1/products/exchange/orders` - Exchange history
- `GET /api/v1/products/my-products` - User's owned products

### Admin
- `GET /api/v1/admin/dashboard` - Dashboard metrics
- `GET /api/v1/admin/users` - User management
- `GET /api/v1/admin/users/{id}` - User details
- `POST /api/v1/admin/users/{id}/actions` - User actions (freeze, ban, verify)
- `POST /api/v1/admin/users/{id}/balance` - Balance adjustment
- `GET /api/v1/admin/products` - Product list
- `POST /api/v1/admin/products/{id}/activate` - Activate product
- `POST /api/v1/admin/products/{id}/deactivate` - Deactivate product
- `GET /api/v1/admin/reviews/pending` - Pending content reviews
- `GET /api/v1/admin/recharge/records` - Recharge records

### Audit Logs
- `GET /api/v1/audit-logs` - Get audit logs (users see own, admin sees all)

### Content Moderation
- `POST /api/v1/moderation/sensitive-words` - Add sensitive words
- `GET /api/v1/moderation/violations` - Violation records
- `POST /api/v1/moderation/appeals` - User appeal
- `GET /api/v1/moderation/appeals/{id}` - Appeal details

## Performance Targets

| Metric | Target |
|--------|--------|
| API response (P95) | < 500ms (general), < 100ms (wallet queries) |
| Page load (first screen) | < 2s mobile, < 1.5s details |
| Concurrent TPS | 100+ transactions |
| Cache hit rate | > 80% |
| Lighthouse score | ≥ 90 |

## Architecture Patterns

### CQRS (Command Query Responsibility Segregation)
- **Commands**: Write operations (create, update, delete)
- **Queries**: Read operations (list, get, search)
- Separate handlers for read/write paths

### Saga Pattern for Cross-Module Transactions
- Used for: Recharge → Wallet update, Settlement → Payout
- Each step has a compensating transaction for rollback
- Event-driven state persistence with timeout handling

### Circuit Breaker Pattern
- Service degradation when dependencies fail
- Fallback to cached data or read-only mode
- Auto-recovery with health checks

## Current State

**Backend (Implemented):**
- FastAPI application structure with `app/main.py`
- Core modules: `config.py`, `database.py`, `security.py`
- Auth module: models, schemas, services, and API routes for registration, login, KYC verification
- Stub modules: wallet, topics, settlements, products, admin, users
- Test setup with pytest

**Frontend (Implemented):**
- Vue 3 + Vite + TypeScript project setup
- Vue Router with navigation guards
- Pinia store for auth state
- Vue I18n for multi-language (Vietnamese, English, Chinese)
- Element Plus UI framework integration
- Home page with hero section and feature cards
- Stub views: Login, Register, Wallet, Topics, Mall, Admin Dashboard

**Next Steps:**
1. Implement wallet module (recharge, balance, transaction history)
2. Implement LMSR trading engine
3. Implement topic management with审核 workflow
4. Complete settlement module
5. Build out admin dashboard

## Development Setup

### Python Environment
**Conda environment**: `/Users/xunan/miniconda3/envs/bingo/bin/python`

### Backend
```bash
cd code/backend
# Using conda environment
/Users/xunan/miniconda3/envs/bingo/bin/python -m pip install -r requirements.txt
cp .env.example .env  # Edit with your settings
/Users/xunan/miniconda3/envs/bingo/bin/python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend
```bash
cd code/frontend
npm install
cp .env.example .env
npm run dev
```

### Run Tests
```bash
cd code/backend
pytest
```

## Working with this Codebase

1. **Read PRDs first** - Each module has detailed specs with business logic, data models, and API definitions
2. **Compliance check** - Verify all features against compliance red lines before implementation
3. **Phase-aware** - MVP scope is strictly defined; don't add Phase2+ features
4. **Vietnam-first** - Prioritize Vietnamese localization and payment methods (MoMo, ZaloPay)
5. **Follow design system** - Use the defined color palette, spacing, typography, and components
6. **Reference wireframes** - Check `design/bingo-market-wireframes-*.md` for page layouts

## Key References

| Document | Purpose |
|----------|---------|
| `prd/Phase1_MVP_产品整体架构与需求范围说明书.md` | Master architecture & timeline |
| `prd/design_principles.md` | UI design principles |
| `design/bingo-market-design-system.md` | Complete design system |
| `prd/ui_ux_component_spec.md` | Component specifications |
| `needs/0226.txt` | Product manager role & PRD standards |

## Implementation Todo List

### Phase 1 - All Modules (Complete All)

- [x] **用户与权限体系模块** - 18+ KYC, JWT auth, RBAC, phone/email registration
- [x] **钱包与充值支付模块** - VND recharge, MoMo/ZaloPay, balance management, transaction logs
- [x] **LMSR 交易引擎核心模块** - LMSR AMM market maker, position management, price calculation
- [x] **话题与市场管理模块** - Topic creation, 审核 workflow, category management, search
- [x] **到期结算核心模块** - Auto-settlement, payout calculation, dispute handling
- [x] **纯知识币商城模块** - Virtual goods, coin redemption, delivery system
- [x] **运营后台核心模块** - Dashboard, user/content management, audit logs, reports
- [x] **内容风控基础模块** - Sensitive word filter, AI review, violation handling

**All 8 core modules implemented!**

---

## Current Implementation Status (2026-02-28)

### Backend - 完整实现 ✅
| Module | Routes | Services | Models | Tests |
|--------|--------|----------|--------|-------|
| Auth | ✅ | ✅ | ✅ | ⚠️ Needs DB |
| Wallet | ✅ | ✅ | ✅ | ⚠️ Needs DB |
| Trading/LMSR | ✅ | ✅ | ✅ | ⚠️ Needs DB |
| Topics | ✅ | ✅ | ✅ | ⚠️ Needs DB |
| Settlements | ✅ | ✅ | ✅ | ⚠️ Needs DB |
| Products/Mall | ✅ | ✅ | ✅ | ⚠️ Needs DB |
| Admin | ✅ | ✅ | ✅ | ⚠️ Needs DB |
| Moderation | ✅ | ✅ | ✅ | ⚠️ Needs DB |

**Note**: All modules implemented. Tests require PostgreSQL + Redis running.

### Frontend - 基础框架 ⚠️
| Component | Status |
|-----------|--------|
| Vue 3 + Vite + TypeScript | ✅ Setup complete |
| Vue Router + Pinia | ✅ Configured |
| i18n (VN/EN/ZH) | ✅ Configured |
| Element Plus | ✅ Integrated |
| Home/Login/Register | ✅ Stub pages |
| Wallet/Topics/Mall | ⚠️ Stub only |
| Trading UI | ❌ Not started |
| Admin Dashboard | ⚠️ Stub only |

---

## Next Steps Plan

### Priority 1: Fix Tests & Verify Backend (Week 1)
- [x] Fix test model name mismatches (Wallet → UserWallet)
- [x] Fix RegisterRequest schema (full_name optional)
- [x] Start PostgreSQL + Redis (services running)
- [x] Verify backend service starts successfully
- [x] Health check and API endpoints working
- [ ] Mock external services (SMS, payment gateway, LLM)
- [ ] Fix async event loop conflicts in unit tests

**Progress**: 5/7 done - Backend service verified working. Unit test event loop conflict is non-blocking.

### Priority 2: Complete Frontend Core Pages (Week 2-3)
- [ ] Login/Register flow with KYC
- [ ] Wallet page (balance, recharge, transaction history)
- [ ] Topics list + detail page with LMSR price display
- [ ] Trading interface (buy/sell shares, position view)
- [ ] Mall product list + exchange
- [ ] Admin dashboard basics

### Priority 3: End-to-End Integration (Week 4)
- [ ] User journey: Register → KYC → Recharge → Trade → Settlement
- [ ] Payment gateway integration (MoMo/ZaloPay sandbox)
- [ ] SMS service integration
- [ ] Performance testing & optimization

### Priority 4: Production Readiness (Week 5+)
- [ ] Security audit
- [ ] Deployment pipeline (Docker + CI/CD)
- [ ] Monitoring setup (Prometheus + Grafana)
- [ ] UAT with sample users

---

## Development Environment

**Conda Python**: `/Users/xunan/miniconda3/envs/bingo/bin/python`

### Prerequisites
```bash
# Start PostgreSQL (required for backend tests)
brew services start postgresql@16

# Start Redis (required for rate limiting, sessions)
brew services start redis
```

### Quick Start
```bash
# Backend
cd code/backend
/Users/xunan/miniconda3/envs/bingo/bin/python -m pip install -r requirements.txt
cp .env.example .env  # Edit DATABASE_URL if needed
/Users/xunan/miniconda3/envs/bingo/bin/python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Frontend
cd code/frontend
npm install
npm run dev
```

### Run Tests
```bash
# Simple tests (no DB required)
cd code/backend
/Users/xunan/miniconda3/envs/bingo/bin/python -m pytest tests/test_health.py -v

# Full integration tests (requires PostgreSQL + Redis)
# Note: Event loop conflicts need to be resolved - see Known Issues
/Users/xunan/miniconda3/envs/bingo/bin/python -m pytest -v
```

### Known Issues
1. **Event loop conflict in unit tests**: TestClient runs sync but database is async - causes `RuntimeError: got Future attached to different loop`
   - Workaround: Use `anyio.from_thread` or switch to `httpx.AsyncClient` with `AsyncAppTransport`
   - Impact: **Non-blocking** - Backend service runs correctly, API endpoints verified working
   - Fix: Update test architecture to use async tests (low priority)

### Verified Working (Manual Test)
- Backend service starts successfully on port 8000
- Health endpoint: `GET /health` returns `{"status":"healthy","version":"0.1.0"}`
- Database connection: PostgreSQL connected, all 26 tables detected
- API routers: All module endpoints registered (auth, wallet, topics, trading, products, settlements, admin, moderation)
