import { AnimatePresence, motion } from "framer-motion";
import { useEffect, useMemo, useRef, useState } from "react";
import { ART, type EvKind, type Scene } from "../data";
import { aiResult, EVENT_NAMES, starsOf } from "../game/engine";
import { aiPick, sp, type Plan } from "../game/meta";
import { cur, useGame, type SceneStep } from "../game/store";
import { buzz, sfx } from "../lib/sound";
import { Hud } from "../ui/Hud";
import { Sheet, SpeciesAvatar, Stars, Steps } from "../ui/kit";
import { Rich } from "../ui/Term";
import { aiLine } from "../arcade/ai";
import { Big, PathChart } from "../arcade/Arcade";
import { foeRun, optionOf, reasonOf } from "../arcade/bridge";
import { Game, type Run } from "../arcade/Game";
import type { Level } from "../arcade/levels";
import { describe, stampOf } from "../arcade/profile";

/**
 * 桌游名场面的线上玩法：同一张名场面卡、同一段行情。
 * 盲盒（认出来了可以申报）→ 线索（翻证据卡、说好跌了怎么办）→ 出手（按住 = 拿着）→ 揭幕（入账、资金榜、方法星）。
 */
const STEP_AT: Partial<Record<SceneStep, number>> = { blind: 0, evidence: 1, slip: 1, flip: 1, ff: 2, reveal: 3 };
const LABELS = ["盲盒", "线索", "出手", "揭幕"];
const KINDS: EvKind[] = ["price", "data", "news", "tip"];
const EV_CN: Record<EvKind, string> = { price: "量价", data: "数据", news: "消息", tip: "锦囊" };
const EV_ICON: Record<EvKind, string> = { price: "chart", data: "ledger", news: "phone", tip: "letter" };
const r1 = (x: number) => Math.round(x * 10) / 10;

export function LiveScene({ scene, level, onStation }: { scene: Scene; level: Level; onStation: () => void }) {
  const { g, update } = useGame();
  const at = STEP_AT[g!.step] ?? 0;
  const go = (s: SceneStep) => update((x) => void (x.step = s));
  return (
    <div className={`screen arc live s-${scene.season}`}>
      {at !== 2 && <Hud title={`${scene.season_cn} · ${LABELS[at]}`} />}
      {at !== 2 && <div style={{ padding: "6px 16px 0" }}><Steps n={4} at={at} labels={LABELS} /></div>}
      <AnimatePresence mode="wait">
        <motion.div key={at} className="arc-body" initial={{ opacity: 0, x: 30 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -30 }} transition={{ duration: 0.25 }}>
          {at === 0 && <Blind scene={scene} onNext={() => { sfx.paper(); go("evidence"); }} />}
          {at === 1 && <Clues scene={scene} onNext={() => { sfx.bell(); go("ff"); }} />}
          {at === 2 && <Play scene={scene} level={level} />}
          {at === 3 && <Reveal scene={scene} level={level} onNext={onStation} />}
        </motion.div>
      </AnimatePresence>
    </div>
  );
}

/* ---------- 盲盒：一张海报，一句处境 ---------- */
function Blind({ scene, onNext }: { scene: Scene; onNext: () => void }) {
  const { g, update } = useGame();
  const rec = cur(g!);
  const [open, setOpen] = useState(false);
  const [pick, setPick] = useState<string | null>(null);
  return (
    <div className="live-blind">
      <div className="live-poster">
        <motion.img src={ART(`blind_${scene.id}`)} alt="" initial={{ scale: 1.15 }} animate={{ scale: 1 }} transition={{ duration: 2.4, ease: "easeOut" }} />
        <div className="live-poster-txt">
          <span className="arc-kicker">名场面 · 名字和日期已隐藏</span>
          <motion.h1 className="display" initial={{ y: 16, opacity: 0 }} animate={{ y: 0, opacity: 1 }} transition={{ delay: 0.3 }}>{scene.blind.headline}</motion.h1>
          <motion.p initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.8 }}><Rich text={scene.blind.position} /></motion.p>
        </div>
      </div>
      <div className="live-actions">
        <button className="btn primary big block" onClick={onNext}>开盘前，先翻线索 →</button>
        <button className={"btn ghost block mt8" + (rec.recognized ? " on" : "")} onClick={() => { sfx.tap(); setOpen(true); }}>
          {rec.recognized ? `✓ 已申报：${rec.recognized.name}` : "我认出来了，这是哪一次"}
        </button>
      </div>
      <Sheet open={open} onClose={() => setOpen(false)}>
        <div className="h3">认出这是哪一次了？</div>
        <p className="small mt4">知道结局就不算盲选：这一场的钱按两位对手的平均记，物种币算半枚；猜对记一次金融史。</p>
        <div className="col gap6 mt12">
          {EVENT_NAMES.map((e) => (
            <button key={e.id} className={"opt" + (pick === e.id ? " on" : "")} style={{ gridTemplateColumns: "1fr", padding: "10px 14px", fontSize: 15 }} onClick={() => setPick(e.id)}>{e.name}</button>
          ))}
        </div>
        <div className="row gap8 mt12">
          {rec.recognized && <button className="btn ghost" onClick={() => { update((x) => void (cur(x).recognized = null)); setOpen(false); }}>撤回</button>}
          <button className="btn season grow" disabled={!pick} onClick={() => {
            sfx.stamp();
            update((x) => void (cur(x).recognized = { name: EVENT_NAMES.find((e) => e.id === pick)!.name, correct: pick === scene.id }));
            setOpen(false);
          }}>就是它</button>
        </div>
      </Sheet>
    </div>
  );
}

/* ---------- 线索：四张扣着的证据卡，翻几张由研究点决定；再说好跌了怎么办 ---------- */
function Clues({ scene, onNext }: { scene: Scene; onNext: () => void }) {
  const { g, update } = useGame();
  const rec = cur(g!);
  const [open, setOpen] = useState<EvKind | null>(null);
  const [nope, setNope] = useState<EvKind | null>(null);
  const t0 = useRef(0);
  const free = rec.freeEvidence || 0;
  const left = free + g!.rp;
  const plan = rec.plan || null;
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
      setTimeout(() => setNope(null), 700);
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
  const setPlan = (p: Plan) => {
    sfx.tap();
    buzz(10);
    update((x) => void (cur(x).plan = p));
  };
  const ev = open ? scene.evidence[open] : null;
  return (
    <div className="live-clues">
      <div className="row between" style={{ alignItems: "flex-end" }}>
        <h2 className="display">翻开线索</h2>
        <span className={"live-rp" + (left <= 0 ? " out" : "")}>{left > 0 ? `还能翻 ${left} 张` : "研究点用完了"}</span>
      </div>
      <div className="live-cards mt8">
        {KINDS.map((k, i) => {
          const seen = rec.evidence.includes(k);
          return (
            <motion.button key={k} className={"live-card" + (seen ? " seen" : "") + (!seen && left <= 0 ? " locked" : "")} onClick={() => tap(k)}
              initial={{ y: 16, opacity: 0 }} animate={nope === k ? { x: [0, -7, 7, -4, 4, 0], y: 0, opacity: 1 } : { x: 0, y: 0, opacity: 1 }} transition={nope === k ? { duration: 0.35 } : { delay: i * 0.06 }}>
              {seen ? (
                <>
                  <span className="live-card-k">{EV_CN[k]}</span>
                  <b>{scene.evidence[k].stat?.value || scene.evidence[k].title}</b>
                  {scene.evidence[k].stat && <span className="live-card-t">{scene.evidence[k].title}</span>}
                </>
              ) : (
                <>
                  <img src={ART(`icon_${EV_ICON[k]}`)} alt="" />
                  <b>{EV_CN[k]}</b>
                  <span className="live-card-t">{left > 0 ? "点开 · 1 研究点" : "🔒"}</span>
                </>
              )}
            </motion.button>
          );
        })}
      </div>
      <div className="live-plan mt12">
        <b>要是买了以后跌 5%，你会？</b>
        <div className="live-plan-row mt8">
          {([["cut", "走"], ["add", "加"], ["none", "到时再说"]] as [Plan, string][]).map(([id, t]) => (
            <button key={id} className={"btn" + (plan === id ? " dark" : "")} onClick={() => setPlan(id)}>{t}</button>
          ))}
        </div>
      </div>
      <div className="grow" />
      <button className="btn primary big block mt12" disabled={!plan} onClick={onNext}>{plan ? "开盘 →" : "先选上面那一句"}</button>
      <div className="tiny center mt4">说好的计划会画在走势上，揭幕时看你有没有照做</div>
      <Sheet open={!!open} onClose={close}>
        {ev && open && (
          <motion.div initial={{ rotateX: -70, opacity: 0, y: 30 }} animate={{ rotateX: 0, opacity: 1, y: 0 }} transition={{ type: "spring", stiffness: 170, damping: 18 }} style={{ transformPerspective: 900 }}>
            <div className="row gap8"><span className="pill dark">{EV_CN[open]}</span>{ev.risk && <span className="pill" style={{ background: "#D4432A", color: "#fff" }}>风险</span>}</div>
            <div className="h2 mt8">{ev.title}</div>
            {ev.stat && <div className="row gap8 mt8" style={{ alignItems: "baseline" }}><span className="display" style={{ fontSize: 46, color: "var(--season)" }}>{ev.stat.value}</span><span className="small"><Rich text={ev.stat.caption} /></span></div>}
            <div className="body mt8"><Rich text={ev.lines[0]} /></div>
            {ev.lines[1] && <div className="small muted mt4"><Rich text={ev.lines[1]} /></div>}
            <div className="tiny mt8">{ev.source}</div>
            <button className="btn primary block mt12" onClick={close}>记下了</button>
          </motion.div>
        )}
      </Sheet>
    </div>
  );
}

/* ---------- 出手：同一段行情，你和两位 AI 对手都在场 ---------- */
function Play({ scene, level }: { scene: Scene; level: Level }) {
  const { g, update } = useGame();
  const rec = cur(g!);
  const cap = g!.money > 1 ? g!.money : 20;
  const foes = useMemo(() => g!.opponents.map((id) => ({ id, ...foeRun(level, id, g!.aiMoney[id] ?? 20) })), [level.id]);
  function done(run: Run) {
    const ai = Object.fromEntries(foes.map((f) => {
      const base = aiResult(scene, f.id);
      const d = r1(f.eq - (g!.aiMoney[f.id] ?? 20));
      return [f.id, { ...base, seg1: d, seg2: 0, extra: 0, total: d }];
    }));
    const mine = r1(run.eq - cap);
    const avg = r1(Object.values(ai).reduce((a, x) => a + x.total, 0) / Math.max(1, foes.length));
    update((x) => {
      const r = cur(x);
      r.run = run;
      r.option = optionOf(level, scene, run);
      r.reason = reasonOf(r.evidence, r.evidenceMs);
      r.plan = r.plan || "none";
      r.ff = {
        actions: run.trades.filter((t) => t.why !== "end").map((t) => `${t.k}@${t.i}`),
        changes: run.trades.filter((t) => t.why !== "end" && t.why !== "start").length,
        planTriggered: !!run.planTriggered,
        planFollowed: run.planTriggered ? !!run.planFollowed : null,
        ruleFollowed: null,
        locked: run.lockTries,
        forced: run.liq,
        leavers: run.leftRank ?? undefined,
        debt: run.lev > 1,
      };
      r.ai = ai;
      r.money = { seg1: mine, seg2: 0, extra: 0, total: mine, counted: r.recognized ? avg : mine, note: r.recognized ? "认出来了，按对手平均记" : undefined };
      x.step = "reveal";
    });
    aiLine(run).then((line) => line && update((x) => void (cur(x).line = line)));
  }
  return <Game level={level} cap={cap} plan={rec.plan || "none"} foes={foes.map((f) => f.foe)} onDone={done} noMax={rec.calm === "sat"} />;
}

/* ---------- 揭幕：先看结果、入账；再看资金榜和方法星 ---------- */
function Reveal({ scene, level, onNext }: { scene: Scene; level: Level; onNext: () => void }) {
  const { g, update } = useGame();
  const rec = cur(g!);
  const run = rec.run!;
  const m = rec.money!;
  const booked = !!rec.stars;
  const st = stampOf(level, run);
  const stars = starsOf(rec);
  const foes = useMemo(() => g!.opponents.map((id) => foeRun(level, id, 20).foe), [level.id]);
  const [wait, setWait] = useState(true);
  useEffect(() => {
    sfx.reveal();
    const t1 = setTimeout(() => { sfx.stamp(); buzz(30); }, 900);
    const t2 = setTimeout(() => setWait(false), 5000);
    return () => { clearTimeout(t1); clearTimeout(t2); };
  }, []);
  function book() {
    buzz(m.counted >= 0 ? [20, 40, 20] : 60);
    sfx.coin();
    setTimeout(() => (m.counted >= 0 ? sfx.gain() : sfx.loss()), 300);
    update((x) => {
      const r = cur(x);
      x.money = r1(x.money + m.counted);
      Object.entries(r.ai || {}).forEach(([id, a]) => (x.aiMoney[id] = r1((x.aiMoney[id] ?? 20) + a.total)));
      r.stars = starsOf(r);
    });
  }
  const quick = g!.mode === "quick";
  const plan = rec.plan && rec.plan !== "none" ? (rec.plan === "cut" ? "跌 5% 就走" : "跌 5% 就加") : null;
  const kept = !plan ? null : !run.planTriggered ? `你说好“${plan}”，这一场没跌到那里。` : run.planFollowed ? `你说好“${plan}”，真跌到了，你照做了。` : `你说好“${plan}”，真跌到了，你没照做。`;
  if (!booked) {
    return (
      <div className="arc-reveal">
        <div className="arc-kicker dim">原来是</div>
        <motion.h1 className="display" initial={{ scale: 1.3, opacity: 0 }} animate={{ scale: 1, opacity: 1 }}>{scene.title}</motion.h1>
        <div className="tiny">{scene.reveal.date_line}</div>
        <div className="arc-reveal-card mt12">
          <PathChart level={level} run={run} foes={foes} />
          <motion.b className={"arc-stamp2 " + (st.good === true ? "good" : st.good === false ? "bad" : "")} initial={{ scale: 2.6, rotate: -24, opacity: 0 }} animate={{ scale: 1, rotate: -8, opacity: 1 }} transition={{ delay: 0.9, type: "spring", stiffness: 420, damping: 15 }}>{st.t}</motion.b>
        </div>
        <motion.div className="arc-money mt12" initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 1.2 }}>
          <b className={"display num " + (m.total > 0 ? "up" : m.total < 0 ? "down" : "")}>{m.total >= 0 ? "+" : "−"}{Math.abs(m.total).toFixed(1)} 万</b>
          <span className="small">{st.sub}</span>
        </motion.div>
        {rec.recognized && <motion.div className="live-kept mt8" initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 1.5 }}>你说认出来了：按桌游规则，这一场按两位对手的平均记 {m.counted >= 0 ? "+" : "−"}{Math.abs(m.counted).toFixed(1)} 万</motion.div>}
        {kept && <motion.div className={"live-kept mt8" + (run.planTriggered ? (run.planFollowed ? " good" : " bad") : "")} initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 1.6 }}>{kept}</motion.div>}
        <motion.div className="arc-ai mt12" initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 2 }}>
          <span className="arc-ai-tag">AI</span>
          <span>{rec.line || (wait ? "……" : scene.reveal.lesson)}</span>
        </motion.div>
        <div className="grow" />
        <button className="btn primary big block mt12" onClick={book}>入账 {m.counted >= 0 ? "+" : "−"}{Math.abs(m.counted).toFixed(1)} 万</button>
        <div className="tiny center mt8">真实行情：{level.reveal.source}{rec.line ? " · 旁白由 AI 生成" : ""}</div>
      </div>
    );
  }
  const rank = [
    { id: "me", d: m.counted, total: g!.money },
    ...Object.entries(rec.ai || {}).map(([id, a]) => ({ id, d: a.total, total: g!.aiMoney[id] ?? 20 })),
  ].sort((a, b) => b.total - a.total);
  return (
    <div className="arc-reveal">
      <div className="arc-kicker dim">{scene.season_cn} · 资金榜</div>
      <div className="col gap8 mt8">
        {rank.map((x, i) => (
          <motion.div key={x.id} className={"live-rank" + (x.id === "me" ? " me" : "")} initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.12 * i }}>
            <b className="live-rank-n">{i + 1}</b>
            {x.id === "me" ? <span className="rank-me">你</span> : <SpeciesAvatar id={x.id} size={34} />}
            <span className="grow">{x.id === "me" ? "你" : sp(x.id).cn}<small>{x.id === "me" ? "" : aiPick(x.id, scene.id as never).line}</small></span>
            <span className={"num " + (x.d > 0 ? "up" : x.d < 0 ? "down" : "")}>{x.d >= 0 ? "+" : "−"}{Math.abs(x.d).toFixed(1)}</span>
            <b className="num">{x.total.toFixed(1)} 万</b>
          </motion.div>
        ))}
      </div>
      <div className="live-stars mt16">
        <div className="row between"><b>方法星</b><Stars n={stars.total} /></div>
        <div className="live-star-row mt8">
          <span className={stars.ev >= 1 ? "on" : ""}>{stars.ev >= 2 ? "★★" : "★"} 翻了线索</span>
          <span className={stars.consistent ? "on" : ""}>★ 照着线索做</span>
          <span className={stars.plan ? "on" : ""}>★ 说到做到</span>
        </div>
      </div>
      {rec.recognized && (
        <div className="live-kept mt12">{rec.recognized.correct ? "你认出来了，猜对了：记一次金融史。" : `你说是“${rec.recognized.name}”，不是这一次。`}</div>
      )}
      <motion.div className="arc-fact mt12" initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.5 }}>
        <Big n={level.reveal.big} unit={level.reveal.unit} delay={0.6} />
        <span className="small">{level.reveal.label}</span>
      </motion.div>
      <div className="grow" />
      <button className="btn season big block mt12" onClick={() => { sfx.tap(); onNext(); }}>{quick ? "看看这一场你像哪一种 →" : "去驿站，领物种币 →"}</button>
      <div className="tiny center mt8">对手按桌游里自己的牌出手 · {describe(level, run).split("；")[0]}</div>
    </div>
  );
}
