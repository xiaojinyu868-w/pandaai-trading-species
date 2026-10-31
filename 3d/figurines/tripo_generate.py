#!/usr/bin/env python3.11
"""Tripo API v3：物种手办概念图 → 3D 模型（tripo.glb）。

用法：
    python3.11 tripo_generate.py balance
    python3.11 tripo_generate.py run fox
    python3.11 tripo_generate.py run cheetah elephant owl meerkat chameleon beaver

密钥只在本进程内从 /root/.config/tripo/env 读取（TRIPO_API_KEY），
不打印、不写日志、不写进任何文件。任务元数据（不含下载链接）写到
<species>/tripo_task.json，供 AI 工具披露表使用。
"""
import json
import pathlib
import sys
import threading
import time

import requests

BASE = "https://openapi.tripo3d.com/v3"
ENV_FILE = "/root/.config/tripo/env"
ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT = ROOT / "3d" / "figurines"
SRC = ROOT / "art" / "vmc-output" / "style-v7"
SPECIES = ["cheetah", "elephant", "fox", "owl", "meerkat", "chameleon", "beaver"]

PARAMS = {
    "model": "v3.1-20260211",
    "texture": True,
    "pbr": True,
    "texture_version": "v3.5-20260815",
    "texture_quality": "detailed",
    "geometry_quality": "detailed",
    "texture_alignment": "original_image",
    "enable_image_autofix": False,
    "model_seed": 1031,
    "texture_seed": 1031,
}

_print_lock = threading.Lock()


def log(*a):
    with _print_lock:
        print(time.strftime("%H:%M:%S"), *a, flush=True)


def _api_key():
    with open(ENV_FILE, encoding="utf-8") as fh:
        for line in fh:
            s = line.strip()
            if s.startswith("export "):
                s = s[7:].strip()
            name, sep, value = s.partition("=")
            if sep and name.strip() == "TRIPO_API_KEY":
                return value.strip().strip('"').strip("'")
    raise SystemExit("TRIPO_API_KEY 不在 env 文件里")


def session():
    s = requests.Session()
    s.headers["Authorization"] = "Bearer " + _api_key()
    return s


def check(resp):
    try:
        body = resp.json()
    except ValueError:
        raise RuntimeError(f"HTTP {resp.status_code}，非 JSON 响应")
    if resp.status_code != 200 or body.get("code") != 0:
        raise RuntimeError(f"HTTP {resp.status_code} code={body.get('code')} "
                           f"{body.get('message')} / {body.get('suggestion')}")
    return body["data"]


def request(s, method, path, **kw):
    for attempt in range(6):
        r = s.request(method, BASE + path, timeout=120, **kw)
        if r.status_code == 429:
            wait = int(r.headers.get("Retry-After") or 2 ** attempt)
            log(f"429，等待 {wait}s")
            time.sleep(wait)
            continue
        return check(r)
    raise RuntimeError("429 重试次数用完")


def balance(s):
    return request(s, "GET", "/account/balance")


def source_image(sp):
    files = sorted((SRC / f"v7_figurine_{sp}").rglob("*.png"))
    if len(files) != 1:
        raise RuntimeError(f"{sp}: 期望 1 张 png，实际 {len(files)}")
    return files[0]


def upload(s, path):
    with open(path, "rb") as fh:
        data = request(s, "POST", "/files", files={"file": (path.name, fh, "image/png")})
    return data["file_token"]


def create(s, file_token):
    payload = dict(PARAMS, input=file_token)
    return request(s, "POST", "/generation/image-to-model", json=payload)["task_id"]


def wait(s, sp, task_id, timeout=3600):
    t0, last = time.time(), None
    while time.time() - t0 < timeout:
        d = request(s, "GET", f"/tasks/{task_id}")
        st, pg = d.get("status"), d.get("progress")
        if (st, pg) != last:
            log(f"{sp}: {st} {pg}%")
            last = (st, pg)
        if st == "success":
            return d
        if st in ("failed", "cancelled", "banned", "expired"):
            raise RuntimeError(f"{sp}: 任务 {task_id} 结束于 {st} "
                               f"{d.get('error_code')} {d.get('error_message')}")
        time.sleep(5)
    raise TimeoutError(f"{sp}: 任务 {task_id} 超时")


def download(url, dest):
    tmp = dest.with_suffix(dest.suffix + ".part")
    with requests.get(url, stream=True, timeout=600) as r:
        r.raise_for_status()
        with open(tmp, "wb") as fh:
            for chunk in r.iter_content(1 << 20):
                fh.write(chunk)
    tmp.replace(dest)


def run_one(sp):
    s = session()
    img = source_image(sp)
    out_dir = OUT / sp
    out_dir.mkdir(parents=True, exist_ok=True)
    attempts = []
    for attempt in range(2):  # 失败最多重试 1 次
        try:
            token = upload(s, img)
            task_id = create(s, token)
            log(f"{sp}: 创建任务 {task_id}（第 {attempt + 1} 次）")
            attempts.append(task_id)
            d = wait(s, sp, task_id)
            out = d.get("output") or {}
            url = out.get("model_url") or out.get("pbr_model") or out.get("model")
            if not url:
                raise RuntimeError(f"{sp}: 输出里没有 model_url，键={sorted(out)}")
            download(url, out_dir / "tripo.glb")
            if out.get("rendered_image_url"):
                try:
                    download(out["rendered_image_url"], pathlib.Path(f"/tmp/tripo_render_{sp}.img"))
                except Exception as e:  # 预览图只是参考
                    log(f"{sp}: 渲染图下载失败 {e}")
            meta = {
                "species": sp,
                "task_id": task_id,
                "failed_attempts": attempts[:-1],
                "endpoint": "POST /v3/generation/image-to-model",
                "params": PARAMS,
                "source_image": str(img.relative_to(ROOT)),
                "status": d.get("status"),
                "credits_consumed": d.get("credits_consumed"),
                "created_at": d.get("created_at"),
                "completed_at": d.get("completed_at"),
                "output_keys": sorted(out),
                "glb_bytes": (out_dir / "tripo.glb").stat().st_size,
            }
            (out_dir / "tripo_task.json").write_text(
                json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
            log(f"{sp}: 完成，{meta['glb_bytes'] / 1e6:.1f} MB，"
                f"消耗 {meta['credits_consumed']} 积分")
            return meta
        except Exception as e:
            log(f"{sp}: 失败：{e}")
            if attempt == 1:
                raise
    return None


def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    cmd = sys.argv[1]
    if cmd == "balance":
        b = balance(session())
        print(json.dumps(b, ensure_ascii=False))
        return
    if cmd == "run":
        names = sys.argv[2:] or SPECIES
        bad = [n for n in names if n not in SPECIES]
        if bad:
            raise SystemExit(f"未知物种：{bad}")
        log("开始前余额", balance(session()))
        results, errors = {}, {}

        def worker(n):
            try:
                results[n] = run_one(n)
            except Exception as e:
                errors[n] = str(e)

        threads = [threading.Thread(target=worker, args=(n,)) for n in names]
        for i, t in enumerate(threads):
            t.start()
            time.sleep(2 if i < len(threads) - 1 else 0)
        for t in threads:
            t.join()
        log("结束后余额", balance(session()))
        for n in names:
            if n in results:
                log(f"OK  {n} {results[n]['task_id']} {results[n]['credits_consumed']}")
            else:
                log(f"ERR {n} {errors.get(n)}")
        if errors:
            sys.exit(1)
        return
    raise SystemExit(__doc__)


if __name__ == "__main__":
    main()
