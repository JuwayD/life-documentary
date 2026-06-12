# 2026-06-09 Phase 8: 渲染签名缓存

## 本次目标

启动 Phase 8 体验优化,选择 roadmap 中最靠前且可独立验收的“优化当前的实时渲染”,实现最小安全垂直切片。

## 实现内容

- 前端 `renderScene` 增加渲染签名缓存。
- 签名覆盖当前 Pixi 视口实际依赖的状态:玩家当前位置、地点尺寸/出口/标签、当前位置实体的 id/name/type/location/pos/hp/max_hp/tags。
- 状态未变化时跳过 Pixi 重绘和实体 sprite 更新。
- 地点结构变化或实体位置/HP/出入场变化时仍正常重绘。
- 增加 `window.__renderSceneStats` 供 E2E 验证跳过次数。
- 补充 Playwright E2E 测试重复渲染相同状态时不增加 draw 次数。
- 新增 ADR-0024。

## 设计原则

- 只优化浏览器端渲染路径,不改变世界状态、工具层或 GM Agent 决策边界。
- 缓存依据只来自已有快照事实,不引入规则判断。
- 保持侧栏和对话刷新逻辑不变,避免把渲染优化扩大为 UI 重构。

## 测试

- `.venv/bin/pytest tests/web/test_e2e_browser.py -q` → 24 passed

## 下一步

Phase 8 后续可继续追加小切片:节流高频状态推送、优化右栏信息分组、或减少大面板 DOM 重排。
