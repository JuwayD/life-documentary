# ADR-0107: Phase 21 — 新地域 (苏州)

## 状态

已接受

## 背沿

Phase 20 新增南京后，`.plan.md` 下一步第一个可选方向是"更多新地域"。苏州是明代江南经济文化重镇，丝绸之都，通过运河与扬州相连，是自然的下一个扩展目标。

## 决策

新增苏州区域，遵循 Phase 17 (瓜洲渡) / Phase 20 (南京) 的实现模式：

- **3 个地点**：阊门丝市、拙政园、枫桥
- **3 个 NPC**：钱掌柜（丝绸商人）、沈园丁（园丁）、冯船家（运河船夫）
- **1 条支线素材**：丝税暗流 — 连接扬州吴员外的商业网络
- **地理连接**：扬州 river_dock → 苏州 suzhou_canal_bridge（运河水路）
- **演化注册**：3 个 NPC 加入演化注册表
- **GM 提示词**：增加苏州地域描述和 3 个新 NPC

## 地理链路

```
扬州 river_dock ←→ 苏州 suzhou_canal_bridge
苏州 suzhou_canal_bridge → suzhou_silk_market → suzhou_garden

扬州 ferry_pier ←→ 瓜洲渡 guazhou_ferry ←→ 南京 nanjing_jubaomen
```

## NPC 设计

| NPC | ID | 职业 | 特点 | 服务 |
|-----|-----|------|------|------|
| 钱掌柜 | silk_merchant_qian | 丝绸商人 | 精明老练，商帮消息灵通 | 商路消息/引见商帮 |
| 沈园丁 | garden_keeper_shen | 园丁 | 忠厚寡言，知晓园中来客 | 无 |
| 冯船家 | canal_boatman_feng | 运河船夫 | 嘴碎心善，熟悉水路 | 搭船/暗舱 |

## 后果

- 测试新增 21 个用例，全量 591 通过
- 与扬州主线通过吴员外商业网络形成叙事联动
- 苏州支线"丝税暗流"可与南京"盐税调查"互为印证
