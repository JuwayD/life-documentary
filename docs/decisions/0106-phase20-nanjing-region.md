# ADR-0106: Phase 20 — 新地域 (南京)

## 状态

已接受

## 背景

项目完成至 Phase 19（法律专家 Agent），.plan.md 列出三个可选方向：更多新地域、前端 replay 播放器、主线剧情推进。按"最靠前且可独立验收"原则，选择新地域作为下一个最小垂直切片。Phase 17 已实现瓜洲渡（扬州南岸），南京是明代南直隶，地理位置上通过瓜洲渡可达，是扩展世界的自然选择。

## 决策

新增 **南京** 区域，作为扬州/瓜洲渡之后的第二个新地域。

### 新增内容

#### 地点 (4)
| ID | 名称 | 类型 | 出口 |
|---|---|---|---|
| `nanjing_confucius` | 夫子庙贡院 | outdoor | south→nanjing_qinhuai, east→nanjing_jiming |
| `nanjing_qinhuai` | 秦淮河畔 | outdoor | north→nanjing_confucius, west→nanjing_jubaomen |
| `nanjing_jubaomen` | 聚宝门大街 | outdoor | east→nanjing_qinhuai, north_gate→guazhou_ferry |
| `nanjing_jiming` | 鸡鸣寺 | indoor_religious | west→nanjing_confucius |

#### NPC (4)
| ID | 名称 | 职业 | 特点 |
|---|---|---|---|
| `scholar_zhou` | 周举子 | 赴考举子 | 浙江来的举子，才华横溢但性格孤傲，对科场弊案深恶痛绝 |
| `qinhuai_madam` | 秦淮鸨母 | 画舫管事 | 月华舫管事，八面玲珑，消息灵通，暗中为达官显贵牵线搭桥 |
| `gate_officer_sun` | 孙守备 | 聚宝门守备 | 恪尽职守但贪财，对过往商旅雁过拔毛 |
| `monk_huiyuan` | 慧远禅师 | 鸡鸣寺住持 | 博学多才，与南京官场中人颇有往来 |

#### 支线素材
- **科场风云**：周举子说今科主考官与扬州某富商有旧，贡院里有人夹带小抄，扬州甚至有人卖考题
- **江南盐税**：秦淮鸨母说朝廷要查江南盐税，扬州盐商常来月华舫宴客，聚宝门守备说最近有批货没交税就过去了

#### 连接
- `guazhou_ferry` 新增出口 `north_nanjing` → `nanjing_jubaomen`
- `nanjing_jubaomen` 新增出口 `north_gate` → `guazhou_ferry`

### 设计原则
- 最小切片：4 地点 + 4 NPC + 2 支线，可独立验收
- 复用现有模式：场景文件结构、seed 函数、演化注册表、支线素材挂载
- 历史真实：南京是明代南直隶，夫子庙贡院是江南科举中心，秦淮河是繁华之地
- 故事联动：2 条支线均连接扬州主线（科场弊案/盐税走私），NPC 可作为新消息源
- 跨地域联动：通过瓜洲渡连接，玩家可从扬州经瓜洲渡到南京

## 后果

- 新增 `src/mingrpg/scenarios/nanjing.py` 场景文件
- 更新 `server.py` 和 `cli.py` 加载新场景
- 更新 GM Agent 系统提示词（南京地域 + 4 个新 NPC）
- 新增 21 个测试用例，覆盖地点/NPC/出口/支线/演化/幂等性
- 项目规模扩展至 42 NPC、29+ 地点、570 测试
