# ADR-0103: Phase 17 — 新地域 (瓜洲渡)

## 状态

已接受

## 背景

项目完成至 Phase 16（多 Agent 协作），扬州城已有 34 个 NPC、22+ 地点。.plan.md 列出三个可选方向：新地域、前端 replay 播放器、更多专业 Agent。按"最靠前且可独立验收"原则，选择新地域作为下一个最小垂直切片。

## 决策

新增 **瓜洲渡** 区域，作为扬州城外第一个可到达的新地域。

### 新增内容

#### 地点 (3)
| ID | 名称 | 类型 | 出口 |
|---|---|---|---|
| `guazhou_ferry` | 瓜洲渡口 | outdoor | north→ferry_pier, south→guazhou_town |
| `guazhou_town` | 瓜洲镇街 | outdoor | north→guazhou_ferry, east→guazhou_inn |
| `guazhou_inn` | 瓜洲客栈 | indoor_commercial | west→guazhou_town |

#### NPC (3)
| ID | 名称 | 职业 | 特点 |
|---|---|---|---|
| `ferryman_chen` | 陈老渡 | 渡夫 | 沉默寡言，知晓夜间渡船动向，提供渡河服务 |
| `guazhou_clerk` | 郑书办 | 瓜洲镇书办 | 掌握渡口税簿，贪小便宜，可提供过境信息 |
| `traveler_li` | 李行客 | 行商 | 走南闯北，消息灵通但真假参半 |

#### 支线素材
- **夜渡暗货**：陈老渡发现半夜有船从北岸过来在芦苇荡靠岸接货，可追查吴员外走私渠道

#### 连接
- `ferry_pier` 新增出口 `south_guazhou` → `guazhou_ferry`
- 通过渡河服务（5 文钱）可往返两岸

### 设计原则
- 最小切片：3 地点 + 3 NPC + 1 支线，可独立验收
- 复用现有模式：场景文件结构、seed 函数、演化注册表、支线素材挂载
- 历史真实：瓜洲渡是明代扬州南岸真实渡口，与运河码头呼应
- 故事联动：支线连接吴员外走私线，NPC 可作为新消息源

## 后果

- 新增 `src/mingrpg/scenarios/guazhou.py` 场景文件
- 更新 `server.py` 和 `cli.py` 加载新场景
- 新增 22 个测试用例，覆盖地点/NPC/出口/支线/演化/幂等性
- 项目规模扩展至 38 NPC、25+ 地点
