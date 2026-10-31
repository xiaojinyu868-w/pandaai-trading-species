"""把一个 JSONL 里的出图任务并行提交给 vmc（每行一条 vmc image gen），比 image batch 快。

  python3.11 run_parallel.py style-explore-v5.jsonl vmc-output/style-v5          # 只拿计划，不下单
  python3.11 run_parallel.py style-explore-v5.jsonl vmc-output/style-v5 --yes    # 用户确认后再提交

两次运行的命令完全相同，只差 --yes。结果写到 <out>/results.json。
"""

import json
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path


def command(row, out_dir: Path, yes: bool):
    # 写成 --version=<id>：分开写会被当成全局的“打印版本号”，命令直接退出
    cmd = ["vmc", "image", "gen", "--prompt", row["prompt"], "--model", row["model"], f"--version={row['version']}",
           "--size", row["size"], "--count", str(row.get("count", 1)), "--quality", row["quality"],
           "--out", str(out_dir / row["id"]), "--json"]
    for ref in row.get("ref", []):
        cmd += ["--ref", ref]
    if row.get("background"):
        cmd += ["--background", row["background"]]
    if yes:
        cmd.append("--yes")
    return cmd


def run(row, out_dir, yes):
    result = subprocess.run(command(row, out_dir, yes), capture_output=True, text=True)
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError:
        payload = {"ok": False, "raw": result.stdout[-2000:], "stderr": result.stderr[-2000:]}
    return row, result.returncode, payload


def main():
    archive, out_dir = Path(sys.argv[1]), Path(sys.argv[2])
    yes = "--yes" in sys.argv[3:]
    rows = [json.loads(line) for line in archive.read_text(encoding="utf-8").splitlines() if line.strip()]
    with ThreadPoolExecutor(max_workers=min(len(rows), 16)) as pool:
        outcomes = list(pool.map(lambda r: run(r, out_dir, yes), rows))

    if not yes:
        plans = [payload.get("plan") or {} for _, _, payload in outcomes]
        summary = {
            "exit_codes": sorted({code for _, code, _ in outcomes}),
            "tasks": len(rows),
            "images": sum(p.get("count", 0) for p in plans),
            "models": sorted({f"{p.get('model')} / {p.get('version')}" for p in plans}),
            "sizes": sorted({p.get("request", {}).get("size") for p in plans if p}),
            "quality": sorted({p.get("request", {}).get("quality") for p in plans if p}),
            "quota_used_now": min((p["quota"]["used"] for p in plans if p.get("quota")), default=None),
            "quota_limit": plans[0].get("quota", {}).get("limit") if plans else None,
            "running": plans[0].get("running") if plans else None,
            "allowed": all(p.get("allowed") for p in plans),
            "blockers": [b for p in plans for b in p.get("blockers", [])],
            "cost_priced": any(p.get("cost", {}).get("priced") for p in plans),
        }
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        return

    out_dir.mkdir(parents=True, exist_ok=True)
    results = []
    for row, code, payload in outcomes:
        data = payload.get("data") or {}
        files = data.get("files") or []
        results.append({"id": row["id"], "label": row.get("label", ""), "exit": code,
                        "task": data.get("id"), "files": files,
                        "error": None if code == 0 else payload.get("error") or payload})
    (out_dir / "results.json").write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    for r in results:
        print(r["id"], r["exit"], r["task"], len(r["files"]), "" if r["exit"] == 0 else json.dumps(r["error"], ensure_ascii=False)[:300])


if __name__ == "__main__":
    main()
