import { AnimatePresence, motion } from "framer-motion";
import { toPng } from "html-to-image";
import QRCode from "qrcode";
import { useEffect, useMemo, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { ART, qrById, sceneById } from "../data";
import { suggestNext } from "../game/adaptive";
import { profileJson, profileOf, type Profile } from "../game/engine";
import { handoffOf, QUBE_URL, type Handoff } from "../game/handoff";
import { badge, BADGES, sp, type SpeciesId } from "../game/meta";
import { useGame, type Game } from "../game/store";
import { sfx } from "../lib/sound";
import { Fade, Glyph, Money, Sheet, SpeciesAvatar } from "../ui/kit";
import { enterQuickScene } from "./Quick";
import { Coin } from "./Station";
import { TaskNow } from "./TaskNow";

const BASE_URL = "https://meetmind.online/ts/";

const CN_NUM = ["零", "一", "两", "三", "四", "五", "六"];
const cnNum = (n: number) => CN_NUM[n] || String(n);

type Tab = "next" | "profile" | "score";
const TABS: [Tab, string, string][] = [
  ["next", "PandaAI 下一步", "根据你在游戏里的做法生成，接到 PandaAI 的真实工具上。"],
  ["profile", "画像依据", "分清能力和偏好，每条判断都标出依据和把握。"],
  ["score", "输赢", "物种没有输赢，赢的是方法和结果都不错的人。"],
];

function Hatch({ p, onDone, kicker = "四季走完 · 终局" }: { p: Profile; onDone: () => void; kicker?: string }) {
  const [stage, setStage] = useState(0);
  useEffect(() => {
    const ts = [setTimeout(() => { setStage(1); sfx.crack(); }, 900), setTimeout(() => { setStage(2); sfx.crack(); }, 1800), setTimeout(() => { setStage(3); sfx.fanfare(); }, 2600), setTimeout(onDone, 3600)];
    return () => ts.forEach(clearTimeout);
  }, []);
  const main = p.species || p.tied[0];
  return (
    <div className="screen" style={{ background: "#2A2A1C", display: "grid", placeItems: "center", color: "#FBF4E4" }}>
      <div className="center">
        <div className="kicker" style={{ color: "#F3D27F" }}>{kicker}</div>
        <div style={{ height: 300, display: "grid", placeItems: "center" }}>
          <AnimatePresence mode="wait">
            {stage < 3 ? (
              <motion.svg key="egg" viewBox="0 0 120 150" width="170" animate={{ rotate: stage ? [0, -8, 8, -6, 6, 0] : [0, -3, 3, 0] }} transition={{ repeat: Infinity, duration: stage ? 0.5 : 1.2 }} exit={{ scale: 1.6, opacity: 0 }}>
                <path d="M60 6 C92 6 112 56 112 88 C112 122 88 144 60 144 C32 144 8 122 8 88 C8 56 28 6 60 6 Z" fill="#FBF4E4" stroke="#F3D27F" strokeWidth="5" />
                <path d="M22 80 l12 -10 l12 13 l14 -14 l14 14 l12 -13 l12 10" fill="none" stroke="#D4432A" strokeWidth="6" strokeLinecap="round" strokeLinejoin="round" />
                {stage >= 1 && <path d="M60 20 l-8 18 l10 8 l-6 16" fill="none" stroke="#2A2A1C" strokeWidth="3" />}
                {stage >= 2 && <path d="M80 30 l6 16 l-10 10 l8 14 M40 40 l-6 14 l10 8" fill="none" stroke="#2A2A1C" strokeWidth="3" />}
              </motion.svg>
            ) : p.species || p.tied.length < 2 ? (
              <motion.div key="sp" initial={{ scale: 0.3, opacity: 0, y: 40 }} animate={{ scale: 1, opacity: 1, y: 0 }} transition={{ type: "spring", stiffness: 180, damping: 12 }}>
                {main && <img src={ART(`fig_${main}`)} alt="" style={{ height: 280, filter: "drop-shadow(0 0 30px rgba(243,210,127,.6))" }} />}
              </motion.div>
            ) : (
              <motion.div key="tied" style={{ display: "flex", flexWrap: "wrap", justifyContent: "center", alignItems: "flex-end", width: 340, gap: 2 }}>
                {p.tied.map((t, i) => (
                  <motion.img key={t} src={ART(`fig_${t}`)} alt="" initial={{ scale: 0.3, opacity: 0, y: 40 }} animate={{ scale: 1, opacity: 1, y: 0 }} transition={{ type: "spring", stiffness: 200, damping: 12, delay: i * 0.14 }}
                    style={{ height: p.tied.length > 2 ? 136 : 220, filter: "drop-shadow(0 0 22px rgba(243,210,127,.5))" }} />
                ))}
              </motion.div>
            )}
          </AnimatePresence>
        </div>
        <div className="display" style={{ fontSize: 26 }}>{stage < 3 ? "你的蛋在动……" : p.species ? `${sp(p.species).cn}！` : p.tied.length > 2 ? `${p.tied.length} 种都像你` : "两只都像你"}</div>
      </div>
    </div>
  );
}

export function ModelOrFigure({ id }: { id: SpeciesId }) {
  const [has3d, setHas3d] = useState(false);
  const [show3d, setShow3d] = useState(false);
  const src = `${import.meta.env.BASE_URL}models/${id}.glb`;
  useEffect(() => {
    fetch(src, { method: "HEAD" }).then((r) => setHas3d(r.ok && (r.headers.get("content-type") || "").includes("model") || (r.ok && Number(r.headers.get("content-length") || 0) > 10000))).catch(() => {});
  }, [id]);
  useEffect(() => {
    if (show3d) import("@google/model-viewer");
  }, [show3d]);
  return (
    <div style={{ position: "relative" }}>
      {show3d ? (
        // @ts-ignore 自定义元素
        <model-viewer src={src} auto-rotate camera-controls exposure="1.05" shadow-intensity="1" style={{ width: "100%", height: 320, background: "transparent" }} />
      ) : (
        <motion.img src={ART(`fig_${id}`)} alt={sp(id).cn} initial={{ y: 20, opacity: 0 }} animate={{ y: 0, opacity: 1 }} style={{ height: 300, margin: "0 auto", filter: "drop-shadow(6px 8px 0 rgba(42,42,28,.25))" }} />
      )}
      {has3d && <button className="btn sm dark" style={{ position: "absolute", right: 0, bottom: 14, color: "#F3D27F" }} onClick={() => { sfx.tap(); setShow3d(!show3d); }}>{show3d ? "看插画" : "转一转 3D 手办"}</button>}
    </div>
  );
}

const DROP = ["卖了", "拿着没动", "加仓了", "还没遇到过"];
const BUY = ["看走势", "看估值和财报", "看新闻消息", "朋友或群里推荐", "按自己的规则", "凭感觉", "还没买过"];

export function Ending({ archive = false }: { archive?: boolean }) {
  const { g, update, reset } = useGame();
  const nav = useNavigate();
  const [hatched, setHatched] = useState(archive);
  const p = useMemo(() => {
    const x = profileOf(g!);
    if (g?.verdict) {
      x.species = g.verdict.species;
      x.tied = [];
    }
    return x;
  }, [g]);
  const [shareOpen, setShareOpen] = useState(false);
  const [jsonOpen, setJsonOpen] = useState(false);
  const [openClaim, setOpenClaim] = useState<string | null>(null);
  const [tab, setTab] = useState<Tab>("next");
  if (!g) return null;
  const done = g.seasons.filter((r) => r.coin);
  const quick = g.mode === "quick";
  if (!hatched && g.source === "h5") return <Hatch p={p} kicker={quick ? `${cnNum(done.length)}场走完 · 初步画像` : undefined} onDone={() => setHatched(true)} />;
  const main = p.species || p.tied[0] || "owl";
  const m = sp(main);
  const basis = p.claims.find((c) => c.dim === "决策依据")?.level;
  const go = (t: Tab) => {
    sfx.paper();
    setTab(t);
    const el = document.getElementById("ending-tabs");
    if (el && el.getBoundingClientRect().top < 0) el.scrollIntoView({ behavior: "smooth", block: "start" });
  };
  return (
    <div className="screen">
      <div className="pad" style={{ background: m.color, color: "#FBF4E4", paddingBottom: 0, borderBottom: "3px solid #2A2A1C", position: "relative", overflow: "hidden" }}>
        <img src={ART(`species_${main}`)} alt="" className="abs-fill" style={{ width: "100%", height: "100%", objectFit: "cover", opacity: 0.28, filter: "blur(2px)" }} />
        <div style={{ position: "relative" }}>
          <div className="row between">
            <span className="pill" style={{ background: "#F3D27F" }}>你的交易物种</span>
            <span className="pill dark">{p.confidence}</span>
          </div>
          <h1 className="display" style={{ fontSize: p.species ? 66 : p.tied.length > 2 ? 58 : 50, margin: "12px 0 0", textShadow: "4px 4px 0 #2A2A1C" }}>{p.species ? m.cn : p.tied.length > 2 ? "还没定型" : p.tied.map((t) => sp(t).cn).join(" / ")}</h1>
          <div className="h3 mt4">{p.species ? m.tagline : p.tied.length > 2 ? `待确认：${p.tied.length} 种物种各 ${p.coins[p.tied[0]] ?? 1} 枚，物种牌并排放` : "待确认：两张物种牌并排放"}</div>
          {basis && basis !== "—" && <div className="small bold mt4" style={{ color: "#F3D27F", textShadow: "0 1px 4px rgba(0,0,0,.4)" }}>依据：{basis}</div>}
          {!p.species && p.tied.length > 2 && (
            <div className="row gap6 mt8">{p.tied.map((t) => <span key={t} className="row gap4 pill" style={{ background: "#FBF4E4", color: "#2A2A1C", padding: "2px 10px 2px 2px" }}><SpeciesAvatar id={t} size={26} />{sp(t).cn}</span>)}</div>
          )}
          {p.hidden && <div className="pill mt8" style={{ background: "#2A2A1C", color: "#F3D27F" }}>隐藏特质：{sp(p.hidden).cn} · {sp(p.hidden).tagline}</div>}
          <div className="mt12" style={{ position: "relative" }}>
            <ModelOrFigure id={main} />
            <button className="btn sm primary" style={{ position: "absolute", left: 0, bottom: 14 }} onClick={() => { sfx.tap(); setShareOpen(true); }}>存分享图</button>
          </div>
        </div>
      </div>
      <div className="pad col gap16">
        <Fade>
          <div className="card">
            <div className="kicker">{cnNum(done.length)}枚物种币 = {cnNum(done.length)}条证据</div>
            <div className="row between mt12">
              {done.map((r) => (
                <div key={r.season} className="center" style={{ width: "24%" }}>
                  <div style={{ display: "grid", placeItems: "center" }}><Coin id={r.coin!} half={r.coinHalf} size={70} spin={false} /></div>
                  <div className="tiny mt4">{sceneById(r.scene!)!.season_cn} · {sceneById(r.scene!)!.title.split(" · ")[0]}{r.coinHalf ? " · 半" : ""}{r.coinChanged ? " · 改" : ""}</div>
                </div>
              ))}
            </div>
            <div className="small mt12">{g.verdict ? `AI 综合各季在行情里的操作，判断你是${m.cn}（${g.verdict.title}）；物种币是每一季单独的证据，可以和它不一样。` : p.species ? `${m.cn}有 ${p.coins[main]} 枚：${p.confidence}。` : "最多的物种并列，写进“待确认”。"}物种只表示偏好，不分高低；能力用徽章单独看。</div>
          </div>
        </Fade>
        {quick && <QuickNext g={g} />}
        <div id="ending-tabs" className="tabs" style={{ scrollMarginTop: 0 }}>
          {TABS.map(([id, cn]) => (
            <button key={id} className={"tab" + (tab === id ? " on" : "")} onClick={() => go(id)}>{cn}</button>
          ))}
        </div>
        <div className="tiny" style={{ marginTop: -8 }}>{TABS.find((t) => t[0] === tab)![2]}</div>
        <AnimatePresence mode="wait">
        <motion.div key={tab} className="col gap16" initial={{ opacity: 0, x: 24 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -24 }} transition={{ duration: 0.22 }}>
        {tab === "next" && <>
        <QubeHandoff h={handoffOf(g)} />
        <Recommend p={p} />
        <TaskNow p={p} g={g} />
        <button className="btn block" onClick={() => go("profile")}>下一页：画像依据 →</button>
        </>}
        {tab === "profile" && <>
        <TwoYou g={g} p={p} onReal={(k, v) => update((x) => void (x.real = { ...(x.real || {}), [k]: v }))} />
        <Fade delay={0.2}>
          <div className="card">
            <div className="kicker">画像 · 每条判断都有依据</div>
            <div className="tiny mt4">能力 = 你会不会；偏好 = 你喜欢怎么做；习惯 = 你通常怎么做。“把握”是证据够不够，不是分数高低。</div>
            <div className="col mt8">
              {p.claims.map((c) => (
                <div key={c.dim} style={{ borderTop: "1.5px dashed rgba(42,42,28,.25)", padding: "10px 0" }}>
                  <button onClick={() => setOpenClaim(openClaim === c.dim ? null : c.dim)} style={{ all: "unset", cursor: "pointer", display: "block", width: "100%" }}>
                    <div className="row between">
                      <span className="bold">{c.dim} <span className="tiny">{c.kind}</span></span>
                      <span className="row gap6">
                        <span className={"pill" + (c.status === "待确认" ? " warn" : "")}>{c.level}</span>
                      </span>
                    </div>
                    <div className="row gap6 mt4">
                      <div style={{ flex: 1, height: 6, background: "rgba(42,42,28,.12)", borderRadius: 3, overflow: "hidden" }}>
                        <motion.div initial={{ width: 0 }} animate={{ width: `${c.confidence * 100}%` }} transition={{ duration: 0.8 }} style={{ height: "100%", background: c.confidence >= 0.6 ? "#2A2A1C" : "#C79A2E" }} />
                      </div>
                      <span className="tiny">把握 {Math.round(c.confidence * 100)}% · {openClaim === c.dim ? "收起" : "看依据"}</span>
                    </div>
                  </button>
                  <AnimatePresence>
                    {openClaim === c.dim && (
                      <motion.ul initial={{ height: 0, opacity: 0 }} animate={{ height: "auto", opacity: 1 }} exit={{ height: 0, opacity: 0 }} className="small" style={{ margin: "8px 0 0", paddingLeft: 18, overflow: "hidden" }}>
                        {c.evidence.map((e, i) => <li key={i}>{e}</li>)}
                        {c.next_probe && <li className="muted">下一步去哪里校准：{c.next_probe}</li>}
                      </motion.ul>
                    )}
                  </AnimatePresence>
                </div>
              ))}
            </div>
            <div className="card flat mt8" style={{ background: "#FFF4D6" }}>
              <b className="small">待确认</b>
              <ul className="small" style={{ margin: "4px 0 0", paddingLeft: 18 }}>{p.pending.map((x, i) => <li key={i}>{x}</li>)}</ul>
            </div>
            {(g.terms?.length || 0) > 0 && (
              <div className="mt8">
                <div className="small bold">你点开查过的词（{g.terms!.length} 个）</div>
                <div className="row wrap gap6 mt4">{g.terms!.slice(0, 12).map((t) => <span key={t} className="pill">{t}</span>)}</div>
                <div className="tiny mt4">查词是好习惯，不扣分。它帮我们分清“在等证据”和“信息没看懂”。</div>
              </div>
            )}
          </div>
        </Fade>
        <BadgesCard p={p} />
        <SpeciesCard p={p} id={main} />
        <button className="btn block" onClick={() => go("score")}>下一页：输赢 →</button>
        </>}
        {tab === "score" && <>
        <Score p={p} g={g} />
        <button className="btn block" onClick={() => go("next")}>回到：PandaAI 下一步</button>
        </>}
        </motion.div>
        </AnimatePresence>
        <div className="row gap8">
          <button className="btn primary big grow" onClick={() => { sfx.tap(); setShareOpen(true); }}>生成分享图</button>
          <button className="btn grow" onClick={() => setJsonOpen(true)}>画像 JSON</button>
        </div>
        <div className="row gap8">
          <button className="btn grow" onClick={() => { reset(); nav("/"); }}>再玩一局</button>
          <button className="btn ghost grow" onClick={() => nav("/atlas")}>物种图鉴</button>
        </div>
        <div className="tiny center">投资者教育游戏，不构成投资建议。你的游戏记录只保存在这台手机的浏览器里；分享图只有物种和徽章，不含任何行为记录。</div>
      </div>
      <ShareSheet open={shareOpen} onClose={() => setShareOpen(false)} p={p} />
      <Sheet open={jsonOpen} onClose={() => setJsonOpen(false)}>
        <div className="row between"><b className="h3">给 PandaAI 的结构化画像</b><button className="btn sm" onClick={() => copyText(JSON.stringify(profileJson(g, p), null, 2))}>复制</button></div>
        <p className="tiny mt4">每条判断都带依据、把握和来源。同一份结构可以交给 PandaAI 的回测、因子评估和模拟盘继续修正。格式示例，尚未接入平台。</p>
        <pre style={{ fontSize: 11, background: "#1f2a26", color: "#d9f0c8", padding: 12, borderRadius: 12, overflowX: "auto", maxHeight: "60vh" }}>{JSON.stringify(profileJson(g, p), null, 2)}</pre>
      </Sheet>
    </div>
  );
}

function copyText(s: string): Promise<void> {
  if (navigator.clipboard?.writeText) return navigator.clipboard.writeText(s);
  const ta = document.createElement("textarea");
  ta.value = s;
  ta.style.position = "fixed";
  ta.style.opacity = "0";
  document.body.appendChild(ta);
  ta.select();
  document.execCommand("copy");
  ta.remove();
  return Promise.resolve();
}

export function QubeHandoff({ h, compact = false }: { h: Handoff; compact?: boolean }) {
  const [copied, setCopied] = useState(false);
  return (
    <div className="card" style={{ background: "#2A2A1C", color: "#FBF4E4", borderWidth: 3, boxShadow: "5px 5px 0 #C79A2E" }}>
      <div className="row between gap8">
        <span className="panda-tag" style={{ background: "#F3D27F", color: "#2A2A1C" }}>PandaAI · Qube</span>
        <span className="tiny" style={{ color: "#cfc6a8", textAlign: "right" }}>一句话，把想法变成可回测的策略</span>
      </div>
      {!compact && <div className="h2 mt8" style={{ color: "#F3D27F" }}>你的第一条策略，已经写好了</div>}
      <div className="mt8" style={{ background: "#FBF4E4", color: "#2A2A1C", borderRadius: 12, padding: "12px 14px", border: "2px solid #F3D27F", fontSize: 15.5, lineHeight: 1.6, fontWeight: 600 }}>“{h.prompt}”</div>
      <div className="tiny mt8" style={{ color: "#cfc6a8" }}>为什么是这一句：{h.from}。</div>
      <div className="row gap8 mt12">
        <button className="btn grow" style={{ color: "#2A2A1C" }} onClick={() => { sfx.tap(); copyText(h.prompt).then(() => setCopied(true)).catch(() => {}); }}>{copied ? "已复制 ✓" : "复制这句话"}</button>
        <a className="btn primary grow" href={QUBE_URL} target="_blank" rel="noreferrer" onClick={() => copyText(h.prompt).catch(() => {})}>打开 Qube ↗</a>
      </div>
      <div className="tiny mt8" style={{ color: "#a9a48a" }}>游戏没有接入你的 PandaAI 账号：打开 Qube 后粘贴这句话，它会写成策略并回测。</div>
    </div>
  );
}

function QuickNext({ g }: { g: Game }) {
  const { update } = useGame();
  const nx = suggestNext(g);
  const n = g.seasons.filter((r) => r.coin).length;
  return (
    <div className="card" style={{ borderWidth: 3, boxShadow: "5px 5px 0 #D4432A" }}>
      <div className="row between"><div className="kicker">画像还很初步</div><span className="pill warn">只看了 {n} 场</span></div>
      <div className="h3 mt8">{n === 1 ? "一次选择，说明不了一个人。" : "再来一场，画像会更准。"}</div>
      {nx ? (
        <>
          <div className="small mt4">{nx.why}</div>
          <div className={`card flat mt8 row gap10 s-${nx.scene.season}`} style={{ padding: 8, alignItems: "center" }}>
            <img src={ART(`blind_${nx.scene.id}`)} alt="" style={{ width: 64, height: 64, objectFit: "cover", borderRadius: 10, border: "2px solid #2A2A1C", flex: "none" }} />
            <div>
              <span className="pill" style={{ background: "var(--season)", color: "#fff8ec" }}>{nx.scene.season_cn} · {nx.scene.season_name}</span>
              <div className="bold mt4">{nx.scene.blind.headline}</div>
            </div>
          </div>
          <button className="btn primary big block mt12" onClick={() => { sfx.bell(); update((x) => enterQuickScene(x, nx.scene.id)); }}>再玩一场 · 约 3 分钟</button>
          <button className="btn ghost block mt8" onClick={() => { sfx.tap(); update((x) => { x.phase = "pick"; }); }}>我想自己挑一场</button>
        </>
      ) : <div className="small mt4">六个名场面都走完了。</div>}
      <div className="tiny mt8">每多一场，物种币多一枚，下面每条判断的“把握”也会跟着变。</div>
    </div>
  );
}

function BadgesCard({ p }: { p: Profile }) {
  return (
    <Fade delay={0.15}>
      <div className="card">
        <div className="kicker">徽章 · 能力和习惯（和物种分开）</div>
        <div className="row wrap gap8 mt12">
          {BADGES.map((b) => {
            const on = p.badges.includes(b.id);
            return (
              <div key={b.id} className="center" style={{ width: "30%", opacity: on ? 1 : 0.32 }}>
                <motion.div initial={on ? { scale: 0, rotate: -30 } : false} animate={{ scale: 1, rotate: 0 }} transition={{ type: "spring", delay: 0.3 }} style={{ display: "inline-block" }}>
                  <Glyph ch={b.glyph} size={50} color={on ? "#D4432A" : "#77745A"} filled={on} />
                </motion.div>
                <div className="small bold mt4">{b.cn}</div>
                <div className="tiny">{on ? "已获得" : b.desc}</div>
              </div>
            );
          })}
        </div>
      </div>
    </Fade>
  );
}

function SpeciesCard({ p, id }: { p: Profile; id: SpeciesId }) {
  const m = sp(id);
  return (
    <Fade delay={0.1}>
      <div className="card">
        <div className="row between"><div className="kicker">{p.species ? "" : "并列之一 · "}{m.cn}的样子</div><span className="pill">{m.plain || m.style}</span></div>
        {m.one && <div className="body mt8" style={{ fontWeight: 600 }}>{m.one}</div>}
        {m.looks && m.looks.length > 0 && (
          <ul className="small" style={{ margin: "8px 0 0", paddingLeft: 18 }}>{m.looks.map((l, i) => <li key={i}>{l}</li>)}</ul>
        )}
        <div className="col gap6 mt8 small">
          <div><b>擅长：</b>{m.strength}</div>
          <div><b>要留意：</b>{m.watch}</div>
        </div>
        <div className="tiny mt8">游戏里的表现，仅供参考；物种只说明偏好，不代表能力高低。</div>
      </div>
    </Fade>
  );
}

function TwoYou({ g, p, onReal }: { g: Game; p: Profile; onReal: (k: "drop" | "buy", v: string) => void }) {
  const self = g.self;
  const game = p.species || p.tied[0];
  const n = cnNum(g.seasons.filter((r) => r.coin).length);
  return (
    <Fade delay={0.18}>
      <div className="card" style={{ background: "#2D5F6B", color: "#FBF4E4" }}>
        <div className="kicker" style={{ color: "#F3D27F" }}>两个你</div>
        <div className="row mt12" style={{ alignItems: "stretch", gap: 10 }}>
          {[{ t: "你说的你", id: self }, { t: "游戏里的你", id: game }].map((x) => (
            <div key={x.t} className="center grow" style={{ background: "rgba(251,244,228,.1)", borderRadius: 12, padding: 10, border: "2px solid rgba(251,244,228,.4)" }}>
              <div className="tiny" style={{ color: "#cfe1e1" }}>{x.t}</div>
              {x.id ? <div style={{ display: "grid", placeItems: "center", marginTop: 6 }}><SpeciesAvatar id={x.id} size={64} /></div> : null}
              <div className="h3 mt4">{x.id ? sp(x.id).cn : "—"}</div>
            </div>
          ))}
        </div>
        <div className="small mt12">{p.twoYou.same ? `一致：你对自己的判断，和你在${n}个名场面里的做法对得上。` : !p.species ? `还没定型：${n}场里你在${p.tied.map((t) => sp(t).cn).join("、")}之间换来换去${self && p.tied.includes(self) ? `，其中就有你自评的${sp(self).cn}` : `，你自评的${self ? sp(self).cn : "—"}不在里面`}。牌并排放，不用急着选哪个是真的。` : `不一致：你觉得自己是${self ? sp(self).cn : "—"}，但${n}场里你的做法更像${game ? sp(game).cn : "—"}。两张牌并排放，不用急着选哪个是真的。`}</div>
        <div className="dash mt12 mb8" style={{ borderColor: "rgba(251,244,228,.4)" }} />
        <div className="small bold">两道现实题（只存在这台手机里）</div>
        <div className="small mt8">现实里你上一次遇到大跌，实际做了什么？</div>
        <div className="row wrap gap6 mt4">{DROP.map((d) => <button key={d} className={"chip" + (g.real?.drop === d ? " on" : "")} style={{ background: g.real?.drop === d ? "#F3D27F" : "rgba(251,244,228,.9)", color: "#2A2A1C" }} onClick={() => { sfx.tap(); onReal("drop", d); }}>{d}</button>)}</div>
        <div className="small mt12">你上一次买入，主要原因是什么？</div>
        <div className="row wrap gap6 mt4">{BUY.map((d) => <button key={d} className={"chip" + (g.real?.buy === d ? " on" : "")} style={{ background: g.real?.buy === d ? "#F3D27F" : "rgba(251,244,228,.9)", color: "#2A2A1C" }} onClick={() => { sfx.tap(); onReal("buy", d); }}>{d}</button>)}</div>
        <div className="tiny mt8" style={{ color: "#cfe1e1" }}>{p.twoYou.realLines.length > 0 ? "已记下。现实题会进入“风险姿态”，也会更新上面的推荐。" : "游戏里没有真钱。两道现实题帮我们校准：游戏里的你和现实里的你差多远。"}</div>
      </div>
    </Fade>
  );
}

function Recommend({ p }: { p: Profile }) {
  const t = p.rec.main;
  return (
    <Fade delay={0.22}>
      <div className="card" style={{ borderWidth: 3, boxShadow: "5px 5px 0 #D4432A" }}>
        <div className="row between"><div className="kicker">学习路线 · 推荐给你</div><span className="pill dark">{t.cn.split(" · ")[1] || "入门"}</span></div>
        <div className="h2 mt8">{t.cn.split(" · ")[0]}</div>
        <p className="body mt4" style={{ fontWeight: 600 }}>{t.now}</p>
        <div className="small bold mt12">为什么推荐给你</div>
        <ul className="small" style={{ margin: "4px 0 0", paddingLeft: 18 }}>{p.rec.because.map((b, i) => <li key={i}>因为{b.replace(/^你/, "你")}</li>)}</ul>
        <div className="col gap8 mt12">
          {t.resources.map((r) => (
            <a key={r.name} href={r.url} target="_blank" rel="noreferrer" className="card flat" style={{ textDecoration: "none", padding: "10px 12px", background: "#FBF4E4" }}>
              <div className="row between"><b className="small">{r.name}</b><span className="tiny">{r.kind} ↗</span></div>
              {r.note && <div className="tiny mt4">{r.note}</div>}
              {r.example && <div className="tiny mt4">示例入口，具体课程待选</div>}
            </a>
          ))}
        </div>
        {p.rec.extra && (
          <div className="card flat mt12" style={{ background: "#FFF4D6" }}>
            <b className="small">另加一张：{p.rec.extra.cn}</b>
            <div className="small mt4">{p.rec.extra.now}</div>
            {p.rec.extra.resources.slice(0, 1).map((r) => <a key={r.name} href={r.url} target="_blank" rel="noreferrer" className="tiny" style={{ display: "block", marginTop: 4 }}>{r.name} ↗</a>)}
          </div>
        )}
        {p.rec.notNow.length > 0 && (
          <div className="mt12">
            <div className="small bold">暂时不推荐</div>
            {p.rec.notNow.map((n) => <div key={n.name} className="small muted">· {n.name}：{n.reason}</div>)}
          </div>
        )}
      </div>
    </Fade>
  );
}

function Score({ p, g }: { p: Profile; g: Game }) {
  if (!p.score.ais.length) {
    return (
      <Fade delay={0.26}>
        <div className="card">
          <div className="kicker">这一局的输赢</div>
          <div className="row gap16 mt8">
            <div><div className="tiny">方法星</div><div className="display" style={{ fontSize: 34 }}>★{p.score.stars}</div></div>
            <div><div className="tiny">终局资金</div><div className="display" style={{ fontSize: 34 }}><span className={g.money < 0 ? "down" : ""}>{g.money}</span><small style={{ fontSize: 16 }}> 万</small></div><div className="tiny">开局 20 万 · {g.money >= 20 ? "+" : "−"}{Math.abs(g.money - 20)} 万</div></div>
          </div>
          <div className="tiny mt8">终局分 = 方法星 + 资金名次分（第一 6 分、第二 4 分、第三 2 分、其余 1 分，亏光倒欠 0 分）。</div>
        </div>
      </Fade>
    );
  }
  const rows = [{ id: "me", name: "你", money: g.money, stars: p.score.stars, score: p.score.me }, ...p.score.ais.map((a) => ({ id: a.id, name: sp(a.id).cn, money: a.money, stars: a.stars, score: a.score }))].sort((a, b) => b.score - a.score);
  return (
    <Fade delay={0.26}>
      <div className="card">
        <div className="row between"><div className="kicker">这一局的输赢</div><span className={"pill " + (p.score.win ? "dark" : "warn")}>{p.score.win ? "你赢了" : `第 ${p.score.rank} 名`}</span></div>
        <table className="ptable mt8">
          <thead><tr><th>玩家</th><th>资金（万）</th><th>方法星</th><th>终局分</th></tr></thead>
          <tbody>
            {rows.map((r) => (
              <tr key={r.id} className={r.id === "me" ? "me" : ""}>
                <td className="row gap6">{r.id === "me" ? <b>你</b> : <><SpeciesAvatar id={r.id} size={22} />{r.name}</>}</td>
                <td><span className={r.money < 0 ? "down" : ""}>{r.money}</span></td>
                <td>★{r.stars}</td>
                <td><b>{r.score}</b></td>
              </tr>
            ))}
          </tbody>
        </table>
        <div className="tiny mt8">终局分 = 方法星 + 资金名次分（第一 6 分、第二 4 分、第三 2 分，亏光倒欠 0 分）。物种没有输赢，赢的是方法和结果都不错的人。</div>
      </div>
    </Fade>
  );
}

function ShareSheet({ open, onClose, p }: { open: boolean; onClose: () => void; p: Profile }) {
  const ref = useRef<HTMLDivElement>(null);
  const [img, setImg] = useState<string | null>(null);
  const [qr, setQr] = useState<string>("");
  const main = p.species || p.tied[0] || "owl";
  const m = sp(main);
  useEffect(() => {
    QRCode.toDataURL(qrById("start")?.url || BASE_URL, { margin: 1, width: 240, color: { dark: "#2A2A1C", light: "#FBF4E4" } }).then(setQr);
  }, []);
  useEffect(() => {
    if (!open || !qr) return;
    setImg(null);
    const t = setTimeout(async () => {
      if (!ref.current) return;
      try {
        const url = await toPng(ref.current, { pixelRatio: 3, cacheBust: true });
        setImg(url);
      } catch {
        setImg(null);
      }
    }, 400);
    return () => clearTimeout(t);
  }, [open, qr]);
  return (
    <Sheet open={open} onClose={onClose}>
      <div className="row between"><b className="h3">分享图</b><span className="tiny">只有物种和徽章，不含行为记录</span></div>
      <div style={{ position: "relative", marginTop: 12 }}>
        <div ref={ref} style={{ width: 360, height: 520, margin: "0 auto", background: "#F2E6CC", border: "3px solid #2A2A1C", borderRadius: 18, overflow: "hidden", position: "relative", fontFamily: "var(--body)" }}>
          <div style={{ height: 300, position: "relative", background: m.color }}>
            <img src={ART(`species_${main}`)} alt="" style={{ width: "100%", height: "100%", objectFit: "cover", objectPosition: "50% 15%" }} />
            <div style={{ position: "absolute", left: 14, top: 12, background: "#FBF4E4", border: "2px solid #2A2A1C", borderRadius: 999, padding: "3px 10px", fontSize: 12, fontWeight: 800 }}>交易物种起源</div>
          </div>
          <div style={{ height: 6, background: "#C79A2E", borderTop: "2px solid #2A2A1C", borderBottom: "2px solid #2A2A1C" }} />
          <div style={{ padding: "12px 16px" }}>
            <div style={{ fontSize: 12, color: "#4A4A33", fontWeight: 700 }}>走过金融史上的四个名场面，我是</div>
            <div style={{ fontFamily: "var(--display)", fontSize: p.species ? 46 : 34, lineHeight: 1.05 }}>{p.species ? m.cn : p.tied.length > 2 ? "还没定型的物种" : p.tied.map((t) => sp(t).cn).join(" / ")}</div>
            <div style={{ fontSize: 14, fontWeight: 700 }}>{p.species ? `${m.tagline} · ${p.confidence}` : `${p.tied.map((t) => sp(t).cn).join("、")}都像我 · 待确认`}</div>
            <div style={{ display: "flex", gap: 6, marginTop: 10, flexWrap: "wrap" }}>
              {p.badges.length ? p.badges.map((b) => (
                <span key={b} style={{ border: "2px solid #2A2A1C", borderRadius: 999, padding: "2px 8px", fontSize: 12, fontWeight: 800, background: "#FBF4E4" }}>{badge(b).cn}</span>
              )) : <span style={{ fontSize: 12, color: "#77745A" }}>徽章还在路上</span>}
              {p.hidden && <span style={{ border: "2px solid #2A2A1C", borderRadius: 999, padding: "2px 8px", fontSize: 12, fontWeight: 800, background: "#2A2A1C", color: "#F3D27F" }}>隐藏：{sp(p.hidden).cn}</span>}
            </div>
            <div style={{ position: "absolute", right: 14, bottom: 14, textAlign: "center" }}>
              {qr && <img src={qr} alt="" style={{ width: 74, height: 74, border: "2px solid #2A2A1C", borderRadius: 8 }} />}
              <div style={{ fontSize: 9, fontWeight: 700, marginTop: 2 }}>扫码测你的物种</div>
            </div>
            <div style={{ position: "absolute", left: 16, bottom: 12, fontSize: 9, color: "#77745A" }}>投资者教育游戏，不构成投资建议</div>
          </div>
        </div>
        {img && <img src={img} alt="分享图" style={{ position: "absolute", inset: 0, width: 360, height: 520, margin: "0 auto", borderRadius: 18 }} />}
      </div>
      <div className="tiny center mt8">{img ? "长按图片保存，或者点下面的按钮下载" : "正在生成……"}</div>
      <div className="row gap8 mt12">
        {img && <a className="btn primary grow" href={img} download={`交易物种-${m.cn}.png`}>下载图片</a>}
        <button className="btn grow" onClick={onClose}>关闭</button>
      </div>
    </Sheet>
  );
}
