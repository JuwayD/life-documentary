# 会话日志: 2026-06-09 Phase 5B — 经济系统小切片

## 触发

Phase 5A 世界扩展已完成,README 与 roadmap 指向下一步 Phase 5B:经济系统(物价、雇佣)与主线/涌现支线。

## 决策

- **先做经济小切片**:实现物价、购买、雇佣/服务购买,暂不做完整任务系统。
- **经济数据放实体属性**:`attributes.price_list` 和 `attributes.service_catalog`,不新增数据库表。
- **购买工具负责机械结算**:`purchase_item` 扣钱、给钱、转移库存、记录事件,不判断卖方是否愿卖。
- **雇佣工具记录轻量契约**:`hire_service` 转钱并写 `attributes.current_contract`,由 GM Agent 决定后续履约叙事。
- **继续保持 AI 主导**:代码不做砍价、供需、任务判断。

## 代码产出

### 工具

- `tools/write.py`
  - 新增 `purchase_item(world, buyer, seller, item_id, qty, unit_price_wen, reason)`。
  - 新增 `hire_service(world, payer, provider, service_id, price_wen, duration, reason)`。

### GM Agent 接入

- `llm/tools_registry.py`
  - 注册 `purchase_item` 与 `hire_service` 两个工具 schema。
- `llm/agent.py`
  - 更新系统提示词:购买物品用 `purchase_item`,雇佣/服务购买用 `hire_service`,纯赏钱/赔偿/贿赂用 `transfer_money`。

### 场景数据

- `scenarios/yangzhou_market.py`
  - 小吃摊、布匹摊、茶楼加入 `price_list` / `service_catalog`。
- `scenarios/yangzhou_inn.py`
  - 客栈掌柜加入通铺、客房、热饭服务目录。
- `scenarios/yangzhou_districts.py`
  - 医馆加入草药/问诊价格。
  - 渡船、码头加入摆渡、夜渡、雇脚夫服务。

### 测试

- `tests/tools/test_write.py`
  - 新增购买成功、显式价格、库存不足、缺价格测试。
  - 新增雇佣成功、显式价格、缺服务价格测试。
- `tests/scenarios/test_scenarios.py`
  - 固定首批商贩和服务 NPC 的经济数据契约。
- `tests/llm/test_agent_stream.py`
  - 固定 Phase 5B 工具已注册。

### 文档

- `docs/decisions/0009-phase5b-economy-services.md`:记录 Phase 5B 经济小切片架构决策。
- `README.md` / `docs/04-roadmap.md`:更新当前阶段和测试总览。

## 测试

```bash
.venv/bin/pytest tests/tools/test_write.py tests/scenarios/test_scenarios.py tests/llm/test_agent_stream.py
# 67 passed

.venv/bin/pytest
# 150 passed, 4 skipped
```

## 下一步

Phase 5B/C 可继续推进主线与涌现式支线素材结构:让 `rumor_hooks`、服务契约、近期事件组合成可追踪但不硬编码的剧情锚点。
