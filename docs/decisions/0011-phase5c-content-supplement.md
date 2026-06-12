# ADR-0011: Phase 5C 内容补充

- **状态**: Accepted
- **日期**: 2026-06-09
- **关联**: docs/04-roadmap.md (Phase 5C)

## 背景

Phase 5A 完成了世界扩展（22 地点、21 实体、NPC 日程），Phase 5B 构建了经济系统初版（购买/雇佣），Phase 5B/C 引入了线索记录与压力钟机制。Phase 5C 的目标是在不改动任何代码逻辑的前提下，补充内容数据，让世界在法律、支线和商业三个维度更丰富。

## 决策

### 1. 新增法条文件

新增两类法条，对应明代社会的高频冲突场景：

**data/laws/05_household.yaml** — 户律·田宅/婚姻/继承（5 条）
- 典卖田宅（土地交易须经官印契）
- 盗卖田宅（盗卖他人田产）
- 男女婚姻（婚约/媒妁规定）
- 立嫡违法（继承顺序违规）
- 卑幼私擅用财（未成年/子弟擅自动用家财）

**data/laws/06_official_discipline.yaml** — 吏律·受赃/职制（5 条）
- 官员受财（受贿按赃论罪）
- 有事以财请求（行贿者同罪）
- 在官求索借贷财物（官员向民间强索财物）
- 漏泄军情大事（泄密）
- 擅离职役（官员擅离职守）

### 2. 新增支线素材

在 `yangzhou_districts.py` 的 `STORY_SEEDS.side_threads` 中补充 2 条支线：

- **court_yard_secret** — 府衙庭院：衙役私下议论状纸已被师爷压下
- **street_main_rumor** — 主街：路人传言漕帮新到避人耳目的一批货

补充后副线程总数从 10 → 12。

### 3. 补充商业细节

为 Phase 5A 扩展 NPC 补齐 `price_list` / `service_catalog`：

- 顾先生（teacher_gu）：批注经书/抄书/代写讼状/讲学
- 庙祝沈老（temple_keeper）：香烛/祈福/求签
- 乞丐老刘（beggar_liu）：打听消息（已在 Phase 2 创建，补全服务目录）

### 4. 覆盖测试

- `test_scenarios.py`: 新增 `test_phase5c_new_side_threads`、`test_phase5c_commercial_details_*` 三个测试
- `test_read.py`: `test_query_laws_covers_new_categories` 验证户律和吏律关键词搜索
- 法条总计数从 20 → 30

## 不包含

- ❌ 前端剧情面板（留待 Phase 6）
- ❌ 新工具
- ❌ 新实体/地点
- ❌ 代码逻辑改动

## 后果

### 正面

- ✓ 总法条数 30 条，覆盖刑事、夜禁、商业、战斗、户律、吏律六大类
- ✓ 支线素材从 10 → 12，接线更密集
- ✓ 所有有经济行为的 NPC 都配有物价/服务数据
- ✓ 所有改动均不涉及核心代码，维持低风险

### 负面

- ✗ 内容数据仍有继续补充的空间（可再增加更多商业法条细化条目）
  - **对策**: 视为持续可操作项，不受 Phase 边界约束