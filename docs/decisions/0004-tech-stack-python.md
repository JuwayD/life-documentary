# ADR-0004: 技术栈 Python + Claude + SQLite

- **状态**: Accepted
- **日期**: 2026-06-06
- **关联**: docs/03-tech-stack.md

## 决策

- **语言**: Python 3.11+
- **LLM**: Claude Sonnet 4.6 (官方 SDK)
- **存储**: SQLite (stdlib)
- **测试**: pytest
- **CLI 美化**: rich

## 备选与取舍

### 语言
- ✗ TypeScript: AI 生态略弱,Tool Use 集成稍麻烦
- ✗ Rust/Go: AI 协作友好度低,过早优化
- ✓ **Python**: 标准选择

### LLM
- ✗ GPT-4: Tool Use 也行,但用户已选 Claude
- ✗ 本地模型(qwen/glm): 判定能力跟不上,Phase 0 先不考虑
- ✓ **Claude Sonnet 4.6**: 用户指定

### 存储
- ✗ PostgreSQL: 需要服务,Phase 0 过重
- ✗ JSON 文件: 查询能力差,不适合实体表
- ✗ DuckDB: 优秀但分析向,本场景 SQLite 更合适
- ✓ **SQLite**: 零依赖、足够

### Web 框架(暂不引入)
Phase 0 是 CLI,不需要 web。Phase 3 引入渲染时再决定 Pygame vs Web。

## 后果

锁定上述选型后,所有 ADR 和代码均默认基于此栈。如需更换,应新开 ADR 替代本条。