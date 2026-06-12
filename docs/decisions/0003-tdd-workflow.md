# ADR-0003: TDD 工作流(含 AI 协作)

- **状态**: Accepted
- **日期**: 2026-06-06

## 背景

本项目以 AI 协作开发为前提,需要确立适合人机协作的 TDD 工作流。

## 决策

**严格 Red-Green-Refactor 循环,且测试先于实现。**

### 工作流

```
1. (人/AI) 写一个失败的测试,明确表达需求
2. (人) Review 测试,确认表达了真实意图
3. (AI) 写最小实现使其通过
4. (人/AI) Refactor,保持测试通过
5. (人) 决定是否 commit
```

### 不同层的测试策略

#### 工具层 (Tool Layer) — 传统 TDD
```python
def test_set_attribute_updates_value():
    world = make_world(entities={"player": {"hp": 100}})
    result = set_attribute(world, "player", "hp", 80)
    assert result["old"] == 100
    assert result["new"] == 80
    assert world.get_entity("player")["hp"] == 80
```

#### State Layer — 数据契约测试
```python
def test_entity_round_trip():
    e = {"id": "wang", "type": "npc", ...}
    world.save_entity(e)
    assert world.get_entity("wang") == e
```

#### AI Agent 层 — 行为约束测试
不测"输出什么文字",而测"调用了什么工具":
```python
def test_agent_violence_against_official_queries_laws():
    trace = run_agent("我打知府", scenario="court_hall")
    tool_names = [t.name for t in trace.tool_calls]
    assert "query_laws" in tool_names
    assert any("斗殴" in arg for arg in trace.law_queries)
```

#### 集成测试 — 场景回放
固定 random seed + mock LLM response,验证端到端流程:
```python
def test_walk_into_tavern_full_flow(snapshot):
    result = game.process_input("我推门进入茶馆")
    assert snapshot == result  # snapshot 测试
```

## 测试运行规则

- **每次代码改动前**: 先跑相关测试,确认当前是绿
- **写完测试后**: 必须先验证它会失败(red)再写实现
- **commit 前**: 全量跑 `pytest`,必须全绿
- **AI 写代码后**: AI 自己跑 `pytest tests/<changed_module>` 验证

## CI(后续接入)

Phase 0 不引入 CI,但项目设计为可加:
- GitHub Actions / 本地 git hook
- `pytest` + `pytest-cov` + 覆盖率门槛 80%

## 例外

- **探索性 spike 代码**: 在 `experiments/` 下不强制 TDD
- **prompt 调试**: prompt 改动只测"是否仍调用了关键工具",不测 LLM 输出文字

## 后果

### 正面
- ✓ 测试名即需求文档,AI 改代码时能看清意图
- ✓ 重构有安全网
- ✓ 测试用例可作为分享素材("我们靠这些测试逼出了正确实现")

### 负面
- ✗ 写测试本身需要时间
  - **对策**: 接受这个成本,长期收益远大于
- ✗ AI 可能写出"过测试但不解决问题"的代码
  - **对策**: 测试用例要表达真实意图,不只是 happy path