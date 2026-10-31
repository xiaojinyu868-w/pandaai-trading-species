import { AnimatePresence, motion } from "framer-motion";
import { useEffect, useRef, useState } from "react";
import { ART, sceneById, type EvKind, type Evidence, type OptKey, type Scene } from "../data";
import { RULES, ruleView } from "../game/cards";
import { EVENT_NAMES, sharesOf } from "../game/engine";
import { aiPick, PLANS, REASONS, reasonCn, sp, type Plan, type Reason } from "../game/meta";
import { cur, useGame, type SceneStep } from "../game/store";
import { buzz, sfx } from "../lib/sound";
import { EvChart, LineChart } from "../ui/Chart";
import { Hud } from "../ui/Hud";
import { DataStamp, SourceLine } from "../ui/DataStamp";
import { Fade, RP, Shares, Sheet, sleep, SpeciesAvatar, Steps } from "../ui/kit";
import { Help, Rich } from "../ui/Term";
import { FFStep } from "../scenes/FF";
import { STAGES } from "../scenes/stages";
import { RevealStep } from "./Reveal";

/** 情境、证据、出手合在交易台一屏里；老存档停在 evidence / slip 也进交易台 */
const STEP_AT: Record<SceneStep, number> = { blind: 0, evidence: 0, slip: 0, flip: 1, ff: 2, reveal: 3 };
const STEP_CN = ["下单", "亮牌", "快进", "揭幕"];
export const EV_CN: Record<EvKind, string> = { price: "量价", data: "数据", news: "消息", tip: "锦囊" };
export const EV_OBJ: Record<EvKind, string> = { price: "行情纸带", data: "账本", news: "电报", tip: "猫头鹰的信" };

export function SceneFlow({ onStation }: { onStation: () => void }) {
  const { g, update } = useGame();
  const top = useRef<HTMLDivElement>(null);
  const step = g?.step || "blind";
  useEffect(() => {
    window.scrollTo({ top: 0 });
  }, [step]);
  if (!g) return null;
  const rec = cur(g);
  const scene = sceneById(rec.scene!)!;
  const at = STEP_AT[g.step] ?? 0;
  const go = (s: SceneStep) => update((x) => void (x.step = s));
  return (
    <div className={`screen s-${scene.season}`} ref={top}>
      <Hud title={`${scene.season_cn} · ${STEP_CN[at]}`} />
      <div style={{ padding: "8px 14px 0" }}><Steps n={4} at={at} labels={STEP_CN} /></div>
      <AnimatePresence mode="wait">
        <motion.div key={at} initial={{ opacity: 0, x: 40 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -40 }} transition={{ duration: 0.3 }}>
          {at === 0 && <DeskStep scene={scene} onNext={() => go("flip")} />}
          {g.step === "flip" && <FlipStep scene={scene} onNext={() => go("ff")} />}
          {g.step === "ff" && <FFStep scene={scene} onNext={() => go("reveal")} />}
          {g.step === "reveal" && <RevealStep scene={scene} onNext={onStation} />}
        </motion.div>
      </AnimatePresence>
    </div>
  );
}

/* ---------------- 1 盲入场 ---------------- */
export function BlindView({ scene, compact = false }: { scene: Scene; compact?: boolean }) {
  const b = scene.blind;
  const vals = b.chart.values;
  return (
    <div>
      <div className="poster" style={{ height: compact ? 260 : "40vh", minHeight: 240 }}>
        <motion.img src={ART(`blind_${scene.id}`)} alt="" initial={{ scale: 1.15 }} animate={{ scale: 1 }} transition={{ duration: 1.6, ease: "easeOut" }} style={{ objectPosition: "50% 35%" }} />
        <div className="abs-fill" style={{ background: "linear-gradient(180deg, rgba(0,0,0,0) 55%, rgba(0,0,0,.45))" }} />
        <div style={{ position: "absolute", left: 12, top: 12 }} className="row gap6">
          <span className="pill season">{scene.season_cn} · {scene.season_name}</span>
          <span className="pill dark">名字和日期已隐藏</span>
        </div>
        <div style={{ position: "absolute", left: 14, bottom: 12, right: 14 }}>
          <motion.h2 className="display" style={{ color: "#FBF4E4", fontSize: 32, margin: 0, textShadow: "3px 3px 0 #2A2A1C" }} initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.4 }}>
            {b.headline}
          </motion.h2>
        </div>
      </div>
      <div className="col gap8 mt12">
        {b.lines.map((l, i) => (
          <Fade key={i} delay={0.5 + i * 0.25}><div className="row gap8" style={{ alignItems: "flex-start" }}><b className="display" style={{ color: "var(--season)", fontSize: 18 }}>{i + 1}</b><span className="body"><Rich text={l} /></span></div></Fade>
        ))}
      </div>
      <Fade delay={1.3}>
        <div className="card mt12" style={{ padding: "12px 12px 14px" }}>
          <div className="row between">
            <span className="tiny bold">走势 · {b.chart.label}</span>
            <span className="bold num">{vals[0].toFixed(0)} → <span className={vals[vals.length - 1] >= vals[0] ? "up" : "down"}>{vals[vals.length - 1].toFixed(0)}</span></span>
          </div>
          <LineChart values={vals} height={120} base={100} color="#2A2A1C" />
          <div className="mt8"><DataStamp scene={scene} phase="blind" /></div>
        </div>
      </Fade>
    </div>
  );
}

/* ---------------- 2 开证据 ---------------- */
const EV_ICON: Record<EvKind, string> = { price: "chart", data: "ledger", news: "phone", tip: "letter" };

export function EvidenceView({ ev, scene }: { ev: Evidence; scene: Scene }) {
  const k = ev.kind;
  if (k === "price") {
    return (
      <div style={{ background: "#1f2a26", color: "#e9f2ea", borderRadius: 16, border: "2px solid #2A2A1C", padding: 16, boxShadow: "4px 4px 0 #2A2A1C" }}>
        <div className="row between"><span className="pill" style={{ background: "#F3D27F" }}>量价 · 行情纸带</span>{ev.risk && <span className="pill" style={{ background: "#D4432A", color: "#fff" }}>风险</span>}</div>
        <div className="h2 mt8" style={{ color: "#F3D27F" }}>{ev.title}</div>
        {ev.stat && <div className="row gap8 mt8" style={{ alignItems: "baseline" }}><span className="display" style={{ fontSize: 44, color: "#ff8a6b" }}>{ev.stat.value}</span><span className="small" style={{ opacity: 0.8 }}><Rich text={ev.stat.caption} /></span></div>}
        <div className="mt8" style={{ background: "rgba(255,255,255,.04)", borderRadius: 8, padding: 6 }}><EvChart c={ev.chart} /></div>
        <ul className="body" style={{ paddingLeft: 18, margin: "10px 0 0" }}>{ev.lines.map((l, i) => <li key={i}><Rich text={l} /></li>)}</ul>
        <SourceLine text={ev.source} dark />
      </div>
    );
  }
  if (k === "data") {
    return (
      <div style={{ background: "repeating-linear-gradient(#FBF4E4 0 27px, #e2d3b0 27px 28px)", borderRadius: 16, border: "2px solid #2A2A1C", padding: 16, boxShadow: "4px 4px 0 #2A2A1C", position: "relative" }}>
        <div style={{ position: "absolute", left: 30, top: 0, bottom: 0, width: 2, background: "rgba(212,67,42,.45)" }} />
        <div style={{ paddingLeft: 26 }}>
          <div className="row between"><span className="pill">数据 · 账本</span>{ev.risk && <span className="pill" style={{ background: "#D4432A", color: "#fff" }}>风险</span>}</div>
          <div className="h2 mt8">{ev.title}</div>
          {ev.stat && <div className="row gap8 mt8" style={{ alignItems: "baseline" }}><span className="display" style={{ fontSize: 44, color: "#2D5F6B" }}>{ev.stat.value}</span><span className="small muted"><Rich text={ev.stat.caption} /></span></div>}
          <div className="mt8"><EvChart c={ev.chart} /></div>
          <ul className="body" style={{ paddingLeft: 18, margin: "10px 0 0" }}>{ev.lines.map((l, i) => <li key={i}><Rich text={l} /></li>)}</ul>
          <SourceLine text={ev.source} />
        </div>
      </div>
    );
  }
  if (k === "news") {
    return (
      <div style={{ background: "#f7eed8", borderRadius: 6, border: "2px solid #2A2A1C", padding: "18px 16px", boxShadow: "4px 4px 0 #2A2A1C", position: "relative" }}>
        <div style={{ height: 8, margin: "-18px -16px 12px", background: "repeating-linear-gradient(90deg, #D4432A 0 18px, #FBF4E4 18px 26px, #2D5F6B 26px 44px, #FBF4E4 44px 52px)", borderBottom: "2px solid #2A2A1C" }} />
        <div className="row between"><span className="pill dark">消息 · 电报</span>{ev.risk && <span className="pill" style={{ background: "#D4432A", color: "#fff" }}>风险</span>}</div>
        <div className="h2 mt8">{ev.title}</div>
        <div className="col gap8 mt8">
          {ev.lines.map((l, i) => (
            <motion.div key={i} initial={{ opacity: 0, x: -10 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.2 + i * 0.25 }}
              style={{ borderLeft: "4px solid #C79A2E", paddingLeft: 10, fontSize: 15.5, lineHeight: 1.6, fontWeight: 500 }}><Rich text={l} /></motion.div>
          ))}
        </div>
        {ev.stat && <div className="mt8 bold">{ev.stat.value} <span className="small muted"><Rich text={ev.stat.caption} /></span></div>}
        {ev.chart && <div className="mt8"><EvChart c={ev.chart} /></div>}
        <SourceLine text={ev.source} />
      </div>
    );
  }
  return (
    <div style={{ background: "#2D5F6B", color: "#FBF4E4", borderRadius: 16, border: "2px solid #2A2A1C", padding: 18, boxShadow: "4px 4px 0 #2A2A1C", position: "relative", overflow: "hidden" }}>
      <motion.div initial={{ scale: 1.6, rotate: -30, opacity: 0 }} animate={{ scale: 1, rotate: -8, opacity: 1 }} transition={{ type: "spring", stiffness: 200 }}
        style={{ position: "absolute", right: 14, top: 12, width: 54, height: 54, borderRadius: "50%", background: "#A8321E", border: "3px solid #7a2416", display: "grid", placeItems: "center", fontFamily: "var(--display)", fontSize: 24, color: "#F3D27F", boxShadow: "inset 0 0 0 4px rgba(255,255,255,.12)" }}>鹰</motion.div>
      <span className="pill" style={{ background: "#F3D27F" }}>锦囊 · 猫头鹰的信</span>
      <div className="h2 mt8">{ev.title}</div>
      <div className="col gap8 mt12">
        {ev.lines.map((l, i) => <div key={i} className="display" style={{ fontSize: 21, lineHeight: 1.45 }}>“<Rich text={l} />”</div>)}
      </div>
      <SourceLine text={ev.source} dark />
    </div>
  );
}

/* ---------------- 排队条（924 按顺序选） ---------------- */
function QueueStrip({ scene, n, me }: { scene: Scene; n: number; me?: boolean }) {
  const { g } = useGame();
  const ai = g!.opponents.filter((id) => ["A", "B"].includes(aiPick(id, scene.id).option));
  const crowd = 9;
  return (
    <div className="card" style={{ background: "#2A2A1C", color: "#FBF4E4", padding: 12 }}>
      <div className="row between"><b>排队开户的人</b><span className="pill" style={{ background: "#F3D27F" }}>已经有 {n} 个</span></div>
      <div className="row mt8" style={{ gap: 4, overflow: "hidden" }}>
        {Array.from({ length: crowd }).map((_, i) => (
          <motion.span key={i} initial={{ x: 60, opacity: 0 }} animate={{ x: 0, opacity: 1 }} transition={{ delay: i * 0.08 }}
            style={{ width: 22, height: 30, borderRadius: "11px 11px 4px 4px", background: ["#D4432A", "#C79A2E", "#4E8792", "#A3AE91"][i % 4], border: "2px solid #FBF4E4", flex: "none" }} />
        ))}
        {ai.map((id) => <SpeciesAvatar key={id} id={id} size={30} />)}
        {me && <motion.span initial={{ scale: 0 }} animate={{ scale: 1 }} className="pill" style={{ background: "#D4432A", color: "#fff" }}>你</motion.span>}
      </div>
      <div className="tiny mt8" style={{ color: "#cfc6a8" }}>{ai.length ? ai.map((id) => sp(id).cn).join("、") + "已经排进去了。" : "两位 AI 对手都没排队。"}你也排吗？</div>
    </div>
  );
}

const HEAT: Record<OptKey, string> = { A: "#D4432A", B: "#C79A2E", C: "#4E8792", D: "#8C8A70" };
const R_EV: Partial<Record<Reason, EvKind>> = { price: "price", data: "data", news: "news" };
const R_GLYPH: Partial<Record<Reason, string>> = { follow: "跟", gut: "感", lost: "?", rule: "规" };
const PLAN_IC: Record<Plan, string> = { cut: "走", add: "加", none: "—" };

function Coins({ n }: { n: number }) {
  return <span className="coins">{[0, 1, 2].map((i) => <i key={i} className={i < n ? "f" : ""} />)}</span>;
}

/* ---------------- 1 交易台：看盘、翻情报、下单，一屏做完 ---------------- */
const KINDS: EvKind[] = ["price", "data", "news", "tip"];
const nowShares = (scene: Scene) => (/空仓|闲钱/.test(scene.blind.position) ? 0 : 2);
const pctChg = (a: number, b: number) => (b / a - 1) * 100;
const pctTxt = (p: number) => `${p >= 0 ? "+" : "−"}${Math.abs(p).toFixed(1)}%`;

/** 下单按钮上的动词：按现在的持仓算是买、卖还是不动 */
function orderVerb(now: number, shares: number) {
  const d = shares - now;
  if (d > 0) return `买入 ${d} 份`;
  if (d < 0) return shares === 0 ? "全部卖出" : `卖出 ${-d} 份`;
  return now > 0 ? "拿着不动" : "先不买";
}

function DeskTop({ scene }: { scene: Scene }) {
  const { g, update } = useGame();
  const rec = cur(g!);
  const [open, setOpen] = useState(false);
  const [pick, setPick] = useState<string | null>(null);
  return (
    <>
      <div className="poster desk-top">
        <motion.img src={ART(`blind_${scene.id}`)} alt="" initial={{ scale: 1.15 }} animate={{ scale: 1 }} transition={{ duration: 1.4, ease: "easeOut" }} style={{ objectPosition: "50% 35%" }} />
        <div className="abs-fill" style={{ background: "linear-gradient(180deg, rgba(0,0,0,.05) 30%, rgba(0,0,0,.62))" }} />
        <div className="row gap6" style={{ position: "absolute", left: 10, top: 10, right: 10 }}>
          <span className="pill season">{scene.season_cn} · {scene.season_name}</span>
          <span className="grow" />
          <button className={"pill desk-rec" + (rec.recognized ? " on" : "")} onClick={() => { sfx.tap(); setOpen(true); }}>{rec.recognized ? "✓ 已申报" : "认出来了？"}</button>
        </div>
        <div style={{ position: "absolute", left: 12, right: 12, bottom: 10 }}>
          <motion.h2 className="display" style={{ color: "#FBF4E4", fontSize: 27, lineHeight: 1.15, margin: 0, textShadow: "2px 2px 0 #2A2A1C" }} initial={{ opacity: 0, y: 14 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.3 }}>
            {scene.blind.headline}
          </motion.h2>
          <span className="pill dark mt4" style={{ display: "inline-block" }}><Rich text={scene.blind.position} /></span>
        </div>
      </div>
      <Sheet open={open} onClose={() => setOpen(false)}>
        <div className="h3">认出这是哪一次了？</div>
        <p className="small mt4">知道结局就不算盲选。申报后：收益按 AI 平均记，物种币算半枚；猜对记一次金融史。</p>
        <div className="col gap6 mt12">
          {EVENT_NAMES.map((e) => (
            <button key={e.id} className={"opt" + (pick === e.id ? " on" : "")} style={{ gridTemplateColumns: "1fr", padding: "10px 14px", fontSize: 15 }} onClick={() => setPick(e.id)}>{e.name}</button>
          ))}
        </div>
        <div className="row gap8 mt12">
          {rec.recognized && <button className="btn ghost" onClick={() => { update((x) => void (cur(x).recognized = null)); setOpen(false); }}>撤回申报</button>}
          <button className="btn season grow" disabled={!pick} onClick={() => {
            sfx.stamp();
            update((x) => void (cur(x).recognized = { name: EVENT_NAMES.find((e) => e.id === pick)!.name, correct: pick === scene.id }));
            setOpen(false);
          }}>就是它（揭幕时见分晓）</button>
        </div>
      </Sheet>
    </>
  );
}

/** 快讯一条一条滚，点一下换下一条 */
function Ticker({ lines }: { lines: string[] }) {
  const [i, setI] = useState(0);
  useEffect(() => {
    const t = setInterval(() => setI((x) => (x + 1) % lines.length), 4200);
    return () => clearInterval(t);
  }, [lines.length, i]);
  return (
    <div className="ticker" onClick={() => { sfx.tick(); setI((x) => (x + 1) % lines.length); }}>
      <span className="ticker-tag">快讯</span>
      <AnimatePresence mode="wait">
        <motion.span key={i} className="ticker-text" initial={{ y: 12, opacity: 0 }} animate={{ y: 0, opacity: 1 }} exit={{ y: -12, opacity: 0 }} transition={{ duration: 0.22 }}>
          <Rich text={lines[i]} />
        </motion.span>
      </AnimatePresence>
      <span className="ticker-dots">{lines.map((_, k) => <i key={k} className={k === i ? "on" : ""} />)}</span>
    </div>
  );
}

/** 散户弹幕：虚构的股吧声音，做决定时的情绪压力 */
const CROWD: Record<string, string[]> = {
  s924: ["开户排了两小时", "节后必涨停", "我妈都问我怎么买股票", "满仓过节", "牛市来了", "放假前不上车就晚了", "这次不一样"],
  s2015: ["配资一比五", "这轮能到一万点", "辞职炒股了", "跑步进场", "借钱也要上", "菜市场都在聊股票", "下跌就是机会"],
  smt: ["核心资产不会跌", "拿住别卖", "基金经理是我偶像", "买了就是赚", "过完年继续涨", "贵有贵的道理"],
  scb: ["又熔断了？", "抄底的机会！", "清仓保命", "这次是真崩了", "美股不会倒", "别人恐惧我贪婪"],
  squant: ["规则失灵了？", "小盘股完了", "坚持就是胜利", "量化在收割散户", "割了吧", "三年都赚，怕什么"],
  soil: ["油价不可能为负", "抄底原油！", "银行产品很安全", "一桶油比一瓶水便宜", "闭眼买", "跌了一大半还能跌？"],
};

function Crowd({ id }: { id: string }) {
  const pool = CROWD[id] || [];
  const [bs, setBs] = useState<{ k: number; t: string; top: number }[]>([]);
  useEffect(() => {
    if (!pool.length) return;
    let k = 0;
    const spawn = () => {
      k += 1;
      const n = k;
      setBs((b) => [...b.slice(-3), { k: n, t: pool[n % pool.length], top: [6, 30, 54][n % 3] }]);
    };
    const first = setTimeout(spawn, 900);
    const t = setInterval(spawn, 1700);
    return () => {
      clearTimeout(first);
      clearInterval(t);
    };
  }, [id]);
  return (
    <div className="ride-bullets">
      {bs.map((b) => (
        <motion.span key={b.k} className="ride-bullet" style={{ top: `${b.top}%` }} initial={{ x: 360, opacity: 0 }} animate={{ x: -280, opacity: [0, 1, 1, 0] }} transition={{ duration: 5.2, ease: "linear" }}
          onAnimationComplete={() => setBs((xs) => xs.filter((x) => x.k !== b.k))}>{b.t}</motion.span>
      ))}
    </div>
  );
}

function Tape({ scene }: { scene: Scene }) {
  const v = scene.blind.chart.values;
  const n = v.length;
  const p5 = pctChg(v[n - 6], v[n - 1]);
  const pAll = pctChg(v[0], v[n - 1]);
  return (
    <div className="card desk-tape mt12">
      <div className="row between" style={{ alignItems: "flex-end" }}>
        <div>
          <div className="tiny bold">近 5 个交易日</div>
          <div className={"display num " + (p5 >= 0 ? "up" : "down")} style={{ fontSize: 30, lineHeight: 1 }}>{pctTxt(p5)}</div>
        </div>
        <div style={{ textAlign: "right" }}>
          <div className="tiny bold">近 {n} 个交易日</div>
          <b className={"num " + (pAll >= 0 ? "up" : "down")}>{pctTxt(pAll)}</b>
        </div>
      </div>
      <div style={{ position: "relative" }}>
        <LineChart values={v} height={104} base={100} color="#2A2A1C" />
        <Crowd id={scene.id} />
        <span className="crowd-tag">弹幕为虚构的散户声音</span>
      </div>
      <Ticker lines={scene.blind.lines} />
      <div className="mt8"><DataStamp scene={scene} phase="blind" /></div>
    </div>
  );
}

function IntelRow({ scene }: { scene: Scene }) {
  const { g, update } = useGame();
  const rec = cur(g!);
  const [open, setOpen] = useState<EvKind | null>(null);
  const [nope, setNope] = useState<EvKind | null>(null);
  const t0 = useRef(0);
  const free = rec.freeEvidence || 0;
  const left = free + g!.rp;
  function tap(k: EvKind) {
    if (rec.evidence.includes(k)) {
      sfx.tap();
      setOpen(k);
      t0.current = Date.now();
      return;
    }
    if (left <= 0) {
      buzz(60);
      sfx.thud();
      setNope(k);
      setTimeout(() => setNope(null), 600);
      return;
    }
    sfx.paper();
    buzz(15);
    update((x) => {
      const r = cur(x);
      if ((r.freeEvidence || 0) > 0) r.freeEvidence = (r.freeEvidence || 0) - 1;
      else x.rp -= 1;
      r.evidence.push(k);
    });
    setOpen(k);
    t0.current = Date.now();
  }
  function close() {
    const k = open;
    if (k) update((x) => void (cur(x).evidenceMs[k] = (cur(x).evidenceMs[k] || 0) + (Date.now() - t0.current)));
    setOpen(null);
  }
  return (
    <div className="mt12">
      <div className="row between">
        <b className="small">翻证据卡 <span className="tiny" style={{ fontWeight: 600 }}>每张 1 研究点</span></b>
        <span className="row gap6">{free > 0 && <span className="pill warn">免费 {free} 张</span>}<Help k="研究点"><RP n={g!.rp} /></Help></span>
      </div>
      <div className="intel-row mt8">
        {KINDS.map((k, i) => {
          const seen = rec.evidence.includes(k);
          const locked = !seen && left <= 0;
          return (
            <motion.button key={k} className={"intel" + (seen ? " seen" : "") + (locked ? " locked" : "")} onClick={() => tap(k)}
              initial={{ opacity: 0, y: 12 }} animate={nope === k ? { x: [0, -6, 6, -4, 4, 0], opacity: 1, y: 0 } : { x: 0, opacity: 1, y: 0 }} transition={nope === k ? { duration: 0.35 } : { delay: 0.2 + i * 0.06 }}>
              {scene.evidence[k].risk && <span className="intel-risk">险</span>}
              <img src={ART(`icon_${EV_ICON[k]}`)} alt="" />
              <b>{EV_CN[k]}</b>
              <span className="intel-cost">{seen ? "已看" : locked ? "🔒" : "1 点"}</span>
            </motion.button>
          );
        })}
      </div>
      {left <= 0 && !rec.evidence.length && <div className="tiny mt4">研究点用完了，这一场凭感觉下单。</div>}
      <Sheet open={!!open} onClose={close}>
        {open && (
          <motion.div initial={{ rotateX: -70, opacity: 0, y: 40 }} animate={{ rotateX: 0, opacity: 1, y: 0 }} transition={{ type: "spring", stiffness: 160, damping: 18 }} style={{ transformPerspective: 900 }}>
            <EvidenceView ev={scene.evidence[open]} scene={scene} />
            <button className="btn block mt12" onClick={close}>看完了</button>
          </motion.div>
        )}
      </Sheet>
    </div>
  );
}

function Order({ scene, onNext }: { scene: Scene; onNext: () => void }) {
  const { g, update } = useGame();
  const rec = cur(g!);
  const [opt, setOpt] = useState<OptKey | null>(rec.option || null);
  const [reason, setReason] = useState<Reason | null>(rec.reason || null);
  const [ruleId, setRuleId] = useState<string | null>(rec.ruleId || null);
  const [plan, setPlan] = useState<Plan>(rec.plan || "none");
  const [stamped, setStamped] = useState(false);
  const [ruleSheet, setRuleSheet] = useState(false);
  const noA = rec.calm === "sat";
  const stage = STAGES[scene.id];
  const seq = scene.decision_mode === "sequential";
  const queueN = seq ? 9 + g!.opponents.filter((id) => ["A", "B"].includes(aiPick(id, scene.id).option)).length : 0;
  const myRules = RULES.filter((r) => g!.rules.includes(r.id));
  const revealed = g!.seasons.filter((r) => r.stars).map((r) => r.scene!);
  const ruleName = (id: string) => { const r = RULES.find((x) => x.id === id); return r ? ruleView(r, revealed).name : id; };
  const now = nowShares(scene);
  const shares = opt ? sharesOf(scene, opt) : now;
  const needPlan = !!opt && shares > 0;
  const ok = opt && reason && (reason !== "rule" || ruleId);
  const verb = orderVerb(now, shares);
  const reasonRef = useRef<HTMLDivElement>(null);
  const goRef = useRef<HTMLButtonElement>(null);
  const first = useRef(!rec.option);
  const reveal = (r: { current: HTMLElement | null }) => setTimeout(() => r.current?.scrollIntoView({ behavior: "smooth", block: "center" }), 260);
  function pickOpt(k: OptKey) {
    sfx.tap();
    buzz(12);
    setOpt(k);
    if (first.current) {
      first.current = false;
      reveal(reasonRef);
    }
  }
  function pickReason(id: Reason) {
    sfx.paper();
    buzz(12);
    setReason(id);
    if (id === "rule") setRuleSheet(true);
    else reveal(goRef);
  }
  async function submit() {
    setStamped(true);
    sfx.stamp();
    setTimeout(() => sfx.coin(), 180);
    buzz([30, 40, 60]);
    update((x) => {
      const r = cur(x);
      r.option = opt!;
      r.reason = reason!;
      r.ruleId = reason === "rule" ? ruleId! : undefined;
      r.plan = needPlan ? plan : "none";
      r.queueSeen = seq ? queueN : undefined;
    });
    await sleep(1000);
    onNext();
  }
  return (
    <>
      {seq && !stage?.Order && <div className="mt12"><QueueStrip scene={scene} n={queueN} me={!!opt && shares > 0} /></div>}
      <div className="slip order mt12" style={{ boxShadow: opt ? `6px 6px 0 ${HEAT[opt]}` : undefined, transition: "box-shadow .25s" }}>
        <div className="order-head">
          <b className="display" style={{ fontSize: 21, lineHeight: 1.2 }}>{scene.blind.question}</b>
          <span className="order-pos">
            <span className="tiny bold">持仓</span>
            <Coins n={now} />
            {opt && shares !== now && <><b>→</b><Coins n={shares} /></>}
          </span>
        </div>
        {stage?.Order && <div className="mt8"><stage.Order scene={scene} joined={opt ? shares > 0 : null} /></div>}
        <div className="opt-grid mt8">
          {scene.options.map((o) => {
            const lock = noA && o.key === "A";
            return (
              <button key={o.key} className={"opt tile" + (opt === o.key ? " on" : "")} disabled={lock} onClick={() => pickOpt(o.key)}
                style={opt === o.key ? { background: HEAT[o.key], color: "#fff8ec" } : undefined}>
                <span className="tile-top"><span className="key">{lock ? "🔒" : o.key}</span>{stage?.tag?.[o.key] && <span className="tile-tag">{stage.tag[o.key]}</span>}<Coins n={o.shares} /></span>
                <span className="tile-label"><Rich text={o.label} max={2} /></span>
                {o.hint && <span className="tile-hint"><Rich text={o.hint} max={2} /></span>}
              </button>
            );
          })}
        </div>
        {noA && <div className="tiny mt4">坐过冷静亭：这一季 A 锁住了。</div>}
        <AnimatePresence>
          {opt && (
            <motion.div key="reason" ref={reasonRef} className="sec" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}>
              <div className="slip-q">凭什么？</div>
              <div className="rrow mt8">
                {REASONS.filter((r) => r.id !== "rule" || myRules.length).map((r, i) => {
                  const ek = R_EV[r.id];
                  return (
                    <motion.button key={r.id} className={"chip rchip" + (reason === r.id ? " on" : "")} data-seen={ek && rec.evidence.includes(ek) ? "1" : undefined} onClick={() => pickReason(r.id)}
                      initial={{ y: 16, opacity: 0 }} animate={{ y: 0, opacity: 1 }} transition={{ delay: i * 0.03 }}>
                      {ek ? <img src={ART(`icon_${EV_ICON[ek]}`)} alt="" className="ricon" /> : <i className="ricon glyph" data-ch={R_GLYPH[r.id] || "?"} />}
                      {r.cn}{r.id === "rule" && ruleId && <span className="sub">{ruleName(ruleId)}</span>}
                    </motion.button>
                  );
                })}
              </div>
            </motion.div>
          )}
        </AnimatePresence>
        <AnimatePresence>
          {opt && reason && needPlan && (
            <motion.div key="plan" className="sec" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}>
              <div className="slip-q">跌了 5% 怎么办？<span className="tiny" style={{ fontWeight: 600 }}>定了照做，方法 +1★</span></div>
              <div className="row gap6 mt8">
                {PLANS.map((p) => (
                  <button key={p.id} className={"chip plan-chip" + (plan === p.id ? " on" : "")} data-ic={PLAN_IC[p.id]} onClick={() => { sfx.tap(); buzz(10); setPlan(p.id); }}>{p.cn}</button>
                ))}
              </div>
            </motion.div>
          )}
        </AnimatePresence>
        <AnimatePresence>
          {stamped && (
            <motion.div className="stamp" style={{ right: 16, top: 56, fontSize: 40 }} initial={{ scale: 3, opacity: 0, rotate: -30 }} animate={{ scale: 1, opacity: 0.92, rotate: -14 }} transition={{ type: "spring", stiffness: 500, damping: 20 }}>
              {stage?.stamp ? stage.stamp(opt!) : shares === now ? "确认" : "成交"}
            </motion.div>
          )}
        </AnimatePresence>
      </div>
      <button ref={goRef} className="btn primary big block mt12 order-go" disabled={!ok || stamped} onClick={submit}>{ok ? (stage?.verb ? stage.verb(opt!) : `下单 · ${verb}`) : !opt ? "先选怎么做" : "再选一个理由"}</button>
      <Sheet open={ruleSheet} onClose={() => setRuleSheet(false)}>
        <div className="h3">用哪张规则牌？</div>
        <div className="col gap8 mt12">
          {myRules.map((r) => (
            <button key={r.id} className={"card"} style={{ textAlign: "left", cursor: "pointer", outline: ruleId === r.id ? "3px solid #D4432A" : "none" }} onClick={() => { setRuleId(r.id); setRuleSheet(false); reveal(goRef); }}>
              <b>{ruleName(r.id)}</b>
              <div className="small muted mt4">{r.text}</div>
            </button>
          ))}
        </div>
      </Sheet>
    </>
  );
}

function DeskStep({ scene, onNext }: { scene: Scene; onNext: () => void }) {
  const { g } = useGame();
  const rec = cur(g!);
  const Cold = STAGES[scene.id]?.Cold;
  const [cold, setCold] = useState(() => !!Cold && !rec.option && !rec.evidence.length);
  if (cold && Cold) return <Cold scene={scene} onDone={() => setCold(false)} />;
  return (
    <div className="pad" style={{ paddingTop: 10 }}>
      <DeskTop scene={scene} />
      <Tape scene={scene} />
      <IntelRow scene={scene} />
      <Order scene={scene} onNext={onNext} />
    </div>
  );
}

/* ---------------- 4 亮牌 ---------------- */
function FlipStep({ scene, onNext }: { scene: Scene; onNext: () => void }) {
  const { g } = useGame();
  const rec = cur(g!);
  const [count, setCount] = useState(3);
  useEffect(() => {
    let n = 3;
    sfx.tick();
    const id = setInterval(() => {
      n -= 1;
      setCount(n);
      if (n > 0) sfx.tick();
      else {
        sfx.reveal();
        clearInterval(id);
      }
    }, 650);
    return () => clearInterval(id);
  }, []);
  const players = [
    { id: "me", name: "你", option: rec.option!, reason: rec.reason!, line: rec.plan && rec.plan !== "none" ? `计划：${PLANS.find((p) => p.id === rec.plan)?.cn}` : "" },
    ...g!.opponents.map((id) => {
      const p = aiPick(id, scene.id);
      return { id, name: sp(id).cn, option: p.option, reason: p.reason, line: p.line };
    }),
  ];
  return (
    <div className="pad" style={{ paddingTop: 12 }}>
      <div className="h2">和 AI 对手一起亮牌</div>
      {count > 0 ? (
        <div style={{ height: 320, display: "grid", placeItems: "center" }}>
          <motion.div key={count} initial={{ scale: 2.4, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} className="display" style={{ fontSize: 140, color: "var(--season)", textShadow: "6px 6px 0 #2A2A1C" }}>{count}</motion.div>
        </div>
      ) : (
        <div className="col gap12 mt16">
          {players.map((p, i) => {
            const o = scene.options.find((x) => x.key === p.option)!;
            return (
              <motion.div key={p.id} initial={{ rotateY: 180, opacity: 0 }} animate={{ rotateY: 0, opacity: 1 }} transition={{ delay: i * 0.25, duration: 0.6 }} style={{ transformPerspective: 800 }}>
                <div className="card row gap12" style={{ background: p.id === "me" ? "#FFF4D6" : undefined, alignItems: "flex-start" }}>
                  {p.id === "me" ? <span style={{ width: 48, height: 48, borderRadius: "50%", background: "#D4432A", color: "#fff", display: "grid", placeItems: "center", border: "2px solid #2A2A1C", fontFamily: "var(--display)", fontSize: 22, flex: "none" }}>你</span> : <SpeciesAvatar id={p.id} size={48} />}
                  <div className="grow">
                    <div className="row between">
                      <b>{p.name}</b>
                      <span className="pill dark">{p.option} · {o.label}</span>
                    </div>
                    <div className="row gap6 mt4"><span className="pill">理由：{reasonCn(p.reason)}</span><Shares n={o.shares} /></div>
                    {p.line && <div className="small mt8" style={{ background: "#fff", border: "1.5px solid #2A2A1C", borderRadius: "4px 14px 14px 14px", padding: "6px 10px" }}><Rich text={p.line} max={2} /></div>}
                  </div>
                </div>
              </motion.div>
            );
          })}
          <Fade delay={0.9}>
            <button className="btn season big block" onClick={() => { sfx.tap(); onNext(); }}>快进：{scene.fast_forward.title} →</button>
          </Fade>
        </div>
      )}
    </div>
  );
}
