import { AnimatePresence, motion } from "framer-motion";
import { useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { sceneById, type EvKind, type OptKey } from "../data";
import { buildGame, buildRec, PATHS, type DemoPath, type DemoStep } from "../game/demo";
import { iconsOf, profileOf, type Profile } from "../game/engine";
import { handoffOf } from "../game/handoff";
import { badge, PLANS, REASONS, sp, type Reason } from "../game/meta";
import { useGame } from "../game/store";
import { sfx } from "../lib/sound";
import { ExampleTag, SpeciesAvatar } from "../ui/kit";
import { QubeHandoff } from "../screens/Ending";
import { Coin } from "../screens/Station";

const EVS: { k: EvKind; cn: string }[] = [{ k: "price", cn: "量价" }, { k: "data", cn: "数据" }, { k: "news", cn: "消息" }, { k: "tip", cn: "锦囊" }];
const mini = { fontSize: 12, padding: "3px 9px" } as const;

const spName = (p: Profile) => (p.species ? sp(p.species).cn : `${p.tied.map((t) => sp(t).cn).join(" / ")}`);

function diffsOf(p0: Profile, p: Profile, q0: string, q: string): string[] {
  const out: string[] = [];
  if (spName(p0) !== spName(p)) out.push(`物种：${spName(p0)} → ${spName(p)}`);
  if (p0.confidence !== p.confidence) out.push(`把握：${p0.confidence} → ${p.confidence}`);
  if (p0.rec.main.id !== p.rec.main.id) out.push(`推荐：${p0.rec.main.cn} → ${p.rec.main.cn}`);
  if (p0.rec.extra?.id !== p.rec.extra?.id) out.push(`加推：${p0.rec.extra?.cn || "无"} → ${p.rec.extra?.cn || "无"}`);
  const add = p.badges.filter((b) => !p0.badges.includes(b));
  const del = p0.badges.filter((b) => !p.badges.includes(b));
  if (add.length) out.push(`新徽章：${add.map((b) => badge(b).cn).join("、")}`);
  if (del.length) out.push(`失去徽章：${del.map((b) => badge(b).cn).join("、")}`);
  p.claims.forEach((c, i) => {
    const c0 = p0.claims[i];
    if (c0 && c0.level !== c.level) out.push(`${c.dim}：${c0.level} → ${c.level}`);
  });
  if (q0 !== q) out.push("Qube 一句话策略换了一句");
  return out;
}

export function DemoPage() {
  const nav = useNavigate();
  const [pid, setPid] = useState(PATHS[0].id);
  const [edits, setEdits] = useState<Record<string, DemoPath>>({});
  const orig = PATHS.find((x) => x.id === pid)!;
  const cur = edits[pid] || orig;
  const g0 = useMemo(() => buildGame(orig), [orig]);
  const g = useMemo(() => buildGame(cur), [cur]);
  const p0 = useMemo(() => profileOf(g0), [g0]);
  const p = useMemo(() => profileOf(g), [g]);
  const h0 = useMemo(() => handoffOf(g0), [g0]);
  const h = useMemo(() => handoffOf(g), [g]);
  const overview = useMemo(() => PATHS.map((x) => ({ x, p: profileOf(buildGame(x)) })), []);
  const changed = cur !== orig;
  const diffs = changed ? diffsOf(p0, p, h0.prompt, h.prompt) : [];

  const setStep = (i: number, patch: Partial<DemoStep>) => {
    sfx.tap();
    setEdits((e) => ({ ...e, [pid]: { ...cur, steps: cur.steps.map((s, j) => (j === i ? { ...s, ...patch } : s)) } }));
  };
  const openEnding = () => {
    const now = useGame.getState().g;
    if (now && now.phase !== "ending" && !now.id.startsWith("demo") && !confirm("会覆盖这台手机上没玩完的一局，继续吗？")) return;
    useGame.setState({ g: buildGame(cur) });
    nav("/play");
  };

  return (
    <div className="screen">
      <div className="pad" style={{ background: "#2A2A1C", color: "#FBF4E4" }}>
        <div className="row between"><span className="panda-tag" style={{ background: "#F3D27F", color: "#2A2A1C" }}>评委演示台</span><button className="btn sm ghost" style={{ color: "#FBF4E4", borderColor: "#77745A" }} onClick={() => nav("/")}>回首页</button></div>
        <h1 className="display" style={{ fontSize: 34, margin: "12px 0 0", color: "#F3D27F" }}>同一个画像引擎，五种玩家</h1>
        <p className="small mt8" style={{ color: "#e9e2cc" }}>五位模拟玩家走同样的名场面。改任何一个选择，物种、画像和推荐都会当场重算。用的是真实玩家同一个函数，结果不是预先写好的。</p>
        <ExampleTag>模拟玩家 · 示例数据</ExampleTag>
      </div>

      <div className="pad col gap12">
        <div className="card" style={{ padding: 10 }}>
          <div className="kicker mb8">五条路径，五种结果</div>
          <table className="ptable">
            <thead><tr><th style={{ textAlign: "left" }}>玩家</th><th>游戏里像</th><th>推荐</th></tr></thead>
            <tbody>
              {overview.map(({ x, p: pp }) => (
                <tr key={x.id} className={x.id === pid ? "me" : ""} style={{ cursor: "pointer" }} onClick={() => { sfx.tap(); setPid(x.id); }}>
                  <td style={{ textAlign: "left" }}><b>{x.name}</b><div className="tiny">自评：{sp(x.self).cn}</div></td>
                  <td>{spName(pp)}<div className="tiny">{pp.confidence}{pp.hidden ? ` · 隐藏${sp(pp.hidden).cn}` : ""}</div></td>
                  <td className="small">{pp.rec.main.cn.replace(/ · .*/, "")}{pp.rec.extra ? <div className="tiny">+ {pp.rec.extra.cn.replace(/ · .*/, "")}</div> : null}</td>
                </tr>
              ))}
            </tbody>
          </table>
          <div className="tiny mt4">点一行，下面换成这位玩家。</div>
        </div>

        <div className="card">
          <div className="row between"><b className="h3">{cur.name}</b><span className="pill">自评：{sp(cur.self).cn}</span></div>
          <div className="small muted mt4">{cur.who}</div>
          <div className="tiny mt4">试试改一个关键选择，比如把某一场的理由换掉，看右边哪些结论跟着变。</div>
        </div>

        {cur.steps.map((st, i) => {
          const s = sceneById(st.scene)!;
          const rec = buildRec(cur, st);
          const why = iconsOf(rec).why;
          const o0 = orig.steps[i];
          const hot = (k: keyof DemoStep) => JSON.stringify(o0[k]) !== JSON.stringify(st[k]);
          return (
            <div key={st.scene} className={`card s-${s.season}`} style={{ padding: 12 }}>
              <div className="row between">
                <div><span className="pill" style={{ background: "var(--season)", color: "#fff8ec" }}>{s.season_cn}</span> <b className="small">{s.title.split(" · ")[0]}</b></div>
                <div className="row gap6"><Coin id={rec.coin!} half={rec.coinHalf} size={40} spin={false} /></div>
              </div>
              <div className="tiny bold mt8" style={{ color: hot("ev") ? "#D4432A" : undefined }}>看了哪些证据（按顺序）</div>
              <div className="row wrap gap6 mt4">
                {EVS.map(({ k, cn }) => {
                  const idx = st.ev.indexOf(k);
                  return <button key={k} className={"chip" + (idx >= 0 ? " on" : "")} style={mini} onClick={() => setStep(i, { ev: idx >= 0 ? st.ev.filter((x) => x !== k) : [...st.ev, k] })}>{idx >= 0 ? `${idx + 1}. ` : ""}{cn}</button>;
                })}
              </div>
              <div className="tiny bold mt8" style={{ color: hot("option") ? "#D4432A" : undefined }}>怎么做</div>
              <div className="row wrap gap6 mt4">
                {s.options.map((o) => <button key={o.key} className={"chip" + (st.option === o.key ? " on" : "")} style={mini} onClick={() => setStep(i, { option: o.key as OptKey })}>{o.key} {o.label}</button>)}
              </div>
              <div className="tiny bold mt8" style={{ color: hot("reason") ? "#D4432A" : undefined }}>理由</div>
              <div className="row wrap gap6 mt4">
                {REASONS.filter((r) => r.id !== "rule" || (cur.rules || []).length).map((r) => (
                  <button key={r.id} className={"chip" + (st.reason === r.id ? " on" : "")} style={mini} onClick={() => setStep(i, { reason: r.id as Reason, ruleId: r.id === "rule" ? st.ruleId || cur.rules?.[0] : st.ruleId })}>{r.cn}</button>
                ))}
              </div>
              <div className="row wrap gap6 mt8" style={{ alignItems: "center" }}>
                <span className="tiny bold" style={{ color: hot("plan") ? "#D4432A" : undefined }}>计划</span>
                {PLANS.map((pl) => <button key={pl.id} className={"chip" + (st.plan === pl.id ? " on" : "")} style={mini} onClick={() => setStep(i, { plan: pl.id })}>{pl.cn}</button>)}
                <button className={"chip" + (st.recognized ? " on" : "")} style={{ ...mini, color: hot("recognized") ? "#D4432A" : undefined }} onClick={() => setStep(i, { recognized: !st.recognized })}>认出来了</button>
              </div>
              <div className="dash mt8 mb8" />
              <div className="tiny">{why.length ? why.map((w) => `${sp(w.species).cn} +${w.n}：${w.text}`).join("；") : "没有物种图标（理由是直觉或看不懂，也没看量价、数据、消息）"}{why.length && rec.coin && !(iconsOf(rec).icons[rec.coin]) ? "；打平或没有图标，按补测牌" : ""}</div>
            </div>
          );
        })}

        <div className="card" style={{ borderWidth: 3, boxShadow: "5px 5px 0 #D4432A" }}>
          <div className="kicker">实时结果</div>
          <div className="row gap12 mt8" style={{ alignItems: "center" }}>
            <SpeciesAvatar id={p.species || p.tied[0] || "owl"} size={64} />
            <div>
              <div className="display" style={{ fontSize: 30 }}>{spName(p)}</div>
              <div className="row gap6 wrap"><span className="pill dark">{p.confidence}</span>{p.hidden && <span className="pill warn">隐藏：{sp(p.hidden).cn}</span>}<span className="pill">自评 {sp(cur.self).cn}{p.twoYou.same ? " · 一致" : " · 不一致"}</span></div>
            </div>
          </div>
          <div className="small mt8"><b>徽章（能力）：</b>{p.badges.length ? p.badges.map((b) => badge(b).cn).join("、") : "还没有"}</div>
          <AnimatePresence>
            {changed && (
              <motion.div initial={{ opacity: 0, y: -6 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }} className="card flat mt8" style={{ background: "#FFF4D6", padding: 10 }}>
                <b className="small">和原路径相比</b>
                {diffs.length ? <ul className="small" style={{ margin: "4px 0 0", paddingLeft: 18 }}>{diffs.map((d) => <li key={d}>{d}</li>)}</ul>
                  : <div className="small mt4">改了，但结论没变：这一处证据还推翻不了原来的判断。</div>}
              </motion.div>
            )}
          </AnimatePresence>
          <div className="dash mt12 mb8" />
          <div className="row between"><b className="small">推荐</b><span className="pill dark">{p.rec.main.cn}</span></div>
          <ul className="small" style={{ margin: "4px 0 0", paddingLeft: 18 }}>{p.rec.because.map((b) => <li key={b}>因为{b}</li>)}</ul>
          <div className="small mt4"><b>当场能做：</b>{p.rec.main.now}</div>
          {p.rec.extra && <div className="small mt4"><b>加推：</b>{p.rec.extra.cn}</div>}
          {p.rec.notNow.length > 0 && <div className="tiny mt4">暂时不推荐：{p.rec.notNow.map((n) => `${n.name}（${n.reason}）`).join("；")}</div>}
          <div className="dash mt12 mb8" />
          <b className="small">画像（能力 / 偏好 / 习惯，和把握）</b>
          <table className="ptable mt4">
            <tbody>
              {p.claims.map((c) => (
                <tr key={c.dim}>
                  <td style={{ textAlign: "left" }}>{c.dim}<div className="tiny">{c.kind}</div></td>
                  <td className="small">{c.level}</td>
                  <td className="tiny" style={{ whiteSpace: "nowrap" }}>{Math.round(c.confidence * 100)}%{c.status === "待确认" && <div>待确认</div>}</td>
                </tr>
              ))}
            </tbody>
          </table>
          {p.pending.length > 0 && <div className="tiny mt4">待确认：{p.pending.join("；")}</div>}
        </div>

        <QubeHandoff h={h} compact />

        <div className="row gap8">
          <button className="btn grow" disabled={!changed} onClick={() => { sfx.tap(); setEdits((e) => { const n = { ...e }; delete n[pid]; return n; }); }}>重置这位玩家</button>
          <button className="btn primary grow" onClick={openEnding}>看 TA 的终局页</button>
        </div>
        <div className="tiny center">模拟玩家与示例数据，只用来演示画像和推荐引擎。行情为真实历史数据。投资者教育游戏，不构成投资建议。</div>
      </div>
    </div>
  );
}
