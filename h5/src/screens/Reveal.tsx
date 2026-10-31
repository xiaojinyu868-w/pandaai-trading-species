import { AnimatePresence, motion } from "framer-motion";
import { useEffect, useState } from "react";
import { ART, type Scene } from "../data";
import { money, starsOf } from "../game/engine";
import { sp } from "../game/meta";
import { cur, useGame } from "../game/store";
import { buzz, sfx } from "../lib/sound";
import { tradeTag } from "../game/tags";
import { STAGES } from "../scenes/stages";
import { LineChart } from "../ui/Chart";
import { DataStamp } from "../ui/DataStamp";
import { Counter, Fade, Money, SpeciesAvatar, Stars } from "../ui/kit";
import { Help, Rich } from "../ui/Term";

export function RevealArt({ scene, play = true }: { scene: Scene; play?: boolean }) {
  return (
    <div className="poster" style={{ height: "46vh", minHeight: 280 }}>
      <img src={ART(`reveal_${scene.id}`)} alt="" style={{ objectPosition: "50% 30%" }} />
      {play && (
        <>
          <motion.div className="abs-fill" style={{ clipPath: "polygon(0 0, 52% 0, 46% 100%, 0 100%)" }} initial={{ x: 0, rotate: 0 }} animate={{ x: "-110%", rotate: -8 }} transition={{ delay: 0.5, duration: 0.9, ease: "easeIn" }}>
            <img src={ART(`blind_${scene.id}`)} alt="" style={{ width: "100%", height: "100%", objectFit: "cover", filter: "sepia(.3)" }} />
          </motion.div>
          <motion.div className="abs-fill" style={{ clipPath: "polygon(52% 0, 100% 0, 100% 100%, 46% 100%)" }} initial={{ x: 0, rotate: 0 }} animate={{ x: "110%", rotate: 8 }} transition={{ delay: 0.5, duration: 0.9, ease: "easeIn" }}>
            <img src={ART(`blind_${scene.id}`)} alt="" style={{ width: "100%", height: "100%", objectFit: "cover", filter: "sepia(.3)" }} />
          </motion.div>
        </>
      )}
      <div className="abs-fill" style={{ background: "linear-gradient(180deg, rgba(0,0,0,0) 50%, rgba(0,0,0,.6))", pointerEvents: "none" }} />
      <motion.div style={{ position: "absolute", left: 14, right: 14, bottom: 12 }} initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: play ? 1.3 : 0 }}>
        <span className="pill season">{scene.season_cn} · {scene.year} · {scene.market}</span>
        <h2 className="display" style={{ color: "#FBF4E4", fontSize: 32, margin: "6px 0 0", textShadow: "3px 3px 0 #2A2A1C" }}>{scene.title}</h2>
        <div className="small bold" style={{ color: "#F3D27F" }}>{scene.reveal.date_line}</div>
      </motion.div>
    </div>
  );
}

/** 入账时从按钮处喷出的硬币 */
function CoinBurst({ up }: { up: boolean }) {
  return (
    <div className="coin-burst" aria-hidden>
      {Array.from({ length: up ? 14 : 6 }, (_, i) => {
        const a = (i / (up ? 14 : 6)) * Math.PI - Math.PI;
        const r = 70 + (i % 3) * 30;
        return <motion.i key={i} className={up ? "" : "dn"} initial={{ x: 0, y: 0, opacity: 1, scale: 0.6 }} animate={{ x: Math.cos(a) * r, y: up ? Math.sin(a) * r - 40 : 60 + (i % 2) * 30, opacity: 0, scale: 1.1 }} exit={{ opacity: 0 }} transition={{ duration: up ? 0.9 : 0.7, ease: "easeOut" }} />;
      })}
    </div>
  );
}

export function RevealBody({ scene, mine, unit = "" }: { scene: Scene; mine?: { key?: string; ai?: Record<string, string> }; unit?: string }) {
  const r = scene.reveal;
  const [egg, setEgg] = useState(false);
  const [table, setTable] = useState(false);
  const [story, setStory] = useState(false);
  const [more, setMore] = useState(false);
  const [first, ...rest] = scene.exits;
  return (
    <div className="col gap12">
      <div className="card" style={{ padding: "12px 12px 14px" }}>
        <div className="tiny bold mb8">真实走势（名字和日期已揭开）</div>
        <LineChart values={r.chart.values} height={150} marks={r.chart.marks?.map((m) => ({ i: m.i, label: m.label }))} color="#2A2A1C" labels={r.chart.dates ? [r.chart.dates[0], r.chart.dates[r.chart.dates.length - 1]] : undefined} />
        <div className="col gap6 mt8">
          {(story ? r.lines : r.lines.slice(0, 1)).map((l, i) => (
            <Fade key={i} delay={i ? 0 : 0.3}><div className="row gap8 small" style={{ alignItems: "flex-start" }}><b style={{ color: "var(--season)" }}>▍</b><span><Rich text={l} /></span></div></Fade>
          ))}
        </div>
        {r.lines.length > 1 && <button className="tiny mt4" style={{ all: "unset", cursor: "pointer", fontSize: 12, fontWeight: 700, color: "var(--ink-2)" }} onClick={() => { sfx.paper(); setStory(!story); }}>{story ? "收起 ▴" : "后来还发生了什么 ▾"}</button>}
        <div className="mt12"><DataStamp scene={scene} phase="reveal" /></div>
      </div>
      {r.rule_note && <div className="card" style={{ background: "#E8F1EA" }}><b>规则会怎么做</b><div className="small mt4"><Rich text={r.rule_note} /></div></div>}
      <div className="card" style={{ padding: 12 }}>
        <div className="row between"><b className="small">如果当时选别的？</b><span className="tiny">按选项一直拿着算，不含快进里的操作</span></div>
        <div className="alt-row mt8">
          {r.payoff_rows.map((row, i) => (
            <motion.div key={row.key} className={"alt" + (mine?.key === row.key ? " me" : "")} initial={{ rotateY: 90, opacity: 0 }} animate={{ rotateY: 0, opacity: 1 }} transition={{ delay: 1.8 + i * 0.15 }}>
              <b className="alt-key">{row.key}</b>
              <span className="alt-n"><Money n={row.total} u={unit} /></span>
              <span className="row gap4" style={{ minHeight: 18, justifyContent: "center" }}>
                {mine?.key === row.key && <span className="alt-you">你</span>}
                {mine?.ai && Object.entries(mine.ai).filter(([, k]) => k === row.key).map(([id]) => <SpeciesAvatar key={id} id={id} size={18} ring={false} />)}
              </span>
            </motion.div>
          ))}
        </div>
        <button className="tiny mt8" style={{ all: "unset", cursor: "pointer", fontSize: 12, fontWeight: 700, color: "var(--ink-2)" }} onClick={() => { sfx.paper(); setTable(!table); }}>{table ? "收起明细 ▴" : "看每个选项的明细 ▾"}</button>
        <AnimatePresence initial={false}>
        {table && <motion.div initial={{ height: 0, opacity: 0 }} animate={{ height: "auto", opacity: 1 }} exit={{ height: 0, opacity: 0 }} style={{ overflow: "hidden" }}>
        <table className="ptable mt8">
          <thead><tr><th>选项</th><th>投入</th><th>快进段</th><th>之后</th><th>合计</th></tr></thead>
          <tbody>
            {r.payoff_rows.map((row) => (
              <tr key={row.key} className={mine?.key === row.key ? "me" : ""}>
                <td>
                  <b>{row.key}</b> {row.label}
                  <span className="row gap4" style={{ display: "inline-flex", marginLeft: 4, verticalAlign: "middle" }}>
                    {mine?.ai && Object.entries(mine.ai).filter(([, k]) => k === row.key).map(([id]) => <SpeciesAvatar key={id} id={id} size={18} ring={false} />)}
                  </span>
                </td>
                <td>{row.shares}</td>
                <td><Money n={row.seg1} /></td>
                <td><Money n={row.seg2} /></td>
                <td><b><Money n={row.total} /></b></td>
              </tr>
            ))}
          </tbody>
        </table>
        <div className="tiny mt8">快进段：第二天开盘买入，到快进结束；之后：再拿到第 20 个交易日。这张表只按选项一直拿着算，你在快进里的操作已经单独算进自己的账。</div>
        {r.second_rows && (
          <div className="mt8 small">
            {r.second_rows.map((s) => <div key={s.key} className="row between"><span>{s.label}</span><span className="muted">{s.note}</span></div>)}
          </div>
        )}
        </motion.div>}
        </AnimatePresence>
      </div>
      <div className="card ink">
        <div className="kicker" style={{ color: "#F3D27F" }}>这一场的道理</div>
        <div className="display mt4" style={{ fontSize: 24, lineHeight: 1.35 }}>{r.lesson}</div>
      </div>
      {r.egg && (
        <button className="card" style={{ textAlign: "left", background: "#FFF4D6", cursor: "pointer" }} onClick={() => { setEgg(!egg); sfx.paper(); }}>
          <div className="row between"><b>🥚 彩蛋</b><span className="tiny">{egg ? "收起" : "点开"}</span></div>
          <AnimatePresence>{egg && <motion.div initial={{ height: 0, opacity: 0 }} animate={{ height: "auto", opacity: 1 }} exit={{ height: 0, opacity: 0 }} className="small mt8">{r.egg}</motion.div>}</AnimatePresence>
        </button>
      )}
      {first && (
        <div>
          <div className="row gap8 mb8"><span className="panda-tag">PandaAI</span><span className="kicker">在 PandaAI 里接着研究这一场</span></div>
          <div className="col gap8">
            {[first, ...(more ? rest : [])].map((e) => (
              <a key={e.name} href={e.url} target="_blank" rel="noreferrer" className="card" style={{ textDecoration: "none", display: "block", padding: 12 }}>
                <div className="row between"><b>{e.name}</b><span className="pill">{e.kind}</span></div>
                <div className="small muted mt4">{e.why}</div>
                {e.prompt && <div className="tiny mt4" style={{ background: "#fff", border: "1.5px dashed #77745A", borderRadius: 8, padding: "6px 8px" }}>可以这样问：{e.prompt}</div>}
                {e.note && <div className="tiny mt4">{e.note}</div>}
              </a>
            ))}
            {rest.length > 0 && !more && (
              <button className="btn sm block" onClick={() => { sfx.tap(); setMore(true); }}>再看 {rest.length} 个 PandaAI 工具 ▾</button>
            )}
          </div>
        </div>
      )}
      <div className="tiny">{r.source_note}</div>
    </div>
  );
}

export function RevealStep({ scene, onNext }: { scene: Scene; onNext: () => void }) {
  const { g, update } = useGame();
  const rec = cur(g!);
  const m = rec.money!;
  const booked = !!rec.stars;
  const st = starsOf(rec);
  const aiKeys = Object.fromEntries(Object.entries(rec.ai || {}).map(([id, a]) => [id, a.option]));
  const tag = tradeTag(scene, rec);
  const Moment = STAGES[scene.id]?.Moment;
  const [burst, setBurst] = useState(0);
  useEffect(() => {
    if (!tag) return;
    const t = setTimeout(() => { sfx.stamp(); buzz(30); }, 2100);
    return () => clearTimeout(t);
  }, []);
  const rank = [
    { id: "me", d: m.counted, total: g!.money },
    ...Object.entries(rec.ai || {}).map(([id, a]) => ({ id, d: a.total, total: g!.aiMoney[id] ?? 20 })),
  ].sort((a, b) => b.total - a.total);
  function book() {
    setBurst(Date.now());
    buzz(m.counted >= 0 ? [20, 40, 20] : 60);
    sfx.coin();
    setTimeout(() => (m.counted >= 0 ? sfx.gain() : sfx.loss()), 300);
    update((x) => {
      const r = cur(x);
      x.money += m.counted;
      Object.entries(r.ai || {}).forEach(([id, a]) => (x.aiMoney[id] = (x.aiMoney[id] ?? 20) + a.total));
      r.stars = starsOf(r);
    });
  }
  return (
    <div className="pad" style={{ paddingTop: 12 }}>
      <RevealArt scene={scene} />
      {rec.recognized && (
        <Fade delay={1.5}>
          <div className="card mt12 row gap8" style={{ background: rec.recognized.correct ? "#E3F0D9" : "#FBE3DC" }}>
            <span style={{ fontSize: 26 }}>{rec.recognized.correct ? "✅" : "❌"}</span>
            <div className="small">你说认出来了：“{rec.recognized.name}”。{rec.recognized.correct ? "对了，记一次金融史。" : "不是这一次。"}这一场按 AI 平均记，物种币算半枚。</div>
          </div>
        </Fade>
      )}
      <Fade delay={1.6}>
        <div className="card mt12 ledger" style={{ padding: 0, overflow: "hidden" }}>
          <div className="ledger-top">
            <div>
              <div className="tiny bold"><Help k="资金">这一场盈亏</Help></div>
              <div className="display num" style={{ fontSize: 50, lineHeight: 1 }}><Money n={m.counted} u="万" /></div>
              <div className="tiny mt4">快进段 {money(m.seg1)} · 之后 {money(m.seg2)}{m.extra ? ` · 挤着卖出 ${money(m.extra)}` : ""}{rec.recognized ? " · 认出来了，按 AI 平均记" : ""}</div>
            </div>
            {tag && (
              <motion.div className={"trade-stamp " + (tag.good ? "good" : tag.good === false ? "bad" : "")} initial={{ scale: 2.6, rotate: -26, opacity: 0 }} animate={{ scale: 1, rotate: -9, opacity: 1 }} transition={{ delay: 2.1, type: "spring", stiffness: 420, damping: 15 }}>
                {tag.t}
              </motion.div>
            )}
          </div>
          {tag && <div className="ledger-sub small">{tag.sub}</div>}
          <div className="ledger-stars">
            <Help k="方法星"><Stars n={booked ? rec.stars!.total : st.total} /></Help>
            <span className={"lstar" + (st.ev >= 1 ? " on" : "")}>{st.ev >= 2 ? "★★" : "★"} 翻证据</span>
            <span className={"lstar" + (st.consistent ? " on" : "")}>★ 理由对得上</span>
            <span className={"lstar" + (st.plan ? " on" : "")}>★ 计划照做</span>
          </div>
          <div style={{ borderTop: "2px solid #2A2A1C", padding: "10px 14px", background: "#FBF4E4", position: "relative" }}>
            {!booked ? (
              <button className="btn primary block" onClick={book}>入账 {money(m.counted)} 万</button>
            ) : (
              <div className="rank">
                {rank.map((x, i) => (
                  <motion.div key={x.id} className={"rank-row" + (x.id === "me" ? " me" : "")} initial={{ opacity: 0, x: -16 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.15 * i }}>
                    <b className="rank-n">{i + 1}</b>
                    {x.id === "me" ? <span className="rank-me">你</span> : <SpeciesAvatar id={x.id} size={24} />}
                    <span className="small grow">{x.id === "me" ? "你" : sp(x.id).cn}</span>
                    <Money n={x.d} u="万" />
                    <b className="num" style={{ minWidth: 58, textAlign: "right" }}>{x.id === "me" ? <Counter value={x.total} /> : x.total} 万</b>
                  </motion.div>
                ))}
              </div>
            )}
            <AnimatePresence>{burst && <CoinBurst key={burst} up={m.counted >= 0} />}</AnimatePresence>
          </div>
        </div>
      </Fade>
      {Moment && <Fade delay={2.4}><div className="mt12"><Moment /></div></Fade>}
      <div className="mt16"><RevealBody scene={scene} mine={{ key: rec.option, ai: aiKeys }} unit="万" /></div>
      <button className="btn season big block mt16" disabled={!booked} onClick={() => { sfx.tap(); onNext(); }}>{booked ? `去驿站，领这一${g!.mode === "quick" ? "场" : "季"}的物种币 →` : "先点上面的“入账”"}</button>
      <div className="tiny center mt8">{Object.entries(rec.ai || {}).map(([id, a]) => `${sp(id).cn}：${a.line}`).join(" / ")}</div>
    </div>
  );
}
