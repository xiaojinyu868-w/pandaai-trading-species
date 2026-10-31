#!/usr/bin/env python3.11
"""手办打印件：tripo.glb → print.stl / print.3mf（60 mm 高、平底、封闭流形、最薄 ≥1.2 mm）。

用法：python3.11 make_print.py fox [cheetah ...]

流程
1. 读 tripo.glb，合并 UV 缝处的重复顶点；glTF（Y 上、正面 +X）转成打印坐标
   （Z 上、正面 -Y），缩放到 60 mm 高，底座中心放到原点。
2. 拓扑检查：封闭流形直接进 manifold3d；否则逐壳 pymeshfix 修补后求并。
3. manifold3d 保流形简化（偏差 ≤0.01 mm）。
4. 薄弱结构判定：0.1 mm 体素上做半径 0.6 mm 的开运算，得到“粗主体”；主体之外的薄区按连通块
   统计伸出距离，伸出 >1 mm 的（耳朵、胡须、尾尖、细柄、衣角）才算薄弱结构。
   毛发纹理、衣褶这类贴身浮雕虽然也薄，但不承力，保持原样。
5. 壁厚：表面均匀抽样 100 万点，沿内法线打射线（embree）量到对面的距离。
   落在薄弱结构里、厚度 <1.2 mm 的点取“表面点与对面点的中点”，以 0.65 mm 半径做球的并集
   （距离场 + marching cubes），再与原网格布尔求并。只在薄弱处长肉，其余表面不变。
6. 在 z=0.15 mm 处切出平底，下移到 z=0，再等比缩回 60.00 mm 高。
7. 校验（manifold3d 状态 + trimesh 封闭/定向/体积/壳数），复测壁厚（全部表面 / 薄弱结构上），导出。
"""
import json
import pathlib
import sys
import time

import manifold3d as m3
import numpy as np
import trimesh
from scipy import ndimage
from scipy.spatial import cKDTree
from skimage import measure

ROOT = pathlib.Path(__file__).resolve().parents[2]
FIG = ROOT / "3d" / "figurines"

HEIGHT_MM = 60.0
MIN_THICK = 1.2
BLOB_R = 0.72
BLUR = 0.25      # 球并集距离场的高斯模糊 σ（mm）
SIMPLIFY_TOL = 0.01
BOTTOM_TRIM = 0.15
PITCH = 0.08
SAMPLES = 1_000_000
VOX = 0.1        # 薄弱结构判定用的体素边长（mm）
PROTRUDE = 1.0   # 薄区伸出粗主体超过这个距离（mm）才算薄弱结构


def log(*a):
    print(time.strftime("%H:%M:%S"), *a, flush=True)


def load_print_coords(glb):
    m = trimesh.load(glb, force="mesh", process=False)
    m = trimesh.Trimesh(m.vertices.astype(np.float64), m.faces, process=True)
    x, y, z = m.vertices.T
    v = np.column_stack([-z, -x, y])  # glTF(Y 上, 正面 +X) → Z 上, 正面 -Y
    v *= HEIGHT_MM / (v[:, 2].max() - v[:, 2].min())
    v[:, 2] -= v[:, 2].min()
    base = v[:, 2] < 0.5
    v[:, 0] -= (v[base, 0].min() + v[base, 0].max()) / 2
    v[:, 1] -= (v[base, 1].min() + v[base, 1].max()) / 2
    return trimesh.Trimesh(v, m.faces, process=True)


def topo(mesh):
    e = np.sort(mesh.edges, axis=1)
    _, cnt = np.unique(e, axis=0, return_counts=True)
    return {
        "faces": int(len(mesh.faces)),
        "watertight": bool(mesh.is_watertight),
        "winding_consistent": bool(mesh.is_winding_consistent),
        "is_volume": bool(mesh.is_volume),
        "bodies": int(mesh.body_count),
        "nonmanifold_edges": int((cnt > 2).sum()),
        "boundary_edges": int((cnt == 1).sum()),
    }


def to_manifold(mesh):
    mg = m3.Mesh(vert_properties=np.asarray(mesh.vertices, np.float32),
                 tri_verts=np.asarray(mesh.faces, np.uint32))
    man = m3.Manifold(mg)
    if man.status() != m3.Error.NoError:
        raise RuntimeError(f"manifold3d 拒绝该网格：{man.status()}")
    return man


def from_manifold(man):
    mg = man.to_mesh()
    return trimesh.Trimesh(np.asarray(mg.vert_properties)[:, :3].astype(np.float64),
                           np.asarray(mg.tri_verts), process=False)


def repair(mesh):
    """返回 (Manifold, 说明)。干净的网格直接用；否则逐壳修补后求并。"""
    try:
        return to_manifold(mesh), "原网格已是封闭流形，无需修补"
    except RuntimeError:
        pass
    import pymeshfix
    parts = mesh.split(only_watertight=False)
    total = mesh.area
    fixed, dropped = [], 0
    for p in parts:
        if p.area < total * 1e-4:
            dropped += 1
            continue
        try:
            fixed.append(to_manifold(p))
            continue
        except RuntimeError:
            pass
        mf = pymeshfix.MeshFix(np.asarray(p.vertices), np.asarray(p.faces))
        mf.repair(joincomp=False, remove_smallest_components=False)
        q = trimesh.Trimesh(mf.points, mf.faces, process=True)
        if len(q.faces):
            fixed.append(to_manifold(q))
    man = m3.Manifold.batch_boolean(fixed, m3.OpType.Add)
    return man, f"拆成 {len(parts)} 个壳，pymeshfix 修补后求并 {len(fixed)} 个（丢弃 {dropped} 个碎片）"


def ray_thickness(mesh, n=SAMPLES, seed=0):
    from trimesh.ray.ray_pyembree import RayMeshIntersector
    pts, fid = trimesh.sample.sample_surface(mesh, n, seed=seed)
    nrm = mesh.face_normals[fid]
    ri = RayMeshIntersector(mesh)
    loc, ir, _ = ri.intersects_location(pts - nrm * 1e-3, -nrm, multiple_hits=False)
    th = np.full(len(pts), np.inf)
    th[ir] = np.linalg.norm(loc - pts[ir], axis=1) + 1e-3
    return th, pts, nrm


def solid_voxels(mesh, pitch=VOX):
    """沿 +Z 打一排射线，按穿入/穿出的奇偶性填充体素。返回 (bool 网格, 网格原点)。"""
    from trimesh.ray.ray_pyembree import RayMeshIntersector
    lo = mesh.bounds[0] - 3 * pitch
    nx, ny, nz = np.ceil((mesh.bounds[1] + 3 * pitch - lo) / pitch).astype(int)
    gx, gy = np.meshgrid(lo[0] + (np.arange(nx) + 0.5) * pitch, lo[1] + (np.arange(ny) + 0.5) * pitch,
                         indexing="ij")
    jitter = np.random.default_rng(0).uniform(-1e-4, 1e-4, (gx.size, 2))  # 避开正好打在棱上
    origins = np.column_stack([gx.ravel() + jitter[:, 0], gy.ravel() + jitter[:, 1],
                               np.full(gx.size, lo[2] - 1.0)])
    dirs = np.tile([0.0, 0.0, 1.0], (len(origins), 1))
    loc, ir, _ = RayMeshIntersector(mesh).intersects_location(origins, dirs, multiple_hits=True)
    k = np.clip(np.floor((loc[:, 2] - lo[2]) / pitch - 0.5).astype(int) + 1, 0, nz)
    flips = np.zeros((nx * ny, nz + 1), np.int8)
    np.add.at(flips, (ir, k), 1)
    solid = (np.cumsum(flips[:, :nz], axis=1, dtype=np.int8) & 1).astype(bool)
    return solid.reshape(nx, ny, nz), lo


def _morph(op, mask, steps):
    """交替用 6 邻域和 26 邻域做 steps 次腐蚀/膨胀，近似半径 steps 格的球；只用布尔数组，省内存。"""
    s6 = ndimage.generate_binary_structure(3, 1)
    s26 = ndimage.generate_binary_structure(3, 3)
    for i in range(steps):
        mask = op(mask, structure=s6 if i % 2 == 0 else s26)
    return mask


def weak_regions(mesh, r=MIN_THICK / 2, protrude=PROTRUDE, pitch=VOX):
    """薄弱结构的体素掩码。先对实体做半径 r 的开运算（腐蚀再膨胀）得到“粗主体”，
    主体之外剩下的就是厚度 <2r 的薄区；薄区按连通块统计伸出主体的最远距离，
    超过 protrude 的（耳朵、胡须、尾尖、细柄、衣角）算薄弱结构，
    没超过的是毛发纹理、衣褶这类贴在身上的浮雕细节，不加厚，免得表面长满小球。"""
    solid, lo = solid_voxels(mesh, pitch)
    nr, npr = int(round(r / pitch)), int(round(protrude / pitch))
    core = _morph(ndimage.binary_erosion, solid, nr)
    thin = solid & ~_morph(ndimage.binary_dilation, core, nr)
    del solid
    near = _morph(ndimage.binary_dilation, core, nr + npr)
    del core
    lab, n = ndimage.label(thin, structure=np.ones((3, 3, 3)))
    del thin
    if n == 0:
        return np.zeros(lab.shape, bool), lo, {"thin_parts": 0, "weak_parts": 0}
    weak_ids = np.unique(lab[(lab > 0) & ~near])
    keep = np.zeros(n + 1, bool)
    keep[weak_ids] = True
    keep[0] = False
    weak = keep[lab]
    info = {"thin_parts": int(n), "weak_parts": int(len(weak_ids)),
            "weak_volume_mm3": round(float(weak.sum() * pitch ** 3), 1)}
    return weak, lo, info


def in_mask(mask, lo, pts, pitch=VOX):
    """点是否落在掩码体素里。"""
    ijk = np.floor((pts - lo) / pitch).astype(int)
    ok = np.all((ijk >= 0) & (ijk < mask.shape), axis=1)
    out = np.zeros(len(pts), bool)
    out[ok] = mask[ijk[ok, 0], ijk[ok, 1], ijk[ok, 2]]
    return out


def thin_report(th, pts=None):
    fin = np.isfinite(th)
    if pts is not None:
        fin &= pts[:, 2] > 1.0
    t = th[fin]
    return {
        "samples": int(len(th)),
        "lt_1.2mm_pct": round(float((t < MIN_THICK).mean() * 100), 3),
        "lt_1.0mm_pct": round(float((t < 1.0).mean() * 100), 3),
        "lt_0.8mm_pct": round(float((t < 0.8).mean() * 100), 3),
        "min_mm": round(float(t.min()), 3),
        "p0.1_mm": round(float(np.percentile(t, 0.1)), 3),
        "median_mm": round(float(np.median(t)), 3),
    }


def ball_union(centers, radius, pitch=PITCH, sigma=BLUR):
    """球心集合 → 球并集的封闭网格：精确距离场，轻微高斯模糊把薄边上的“珠串”抹成平滑条带，
    再 marching cubes。模糊会让孤立的球缩小约 sigma²/r，所以 BLOB_R 比 0.6 留了余量。"""
    cap = radius + 2 * pitch + 4 * sigma
    lo = centers.min(0) - cap - 2 * pitch
    shape = np.ceil((centers.max(0) + cap + 2 * pitch - lo) / pitch).astype(int) + 1
    seed = np.ones(shape, bool)
    ij = np.clip(np.round((centers - lo) / pitch).astype(int), 0, shape - 1)
    seed[ij[:, 0], ij[:, 1], ij[:, 2]] = False
    approx = ndimage.distance_transform_edt(seed, sampling=pitch).astype(np.float32)
    band = approx < cap
    del approx
    field = np.full(shape, cap, np.float32)
    idx = np.argwhere(band)
    dist, _ = cKDTree(centers).query(lo + idx * pitch, workers=-1)
    field[idx[:, 0], idx[:, 1], idx[:, 2]] = dist
    field -= radius
    if sigma > 0:
        field = ndimage.gaussian_filter(field, sigma / pitch, mode="nearest")
    field = np.pad(field, 1, constant_values=cap)
    verts, faces, _, _ = measure.marching_cubes(field, level=0.0, spacing=(pitch,) * 3,
                                                gradient_direction="ascent")
    verts = verts - pitch + lo
    b = trimesh.Trimesh(verts, faces, process=True)
    if b.volume < 0:
        b.invert()
    return b


def thickening(centers, radius, tile=8.0):
    """按 8 mm 方块把球心分片，逐片求球并集再整体求并，返回 Manifold。
    分片是为了限制体素网格大小：薄区连成一大片时，整块 0.08 mm 网格会吃掉 4 GB 以上内存。"""
    key = np.floor((centers - centers.min(0)) / tile).astype(int)
    _, grp = np.unique(key, axis=0, return_inverse=True)
    grp = grp.ravel()
    parts = []
    for i in range(grp.max() + 1):
        c = centers[grp == i]
        parts.append(to_manifold(ball_union(c, radius)).simplify(SIMPLIFY_TOL))
    return m3.Manifold.batch_boolean(parts, m3.OpType.Add), len(parts)


def unpinch(v, f, eps=2e-3, rounds=4):
    """布尔求并时两片表面相切，会留下位置重合、拓扑分开的顶点；按坐标焊接后成了非流形边。
    只把这些顶点沿各自的顶点法线向内挪 eps（2 µm 起），其余顶点不动。"""
    v = v.copy()
    moved = 0
    for _ in range(rounds):
        _, inv, cnt = np.unique(np.round(v, 7), axis=0, return_inverse=True, return_counts=True)
        inv = inv.ravel()
        mf = inv[f]
        e = np.sort(np.concatenate([mf[:, [0, 1]], mf[:, [1, 2]], mf[:, [2, 0]]]), axis=1)
        ue, ec = np.unique(e, axis=0, return_counts=True)
        bad = np.unique(ue[ec > 2])
        if len(bad) == 0:
            break
        target = np.isin(inv, bad) & (cnt[inv] > 1)
        fn = np.cross(v[f[:, 1]] - v[f[:, 0]], v[f[:, 2]] - v[f[:, 0]])
        vn = np.zeros_like(v)
        for k in range(3):
            np.add.at(vn, f[:, k], fn)
        vn /= np.linalg.norm(vn, axis=1, keepdims=True) + 1e-20
        v[target] -= vn[target] * eps
        moved += int(target.sum())
        eps *= 2
    return v, moved


def clean_final(man):
    """去掉布尔运算留下的内部空腔（负体积壳）和碎片，再解开相切夹点。"""
    comps = man.decompose()
    keep = [c for c in comps if c.volume() > 1.0]
    man = keep[0] if len(keep) == 1 else m3.Manifold.batch_boolean(keep, m3.OpType.Add)
    mg = man.to_mesh()
    v = np.asarray(mg.vert_properties)[:, :3].astype(np.float64)
    f = np.asarray(mg.tri_verts).astype(np.int64)
    v, moved = unpinch(v, f)
    final = trimesh.Trimesh(v, f, process=True)
    return final, f"去掉 {len(comps) - len(keep)} 个内部空腔/碎片；解开相切夹点顶点 {moved} 个"


def process(sp):
    d = FIG / sp
    rep = {"species": sp}
    log(sp, "读取并转换坐标")
    mesh = load_print_coords(d / "tripo.glb")
    rep["source_topology"] = topo(mesh)
    log(sp, "原始拓扑", rep["source_topology"])

    man, how = repair(mesh)
    rep["repair"] = how
    man = man.simplify(SIMPLIFY_TOL)
    base = from_manifold(man)
    rep["simplified_faces"] = int(man.num_tri())
    log(sp, how, "| 简化后", man.num_tri(), "面，体积 %.2f cm³" % (man.volume() / 1000))

    del mesh
    weak, wlo, rep["weak_regions"] = weak_regions(base)
    # 放宽 2 格（0.2 mm），收进体素化时漏掉的刀口边
    weak = ndimage.binary_dilation(weak, iterations=2)
    log(sp, "薄弱结构", rep["weak_regions"])

    v0 = man.volume()
    rep["thin_samples"], rep["thin_tiles"] = [], []
    for k in range(2):
        th, pts, nrm = ray_thickness(base, seed=10 + k)
        # 贴床的最底 1 mm 由热床托着，底边的射线读数是边缘效应，不加厚
        thin = np.isfinite(th) & (th < MIN_THICK) & (pts[:, 2] > 1.0)
        mid = pts - nrm * (np.where(np.isfinite(th), th, 0.0)[:, None] / 2)
        thin_weak = thin & in_mask(weak, wlo, mid)
        if k == 0:
            rep["thickness_before"] = thin_report(th)
            rep["thin_before_pct"] = {"weak_structures": round(float(thin_weak.mean() * 100), 3),
                                      "surface_detail": round(float((thin & ~thin_weak).mean() * 100), 3)}
            log(sp, "加厚前壁厚", rep["thickness_before"], "| 薄点占比", rep["thin_before_pct"])
        rep["thin_samples"].append(int(thin_weak.sum()))
        if not thin_weak.any():
            break
        bman, ncl = thickening(mid[thin_weak], BLOB_R)
        rep["thin_tiles"].append(ncl)
        man = man + bman
        base = from_manifold(man)
    rep["added_volume_mm3"] = round(float(man.volume() - v0), 2)
    log(sp, "加厚体积 +%.1f mm³（薄点 %s，分片 %s）" % (rep["added_volume_mm3"],
                                                rep["thin_samples"], rep["thin_tiles"]))

    man = man.trim_by_plane((0.0, 0.0, 1.0), BOTTOM_TRIM).translate((0.0, 0.0, -BOTTOM_TRIM))
    bb = man.bounding_box()
    s = HEIGHT_MM / (bb[5] - bb[2])
    man = man.scale((s,) * 3).simplify(SIMPLIFY_TOL)
    final, rep["cleanup"] = clean_final(man)
    rep["final_topology"] = topo(final)
    check = to_manifold(final)
    rep["manifold3d_status"] = str(check.status())
    rep["genus"] = int(check.genus())
    man = check
    ext = final.bounds[1] - final.bounds[0]
    rep["size_mm"] = [round(float(x), 2) for x in ext]
    rep["volume_cm3"] = round(float(man.volume() / 1000), 3)
    z = final.vertices[:, 2]
    flat = final.faces[np.all(z[final.faces] < 1e-4, axis=1)]
    rep["bottom_contact_area_mm2"] = round(float(trimesh.triangles.area(final.vertices[flat]).sum()), 1)
    th1, p1, n1 = ray_thickness(final, seed=1)
    rep["thickness_after"] = thin_report(th1)
    rep["thickness_after_excl_bottom_1mm"] = thin_report(th1, p1)
    # 薄弱结构上的复测：把成品坐标换回加厚时的坐标再查掩码
    mid1 = p1 - n1 * (np.where(np.isfinite(th1), th1, 0.0)[:, None] / 2)
    sel = in_mask(weak, wlo, mid1 / s + (0.0, 0.0, BOTTOM_TRIM)) & (p1[:, 2] > 1.0) & np.isfinite(th1)
    if sel.any():
        rep["thickness_after_weak_structures"] = thin_report(np.where(sel, th1, np.inf))
        rep["thickness_after_weak_structures"]["samples"] = int(sel.sum())
    else:
        rep["thickness_after_weak_structures"] = {"samples": 0}
    log(sp, "最终", rep["final_topology"], rep["size_mm"], "壁厚", rep["thickness_after"],
        "| 不计底部 1 mm", rep["thickness_after_excl_bottom_1mm"],
        "| 薄弱结构上", rep["thickness_after_weak_structures"])

    final.export(d / "print.stl")
    trimesh.Scene({sp: final}).export(d / "print.3mf")
    rep["stl_bytes"] = (d / "print.stl").stat().st_size
    rep["3mf_bytes"] = (d / "print.3mf").stat().st_size
    (d / "print_report.json").write_text(json.dumps(rep, ensure_ascii=False, indent=2), encoding="utf-8")
    log(sp, "完成 STL %.1f MB / 3MF %.1f MB" % (rep["stl_bytes"] / 1e6, rep["3mf_bytes"] / 1e6))
    return rep


if __name__ == "__main__":
    for s in sys.argv[1:]:
        process(s)
