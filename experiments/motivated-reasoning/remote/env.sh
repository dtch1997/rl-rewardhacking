# source this at the top of every remote step
cd /workspace/rl-rewardhacking
export GIT_REPO_NAME=rl-rewardhacking
set -a; source .env.gpu; source .env; set +a
source "$VENV_DIR/bin/activate"
export WANDB_LOG_MODEL=false WANDB_START_METHOD=thread VLLM_WORKER_MULTIPROC_METHOD=spawn LITELLM_LOG=WARNING WANDB__SERVICE_WAIT=600
source commands.sh
