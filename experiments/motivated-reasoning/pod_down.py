"""Tear down the pod recorded in pod_state.json (or --id)."""
import argparse, asyncio, json, os
from bellhop.rest import RunpodRest

async def main(pod_id: str):
    rest = RunpodRest(os.environ["RUNPOD_API_KEY"])
    async with rest:
        await rest.delete_pod(pod_id)
    print("deleted", pod_id)

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--state"); ap.add_argument("--id")
    a = ap.parse_args()
    pid = a.id or json.loads(open(a.state).read())["id"]
    asyncio.run(main(pid))
