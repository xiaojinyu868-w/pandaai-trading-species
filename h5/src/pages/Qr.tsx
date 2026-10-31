import { motion } from "framer-motion";
import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import rulesEval from "../data/rules_eval.json";
import { ART, sceneById, SCENES, type EvKind } from "../data";
import { CHANCE, DATAPORT, RETEST, RULES, TASKS, ruleView } from "../game/cards";
import { sp, type SpeciesId, type TaskType } from "../game/meta";
import { useGame } from "../game/store";
import { sfx } from "../lib/sound";
import { BlindView, EvidenceView, EV_CN } from "../screens/Scene";
import { ModelOrFigure } from "../screens/Ending";
import { RevealArt, RevealBody } from "../screens/Reveal";
import { Big } from "../scenes/common";
import { ExampleTag, Money, MuteButton, SpeciesAvatar } from "../ui/kit";
import { levelOf } from "../arcade/bridge";
import { enterQuickScene } from "../screens/Quick";

const EV: any = rulesEval;

export function PageShell({ kicker, children, season }: { kicker: string; children: React.ReactNode; season?: string }) {
  return (
    <div className={"screen" + (season ? ` s-${season}` : "")}>
      <div className="hud">
        <Link to="/" className="display" style={{ textDecoration: "none", fontSize: 18 }}>交易物种起源</Link>
        <span className="grow" />
        <span className="pill season">{kicker}</span>
        <MuteButton />
      </div>
      <div className="pad">{children}</div>
      <div className="compliance">投资者教育游戏，不构成投资建议 · 扫码页面不需要登录，也不记录你的任何信息</div>
    </div>
  );
}

export function QrResolve() {
  const { code } = useParams();
  const nav = useNavigate();
  const [miss, setMiss] = useState(false);
  useEffect(() => {
    fetch(`${import.meta.env.BASE_URL}q-map.json`, { cache: "no-store" })
      .then((r) => r.json())
      .then((m) => {
        const route = m[code || ""] || m.codes?.[code || ""];
        if (route) nav(route, { replace: true });
        else setMiss(true);
      })
      .catch(() => setMiss(true));
  }, [code]);
  return (
    <PageShell kicker="扫码">
      {miss ? (
        <div className="card center"><div className="h3">这个码没有找到</div><p className="small">可能是印刷版本较旧。可以直接从首页开始。</p><Link className="btn primary mt8" to="/">去首页</Link></div>
      ) : (
        <div className="center" style={{ paddingTop: 80 }}><motion.div animate={{ rotate: 360 }} transition={{ repeat: Infinity, duration: 1.2, ease: "linear" }} style={{ width: 48, height: 48, borderRadius: "50%", border: "5px solid #2A2A1C", borderTopColor: "#D4432A", margin: "0 auto" }} /><p className="small mt12">正在打开……</p></div>
      )}
    </PageShell>
  );
}

export function StartPage() {
  const nav = useNavigate();
  const { g, start, startQuick } = useGame();
  const going = !!g && g.phase !== "ending" && g.source === "h5";
  return (
    <PageShell kicker="开局">
      <div className="poster" style={{ aspectRatio: "300 / 215" }}><img src={ART("box_cover")} alt="" /></div>
      <h2 className="h2 mt16">你拿到的是《交易物种起源》</h2>
      <p className="body mt8">回到真实的金融史时刻，日期被藏起来。你怎么做决定，就会孵出什么物种。纸上能完整玩一局；手机上也能和 AI 物种对局。</p>
      <div className="col gap8 mt12">
        <button className="btn primary big block" onClick={() => { sfx.bell(); startQuick(); nav("/play"); }}>先玩一场 · 3 分钟</button>
        <button className="btn block" onClick={() => { sfx.tap(); if (!going) start(); nav("/play"); }}>{going ? "继续上一局" : "在手机上玩完整四季 · 约 10 分钟"}</button>
        <Link to="/record" className="btn block">桌游玩完了：录入记录卡，拿完整画像</Link>
        <Link to="/ff/scb" className="btn block">熔断沙漏计时器（冬季用）</Link>
        <Link to="/atlas" className="btn block">物种图鉴</Link>
      </div>
    </PageShell>
  );
}

/** 桌上扫到名场面的码：可以直接在手机上玩这一场（同一张卡、同一段行情） */
function PlayHere({ id }: { id: string }) {
  const nav = useNavigate();
  const { startQuick, update } = useGame();
  if (!levelOf(id)) return null;
  return (
    <button className="btn primary big block mt12" onClick={() => { sfx.bell(); startQuick(); update((x) => enterQuickScene(x, id as never)); nav("/play"); }}>
      在手机上玩这一场 →
    </button>
  );
}

export function BlindPage() {
  const { scene: id } = useParams();
  const s = sceneById(id || "");
  if (!s) return <PageShell kicker="盲测">没有这个场景</PageShell>;
  return (
    <PageShell kicker={`${s.season_cn} · 盲测`} season={s.season}>
      <BlindView scene={s} />
      <div className="card mt12" style={{ background: "var(--season)", color: "#fff8ec" }}>
        <div className="small bold">{s.blind.position}</div>
        <div className="display mt4" style={{ fontSize: 24 }}>{s.blind.question}</div>
      </div>
      <div className="tiny mt12">桌游里：每人每轮花 1 研究点看一张证据，看完扣回原处。证据牌背面的码，也能在手机上看。</div>
      <div className="row wrap gap8 mt8">{(["price", "data", "news", "tip"] as EvKind[]).map((k) => <Link key={k} to={`/e/${s.id}/${k}`} className="btn sm">{EV_CN[k]}</Link>)}</div>
      <PlayHere id={s.id} />
    </PageShell>
  );
}

export function EvidencePage() {
  const { scene: id, kind } = useParams();
  const s = sceneById(id || "");
  const ev = s?.evidence[kind as EvKind];
  if (!s || !ev) return <PageShell kicker="证据">没有这张证据</PageShell>;
  return (
    <PageShell kicker={`${s.season_cn} · ${EV_CN[ev.kind]}`} season={s.season}>
      <motion.div initial={{ rotateX: -60, opacity: 0 }} animate={{ rotateX: 0, opacity: 1 }} style={{ transformPerspective: 900 }}><EvidenceView ev={ev} scene={s} /></motion.div>
      <div className="tiny mt12">看完把牌扣回原处。别告诉别人你看到了什么。</div>
    </PageShell>
  );
}

export function RevealPage() {
  const { scene: id } = useParams();
  const s = sceneById(id || "");
  useEffect(() => {
    sfx.reveal();
  }, []);
  if (!s) return <PageShell kicker="揭幕">没有这个场景</PageShell>;
  return (
    <PageShell kicker={`${s.season_cn} · 揭幕`} season={s.season}>
      <RevealArt scene={s} />
      <div className="mt12"><RevealBody scene={s} /></div>
    </PageShell>
  );
}

export function BreakerPage() {
  const { scene: id } = useParams();
  const s = sceneById(id || "scb") || sceneById("scb")!;
  const cards = s.fast_forward.cards;
  const [ci, setCi] = useState(-1);
  const [left, setLeft] = useState(0);
  useEffect(() => {
    if (left <= 0) return;
    const t = setTimeout(() => {
      setLeft(left - 1);
      sfx.heart();
      if (left - 1 === 0) sfx.bell();
    }, 1000);
    return () => clearTimeout(t);
  }, [left]);
  return (
    <PageShell kicker="熔断沙漏" season={s.season}>
      <h2 className="h2">{s.fast_forward.title}</h2>
      <div className="col gap6 mt8 small">{s.fast_forward.board_rules.map((r, i) => <div key={i}>{i + 1}. {r}</div>)}</div>
      {ci >= 0 && ci < cards.length && (
        <div className="card mt12" style={{ background: left > 0 ? "#111" : "#FBF4E4", color: left > 0 ? "#FBF4E4" : undefined }}>
          <div className="kicker" style={{ color: left > 0 ? "#F3D27F" : undefined }}>{cards[ci].title}</div>
          {left > 0 ? (
            <div className="center mt8"><Big color="#FBF4E4">{left}</Big><div className="small mt8">不许说话，不许碰牌</div></div>
          ) : (
            <ul className="body" style={{ paddingLeft: 18 }}>{cards[ci].lines.map((l, i) => <li key={i}>{l}</li>)}<li><b>这一段每份 {cards[ci].per_share}</b></li></ul>
          )}
        </div>
      )}
      <div className="col gap8 mt12">
        {ci < cards.length - 1 && <button className="btn primary big block" onClick={() => { sfx.alarm(); setCi(ci + 1); }}>{ci < 0 ? "翻第 1 张熔断牌" : `翻第 ${ci + 2} 张熔断牌`}</button>}
        {ci >= 0 && left === 0 && ci < cards.length - 1 && <button className="btn dark block" onClick={() => setLeft(30)}>翻沙漏：30 秒</button>}
        {ci === cards.length - 1 && <div className="card" style={{ background: "#FFF4D6" }}><b>{s.fast_forward.second_decision?.prompt}</b><div className="small mt4">补仓、止损，还是不看了？写在委托单上，然后扫揭幕码。</div><Link className="btn sm mt8" to={`/r/${s.id}`}>揭幕 →</Link></div>}
      </div>
      {ci < 0 && <PlayHere id={s.id} />}
    </PageShell>
  );
}

export function RuleEvalTable({ rule, revealed = "all" }: { rule: string; revealed?: string[] | "all" }) {
  const res = EV.rules?.[rule];
  if (!res) return null;
  const open = (sid: string) => revealed === "all" || revealed.includes(sid);
  return (
    <table className="ptable mt8">
      <thead><tr><th>名场面</th><th>规则怎么做</th><th>结果</th></tr></thead>
      <tbody>
        {Object.entries(res).map(([sid, r]: any) => {
          const s = sceneById(sid);
          return (
            <tr key={sid}>
              <td>{s?.season_cn} · {open(sid) ? s?.title.split(" · ")[0] : <span className="muted">{s?.blind.headline}</span>}</td>
              <td className="tiny" style={{ textAlign: "left" }}>{r.applicable ? r.trades.map((t: any) => `${t.date.slice(5)} ${t.action}`).join("；") : r.note}</td>
              <td>{r.applicable ? <Money n={r.total} /> : "—"}</td>
            </tr>
          );
        })}
      </tbody>
    </table>
  );
}

export function RulePage() {
  const { id } = useParams();
  const { g } = useGame();
  const [all, setAll] = useState(false);
  const r = RULES.find((x) => x.id === id);
  if (!r) return <PageShell kicker="规则牌">没有这张规则牌</PageShell>;
  const played = (g?.seasons || []).filter((x) => x.stars).map((x) => x.scene as string);
  const revealed = all ? SCENES.map((s) => s.id) : played;
  const v = ruleView(r, revealed);
  const hidden = SCENES.some((s) => !revealed.includes(s.id));
  return (
    <PageShell kicker="规则牌">
      <div className="card ink">
        <span className="pill" style={{ background: "#C79A2E" }}>{r.does || "规则"}</span>
        <div className="h2 mt8">{v.name}</div>
        <div className="body mt8">{r.text}</div>
      </div>
      <div className="h3 mt16">放回名场面会怎样？</div>
      <RuleEvalTable rule={r.id} revealed={revealed} />
      <div className="tiny mt4">{EV.note}</div>
      {hidden && <button className="btn sm mt8" onClick={() => setAll(true)}>六个名场面都揭幕了？显示真名</button>}
      {v.qube && (
        <div className="card mt12" style={{ background: "#FFF4D6" }}>
          <div className="kicker">想自己验证？把这句话发给 Qube</div>
          <div className="body mt4">“{v.qube}”</div>
          <button className="btn sm mt8" onClick={() => navigator.clipboard?.writeText(v.qube || "").then(() => sfx.coin(), () => {})}>复制这句话</button>
        </div>
      )}
      {r.real && <a className="btn primary block mt12" href={r.real.url} target="_blank" rel="noreferrer">去 {r.real.name} ↗</a>}
      {r.real && <div className="tiny center mt4">登录 PandaAI 后可用</div>}
    </PageShell>
  );
}

export function SpeciesPage() {
  const { id } = useParams();
  const s = sp(id || "");
  if (!s) return <PageShell kicker="物种">没有这个物种</PageShell>;
  return (
    <PageShell kicker="物种牌">
      <div className="poster" style={{ height: 380 }}><img src={ART(`species_${s.id}`)} alt="" style={{ objectPosition: "50% 15%" }} /></div>
      <h2 className="display mt12" style={{ fontSize: 48 }}>{s.cn}</h2>
      <div className="h3">{s.tagline}</div>
      <div className="col gap8 mt12 body">
        <div><b>风格：</b>{s.style}</div>
        <div><b>典型做法：</b>{s.behavior}</div>
        <div><b>擅长：</b>{s.strength}</div>
        <div><b>要留意：</b>{s.watch}</div>
        <div><b>默认推荐方向：</b>{s.rec}</div>
      </div>
      <div className="tiny mt12">物种只表示偏好，不分高低。游戏里的风险表现没有真钱，只做参考。</div>
      <div className="mt16"><ModelOrFigure id={s.id} /></div>
    </PageShell>
  );
}

export function TaskPage() {
  const { id } = useParams();
  const [type, level] = (id || "").split("-") as [TaskType, "basic" | "adv"];
  const t = TASKS.find((x) => x.type === type && x.level === level);
  if (!t) return <PageShell kicker="任务牌">没有这张任务牌</PageShell>;
  return (
    <PageShell kicker="任务牌">
      <span className="pill dark">{t.cn}</span>
      <h2 className="h2 mt8">{t.now}</h2>
      <div className="small muted mt4">给谁：{t.who}</div>
      {t.type === "hypo" && (<><div className="h3 mt16">示例：5/20 双均线放回五个名场面</div><RuleEvalTable rule="rule-ma520" /></>)}
      <div className="col gap8 mt16">
        {t.resources.map((r) => (
          <a key={r.name} href={r.url} target="_blank" rel="noreferrer" className="card" style={{ textDecoration: "none" }}>
            <div className="row between"><b>{r.name}</b><span className="tiny">{r.kind} ↗</span></div>
            {r.note && <div className="tiny mt4">{r.note}</div>}
            {r.example && <div className="mt4"><ExampleTag>示例入口，具体课程待选</ExampleTag></div>}
          </a>
        ))}
      </div>
    </PageShell>
  );
}

export function DataPortPage() {
  const { id } = useParams();
  const d = DATAPORT.find((x) => x.id === id) || DATAPORT[0];
  const [a, setA] = useState<number | null>(null);
  return (
    <PageShell kicker="数据港口">
      <div className="h3">{d.title}</div>
      <pre style={{ background: "#1f2a26", color: "#d9f0c8", borderRadius: 12, padding: 12, fontSize: 12.5, overflowX: "auto" }}>{d.code}</pre>
      <p className="bold">{d.q}</p>
      <div className="col gap8">{d.a.map((x, i) => <button key={i} className={"opt" + (a === i ? " on" : "")} style={{ gridTemplateColumns: "38px 1fr", background: a != null && i === d.correct ? "#E3F0D9" : undefined }} onClick={() => setA(i)}><span className="key">{"ABC"[i]}</span><span>{x}</span></button>)}</div>
      {a != null && <div className="card mt12" style={{ background: a === d.correct ? "#E3F0D9" : "#FBE3DC" }}><b>{a === d.correct ? "答对了：拿 1 研究点" : "差一点"}</b><div className="small mt4">{d.explain}</div></div>}
      <a className="btn block mt12" href="https://www.pandaaiquant.com/docs/api" target="_blank" rel="noreferrer">Panda Data 接口文档 ↗</a>
    </PageShell>
  );
}

export function CardPage() {
  const { id } = useParams();
  const c = [...CHANCE, ...RETEST].find((x) => x.id === id);
  const [a, setA] = useState<number | null>(null);
  if (!c) return <PageShell kicker="卡牌">没有这张牌</PageShell>;
  return (
    <PageShell kicker={id?.startsWith("chance") ? "机会牌" : "补测牌"}>
      {"dimension" in c && <span className="pill dark">{(c as any).dimension}</span>}
      <h2 className="h2 mt8">{c.q}</h2>
      <div className="col gap8 mt12">{c.a.map((x, i) => <button key={i} className={"opt" + (a === i ? " on" : "")} style={{ gridTemplateColumns: "38px 1fr" }} onClick={() => setA(i)}><span className="key">{"甲乙丙丁"[i]}</span><span>{x.text}</span></button>)}</div>
      {a != null && c.a[a].species === "other" && (
        <div className="card mt12"><div className="h3">一直是同一套</div><div className="small mt4">平局时：如果打平的两种里有变色龙，拿另一种；两种都不是变色龙，就在两种里自己挑，档案卡上记“待确认”。</div></div>
      )}
      {a != null && c.a[a].species !== "other" && (
        <div className="card mt12 row gap12"><SpeciesAvatar id={c.a[a].species as SpeciesId} size={56} /><div><div className="tiny">这个回答像</div><div className="h3">{sp(c.a[a].species).cn}</div><div className="tiny">{id?.startsWith("chance") ? "记 1 个物种图标" : "按这个答案拿币"}</div></div></div>
      )}
      {a != null && "why" in c && (c as any).why && <div className="small muted mt8">{(c as any).why}</div>}
    </PageShell>
  );
}

export function SceneIndex() {
  return <div className="col gap8">{SCENES.map((s) => <Link key={s.id} to={`/b/${s.id}`} className="btn block">{s.season_cn} · {s.title}</Link>)}</div>;
}
