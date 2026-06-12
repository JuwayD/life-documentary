# 会话日志: 2026-06-09 Phase 5C — 内容补充

## 触发

README 与 roadmap 指向 Phase 5C:补充更多支线素材、法条/商业细节。此前已完成线索记录与压力钟工具,但法条覆盖、支线锚点和 NPC 商业接口仍有缺口。

## 决策

- **法条选择**:补充户律(田宅/婚姻/继承)和吏律(受赃/职制),覆盖游戏中最可能触发但尚无法条的场景 — 贿赂府衙、土地纠纷、婚姻冲突。
- **支线补充**:为 court_yard 和 street_main 两个尚无支线锚点的主要地点补充素材。
- **商业细节**:为所有有交互价值但缺经济接口的 NPC 补充 price_list/service_catalog。
- **不引入新工具/新实体**:纯内容数据,不改代码逻辑。

## 代码产出

### 法条

- `data/laws/05_household.yaml` — 户律 5 条(典卖田宅、盗卖田宅、男女婚姻、立嫡违法、卑幼私擅用财)
- `data/laws/06_official_discipline.yaml` — 吏律 5 条(官员受财、有事以财请求、在官求索借贷财物、漏泄军情大事、擅离职役)

### 支线素材

- `src/mingrpg/scenarios/yangzhou_districts.py`
  - 新增 `court_yard_secret` (府衙密议)
  - 新增 `street_main_rumor` (漕帮暗货)
  - 支线总数: 10 → 12

### 商业细节

- `src/mingrpg/scenarios/yangzhou_districts.py`
  - teacher_gu: price_list + service_catalog (代写讼状、讲学授课)
  - temple_keeper: price_list + service_catalog (祈福法事、求签问卦)
- `src/mingrpg/scenarios/yangzhou_market.py`
  - beggar_liu: service_catalog (打听街头消息)

### 测试

- `tests/tools/test_read.py`
  - `test_query_laws_loads_real_data` — 验证 30 条法条全部可加载
  - `test_query_laws_covers_new_categories` — 验证受赃/田宅/婚姻/漏泄关键词可匹配
- `tests/scenarios/test_scenarios.py`
  - `test_phase5c_new_side_threads` — 验证 2 条新支线已注册
  - `test_phase5c_commercial_details_teacher_gu` — 验证顾先生商业接口
  - `test_phase5c_commercial_details_temple_keeper` — 验证庙祝商业接口
  - `test_phase5c_commercial_details_beggar_liu` — 验证乞丐商业接口
  - 支线计数断言更新: 10 → 12

### 文档

- `docs/decisions/0011-phase5c-content-enrichment.md` — ADR

## 测试

```bash
.venv/bin/pytest
# 166 passed, 4 skipped (LLM integration)
```

## 下一步

Phase 6: 前端剧情面板,让玩家可视化查看 story_progress 和 pressure_clocks。
