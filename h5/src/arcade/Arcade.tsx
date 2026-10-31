import { AnimatePresence, animate, motion } from "framer-motion";
import { useEffect, useMemo, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { ART } from "../data";
import { QUBE_URL } from "../game/handoff";
import { PICKABLE, sp } from "../game/meta";
import { buzz, sfx } from "../lib/sound";
import { MuteButton } from "../ui/kit";
import { aiJudge, aiLine } from "./ai";
import { CAP, Game, type Run } from "./Game";
import { LEVELS, ticksOf, tickOf, type Level } from "./levels";
import { localVerdict, stampOf, stats } from "./profile";
import { useArcade } from "./store";

/** 新主线：四关小游戏 → 猜物种 → AI 复盘 → 结果 */
export function Arcade() {
  const a = useArcade();
  const level = LEVELS[Math.min(a.idx, LEVELS.length - 1)];
  const run = a.runs.find((r) => r.id === level.id);

  function done(r: Run) {
    const runs = [...a.runs.filter((x) => x.id !== r.id), r];
    a.set({ runs, stage: "reveal" });
    aiLine(r).then((line) => {
      if (!line) return;
      const s = useArcade.getState();
      s.set({ lines: { ...s.lines, [r.id]: line } });
    });
  }
  function next() {
    sfx.tap();
    if (a.idx < LEVELS.length - 1) a.set({ idx: a.idx + 1, stage: "cold" });
    else a.set({ stage: "guess" });
  }

  let body;
  if (a.stage === "cold") body = <Cold key={"c" + level.id} level={level} onDone={() => a.set({ stage: "play" })} />;
  else if (a.stage === "play") body = <Game key={"g" + level.id} level={level} onDone={done} />;
  else if (a.stage === "reveal" && run) body = <Reveal key={"r" + level.id} level={level} run={run} line={a.lines[level.id]} last={a.idx >= LEVELS.length - 1} onNext={next} />;
  else if (a.stage === "guess") body = <Guess onPick={(id) => a.set({ guess: id, stage: "judge" })} />;
  else if (a.stage === "judge") body = <Judge />;
  else if (a.stage === "final" && a.verdict) body = <Final />;
  else body = <Cold key={"c" + level.id} level={level} onDone={() => a.set({ stage: "play" })} />;

  const dark = a.stage === "cold" || a.stage === "judge" || a.stage === "final";
  return (
    <div className={"screen arc s-" + level.season + (dark ? " dark" : "")}>
      {a.stage !== "final" && (
        <div className="arc-top">
          <div className="arc-dots">
            {LEVELS.map((l, i) => (
              <span key={l.id} className={"arc-dot" + (i < a.idx || (i === a.idx && (a.stage === "reveal" || a.stage === "guess" || a.stage === "judge")) ? " done" : i === a.idx ? " on" : "")}>{l.seasonCn}</span>
            ))}
          </div>
          <MuteButton />
        </div>
      )}
      <AnimatePresence mode="wait">
        <motion.div key={a.stage + a.idx} className="arc-body" initial={{ opacity: 0, x: 24 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -24 }} transition={{ duration: 0.25 }}>
          {body}
        </motion.div>
      </AnimatePresence>
    </div>
  );
}

/* ---------- 开场：一张海报，一句话 ---------- */
function Cold({ level, onDone }: { level: Level; onDone: () => void }) {
  const once = useRef(false);
  const go = () => {
    if (once.current) return;
    once.current = true;
    onDone();
  };
  useEffect(() => {
    sfx.paper();
    const t = setTimeout(go, 3600);
    return () => clearTimeout(t);
  }, []);
  return (
    <div className="arc-cold" onClick={go}>
      <motion.img src={ART(`blind_${level.id}`)} alt="" initial={{ scale: 1.15 }} animate={{ scale: 1 }} transition={{ duration: 3.6, ease: "easeOut" }} />
      <div className="arc-cold-txt">
        <span className="arc-kicker">第 {level.n} 场 · {level.seasonCn}</span>
        <motion.h1 className="display" initial={{ y: 20, opacity: 0 }} animate={{ y: 0, opacity: 1 }} transition={{ delay: 0.3 }}>{level.cold.title}</motion.h1>
        <motion.p initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.9 }}>{level.cold.line}</motion.p>
        <span className="arc-skip">点一下继续</span>
      </div>
      <motion.i className="arc-bar" initial={{ scaleX: 0 }} animate={{ scaleX: 1 }} transition={{ duration: 3.6, ease: "linear" }} />
    </div>
  );
}

/* ---------- 揭幕：原来是哪一次 + 你的印章 ---------- */
function PathChart({ level, run }: { level: Level; run: Run }) {
  const { p, dates } = ticksOf(level);
  const W = 340;
  const H = 150;
  const lo = Math.min(...p);
  const hi = Math.max(...p);
  const X = (i: number) => (i / (p.length - 1)) * W;
  const Y = (v: number) => H - 8 - ((v - lo) / (hi - lo || 1)) * (H - 16);
  const d = p.map((v, i) => `${i ? "L" : "M"}${X(i).toFixed(1)},${Y(v).toFixed(1)}`).join("");
  const hol = level.holiday ? tickOf(level, level.holiday.close, "close") : -1;
  return (
    <div className="arc-path">
      <svg viewBox={`0 0 ${W} ${H}`} width="100%" height={H} preserveAspectRatio="none" style={{ display: "block", overflow: "visible" }}>
        {(level.lock || []).map((dd) => {
          const k = tickOf(level, dd, "open");
          return k >= 0 && <rect key={dd} x={X(k) - 2} width={X(k + 1) - X(k) + 4} y={0} height={H} fill="rgba(42,42,28,.1)" />;
        })}
        {hol >= 0 && <rect x={X(hol)} width={Math.max(3, X(hol + 1) - X(hol))} y={0} height={H} fill="rgba(199,154,46,.3)" />}
        {(level.halts || []).map((dd) => {
          const k = tickOf(level, dd, "close");
          return k >= 0 && <text key={dd} x={X(k)} y={10} fontSize={10} fontWeight={900} textAnchor="middle" fill="#D4432A">熔</text>;
        })}
        <path d={d} fill="none" stroke="#2A2A1C" strokeWidth={2.2} strokeLinejoin="round" />
        {run.trades.filter((t) => t.why !== "end").map((t, i) => (
          <g key={i}>
            <circle cx={X(t.i)} cy={Y(t.p)} r={7} fill={t.why === "liq" ? "#2A2A1C" : t.k === "buy" ? "#D4432A" : "#2D5F6B"} stroke="#2A2A1C" strokeWidth={1.3} />
            <text x={X(t.i)} y={Y(t.p) + 3.3} fontSize={8.5} fontWeight={900} textAnchor="middle" fill="#fff">{t.why === "liq" ? "强" : t.k === "buy" ? "买" : "卖"}</text>
          </g>
        ))}
      </svg>
      <div className="row between tiny"><span>{dates[0]}</span><span>{dates[dates.length - 1]}</span></div>
    </div>
  );
}

function Reveal({ level, run, line, last, onNext }: { level: Level; run: Run; line?: string; last: boolean; onNext: () => void }) {
  const st = stampOf(level, run);
  const d = run.eq - CAP;
  const [wait, setWait] = useState(true);
  useEffect(() => {
    sfx.reveal();
    const t1 = setTimeout(() => {
      sfx.stamp();
      buzz(30);
    }, 900);
    const t2 = setTimeout(() => setWait(false), 4500);
    return () => {
      clearTimeout(t1);
      clearTimeout(t2);
    };
  }, []);
  return (
    <div className="arc-reveal">
      <div className="arc-kicker dim">原来是</div>
      <motion.h1 className="display" initial={{ scale: 1.3, opacity: 0 }} animate={{ scale: 1, opacity: 1 }}>{level.reveal.name}</motion.h1>
      <div className="tiny">{level.reveal.when}</div>
      <div className="arc-reveal-card mt12">
        <PathChart level={level} run={run} />
        <motion.b className={"arc-stamp2 " + (st.good === true ? "good" : st.good === false ? "bad" : "")} initial={{ scale: 2.6, rotate: -24, opacity: 0 }} animate={{ scale: 1, rotate: -8, opacity: 1 }} transition={{ delay: 0.9, type: "spring", stiffness: 420, damping: 15 }}>{st.t}</motion.b>
      </div>
      <motion.div className="arc-money mt12" initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 1.2 }}>
        <b className={"display num " + (d > 0.05 ? "up" : d < -0.05 ? "down" : "")}>{d >= 0 ? "+" : "−"}{Math.abs(d).toFixed(1)} 万</b>
        <span className="small">{st.sub}</span>
      </motion.div>
      <motion.div className="arc-fact mt12" initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 1.7 }}>
        <Big n={level.reveal.big} unit={level.reveal.unit} />
        <span className="small">{level.reveal.label}</span>
      </motion.div>
      <motion.div className="arc-ai mt12" initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 2.1 }}>
        <span className="arc-ai-tag">AI</span>
        <span>{line || (wait ? "……" : level.reveal.lesson)}</span>
      </motion.div>
      <div className="grow" />
      <button className="btn primary big block mt12" onClick={onNext}>{last ? "四场打完了，看看你是哪种 →" : "下一场 →"}</button>
      <div className="tiny center mt8">{level.reveal.source}{line ? " · 旁白由 AI 生成" : ""}</div>
    </div>
  );
}

function Big({ n, unit }: { n: string; unit: string }) {
  const target = parseFloat(n);
  const dec = (n.split(".")[1] || "").length;
  const [v, setV] = useState(0);
  useEffect(() => {
    const c = animate(0, target, { duration: 1.4, delay: 1.8, ease: "easeOut", onUpdate: setV });
    return () => c.stop();
  }, [target]);
  return <b className="display num arc-big">{v.toFixed(dec)}<small>{unit}</small></b>;
}

/* ---------- 猜一猜 ---------- */
function Guess({ onPick }: { onPick: (id: string) => void }) {
  return (
    <div className="arc-guess">
      <div className="arc-kicker dim">四场打完了</div>
      <h2 className="display">你觉得自己是哪一种？</h2>
      <div className="arc-sp-grid mt12">
        {PICKABLE.map((s, i) => (
          <motion.button key={s.id} className="arc-sp" onClick={() => { sfx.coin(); onPick(s.id); }} initial={{ y: 20, opacity: 0 }} animate={{ y: 0, opacity: 1 }} transition={{ delay: i * 0.05 }}>
            <img src={ART(`species_${s.id}`)} alt="" />
            <b>{s.cn}</b>
            <span>{s.tagline}</span>
          </motion.button>
        ))}
      </div>
      <div className="tiny center mt12">选一个。AI 会拿你刚才的操作来对照。</div>
    </div>
  );
}

/* ---------- AI 复盘 ---------- */
function Judge() {
  const a = useArcade();
  const rows = useMemo(() => LEVELS.map((l) => ({ l, r: a.runs.find((x) => x.id === l.id) })).filter((x) => x.r), []);
  useEffect(() => {
    let alive = true;
    const local = localVerdict(a.runs, a.guess);
    const t0 = Date.now();
    aiJudge(a.runs, a.guess, local).then((v) => {
      const left = Math.max(0, 2600 - (Date.now() - t0));
      setTimeout(() => {
        if (!alive) return;
        sfx.fanfare();
        buzz([30, 40, 60]);
        useArcade.getState().set({ verdict: v, stage: "final" });
      }, left);
    });
    return () => {
      alive = false;
    };
  }, []);
  return (
    <div className="arc-judge">
      <div className="arc-kicker">AI 复盘中</div>
      <h2 className="display">正在读你的四场操作</h2>
      <div className="col gap8 mt16">
        {rows.map(({ l, r }, i) => {
          const st = stampOf(l, r!);
          return (
            <motion.div key={l.id} className="arc-judge-row" initial={{ x: -30, opacity: 0 }} animate={{ x: 0, opacity: 1 }} transition={{ delay: 0.3 + i * 0.45 }}>
              <span className="arc-dot done">{l.seasonCn}</span>
              <b>{st.t}</b>
              <span className="tiny grow">{l.reveal.name.split(" · ")[0]}</span>
            </motion.div>
          );
        })}
      </div>
      <motion.div className="arc-think mt16" animate={{ opacity: [0.3, 1, 0.3] }} transition={{ repeat: Infinity, duration: 1.2 }}>DeepSeek 正在复盘……</motion.div>
    </div>
  );
}

const fit = (s: string) => (s.length > 70 ? 19 : s.length > 48 ? 21 : 24);

/* ---------- 结果：一页一件事，点一下翻页 ---------- */
function Final() {
  const a = useArcade();
  const nav = useNavigate();
  const v = a.verdict!;
  const m = sp(v.species);
  const [page, setPage] = useState(0);
  const [copied, setCopied] = useState(false);
  const deep = Math.min(0, ...a.runs.map((r) => stats(LEVELS.find((l) => l.id === r.id)!, r).deep));
  const total = a.runs.reduce((s, r) => s + (r.eq - CAP), 0);
  const ai = v.model !== "local";
  const N = 4;
  const turn = () => {
    if (page < N - 1) {
      sfx.paper();
      setPage(page + 1);
    }
  };
  async function copyOpen() {
    try {
      await navigator.clipboard.writeText(v.qube);
    } catch {
      const t = document.createElement("textarea");
      t.value = v.qube;
      document.body.appendChild(t);
      t.select();
      document.execCommand("copy");
      t.remove();
    }
    setCopied(true);
    sfx.coin();
    window.open(QUBE_URL, "_blank", "noopener");
  }
  return (
    <div className="arc-final" onClick={turn}>
      <div className="arc-bars">{Array.from({ length: N }).map((_, i) => <i key={i} className={i <= page ? "on" : ""} />)}</div>
      <AnimatePresence mode="wait">
        <motion.div key={page} className="arc-page" initial={{ opacity: 0, y: 24 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -16 }} transition={{ duration: 0.3 }}>
          {page === 0 && (
            <>
              <div className="arc-kicker">你的交易物种</div>
              <motion.div className="arc-portrait" initial={{ scale: 0.6, rotate: -8 }} animate={{ scale: 1, rotate: 0 }} transition={{ type: "spring", stiffness: 260, damping: 16 }}>
                <img src={ART(`species_${m.id}`)} alt="" />
              </motion.div>
              <h1 className="display arc-sp-name">{m.cn}</h1>
              <div className="arc-title">{v.title}</div>
              {v.self && <div className="arc-self mt12">{v.self}</div>}
              <div className="arc-sum mt12">四场合计 <b className={total >= 0 ? "up" : "down"}>{total >= 0 ? "+" : "−"}{Math.abs(total).toFixed(1)} 万</b></div>
            </>
          )}
          {page === 1 && (
            <>
              <div className="arc-kicker">{ai ? "AI 读你" : "读你"}</div>
              <p className="arc-read" style={{ fontSize: fit(v.read) }}>{v.read}</p>
              <div className="col gap8 mt16">
                {v.moments.map((t, i) => (
                  <motion.div key={i} className="arc-moment" initial={{ x: -20, opacity: 0 }} animate={{ x: 0, opacity: 1 }} transition={{ delay: 0.2 + i * 0.25 }}>{t}</motion.div>
                ))}
              </div>
            </>
          )}
          {page === 2 && (
            <>
              <div className="arc-kicker">模拟盘 ≠ 实盘</div>
              {deep <= -0.08 && (
                <div className="arc-gap mt12">
                  <div><span className="tiny">模拟盘里你扛过</span><b className="display down">−{Math.abs(deep * 100).toFixed(0)}%</b></div>
                  <div><span className="tiny">换成真钱，痛感约等于</span><b className="display">−{Math.abs(deep * 200).toFixed(0)}%</b><span className="tiny">按“亏钱的痛≈赚钱的 2 倍”估算</span></div>
                </div>
              )}
              <p className="arc-read mt16" style={{ fontSize: fit(v.gap) }}>{v.gap}</p>
            </>
          )}
          {page === 3 && (
            <>
              <div className="arc-kicker">PandaAI 下一步</div>
              <h2 className="display">把你的习惯，拿去回测</h2>
              <div className="arc-qube mt12">“{v.qube}”</div>
              <button className="btn primary big block mt16" onClick={(e) => { e.stopPropagation(); copyOpen(); }}>{copied ? "已复制，去 Qube 粘贴 ↗" : "复制这句，打开 Qube ↗"}</button>
              <div className="tiny mt8">适合{m.cn}的 PandaAI 功能：{m.rec}</div>
              <div className="row gap8 mt16">
                <button className="btn grow" onClick={(e) => { e.stopPropagation(); a.reset(); }}>再玩一次</button>
                <button className="btn grow" onClick={(e) => { e.stopPropagation(); nav("/"); }}>回首页</button>
              </div>
            </>
          )}
        </motion.div>
      </AnimatePresence>
      {page < N - 1 && <div className="arc-tapnext">点一下，下一页</div>}
      <div className="arc-foot tiny">{ai ? "AI 生成（DeepSeek）· " : ""}仅供学习娱乐，不构成投资建议 · 行情：Panda Data，纳斯达克 100 为公开接口</div>
    </div>
  );
}
