#!/usr/bin/env bash
# 启动 web 服务 + 自动打开浏览器
set -e
cd "$(dirname "$0")"
PORT="${MINGRPG_PORT:-8765}"

echo "==> 启动 mingrpg 后端 (http://127.0.0.1:$PORT)"
.venv/bin/python -m mingrpg.web.server &
SERVER_PID=$!

# 等服务起来
for _ in $(seq 1 20); do
  if curl -s "http://127.0.0.1:$PORT/api/state" > /dev/null 2>&1; then
    break
  fi
  sleep 0.3
done

# 打开浏览器(macOS/Linux 兼容)
if command -v open > /dev/null; then
  open "http://127.0.0.1:$PORT"
elif command -v xdg-open > /dev/null; then
  xdg-open "http://127.0.0.1:$PORT"
else
  echo "请手动打开 http://127.0.0.1:$PORT"
fi

trap "kill $SERVER_PID 2>/dev/null" EXIT
wait $SERVER_PID
