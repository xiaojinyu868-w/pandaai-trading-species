#!/usr/bin/env python3.11
"""汇总 3d/ 下各报告，打印 3D打印说明.md 用的表格（Markdown）。用法：python3.11 collect_stats.py"""
import json
import pathlib

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
SPECIES = ["cheetah", "elephant", "fox", "owl", "meerkat", "chameleon", "beaver"]
CN = {"cheetah": "猎豹", "elephant": "大象", "fox": "狐狸", "owl": "猫头鹰", "meerkat": "狐獴",
      "chameleon": "变色龙", "beaver": "海狸（隐藏）"}


def mb(p):
    return f"{p.stat().st_size / 1e6:.2f} MB" if p.exists() else "—"


def kb(p):
    return f"{p.stat().st_size / 1e3:.0f} KB" if p.exists() else "—"


def main():
    print("### 手办\n")
    print("| 物种 | 打印尺寸 (mm) | 体积 | print.stl | print.3mf | web.glb | 封闭流形 | 薄弱结构上 <1.2 mm |")
    print("|---|---|---|---|---|---|---|---|")
    for sp in SPECIES:
        d = HERE / "figurines" / sp
        r = json.loads((d / "print_report.json").read_text(encoding="utf-8"))
        t = r["final_topology"]
        ok = (t["watertight"] and t["winding_consistent"] and t["bodies"] == 1
              and t["nonmanifold_edges"] == 0 and r["manifold3d_status"] == "Error.NoError")
        w = r.get("thickness_after_weak_structures", {})
        x, y, z = r["size_mm"]
        print(f"| {CN[sp]} | {x:.1f} × {y:.1f} × {z:.1f} | {r['volume_cm3']:.1f} cm³ | {mb(d / 'print.stl')} | "
              f"{mb(d / 'print.3mf')} | {mb(d / 'web.glb')} | {'是' if ok else '否'} | "
              f"{w.get('lt_1.2mm_pct', '—')}% |")

    print("\n### Tripo 任务\n")
    print("| 物种 | task id | 提交时间 (UTC) | 完成时间 (UTC) | 积分 |")
    print("|---|---|---|---|---|")
    total = 0.0
    for sp in SPECIES:
        j = json.loads((HERE / "figurines" / sp / "tripo_task.json").read_text(encoding="utf-8"))
        total += float(j.get("credits_consumed") or 0)
        print(f"| {CN[sp]} | `{j['task_id']}` | {j['created_at'][:19].replace('T', ' ')} | "
              f"{j['completed_at'][:19].replace('T', ' ')} | {j.get('credits_consumed')} |")
    print(f"\n合计 {total:.0f} 积分")

    print("\n### 令牌\n")
    rep = json.loads((HERE / "tokens" / "tokens_report.json").read_text(encoding="utf-8"))
    print("| 文件 | 尺寸 (mm) | 体积 (mm³) | 文件大小 | 封闭流形 | 悬垂 >45° (mm²) |")
    print("|---|---|---|---|---|---|")
    for name, r in rep.items():
        x, y, z = r["size_mm"]
        print(f"| `tokens/{name}.stl` | {x:g} × {y:g} × {z:g} | {r['volume_mm3']:g} | "
              f"{kb(HERE / 'tokens' / (name + '.stl'))} | {'是' if r['ok'] else '否'} | {r['overhang_gt45_mm2']:g} |")


if __name__ == "__main__":
    main()
