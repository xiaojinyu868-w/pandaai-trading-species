import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { SEASONS, sceneById, type EvKind, type OptKey, type SceneId } from "../data";
import { iconsOf, starsOf, topOf } from "../game/engine";
import { PICKABLE, PLANS, REASONS, sp, SPECIES, type Plan, type Reason, type SpeciesId } from "../game/meta";
import { freshGame, newSeason, useGame, type SeasonRec } from "../game/store";
import { sfx } from "../lib/sound";
import { PageShell } from "./Qr";

interface Row { scene: SceneId; evidence: EvKind[]; option?: OptKey; reason?: Reason; plan: Plan; followed: boolean; recognized: boolean; recCorrect: boolean; coin?: SpeciesId; half: boolean }
const EVK: { k: EvKind; cn: string }[] = [{ k: "price", cn: "量价" }, { k: "data", cn: "数据" }, { k: "news", cn: "消息" }, { k: "tip", cn: "锦囊" }];

export function RecordPage() {
  const nav = useNavigate();
  const { update } = useGame();
  const [self, setSelf] = useState<SpeciesId | null>(null);
  const [rows, setRows] = useState<Row[]>(SEASONS.map((s) => ({ scene: s.doors[0], evidence: [], plan: "none", followed: true, recognized: false, recCorrect: false, half: false })));
  const [tab, setTab] = useState(0);
  const [dp, setDp] = useState(0);
  const [money, setMoney] = useState(20);
  const r = rows[tab];
  const set = (patch: Partial<Row>) => setRows(rows.map((x, i) => (i === tab ? { ...x, ...patch } : x)));
  const scene = sceneById(r.scene)!;
  const autoTop = (x: Row, i: number) => topOf(iconsOf({ ...newSeason(SEASONS[i].id), scene: x.scene, evidence: x.evidence, option: x.option, reason: x.reason, plan: x.plan }).icons).top;
  const coinOk = (x: Row, i: number) => !!x.coin || autoTop(x, i).length === 1;
  const ready = self && rows.every((x, i) => x.option && x.reason && coinOk(x, i));

  function build() {
    const g = freshGame();
    g.source = "record";
    g.self = self!;
    g.opponents = [];
    g.aiMoney = {};
    g.money = money;
    g.dataportRight = dp;
    g.dataportSeen = dp;
    g.seasons = rows.map((x, i) => {
      const rec: SeasonRec = { ...newSeason(SEASONS[i].id), scene: x.scene, door: sceneById(x.scene)!.door, evidence: x.evidence, option: x.option, reason: x.reason, plan: x.plan };
      rec.recognized = x.recognized ? { name: x.recCorrect ? sceneById(x.scene)!.title : "（写错了）", correct: x.recCorrect } : null;
      rec.ff = { actions: [], changes: 0, planTriggered: x.plan !== "none", planFollowed: x.plan === "none" ? true : x.followed, ruleFollowed: x.reason === "rule" ? true : null };
      const { icons } = iconsOf(rec);
      rec.icons = icons;
      rec.coin = x.coin || topOf(icons).top[0];
      rec.coinHalf = x.recognized;
      rec.stars = starsOf(rec);
      return rec;
    });
    g.seasonIdx = 3;
    g.phase = "ending";
    g.finishedAt = Date.now();
    useGame.setState({ g });
    sfx.fanfare();
    nav("/play");
  }

  return (
    <PageShell kicker="录入记录卡">
      <h2 className="h2">把纸上的记录卡录进来</h2>
      <p className="small muted mt4">照着记录卡点 30 秒，生成带证据和置信度的完整画像。只存在这台手机里。</p>
      <div className="card mt12">
        <b className="small">序章里你圈的“我觉得我是”</b>
        <div className="row wrap gap6 mt8">{PICKABLE.map((s) => <button key={s.id} className={"chip" + (self === s.id ? " on" : "")} onClick={() => setSelf(s.id)}>{s.cn}</button>)}</div>
      </div>
      <div className="row gap6 mt12">
        {SEASONS.map((s, i) => (
          <button key={s.id} className={`chip s-${s.id}` + (tab === i ? " on" : "")} style={{ flex: 1, background: tab === i ? "var(--season)" : undefined, color: tab === i ? "#fff" : undefined }} onClick={() => setTab(i)}>
            {s.cn}{rows[i].option && rows[i].reason && coinOk(rows[i], i) ? " ✓" : ""}
          </button>
        ))}
      </div>
      <div className={`card mt8 s-${SEASONS[tab].id}`}>
        {SEASONS[tab].doors.length > 1 && (
          <div className="mb12"><b className="small">走的哪扇门</b><div className="row gap6 mt4">{SEASONS[tab].doors.map((d) => <button key={d} className={"chip" + (r.scene === d ? " on" : "")} onClick={() => set({ scene: d })}>{sceneById(d)!.door} · {sceneById(d)!.title.split(" · ")[0]}</button>)}</div></div>
        )}
        <b className="small">看了哪些证据（按顺序点，第一张最重要）</b>
        <div className="row wrap gap6 mt4">{EVK.map((e) => <button key={e.k} className={"chip" + (r.evidence.includes(e.k) ? " on" : "")} onClick={() => set({ evidence: r.evidence.includes(e.k) ? r.evidence.filter((x) => x !== e.k) : [...r.evidence, e.k] })}>{e.cn}{r.evidence.indexOf(e.k) === 0 ? "（第一张）" : ""}</button>)}</div>
        <b className="small mt12" style={{ display: "block" }}>选项</b>
        <div className="row wrap gap6 mt4">{scene.options.map((o) => <button key={o.key} className={"chip" + (r.option === o.key ? " on" : "")} onClick={() => set({ option: o.key })}>{o.key} {o.label}</button>)}</div>
        <b className="small mt12" style={{ display: "block" }}>理由</b>
        <div className="row wrap gap6 mt4">{REASONS.map((x) => <button key={x.id} className={"chip" + (r.reason === x.id ? " on" : "")} onClick={() => set({ reason: x.id })}>{x.cn}</button>)}</div>
        <b className="small mt12" style={{ display: "block" }}>计划</b>
        <div className="row wrap gap6 mt4">{PLANS.map((p) => <button key={p.id} className={"chip" + (r.plan === p.id ? " on" : "")} onClick={() => set({ plan: p.id })}>{p.cn}</button>)}</div>
        {r.plan !== "none" && <label className="small row gap6 mt8"><input type="checkbox" checked={r.followed} onChange={(e) => set({ followed: e.target.checked })} /> 快进时照计划做了</label>}
        <label className="small row gap6 mt8"><input type="checkbox" checked={r.recognized} onChange={(e) => set({ recognized: e.target.checked })} /> 这一场我认出来了</label>
        {r.recognized && <label className="small row gap6 mt4"><input type="checkbox" checked={r.recCorrect} onChange={(e) => set({ recCorrect: e.target.checked })} /> 事件名写对了</label>}
        <b className="small mt12" style={{ display: "block" }}>这一季拿的物种币（不填就按记录自动算）</b>
        {r.option && r.reason && !coinOk(r, tab) && <div className="tiny mt4" style={{ color: "#B23A22" }}>按记录算不出唯一的物种（没有图标，或者打平了）：照委托单点你拿的那枚币。</div>}
        <div className="row wrap gap6 mt4">{SPECIES.filter((s) => !s.hidden).map((s) => <button key={s.id} className={"chip" + (r.coin === s.id ? " on" : "")} onClick={() => set({ coin: r.coin === s.id ? undefined : s.id })}>{s.cn}</button>)}</div>
      </div>
      <div className="card mt12 row between">
        <span className="small bold">数据港口答对几次</span>
        <span className="row gap6">{[0, 1, 2, 3].map((n) => <button key={n} className={"chip" + (dp === n ? " on" : "")} onClick={() => setDp(n)}>{n}</button>)}</span>
      </div>
      <div className="card mt12 row between">
        <span className="small bold">终局资金</span>
        <input type="number" value={money} onChange={(e) => setMoney(Number(e.target.value))} style={{ width: 90, padding: "6px 10px", border: "2px solid #2A2A1C", borderRadius: 10, fontSize: 16 }} />
      </div>
      <button className="btn primary big block mt16" disabled={!ready} onClick={build}>{ready ? "生成我的完整画像" : "四季都填好选项、理由和物种币"}</button>
      {self && <div className="tiny center mt8">自评：{sp(self).cn}</div>}
    </PageShell>
  );
}
