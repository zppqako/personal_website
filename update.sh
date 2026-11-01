#!/bin/bash
# 从照片 App 的「网站」相簿同步照片，然后开本地预览。
# 用法：./update.sh            同步并预览
#       ./update.sh --dry-run  只看会发生什么
#       其他参数会原样传给 scripts/process_photos.py
set -e
cd "$(dirname "$0")"

if [ ! -x .venv/bin/python ]; then
  echo "首次运行：安装依赖…"
  python3 -m venv .venv
  .venv/bin/pip install -q -r scripts/requirements.txt
fi

.venv/bin/python scripts/process_photos.py "$@"

case " $* " in *" --dry-run "*) exit 0 ;; esac

echo
echo "本地预览：http://localhost:8000   （Ctrl+C 结束）"
echo "确认没问题后发布：git add -A && git commit -m \"update photos\" && git push"
python3 -m http.server 8000 --bind 127.0.0.1
