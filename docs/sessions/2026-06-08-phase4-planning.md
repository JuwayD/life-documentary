# 会话日志: 2026-06-08 Phase 4 — 渲染层与流式叙述

## 触发

Phase 3 战斗与检定系统已交付(119 测试全过),按 roadmap 进入 Phase 4。

## 决策

- **渲染库选 PixiJS v8**:纯渲染、WebGL 加速。不选 Phaser(自带物理/状态机违反 ADR-0001)。
- **渲染层是 State Layer 的镜像**:前端通过 `/api/snapshot` 拉快照派生 PixiJS 场景图,前端不持有任何游戏状态。
- **等距瓦片 64×32 (diamond)**:Location 的 `size` 字段直接当瓦片网格,Entity 的 `pos` 直接当瓦片坐标。
- **流式叙述用 WebSocket**:新增 `/ws/turn`,REST 的 `/api/turn` 保留作为 CLI/E2E 同步入口。
- **战斗反馈最小化**:只做受击闪红 + 伤害飘字。
- **本阶段全用占位美术**:纯色 diamond 瓦片 + 圆形 sprite,美术留迭代。

详见 `docs/decisions/0008-phase4-rendering-layer.md`。

## 代码产出

### 后端
- `llm/agent.py`: 新增 `process_input_stream()` 生成器,为 WebSocket 提供流式事件(text/tool_call/tool_result/done/error)
- `web/server.py`: 新增 `/ws/turn` WebSocket 端点,接收 JSON `{input}` 逐 event 推送

### 前端
- `web/static/index.html`: 三栏布局 + PixiJS CDN + viewport 容器
- `web/static/app.js`: 完整重写
  - PixiJS v8 初始化 + 等距 diamond 瓦片渲染
  - 角色精灵(圆形 body + 方向指示 + 名字 + HP 条)
  - 相机跟随玩家
  - WebSocket 流式叙述(逐 token 追加,带 REST 回退)
  - 战斗反馈: flashEntity() + showFloatText()
  - 场景切换时重绘瓦片 + 重放精灵
- `web/static/style.css`: 新增 viewport/floating-text 样式,三栏 grid

### 测试
- `tests/llm/test_agent_stream.py`: 6 个流式 agent 测试
- `tests/web/test_server.py`: 2 个 WebSocket 测试
- `tests/web/test_e2e_browser.py`: FakeAgent 补 `process_input_stream` 方法

### 文档
- `docs/decisions/0008-phase4-rendering-layer.md` → Accepted
- `docs/04-roadmap.md`: Phase 4 标记完成

## 踩坑

- **FakeAgent 缺 process_input_stream**: E2E 测试的 FakeAgent 只有 process_input,前端改用 WebSocket 后报错。补了 process_input_stream 适配器。
- **PixiJS v8 API 差异**: v8 用 `app.init({...})` 异步初始化,不是构造函数参数;`graphics.fill({color})` 代替 `beginFill`/`endFill`;`Text` 的 `style.dropShadow` 代替 `dropShadow`。

## 测试

| 类型 | 新增 |
|---|---|
| 流式 agent | 6 |
| WebSocket | 2 |

**134 测试 (原 126 + 8 新增),全过。**

## 下一步

Phase 5: 世界扩展 — 多场景地图(20+ 地点)、NPC 日程系统、经济系统、简单主线 + 涌现式支线。
