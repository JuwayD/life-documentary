# ADR-0101: 法条语义检索 (TF-IDF + jieba)

## 状态

已接受

## 背景

`query_laws` 工具原有实现基于关键词子串匹配(+2 关键词命中/+1 文本子串),存在以下问题:

1. **无语义理解**: "伤人" 无法匹配 "持械伤人"(除非关键词列表显式包含)
2. **依赖 GM Agent 选词**: Agent 必须自行提取关键词,选词偏差直接导致漏检
3. **无权重区分**: 所有关键词等权,无法区分罕见词(如 "绞监候")与常见词(如 "打")

项目在 `docs/02-architecture.md` 中已预留向量检索升级路径:`法条/民俗 RAG 索引 (FAISS or naïve)`。

## 决策

采用 **TF-IDF + 余弦相似度** 方案,使用 jieba 中文分词 + numpy 实现:

- **不引入外部向量数据库**(FAISS/ChromaDB): 法条仅 ~38 条,内存计算 < 1ms
- **不引入 OpenAI/sentence-transformers embedding**: 增加外部依赖和 API 成本,对小语料收益有限
- **jieba 分词 + 字符 unigram**: 解决 jieba 分词粒度不一致导致的漏配(如 "偷窃" vs "窃盗" 通过共享字符 "窃" 匹配)
- **保留关键词模式**: 向后兼容现有调用,`keywords` 参数继续工作

### 检索模式

| 参数 | 行为 |
|------|------|
| `keywords` only | 经典关键词子串匹配 (原有行为) |
| `query` only | TF-IDF 语义检索 |
| both | 混合模式,向量分数 ×3 + 关键词分数 |

### 分词策略

```
jieba 分词 + CJK 字符 unigram
"偷窃财物" → ["偷窃", "财物", "偷", "窃", "财", "物"]
"窃盗已行" → ["窃盗", "已行", "窃", "盗", "已", "行"]
共享字符 "窃" → 余弦相似度 > 0
```

## 影响

- **新增依赖**: `jieba>=0.42`, `numpy>=1.26`(均为纯 Python/轻量 C 扩展)
- **新增模块**: `src/mingrpg/retrieval/tfidf.py` — TfidfIndex 类
- **修改**: `src/mingrpg/tools/read.py` — query_laws 支持 query 参数
- **修改**: `src/mingrpg/llm/tools_registry.py` — schema 增加 query 属性
- **修改**: `src/mingrpg/llm/agent.py` — 系统提示词推荐使用 query 参数
- **测试**: 306 → 312 测试通过,新增 15 个向量检索测试
- **向后兼容**: 仅传 keywords 的调用行为不变
