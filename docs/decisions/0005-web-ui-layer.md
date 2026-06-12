# ADR-0005: 加 Web UI 层 (FastAPI + Vanilla JS + Playwright)

- **状态**: Accepted
- **日期**: 2026-06-06
- **关联**: docs/04-roadmap.md (Phase 1 提前)

## 背景

CLI MVP 已跑通,但 UI 测试与玩家体验需要进一步推进。讨论中确认:
- Pygame 的 UI 自动化测试成本高(像素比对、事件模拟、跨平台一致性差)
- Web 在可测试性、可分享性、远程调试上是降维打击
- AI 友好性也更高:Playwright 可直接给 AI 截图

## 决策

**Phase 1 直接在 CLI 之外加 Web 层,不替换现有任何代码。**

### 架构
```
Browser (HTML+JS)
    ↕ WebSocket / HTTP
FastAPI 服务层 (薄包装)
    ↕
现有 mingrpg 模块 (零迁移)
```

### 选型
| 用途 | 选型 | 理由 |
|---|---|---|
| 后端框架 | FastAPI | 与现有 Python 代码无缝;Starlette TestClient 优秀 |
| 实时通信 | WebSocket | 后续支持流式生成、NPC 主动行动 |
| 前端框架 | Vanilla JS (Phase 1) | 不引入构建工具;Phase 2 渲染时再上 Svelte/PixiJS |
| 模板 | 单页静态 HTML | FastAPI StaticFiles 挂载即可 |
| 浏览器测试 | Playwright (Python) | 与 pytest 统一;支持截图回归 |
| 视觉回归 | Playwright `expect_screenshot` | 内置,免额外依赖 |

## 不引入

- ❌ React / Vue / Next.js — 过重
- ❌ npm / webpack — Phase 1 不需要构建
- ❌ Selenium — Playwright 在每个维度上都更优

## 后端 API 设计 (草案)

```
GET  /             静态 HTML 入口
GET  /api/state    获取当前世界状态快照
POST /api/turn     提交玩家输入,同步返回叙述
WS   /ws/game      未来:流式 token 推送 + 推送状态变更
GET  /api/audit    最近 N 条审计记录
```

## 测试策略

| 层 | 测试方法 |
|---|---|
| API 单元 | FastAPI TestClient + mock LLM |
| API 集成 | TestClient + 真实 World,但 mock GMAgent |
| E2E | Playwright 启动 uvicorn,真实浏览器,**默认 mock 服务端 LLM** |
| 视觉回归 | Playwright screenshot diff |
| Live | 加 `MINGRPG_RUN_LIVE=1` 跑端到端真 LLM |

## 后果

### 正面
- ✓ 浏览器原生工具(DevTools)即调试界面
- ✓ 测试可纳入 CI,无需 X server
- ✓ 开发过程可录屏分享(Playwright `--video`)
- ✓ 远程协作友好(部署一个 URL)
- ✓ 为 Phase 2 PixiJS 渲染铺路

### 负面
- ✗ 新增 2-3 个依赖 (fastapi/uvicorn/playwright)
  - **对策**: 都是行业标准,维护成本可控
- ✗ Session 管理增加少量状态
  - **对策**: Phase 1 用进程内单例 World,Phase 2+ 再考虑多用户

## 红线

Web 层只做"传输 + 渲染",不在前端做任何游戏决策:
- 前端不掷骰、不判定、不缓存状态
- 所有真理来源仍是后端的 World 数据库
- 这与 ADR-0001 一脉相承:**代码是手脚,AI 是大脑**,Web 只是"手脚的延伸"
