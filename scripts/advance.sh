#!/bin/zsh
# 人生纪实 - 自动推进脚本
# 通过 cron 定时调用,让 Claude 读取 roadmap 和当前进度,自主推进项目一步。

set -u

PROJECT_DIR="/Users/huangrongqi/Documents/人生纪实"
LOG_DIR="$PROJECT_DIR/runtime/advance-logs"
TIMESTAMP="$(date +%Y%m%d-%H%M%S)"
LOG_FILE="$LOG_DIR/$TIMESTAMP.log"

# cc-haha sidecar(cron 环境拿不到 zsh 函数,必须显式调用)
APP_ROOT="/Applications/Claude Code Haha.app/Contents/Resources/app.asar"
SIDECAR="/Applications/Claude Code Haha.app/Contents/Resources/app.asar.unpacked/src-tauri/binaries/claude-sidecar-aarch64-apple-darwin"

mkdir -p "$LOG_DIR"
cd "$PROJECT_DIR" || exit 1

PROMPT='你正在自主推进"人生纪实·明朝篇"这个 AI-RPG 项目。

请按这个顺序工作:
1. 读 docs/04-roadmap.md 找到当前 Phase 和未完成的下一个小任务。
2. 读 docs/sessions/ 目录最新的会话日志,了解最近做到哪里。
3. 选一个"合适步长"的小推进 —— 一次只做一件能完整跑通的小事。优先遵守 ADR 0003 的 TDD 节奏(红→绿→重构)。
4. 实际写代码 / 加测试 / 改文档。完成后跑 .venv/bin/pytest 确认全绿。
5. 如果测试失败,回滚改动,在日志里说明卡在哪。不要硬塞半成品。
6. 在 docs/sessions/ 下追加或新建当日会话日志,记录这次推进做了什么、为什么、下次接着做什么。

约束:
- 不要碰 .venv / runtime/world.db / runtime/audit.jsonl
- 不要 git push、不要 git commit(留给人工 review)
- 不要修改 .gitignore、pyproject.toml 的依赖项,除非这一步明确需要新依赖
- 单次推进控制在合理规模,不贪多
- 任何不确定的方向选择,写进会话日志留给人工决策,不要自己拍板'

echo "=== advance run @ $TIMESTAMP ===" >> "$LOG_FILE"

CLAUDE_APP_ROOT="$APP_ROOT" "$SIDECAR" cli \
  --app-root "$APP_ROOT" \
  -p "$PROMPT" \
  --permission-mode acceptEdits \
  >> "$LOG_FILE" 2>&1

EXIT=$?
echo "=== exit=$EXIT @ $(date +%Y%m%d-%H%M%S) ===" >> "$LOG_FILE"
exit $EXIT
