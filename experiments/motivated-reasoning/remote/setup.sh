#!/usr/bin/env bash
# One-time pod bootstrap for rl-rewardhacking (run from /workspace/rl-rewardhacking).
# Mirrors setup_gpu.sh but non-interactive; env vars HF_TOKEN / OPENROUTER_API_KEY / MAX_JOBS come from the driver.
set -euo pipefail
cd /workspace/rl-rewardhacking
export GIT_REPO_NAME=rl-rewardhacking
source .env.gpu
cat > .env <<ENV
HF_TOKEN=${HF_TOKEN:-}
WANDB_API_KEY=${WANDB_API_KEY:-}
WANDB_PROJECT=${WANDB_PROJECT:-rl-rewardhacking}
WANDB_ENTITY=${WANDB_ENTITY:-}
OPENROUTER_API_KEY=${OPENROUTER_API_KEY:-}
MAX_JOBS=${MAX_JOBS:-48}
ENV
apt-get update -qq && apt-get install -y -qq git tmux unzip > /dev/null
pip install -q uv
mkdir -p "$(dirname "$VENV_DIR")"
uv venv --python 3.12 "$VENV_DIR"
source "$VENV_DIR/bin/activate"
export WANDB_LOG_MODEL=false WANDB_START_METHOD=thread VLLM_WORKER_MULTIPROC_METHOD=spawn LITELLM_LOG=WARNING
echo "== uv sync (flash-attn builds from source; MAX_JOBS=$MAX_JOBS) =="
time uv sync --dev
uv pip install --no-deps -e verl/
python -c "import torch, vllm, verl, flash_attn; print('torch', torch.__version__, 'vllm', vllm.__version__, 'gpus', torch.cuda.device_count())"
echo "== datasets =="
source commands.sh
create_all_datasets
ls -la results/data/
echo SETUP_DONE
