# ADR-0009: Phase 5B 经济系统小切片

- **状态**: Accepted
- **日期**: 2026-06-09
- **关联**: docs/04-roadmap.md (Phase 5B)

## 背景

Phase 5A 已把扬州扩展到 20+ 地点,并加入 NPC 时辰日程与支线素材。下一步按 roadmap 推进 Phase 5B: 经济系统(物价、雇佣)与主线/涌现支线。

本阶段先做最小垂直切片:让现有商贩、客栈、医馆、码头服务能被 GM Agent 通过工具真实结算,而不是只在叙述里口头发生。

## 决策

### 1. 物价和服务仍是实体属性

不新增经济表。商贩在 `attributes.price_list` 记录库存物品单价,服务提供者在 `attributes.service_catalog` 记录服务价格。

示例:

```json
{
  "price_list": {"baozi": 4},
  "service_catalog": {
    "common_room": {"name": "通铺一晚", "price_wen": 10}
  }
}
```

这延续 Phase 5A 的数据风格:世界信息放 JSON,代码只读写,由 LLM 判断买不买、雇不雇、价格是否合理。

### 2. 新增 purchase_item 工具

`purchase_item(buyer, seller, item_id, qty, unit_price_wen, reason)` 做三件机械操作:

1. 检查买卖双方和卖方库存是否存在。
2. 使用 `unit_price_wen` 或卖方 `price_list[item_id]` 计算总价,调用 `transfer_money`。
3. 从卖方库存扣数量,给买方库存增加数量,并记录事件。

工具不判断交易公平性、是否该砍价、卖方是否愿卖;这些由 GM Agent 决定。

### 3. 新增 hire_service 工具

`hire_service(payer, provider, service_id, price_wen, duration, reason)` 做三件机械操作:

1. 检查付款方和服务提供者是否存在。
2. 使用 `price_wen` 或服务提供者 `service_catalog[service_id].price_wen`,调用 `transfer_money`。
3. 在服务提供者 `attributes.current_contract` 写入当前契约,并记录事件。

契约只是状态事实,不驱动自动任务逻辑。后续是否带路、摆渡、诊病,仍由 GM Agent 叙事和工具调用决定。

### 4. 首批经济内容

- 小吃摊:包子、葱油饼、卤肉。
- 布匹摊:棉布、素绢、云锦。
- 茶楼:茶叶、茶壶、茶座打听消息。
- 客栈:通铺、客房、热饭。
- 医馆:草药包、问诊开方。
- 码头/渡口:雇脚夫、摆渡、夜渡。

## 不引入

- ❌ 动态物价算法
- ❌ 供需/库存自动刷新
- ❌ 债务系统
- ❌ 自动任务状态机
- ❌ NPC 自动履约行为树
- ❌ 税收/行会模拟

## 后果

### 正面

- ✓ 玩家购买物品和雇佣服务会真实影响金钱与库存。
- ✓ 服务契约可被后续叙事读取,为支线提供轻量状态锚点。
- ✓ 仍遵守“代码是手脚,AI 是大脑”:代码只结算,不做剧情判断。
- ✓ 150 单元/E2E 测试通过,4 个 live LLM 集成按需跳过。

### 负面

- ✗ `purchase_item` 比 `transfer_money` 更像复合工具。
  - **对策**: 它仍只做机械结算,不判断交易意愿或剧情意义。
- ✗ `current_contract` 目前只能记录一个契约。
  - **对策**: 足够覆盖 Phase 5B 小切片;多契约可在后续改成列表。
