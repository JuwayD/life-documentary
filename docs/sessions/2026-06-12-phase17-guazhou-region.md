# 2026-06-12 Phase 17: 新地域 — 瓜洲渡

## 目标

从扬州城扩展到城外地域，新增瓜洲渡区域作为第一个可到达的新地点。

## 变更

### 新增文件
- `src/mingrpg/scenarios/guazhou.py` — 瓜洲渡场景（3 地点 + 3 NPC + 1 支线）
- `docs/decisions/0103-phase17-guazhou-region.md` — 架构决策记录

### 修改文件
- `src/mingrpg/web/server.py` — 添加 seed_guazhou 导入与调用
- `src/mingrpg/cli.py` — 添加 seed_guazhou 导入与调用
- `tests/scenarios/test_scenarios.py` — 新增 22 个测试用例

## 新增内容

### 地点
- **瓜洲渡口** (`guazhou_ferry`) — 南岸渡口，老柳歪斜，石阶通向镇子
- **瓜洲镇街** (`guazhou_town`) — 青石板街沿江铺开，低矮瓦房
- **瓜洲客栈** (`guazhou_inn`) — 门面不大的客栈，褪色酒旗

### NPC
- **陈老渡** (`ferryman_chen`) — 摆渡三十年的渡夫，沉默寡言但观察力极强
- **郑书办** (`guazhou_clerk`) — 管渡口税簿的书办，谨慎但贪小便宜
- **李行客** (`traveler_li`) — 走南闯北的行商，消息灵通但真假参半

### 支线素材
- **夜渡暗货** — 陈老渡发现半夜有船从北岸过来在芦苇荡靠岸，可追查吴员外走私渠道

### 连接
- `ferry_pier` → `guazhou_ferry`（新增 south_guazhou 出口）
- `guazhou_ferry` → `guazhou_town` → `guazhou_inn`（内部连通）

## 测试结果

- 22 个新测试全部通过
- 总测试数：95 个场景测试全部通过
- 项目规模：38 NPC、25+ 地点

## 决策

- 选择瓜洲渡作为新地域：历史真实（明代扬州南岸真实渡口），与现有运河码头呼应
- 最小切片原则：3 地点 + 3 NPC + 1 支线，可独立验收
- 复用现有模式：不引入新架构，沿用场景文件 + seed 函数模式
- 故事联动：支线连接吴员外走私线，NPC 可作为新消息源
