# 会话日志: 2026-06-08 Phase 2 — 内容深度

## 触发

按 roadmap 推进,补齐被 Phase 1 Web UI 搁置的内容深度:多场景、时辰、货币、商业法条。

## 决策

- **多场景组合方式**: 每个场景一个 seed 函数,通过 exits 字段连接,`seed_all()` 一次性加载。不引入场景管理器。
- **时间系统**: 新增 `day_index` 字段,tool 层自动追踪天数。时辰绕回时自动 +1。
- **金钱交易**: `transfer_money` 纯机械工具,不判断公平性(AI 判断)。
- **商业法条**: 纯 YAML 数据,query_laws 自动发现,无需代码改动。

详见 `docs/decisions/0006-phase2-content-depth.md`。

## 代码产出

### 工具层
- `tools/write.py`: 增强 `advance_time` (day 单位 + day_index 追踪),新增 `transfer_money`
- `tools/read.py`: 新增 `list_locations` 工具
- `llm/tools_registry.py`: 注册 `list_locations` 和 `transfer_money`
- `audit/logger.py`: `transfer_money` 加入 WRITE_TOOL_NAMES

### 场景数据
- `scenarios/yangzhou_market.py` — 街市(5 地点 + 5 NPC)
- `scenarios/yangzhou_inn.py` — 客栈(3 地点 + 3 NPC)
- `scenarios/yangzhou_court.py` — 更新 `street_main` 出口连接市场

### 法律数据
- `data/laws/03_commerce.yaml` — 5 条大明律·户律(牙行、把持行市、度量衡、匿税、高利贷)

### GM Agent
- `llm/agent.py`: SYSTEM_PROMPT 新增多场景、时间系统、金钱交易指引

### 前端
- `web/static/app.js`: 场景链面包屑 + 天数显示
- `web/static/style.css`: 场景链样式

### 入口
- `cli.py`: 调用 `seed_all` 加载全部 3 场景
- `web/server.py`: 新增 `seed_all` 函数,`create_app` 支持 `seed_func` 参数

## 测试

| 类型 | 数量 | 新增 |
|---|---|---|
| 单元测试 | 83 | +28 |
| Web 后端 (TestClient) | 7 | 0 |
| 浏览器 E2E (Playwright) | 7 | 0 |
| LLM 集成 (skip 默认) | 4 | 0 |

**97 + 4 = 101 个测试,全过。**

新增测试:
- `tests/core/test_world.py`: +1 (day_index 默认值)
- `tests/tools/test_write.py`: +14 (advance_time x6, transfer_money x8)
- `tests/tools/test_read.py`: +2 (list_locations x2)
- `tests/scenarios/test_scenarios.py`: +11 (市场/客栈/全场景连接)

## 踩坑

无重大踩坑。场景链面包屑的图遍历逻辑是唯一需要稍加注意的地方——场景图不是线性链,但通过从当前位置往两边 BFS 遍历,可以生成一条合理的路径指示。

## 下一步

Phase 3 候选:
- 战斗与检定系统(回合制战斗框架)
- WebSocket 流式叙述
- PixiJS 等距瓦片渲染
