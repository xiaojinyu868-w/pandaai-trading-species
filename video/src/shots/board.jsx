import React from 'react';
import {useT, useDur, prog, eo, ex, eio, sio, lerp, clamp, rise, fadeOut, art, pr, Stamp, Flip, Phone} from '../lib.jsx';

const Desk = () => <div className="desk" />;
const SEASON = {春: 'var(--spring)', 夏: 'var(--summer)', 秋: 'var(--autumn)', 冬: 'var(--winter)'};
const Card = ({src, x, y, w, h, rot = 0, style}) => <div className="card" style={{left: x, top: y, width: w, height: h, transform: `rotate(${rot}deg)`, ...style}}><img src={src} alt="" /></div>;
const Label = ({t, at, children, x, y, color, style}) => <div className="label" style={{left: x, top: y, ...(color ? {background: color} : {}), ...rise(t, at, {y: 16}), ...style}}>{children}</div>;
const Head = ({t, kicker, title, at = 0.1, x = 110, y = 70}) => <div className="abs on-desk" style={{left: x, top: y}}>
  <div className="kicker" style={{color: '#c9b896', ...rise(t, at, {y: 12})}}>{kicker}</div>
  <div className="h2" style={{marginTop: 8, ...rise(t, at + 0.1, {y: 20})}}>{title}</div>
</div>;
/** 勾选：在图片上 fx、fy 的位置画一个红勾 */
const Tick = ({t, at, fx, fy, W, H, size = 46}) => {
  const k = eo(prog(t, at, 0.25));
  return <svg className="abs" width={size} height={size} viewBox="0 0 40 40" style={{left: fx * W - size * 0.3, top: fy * H - size * 0.62, overflow: 'visible'}}>
    <path d="M6 22 L16 32 L36 6" fill="none" stroke="var(--kite)" strokeWidth="7" strokeLinecap="round" strokeLinejoin="round" pathLength="1" strokeDasharray="1" strokeDashoffset={1 - k} />
  </svg>;
};
const Ring = ({t, at, x, y, w, h, color = 'var(--kite)'}) => {
  const k = eo(prog(t, at, 0.5));
  return <svg className="abs" width={w} height={h} style={{left: x, top: y, overflow: 'visible'}}>
    <ellipse cx={w / 2} cy={h / 2} rx={w / 2} ry={h / 2} fill="none" stroke={color} strokeWidth="9" pathLength="1" strokeDasharray="1" strokeDashoffset={1 - k} transform={`rotate(-8 ${w / 2} ${h / 2})`} />
  </svg>;
};
const Hi = ({t, at, x, y, w, h, until = 99}) => <div className="abs" style={{left: x, top: y, width: w, height: h, border: '6px solid var(--sun)', borderRadius: 12, boxShadow: '0 0 0 9999px rgba(20,16,12,.35)', opacity: eo(prog(t, at, 0.3)) * (1 - prog(t, until, 0.3))}} />;

export function BTitle() {
  const t = useT();
  const k = ex(prog(t, 0.1, 0.5));
  return <>
    <Desk />
    <div className="card" style={{left: 510, top: 140, width: 900, height: 650, transform: `scale(${lerp(1.25, 1, k)}) rotate(${lerp(-4, -1.5, k)}deg)`, opacity: k}}><img src={pr('box_lid')} alt="" /></div>
    <div className="abs" style={{left: 0, right: 0, top: 830, textAlign: 'center'}}>
      <div className="h1 on-desk" style={{fontSize: 92, ...rise(t, 0.8, {y: 24})}}>桌游怎么玩</div>
      <div className="kicker" style={{color: '#c9b896', marginTop: 6, ...rise(t, 1.0, {y: 10})}}>How to play</div>
    </div>
  </>;
}

export function B01() {
  const t = useT();
  const lid = eio(prog(t, 0.3, 0.8));
  const spread = ['sp_cheetah', 'scene_s2015', 'ev_s2015_price', 'reveal_s2015', 'ai_meerkat', 'task_hyp'];
  return <>
    <Desk />
    <div className="card" style={{left: lerp(510, 80, lid), top: lerp(140, 70, lid), width: lerp(900, 420, lid), height: lerp(650, 303, lid), transform: `rotate(${lerp(-1.5, -6, lid)}deg)`}}><img src={pr('box_lid')} alt="" /></div>
    <div className="card" style={{left: 560, top: 120, width: 1000, height: 711, ...rise(t, 0.8, {y: 80, s: 0.94})}}><img src={pr('board')} alt="" /></div>
    {spread.map((c, i) => <Card key={c} src={pr(c)} x={1380 + (i % 3) * 150} y={520 + Math.floor(i / 3) * 120} w={190} h={i === 1 || i === 3 || i === 0 ? 263 : 258} rot={(i - 2.5) * 6} style={rise(t, 1.4 + i * 0.12, {x: 120, y: -40})} />)}
    <Card src={pr('slip_summer_color')} x={130} y={480} w={330} h={465} rot={-4} style={rise(t, 2.0, {x: -80})} />
    <div className="abs" style={{left: 560, top: 870, display: 'flex', gap: 18}}>
      {[['1–5 人', 2.6], ['展台快玩 15 分钟', 3.9], ['完整一局 60–90 分钟', 5.6]].map(([x, at]) => <span key={x} className="chip" style={{fontSize: 36, ...rise(t, at, {y: 14})}}>{x}</span>)}
    </div>
  </>;
}

export function B02() {
  const t = useT();
  const W = 1350, H = 959, X = 285, Y = 40;
  const pb = eio(prog(t, 7.0, 0.7));
  const edges = [
    {s: '春', name: '春 · 入场', at: 2.3, r: {left: 0, top: 0, width: W, height: H * 0.17}, l: {x: X + W * 0.4, y: Y + H * 0.06}},
    {s: '夏', name: '夏 · 狂热', at: 3.6, r: {left: W * 0.87, top: 0, width: W * 0.13, height: H}, l: {x: X + W * 0.68, y: Y + H * 0.45}},
    {s: '秋', name: '秋 · 松动', at: 4.8, r: {left: 0, top: H * 0.83, width: W, height: H * 0.17}, l: {x: X + W * 0.4, y: Y + H * 0.78}},
    {s: '冬', name: '冬 · 危机', at: 6.0, r: {left: 0, top: 0, width: W * 0.13, height: H}, l: {x: X + W * 0.15, y: Y + H * 0.45}},
  ];
  return <>
    <Desk />
    <div className="abs" style={{left: X, top: Y, width: W, height: H, transform: `translateX(${-pb * 260}px) scale(${lerp(1, 0.86, pb)})`, transformOrigin: '0 50%'}}>
      <div className="card" style={{left: 0, top: 0, width: W, height: H}}><img src={pr('board')} alt="" /></div>
      {edges.map(e => <div key={e.s} className="abs" style={{...e.r, border: `8px solid ${SEASON[e.s]}`, background: SEASON[e.s].replace('var(', '').length ? 'rgba(255,255,255,.0)' : '', borderRadius: 10, opacity: eo(prog(t, e.at, 0.3)) * (1 - prog(t, 6.9, 0.3))}} />)}
    </div>
    {edges.map(e => <Label key={e.s} t={t} at={e.at} x={e.l.x} y={e.l.y} color={SEASON[e.s]} style={{opacity: 1 - prog(t, 6.9, 0.3)}}>{e.name}</Label>)}
    <div className="card" style={{left: 1080, top: 230, width: 760, height: 543, transform: `translateX(${(1 - pb) * 900}px) rotate(2deg)`}}><img src={pr('playerboard')} alt="" /></div>
    <div className="abs" style={{left: 1100, top: 820, display: 'flex', gap: 18}}>
      <span className="chip" style={{fontSize: 38, ...rise(t, 8.9, {y: 14})}}>资金 20 万</span>
      <span className="chip" style={{fontSize: 38, ...rise(t, 10.0, {y: 14})}}>研究点 1</span>
    </div>
  </>;
}

const SIX = ['cheetah', 'elephant', 'fox', 'owl', 'meerkat', 'chameleon'];
export function B03() {
  const t = useT();
  const flip = eio(prog(t, 5.6, 0.6));
  return <>
    <Desk />
    <Head t={t} kicker="开局 · 偷偷自评" title="我觉得我是……" />
    {SIX.map((s, i) => <Card key={s} src={pr('sp_' + s)} x={110 + i * 205} y={300} w={190} h={264} rot={(i - 2.5) * 2} style={rise(t, 0.3 + i * 0.1, {y: 50})} />)}
    <Ring t={t} at={2.4} x={110 + 3 * 205 - 26} y={270} w={242} h={326} />
    <div className="abs" style={{left: 1400, top: 200, width: 420, height: 588, perspective: 1600}}>
      <Flip front={pr('scene_back_s924')} back={pr('record_front')} p={flip} w={420} h={588} />
    </div>
    <Label t={t} at={6.2} x={1430} y={820}>扣好，最后再翻开</Label>
  </>;
}

const TILES = [['supply', '补给站'], ['chance', '机会'], ['research', '研究所'], ['dataport', '数据港口'], ['calm', '冷静亭']];
export function B04() {
  const t = useT();
  const roll = prog(t, 0.6, 1.0);
  return <>
    <Desk />
    <Head t={t} kicker="一季 · 掷骰子" title="两颗骰子，挑一个点数往前走" />
    <div className="abs" style={{left: 1380, top: 60, width: 420, height: 372, transform: `translate(${(1 - eo(roll)) * 500}px, ${Math.sin(roll * Math.PI) * -80}px) rotate(${(1 - eo(roll)) * 260}deg)`, opacity: roll > 0 ? 1 : 0}}>
      <img src={art('icon_dice')} alt="" style={{width: 420, height: 372, objectFit: 'contain'}} />
    </div>
    <span className="chip abs" style={{left: 1420, top: 440, fontSize: 32, ...rise(t, 2.0)}}>1–5 去对应的小格 · 6 直达门口</span>
    {TILES.map(([k, cn], i) => <div key={k} className="abs" style={{left: 110 + i * 350, top: 540, width: 320, textAlign: 'center', ...rise(t, 4.5 + i * 0.75, {y: 60})}}>
      <img src={art('tile_' + k)} alt="" style={{width: 280, height: 280, margin: '0 auto', objectFit: 'contain'}} />
      <div className="h3 on-desk" style={{marginTop: 4}}><span style={{fontSize: 30, opacity: .7, marginRight: 8}}>{i + 1}</span>{cn}</div>
    </div>)}
  </>;
}

export function B05() {
  const t = useT();
  const flip = eio(prog(t, 1.7, 0.7));
  const zoom = eio(prog(t, 4.6, 1.2));
  return <>
    <Desk />
    <Head t={t} kicker="夏 · 名场面之门" title="翻开场景牌" />
    <div className="abs" style={{left: 660, top: 40, width: 600, height: 832, transform: `scale(${lerp(1, 1.55, zoom)})`, transformOrigin: '50% 72%'}}>
      <Flip front={pr('scene_s2015')} back={pr('scene_back_s2015')} p={flip} w={600} h={832} />
    </div>
    <Stamp t={t} at={6.0} rot={-8} size={64} style={{left: 160, top: 520}}>没有名字</Stamp>
    <Stamp t={t} at={6.9} rot={6} size={64} style={{left: 1400, top: 520}}>没有日期</Stamp>
  </>;
}

const SW = 640, SH = 903;
export function B06() {
  const t = useT();
  const tok = ex(prog(t, 3.4, 0.4));
  const typed = '2015 杠杆牛'.slice(0, Math.round(9 * prog(t, 1.9, 1.0)));
  return <>
    <Desk />
    <Head t={t} kicker="认出来了？" title="写下事件名，放一枚认出令牌" />
    <div className="card" style={{left: 140, top: 230, width: SW, height: SH}}><img src={pr('slip_summer_color')} alt="" />
      <div className="abs" style={{left: SW * 0.27, top: SH * 0.155, fontFamily: 'var(--display)', fontSize: 44, color: 'var(--sky-deep)', transform: 'rotate(-2deg)'}}>{typed}</div>
    </div>
    <Hi t={t} at={1.2} x={140 + SW * 0.04} y={230 + SH * 0.155} w={SW * 0.92} h={SH * 0.06} until={5.5} />
    <div className="abs" style={{left: 980, top: 300, width: 220, height: 220, borderRadius: '50%', background: 'var(--sun)', border: '8px solid var(--ink)', boxShadow: '0 16px 30px rgba(0,0,0,.45)', display: 'flex', alignItems: 'center', justifyContent: 'center', transform: `translateY(${(1 - tok) * -400}px) scale(${lerp(1.4, 1, tok)})`, opacity: tok > 0 ? 1 : 0}}>
      <span className="h2" style={{fontSize: 96}}>认</span>
    </div>
    <div className="abs on-desk" style={{left: 980, top: 600, width: 860}}>
      <div className="h3" style={rise(t, 5.9, {x: 30, y: 0})}>这一场的钱，记<span style={{color: 'var(--sun)'}}>其他人的平均</span></div>
      <div className="h3" style={{marginTop: 30, ...rise(t, 8.8, {x: 30, y: 0})}}>物种币放空心面，<span style={{color: 'var(--sun)'}}>只算半枚</span></div>
    </div>
  </>;
}

const EV = [['price', '量价', 2.6], ['data', '数据', 3.2], ['news', '消息', 3.8], ['tip', '锦囊', 4.6]];
export function B07() {
  const t = useT();
  const fp = eio(prog(t, 2.7, 0.6));
  return <>
    <Desk />
    <Head t={t} kicker="开证据 · 花 1 研究点看 1 张" title="先看哪一张，也是线索" at={6.6} />
    {EV.map(([k, cn, at], i) => {
      const x = 170 + i * 420, open = i === 0;
      return <div key={k} className="abs" style={{left: x, top: 260, ...rise(t, 0.2 + i * 0.12, {y: 60})}}>
        <Flip front={pr('ev_s2015_' + k)} back={pr('ev_back')} p={open ? fp : 0} w={360} h={498} style={{transform: `translateY(${open ? -fp * 30 : 0}px) rotate(${(i - 1.5) * 2}deg)`}} />
        <div className="abs h3 on-desk" style={{left: 0, width: 360, top: 530, textAlign: 'center', ...rise(t, at, {y: 12})}}>{cn}</div>
      </div>;
    })}
    <div className="abs" style={{left: 170 + 160, top: 150, width: 90, height: 90, borderRadius: '50%', background: 'var(--sky)', border: '6px solid #fbf4e4', boxShadow: '0 10px 20px rgba(0,0,0,.4)', ...rise(t, 1.8, {y: -60}), opacity: (prog(t, 1.8, 0.3)) * (1 - prog(t, 2.6, 0.3))}} />
  </>;
}

const SL = {a: [0.194, 0.283], b: [0.194, 0.311], reason: [0.383, 0.392], plan: [0.194, 0.451]};
export function B08() {
  const t = useT();
  const W = 590, H = 832;
  const fold = eio(prog(t, 6.8, 0.6)), open = eio(prog(t, 10.2, 0.5));
  const k = Math.max(0, fold - open);
  const cnt = t >= 7.6 && t < 10.2 ? 3 - Math.floor((t - 7.6) / 0.85) : null;
  return <>
    <Desk />
    <Head t={t} kicker="填委托单" title={t < 6.8 ? '勾选项 · 勾理由 · 勾跌了怎么办' : '对折扣好，一起翻开'} />
    <div className="card" style={{left: 1120, top: 90 + k * H * 0.25, width: W, height: H * (1 - k * 0.5), overflow: 'hidden'}}>
      <img src={pr('slip_summer_color')} alt="" style={{height: H, objectFit: 'cover', objectPosition: 'top'}} />
      <Tick t={t} at={2.6} fx={SL.b[0]} fy={SL.b[1]} W={W} H={H} />
      <Tick t={t} at={3.6} fx={SL.reason[0]} fy={SL.reason[1]} W={W} H={H} />
      <Tick t={t} at={5.0} fx={SL.plan[0]} fy={SL.plan[1]} W={W} H={H} />
      <div className="abs" style={{inset: 0, background: 'linear-gradient(#efe4cc, #e2d4b6)', opacity: Math.min(1, k * 1.6), display: 'flex', alignItems: 'center', justifyContent: 'center'}}>
        <div className="h2" style={{color: 'var(--ink-3)', letterSpacing: '.2em'}}>委托单 · 已对折</div>
      </div>
    </div>
    <div className="abs on-desk" style={{left: 110, top: 300, width: 900}}>
      {[['选项', 'B 保持不动', 2.6], ['理由', '量价', 3.6], ['计划', '跌了就走', 5.0]].map(([a, b, at]) => <div key={a} className="h2" style={{marginBottom: 30, ...rise(t, at, {x: -30, y: 0})}}><span className="muted" style={{marginRight: 24}}>{a}</span>{b}</div>)}
    </div>
    {cnt !== null && <div className="abs h1 on-desk" style={{left: 300, top: 680, fontSize: 200, transform: `scale(${lerp(1.4, 1, ex(prog(t, 7.6 + (3 - cnt) * 0.85, 0.3)))})`}}>{cnt}</div>}
    <Stamp t={t} at={10.3} rot={-6} size={80} style={{left: 250, top: 720, background: 'rgba(251,244,228,.9)'}}>亮单！</Stamp>
  </>;
}

const SC = {c: [0.194, 0.34], data: [0.392, 0.392], dunno: [0.83, 0.392]};
export function B09() {
  const t = useT();
  const W = 560, H = 790;
  return <>
    <Desk />
    {[0, 1].map(i => <div key={i} className="card" style={{left: 200 + i * 780, top: 60, width: W, height: H, transform: `rotate(${i ? 2 : -2}deg)`, ...rise(t, 0.2 + i * 0.2, {y: 60})}}>
      <img src={pr('slip_spring_color')} alt="" />
      <Tick t={t} at={1.0 + i * 0.3} fx={SC.c[0]} fy={SC.c[1]} W={W} H={H} />
      <Tick t={t} at={2.2 + i * 1.1} fx={i ? SC.dunno[0] : SC.data[0]} fy={SC.data[1]} W={W} H={H} />
    </div>)}
    <Label t={t} at={2.3} x={260} y={880}>等，因为在等数据</Label>
    <Label t={t} at={3.4} x={1040} y={880}>等，因为看不懂</Label>
    <Stamp t={t} at={5.6} rot={-6} size={86} style={{left: 560, top: 380, background: 'rgba(251,244,228,.92)'}}>理由不同 · 图标不同</Stamp>
  </>;
}

export function B10() {
  const t = useT();
  const seq = [
    {at: 0.0, out: 5.0, kind: 'ff'},
    {at: 5.0, out: 7.2, kind: 'queue', s: '春', name: '开户排队条'},
    {at: 7.2, out: 9.6, kind: 'sell', s: '夏', name: '卖出窗口 + 跌停锁'},
    {at: 9.6, out: 11.4, kind: 'huddle', s: '秋', name: '抱团圈'},
    {at: 11.4, out: 99, kind: 'breaker', s: '冬', name: '熔断沙漏 · 30 秒'},
  ];
  const cur = seq.filter(x => t >= x.at).pop();
  const vis = x => Math.min(eo(prog(t, x.at, 0.45)), 1 - prog(t, x.out, 0.35));
  return <>
    <Desk />
    <Head t={t} kicker={t < 5 ? '快进 · 结算第一段' : '每一场一个招牌机制'} title={t < 5 ? '翻开快进牌' : `${cur.s} · ${cur.name}`} />
    {seq.map(x => {
      const o = vis(x);
      if (o <= 0) return null;
      const st = {opacity: o, transform: `translateY(${(1 - o) * 40}px)`};
      if (x.kind === 'ff') return <div key={x.kind} className="abs" style={{left: 760, top: 210, ...st}}><Flip front={pr('ff_s2015')} back={pr('ev_back')} p={eio(prog(t, 0.6, 0.6))} w={420} h={581} /></div>;
      if (x.kind === 'queue') return <Card key={x.kind} src={pr('queue')} x={260} y={380} w={1400} h={428} rot={-1} style={st} />;
      if (x.kind === 'sell') return <Card key={x.kind} src={pr('sellwindow')} x={720} y={200} w={480} h={665} rot={2} style={st} />;
      if (x.kind === 'huddle') return <Card key={x.kind} src={pr('huddle')} x={720} y={200} w={480} h={665} rot={-2} style={st} />;
      return <div key={x.kind} style={st} className="abs">
        <Card src={pr('breaker1')} x={420} y={230} w={440} h={597} rot={-3} />
        <Phone t={t} style={{left: 1080, top: 150, transform: 'scale(.82)', transformOrigin: '0 0'}} />
      </div>;
    })}
    {t > 13.4 && <div className="abs on-desk" style={{left: 300, top: 860, display: 'flex', gap: 18}}>
      {['全桌 30 秒', '不许说话', '不许碰牌'].map((x, i) => <span key={x} className="chip" style={{fontSize: 34, ...rise(t, 13.5 + i * 0.6, {y: 12})}}>{x}</span>)}
    </div>}
  </>;
}

export function B11() {
  const t = useT();
  return <>
    <Desk />
    <Head t={t} kicker="揭幕 · 结算第二段" title="扫码，看真实走势一根根长出来" />
    <Card src={pr('reveal_s2015')} x={250} y={240} w={560} h={776} rot={-3} style={rise(t, 0.2, {y: 60})} />
    <Ring t={t} at={1.2} x={590} y={300} w={230} h={230} color="var(--sun)" />
    <div className="abs" style={{left: 1080, top: 120, ...rise(t, 1.2, {x: 80, y: 0})}}><Phone t={t} style={{left: 0, top: 0, transform: 'scale(.86)', transformOrigin: '0 0'}} /></div>
  </>;
}

const COINS = [['春', '豹'], ['夏', '象'], ['秋', '象'], ['冬', '鹰']];
export function B12() {
  const t = useT();
  return <>
    <Desk />
    <Head t={t} kicker="驿站 · 每季一枚" title="数一数图标，领一枚物种币" />
    <Card src={pr('station')} x={160} y={250} w={480} h={665} rot={-3} style={rise(t, 0.2, {y: 60})} />
    {COINS.map(([s, sp], i) => {
      const k = ex(prog(t, 2.4 + i * 0.55, 0.35));
      const big = sp === '象' && t > 6.0;
      return <div key={s} className="abs" style={{left: 820 + i * 260, top: 360, width: 220, textAlign: 'center'}}>
        <div style={{position: 'relative', width: 200, height: 200, margin: '0 auto', transform: `translateY(${(1 - k) * -300}px) scale(${big ? 1.16 : 1})`, opacity: k > 0 ? (t > 6.0 && !big ? 0.45 : 1) : 0}}>
          <img src={art('icon_coin')} alt="" style={{width: 200, height: 177, objectFit: 'contain'}} />
          <div className="abs h2" style={{inset: 0, display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--ink)', paddingBottom: 10}}>{sp}</div>
        </div>
        <div className="h3 on-desk" style={{marginTop: 18, color: SEASON[s]}}>{s}</div>
      </div>;
    })}
    <Stamp t={t} at={6.3} rot={-5} size={64} style={{left: 900, top: 720, background: 'rgba(251,244,228,.92)'}}>象最多 → 你像大象</Stamp>
  </>;
}

export function B13() {
  const t = useT();
  return <>
    <Desk />
    <Head t={t} kicker="终局" title="两本账，分开记" />
    <div className="abs" style={{left: 110, top: 260, width: 800, ...rise(t, 1.0, {x: -60, y: 0})}}>
      <div className="card flat" style={{position: 'relative', padding: '40px 44px', background: 'var(--paper-light)', borderRadius: 18}}>
        <div className="kicker">资金账</div><div className="h2" style={{marginTop: 6}}>记结果</div>
        <div className="body muted" style={{marginTop: 10}}>四季下来赚了多少</div>
      </div>
    </div>
    <div className="abs" style={{left: 110, top: 560, width: 800, ...rise(t, 3.2, {x: -60, y: 0})}}>
      <div className="card flat" style={{position: 'relative', padding: '40px 44px', background: 'var(--sun)', borderRadius: 18}}>
        <div className="kicker" style={{color: 'var(--ink-2)'}}>方法账 · 方法星 ★</div><div className="h2" style={{marginTop: 6}}>看证据 · 理由对得上 · 计划照做</div>
        <div className="body" style={{marginTop: 10}}>每场最多 4 颗星</div>
      </div>
    </div>
    <div className="abs" style={{left: 1010, top: 360, width: 800, ...rise(t, 8.4, {x: 80, y: 0})}}>
      <div className="card flat" style={{position: 'relative', padding: '44px 48px', background: '#1d1913', color: '#fbf4e4', borderRadius: 18, border: '3px solid var(--sun)'}}>
        <div className="kicker" style={{color: 'var(--sun)'}}>终局分</div>
        <div className="h2" style={{marginTop: 10, color: '#fbf4e4'}}>方法星 + 资金名次分</div>
        <div className="body" style={{marginTop: 14, color: '#d9c9a6'}}>资金第 1 名 6 分 · 第 2 名 4 分<br />第 3 名 2 分 · 其余 1 分</div>
      </div>
    </div>
  </>;
}

export function B14() {
  const t = useT();
  const W = 640, H = 896;
  return <>
    <Desk />
    <Head t={t} kicker="档案卡背面 · 决策树" title="第一个符合的，就是你的任务牌" />
    <div className="card" style={{left: 160, top: 170, width: W, height: H, ...rise(t, 0.2, {y: 60})}}><img src={pr('record_back')} alt="" /></div>
    {[0, 1, 2].map(i => <Hi key={i} t={t} at={2.0 + i * 0.9} x={190} y={260 + i * 150} w={W - 60} h={130} until={2.0 + (i + 1) * 0.9} />)}
    <Card src={pr('task_hyp')} x={1000} y={200} w={480} h={651} rot={2} style={rise(t, 5.0, {x: 100, y: 0})} />
    <Label t={t} at={6.3} x={1020} y={880}>指向 PandaAI 的真实工具</Label>
  </>;
}

export function B15() {
  const t = useT();
  const f = eio(prog(t, 3.4, 0.7));
  return <>
    <Desk />
    <Head t={t} kicker="单人模式" title="选两张 AI 物种牌当对手" />
    {[['ai_cheetah', 'ai_cheetah_back'], ['ai_meerkat', 'ai_meerkat_back']].map(([a, b], i) => <div key={a} className="abs" style={{left: 330 + i * 680, top: 220, ...rise(t, 0.3 + i * 0.2, {y: 60})}}>
      <Flip front={pr(b)} back={pr(a)} p={f} w={560} h={759} style={{transform: `rotate(${i ? 2 : -2}deg)`}} />
    </div>)}
    <Label t={t} at={4.2} x={700} y={990} style={{transform: 'none'}}>背面：每一场选什么、凭什么</Label>
  </>;
}

export function B16() {
  const t = useT(), D = useDur();
  const end = eio(prog(t, D - 4.2, 0.8));
  return <>
    <Desk />
    <div style={{inset: 0, opacity: 1 - end}} className="abs">
      <Head t={t} kicker="玩完 · 扫档案卡" title="手机再帮你复盘一次" />
      <Card src={pr('record_front')} x={260} y={240} w={560} h={784} rot={-3} style={rise(t, 0.2, {y: 60})} />
      <div className="abs" style={{left: 1080, top: 120, ...rise(t, 0.6, {x: 80, y: 0})}}><Phone t={t} style={{left: 0, top: 0, transform: 'scale(.86)', transformOrigin: '0 0'}} /></div>
    </div>
    <div className="abs" style={{inset: 0, opacity: end}}>
      <div className="paper" />
      <div className="abs" style={{left: 0, right: 0, top: 230, textAlign: 'center'}}>
        <div className="h1 red" style={{fontSize: 120}}>不是韭菜，那你是哪一种？</div>
        <div className="h1" style={{fontSize: 96, marginTop: 30}}>交易物种起源</div>
        <div className="h3" style={{marginTop: 50}}>一盒桌游 · 一部手机 · 同一个游戏</div>
        <div className="h3" style={{marginTop: 20}}>meetmind.online/ts</div>
        <div className="small muted" style={{marginTop: 30}}>投资者教育游戏，不构成投资建议</div>
      </div>
    </div>
  </>;
}
