# ADR-0100: Phase 11 世界内容深化

## 状态

Accepted

## 背景

Phase 0-10 完成了从端到端闭环到世界演化的全部功能。世界规模为 20 NPC、22 地点、6 条法条类别。但存在以下内容缺口：

1. **主线反派缺失**：story_seeds 中引用的"恶霸"和"豪商"从未作为实体存在
2. **女性 NPC 缺失**：所有 NPC 均为男性，世界不够真实
3. **法条覆盖不足**：赌博、毒药、擅入、教唆伪证等常见情境无对应法条
4. **大牢连通性**：jail 地点无出口，玩家进入后无法离开
5. **支线素材不足**：现有 12 条支线需要与新 NPC 联动的新线索

## 决策

### 1. 添加主线反派实体

新增 2 个反派 NPC：

| ID | 姓名 | 身份 | 位置 | 特点 |
|---|---|---|---|---|
| `bully_zhao` | 赵三 | 漕帮打手 | river_dock | 状纸上控告的恶霸,替豪商跑腿,attack=6 |
| `merchant_wu` | 吴员外 | 绸缎商人 | warehouse | 幕后豪商,操控码头货价,持有私账簿,money=5000 |

两人均设置日程(schedule)和 rumor_hooks，与主线"状告漕帮恶霸"直接关联。

### 2. 添加女性 NPC

新增 4 个女性 NPC，分布在不同场景：

| ID | 姓名 | 身份 | 位置 | 信息价值 |
|---|---|---|---|---|
| `teahouse_singer` | 柳姑娘 | 茶楼歌伎 | teahouse | 听过官场密谈,潜在证人 |
| `herb_woman` | 宋婶 | 药婆 | clinic_front | 药材行情、码头伤患消息 |
| `temple_widow` | 周寡妇 | 绣娘 | temple_gate | 丈夫死因蹊跷(疑与赵三有关) |
| `inn_maid` | 阿杏 | 客栈丫鬟 | inn_hall | 知晓住客行踪、吴员外随从活动 |

### 3. 补充法条

新增 4 组法条 YAML 文件：

| 文件 | 类别 | 关键词 |
|---|---|---|
| `07_gambling.yaml` | 赌博 | 赌、骰子、牌九、赌坊、聚赌 |
| `08_poison.yaml` | 毒物 | 毒、蛊、砒霜、下毒、贩卖毒药 |
| `09_trespass.yaml` | 擅入 | 擅入、闯入、夜入民宅、翻墙 |
| `10_witness_tampering.yaml` | 诉讼 | 教唆、伪证、诬告、串供、翻供 |

### 4. 修复大牢连通性

- jail 新增出口 `north → court_yard`
- court_yard 新增出口 `south_jail → jail`

### 5. 新增支线素材

4 条新支线与新 NPC/地点联动：

| ID | 标题 | 关联 NPC | 关联地点 |
|---|---|---|---|
| `dock_gambling_den` | 码头赌局 | bully_zhao, dock_boss_qian | warehouse |
| `widow_husband_death` | 寡妇之冤 | temple_widow, beggar_liu | temple_gate |
| `merchant_ledger` | 豪商暗账 | merchant_wu, shiye | warehouse |
| `singer_secret` | 歌伎知音 | teahouse_singer, merchant_wu | teahouse |

### 6. 演化注册

新 NPC 全部加入演化注册表：
- 反派(bully_zhao, merchant_wu): `every_2_turns` — 需持续关注
- 其余女性 NPC: `every_5_turns` — 低频关注

### 7. GM 系统提示词更新

- 法条关键词触发指引扩展(赌博/毒药/擅入/教唆)
- 新增【关键NPC】段落,描述 6 个新 NPC 的身份与信息价值

## 后果

- 世界实体从 21 增加到 27 (1 玩家 + 26 NPC)
- 法条类别从 6 组扩展到 10 组
- 支线素材从 12 条增加到 16 条
- 大牢可正常出入
- 主线反派有了实体存在,玩家可直接互动
- 女性 NPC 分布在茶楼、药铺、庙宇、客栈,世界更真实
- 新支线与主线自然交织(赌局→赵三, 暗账→吴员外, 寡妇→赵三旧案, 歌伎→密谈证词)
