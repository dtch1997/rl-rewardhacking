"""Provision the 4xH200 pod for the motivated-reasoning runs, push this checkout, bootstrap it, and KEEP it alive.

Usage (from the worktree root, workspace venv):
    . ~/.env && python experiments/motivated-reasoning/pod_up.py --state /path/pod_state.json
Later steps run over SSH (see pod_state.json for the command); tear down with pod_down.py.
"""
import argparse, asyncio, json, os, pathlib, sys
from datetime import timedelta
from bellhop import PodConfig, pod

ROOT = pathlib.Path(__file__).resolve().parents[2]


def load_home_env():
    """Populate os.environ from ~/.env for keys not already set (RUNPOD/HF/OPENROUTER/WANDB)."""
    f = pathlib.Path.home() / ".env"
    if not f.exists():
        return
    for line in f.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        k = k.strip().removeprefix("export ").strip()
        os.environ.setdefault(k, v.strip().strip('"').strip("'"))
REMOTE = "/workspace/rl-rewardhacking"


async def main(state_path: str, gpu_count: int, disk_gb: int):
    cfg = PodConfig(
        name="motivated-reasoning",
        gpu="H200", gpu_count=gpu_count, cloud="SECURE",
        image_preset="pytorch-latest",
        container_disk_gb=disk_gb,
        env={k: os.environ.get(k, "") for k in ("HF_TOKEN", "OPENROUTER_API_KEY", "WANDB_API_KEY", "WANDB_PROJECT", "WANDB_ENTITY")}
            | {"MAX_JOBS": os.environ.get("MAX_JOBS", "48")},
        max_lifetime=timedelta(hours=36),
        provision_timeout=timedelta(minutes=30), ready_timeout=timedelta(minutes=20),
    )
    async with pod(cfg, keep=True) as p:
        state = {"id": p.id, "host": p.host, "port": p.mapped_port(22),
                 "ssh": f"ssh -o StrictHostKeyChecking=no -p {p.mapped_port(22)} root@{p.host}"}
        pathlib.Path(state_path).write_text(json.dumps(state, indent=2))
        print("POD", json.dumps(state), flush=True)
        await p.exec(f"mkdir -p {REMOTE}")
        # push the checkout minus junk; verl/ is needed (editable install)
        await p.push(str(ROOT), REMOTE)
        r = await p.exec(f"cd {REMOTE} && bash experiments/motivated-reasoning/remote/setup.sh", timeout=3 * 3600)
        print("SETUP exit", r.exit_code, flush=True)
        print((r.stdout or "")[-3000:])
        print((r.stderr or "")[-2000:], file=sys.stderr)
        if r.exit_code != 0:
            sys.exit(r.exit_code)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--state", required=True)
    ap.add_argument("--gpu-count", type=int, default=4)
    ap.add_argument("--disk-gb", type=int, default=300)
    a = ap.parse_args()
    load_home_env()
    os.environ.setdefault("MAX_JOBS", "48")
    asyncio.run(main(a.state, a.gpu_count, a.disk_gb))
