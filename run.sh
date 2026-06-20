#!/usr/bin/env bash
# 热点电商导购系统 - 本地启动脚本
# 用法： ./run.sh              （默认 8501 端口，自动开浏览器）
#       ./run.sh --server.port 8888   （自定义端口）
set -euo pipefail

# 切到脚本所在目录（项目根），保证相对路径 data/ 等正确
cd "$(dirname "$0")"

# 自动准备虚拟环境（首次或换机器时）
if [ ! -d ".venv" ]; then
  echo "[run] 创建虚拟环境 .venv ..."
  python3 -m venv .venv
fi
source .venv/bin/activate

# 依赖缺失时才安装（已装会跳过，日常启动不卡）
if ! python -c "import streamlit, sqlalchemy" 2>/dev/null; then
  echo "[run] 安装依赖（requirements.txt）..."
  pip install -q -r requirements.txt
fi

# 从 .env 读配置（若有）—— python-dotenv 已在 app 内加载，这里仅为提示
if [ -f ".env" ]; then
  echo "[run] 检测到 .env（将据此读取 LLM/GLM 等配置）"
else
  echo "[run] 未发现 .env，使用 mock 模式（无需 GLM key 即可演示）。需要真实 GLM 时参考 .env.example。"
fi

echo "[run] 启动 Streamlit ...  http://localhost:8501  （Ctrl+C 停止）"
exec streamlit run app.py "$@"
