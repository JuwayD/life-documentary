# 2026-06-11 Phase 11 世界内容深化

## 目标

补全世界内容缺口,让扬州城更真实、更完整。

## 完成内容

### 1. 修复语法错误
- `yangzhou_phase11.py` 第 33 行 schedule 字典闭合括号错误(`]` → `}`)

### 2. 补充法条覆盖 (4 组 8 条)
- `07_gambling.yaml`: 赌博罪 + 开场诱赌罪
- `08_poison.yaml`: 造畜蛊毒罪 + 贩卖毒药罪
- `09_trespass.yaml`: 擅入官署罪 + 夜入民宅罪
- `10_witness_tampering.yaml`: 教唆词讼罪 + 证人翻供罪

### 3. 添加主线反派实体 (2 NPC)
- 赵三(bully_zhao): 漕帮打手,状纸上控告的恶霸,attack=6,defense=12
- 吴员外(merchant_wu): 绸缎商人,幕后豪商,money=5000,持有私账簿

### 4. 添加女性 NPC (4 NPC)
- 柳姑娘(teahouse_singer): 茶楼歌伎,听过官场秘闻
- 宋婶(herb_woman): 药婆,懂草药偏方,消息灵通
- 周寡妇(temple_widow): 绣娘,丈夫死因蹊跷
- 阿杏(inn_maid): 客栈丫鬟,知晓住客行踪

### 5. 修复大牢连通性
- jail → north → court_yard
- court_yard → south_jail → jail

### 6. 新增支线素材 (4 条)
- 码头赌局(dock_gambling_den): 赵三 + 赌局 → 抓捕切入点
- 寡妇之冤(widow_husband_death): 周寡妇丈夫溺亡疑案
- 豪商暗账(merchant_ledger): 吴员外私账簿
- 歌伎知音(singer_secret): 柳姑娘听到的密谈

### 7. 演化注册
- 反派: every_2_turns
- 女性 NPC: every_5_turns

### 8. GM 系统提示词更新
- 法条关键词触发指引(赌博/毒药/擅入/教唆)
- 新增【关键NPC】段落

### 9. 测试
- 新增 18 个 Phase 11 测试用例
- 覆盖: 反派创建、女性 NPC 创建、战斗属性、记忆、日程、经济、服务、大牢连通、演化注册、支线挂载、rumor hooks、防重复、实体计数、库存

## 统计

- 世界实体: 21 → 27 (1 玩家 + 26 NPC)
- 法条类别: 6 → 10 组
- 支线素材: 12 → 16 条
- 测试用例: 399 → 417
- ADR: 100 → 101 (ADR-0100)

## ADR

- ADR-0100: Phase 11 世界内容深化
