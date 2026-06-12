# 会话日志: Phase 36 — 宁波地域

## 目标

新增宁波地域（3 地点 + 3 NPC + 1 支线），集成到种子系统、GM 提示词和跨地域调查网络。

## 变更清单

### 场景 (ningbo.py)

- 新增 `seed_ningbo()` 函数，含 3 个地点、3 个 NPC、演化注册表、支线素材
- 杭州拱宸桥码头 → 宁波码头出口连接

### 后端 (server.py)

- 添加 `from mingrpg.scenarios.ningbo import seed_ningbo`
- 在 `seed_all()` 中调用 `seed_ningbo(world)`

### GM Agent (agent.py)

- 系统提示词【地域】章节添加宁波描述
- 系统提示词【宁波 NPC】章节添加范钦、陈把总、赵海商

### 跨地域主线 (phase23_main_story.py)

- `CROSS_REGION_THREAD.anchors` 添加宁波 3 NPC + 3 地点
- `INVESTIGATION_MILESTONES` 添加 `nb_sea_route`（海上暗线）
- `merchant_wu.network_regions` 扩展至含 `ningbo`
- 跨地域 hook 文案添加"宁波的出海"

### 测试 (test_scenarios.py)

- 24 个新增覆盖测试：地点创建、NPC 创建、属性、日程、传闻钩子、背包、可观察细节、标签、服务、价格表、出口连接、内部连通、演化注册表、支线创建、location story threads、去重幂等、dialogue_lines

### 文档

- ADR-0122
- 会话日志
- roadmap Phase 36
- .plan.md 更新
- README 更新

## 测试结果

待运行验证。
