# 2026-06-11 Phase 8: 压力钟趋势可视化

## 变更

- `write.py`: `advance_pressure_clock` 新增 `history` 数组追踪值变化
- `app.js`: 压力钟面板增加趋势箭头(↑/↓/→)和 SVG 迷你折线图
- `style.css`: 趋势指示器样式(上升红色/下降绿色/持平灰色)
- `test_write.py`: 新增 `test_advance_pressure_clock_tracks_history` 测试

## 测试

83 个 write 工具测试全部通过。
