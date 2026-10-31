import React from 'react';
import {useT, useDur, prog, eo, ex, eio, sio, lerp, clamp, rise, art, pr, Stamp, Chart, chartPoint, Phone, LEVELS} from '../lib.jsx';

const PH = {left: 1290, top: 22};
const PS = 0.86;
const Ph = ({t, zoom, style}) => <Phone t={t} zoom={zoom} style={{left: PH.left, top: PH.top, transform: `scale(${PS})`, transformOrigin: '0 0', ...style}} />;

/** 手机镜头的左侧文案区 */
function Side({t, kicker, title, children, at = 0.15}) {
  return <div className="abs" style={{left: 130, top: 120, width: 1060}}>
    <div className="kicker" style={rise(t, at, {y: 14})}>{kicker}</div>
    <div className="h1" style={{marginTop: 18, whiteSpace: 'pre-line', ...rise(t, at + 0.12, {y: 26})}}>{title}</div>
    {children}
  </div>;
}

export function Hook() {
  const t = useT(), D = useDur();
  const push = lerp(1, 1.07, sio(prog(t, 0, D)));
  return <>
    <div className="paper" />
    <div className="abs card flat" style={{left: 1000, top: 60, width: 720, height: 932, transform: `scale(${push})`, transformOrigin: '60% 40%'}}>
      <img src={art('prologue')} alt="" />
    </div>
    <div className="abs" style={{left: 150, top: 210, width: 800}}>
      <div className="kicker">1720 · London · South Sea Bubble</div>
      <div className="h1" style={{fontSize: 150, marginTop: 20}}>南海泡沫</div>
      <div className="body" style={{marginTop: 34, color: 'var(--ink-2)'}}>相传牛顿先赚了一笔，<br />又在更高的价格买了回去。</div>
    </div>
    <Stamp t={t} at={5.6} rot={-8} size={84} style={{left: 190, top: 690}}>亏掉约 2 万英镑</Stamp>
  </>;
}

const MONT = [
  {id: 's2015', img: 'blind_s2015', year: '2015', what: '人人借钱买股票', src: '上证指数 · Panda Data', at: 3.1, color: 'var(--kite)'},
  {id: 'scb', img: 'blind_scb', year: '2020', what: '美股十天熔断四次', src: '纳斯达克 100 · 公开接口', at: 5.7, color: 'var(--winter)'},
  {id: 's924', img: 'blind_s924', year: '2024', what: '国庆前全民排队开户', src: '上证指数 · Panda Data', at: 8.1, color: 'var(--spring)'},
];
export function Montage() {
  const t = useT();
  return <>
    <div className="paper" />
    <div className="abs h2" style={{left: 150, top: 56, ...rise(t, 0.3, {y: 20})}}>这些名场面，现在亲手再玩一遍</div>
    {MONT.map((m, i) => {
      const x = 150 + i * 560;
      const k = rise(t, m.at, {y: 60, d: 0.55});
      return <div key={m.id} className="abs" style={{left: x, top: 180, width: 500, ...k}}>
        <div className="card flat" style={{position: 'relative', width: 500, height: 520}}><img src={art(m.img)} alt="" style={{objectPosition: '50% 20%'}} /></div>
        <div className="abs" style={{left: 0, top: 560, width: 500, height: 120}}>
          <Chart id={m.id} w={500} h={110} p={eo(prog(t, m.at + 0.3, 1.4))} color={m.color} width={5} />
        </div>
        <div className="abs h3" style={{left: 0, top: 690}}>{m.what}</div>
        <div className="abs small muted" style={{left: 0, top: 752}}>{m.src}</div>
        <Stamp t={t} at={m.at + 0.35} rot={-7} size={60} style={{left: 300, top: 18, background: 'rgba(251,244,228,.85)'}}>{m.year}</Stamp>
      </div>;
    })}
  </>;
}

const WHO = [
  {sp: 'cheetah', act: '追？', at: 1.9},
  {sp: 'owl', act: '等？', at: 2.7},
  {sp: 'meerkat', act: '借钱加仓？', at: 4.0},
  {sp: 'elephant', act: '先跑？', at: 5.1},
];
export function Choices() {
  const t = useT();
  return <>
    <div className="paper" />
    <div className="abs" style={{left: 0, top: 0, width: 1920}}>
      <div className="abs h2" style={{left: 150, top: 60, ...rise(t, 0.2)}}>每一场，你都站在当年那个路口</div>
      {WHO.map((w, i) => <div key={w.sp} className="abs" style={{left: 140 + i * 420, top: 210, width: 380, textAlign: 'center', ...rise(t, w.at, {y: 40})}}>
        <img src={art('fig_' + w.sp)} alt="" style={{width: 360, height: 360, margin: '0 auto', objectFit: 'contain'}} />
        <div className="h2" style={{marginTop: 10}}>{w.act}</div>
      </div>)}
    </div>
    <Stamp t={t} at={6.0} rot={-5} size={76} style={{left: 700, top: 760, background: 'rgba(251,244,228,.9)'}}>你会怎么选？</Stamp>
  </>;
}

export function Title() {
  const t = useT();
  const W = 1920, wipe = eio(prog(t, 0, 1.0));
  const [lx, ly] = chartPoint('s2015', W, 700, wipe);
  return <div className="abs" style={{inset: 0, clipPath: `inset(0 ${(1 - wipe) * 100}% 0 0)`}}>
    <div className="paper" />
    <div className="abs" style={{left: 0, top: 190, opacity: 1 - prog(t, 1.0, 0.6)}}><Chart id="s2015" w={W} h={700} p={wipe} color="var(--kite)" width={8} /></div>
    <div className="abs card flat" style={{left: 120, top: 120, width: 760, height: 548, ...rise(t, 0.6, {y: 30})}}><img src={art('box_cover')} alt="" /></div>
    <Stamp t={t} at={0.9} rot={-5} size={70} style={{left: 140, top: 720, background: 'rgba(251,244,228,.9)'}}>不是韭菜，那你是哪一种？</Stamp>
    <div className="abs" style={{left: 1000, top: 150, width: 820}}>
      <div className="kicker" style={rise(t, 2.6, {y: 14})}>The Origin of Trading Species</div>
      <div className="h1" style={{fontSize: 136, marginTop: 14, ...rise(t, 2.7, {y: 30})}}>交易物种起源</div>
    </div>
    <div className="abs card" style={{left: 1010, top: 400, width: 520, height: 375, ...rise(t, 4.2, {y: 40, x: -30})}}><img src={pr('box_lid')} alt="" /></div>
    <div className="abs" style={{left: 1580, top: 330, ...rise(t, 4.6, {y: 40, x: 30})}}>
      <div className="phone" style={{left: 0, top: 0, transform: 'scale(.5)', transformOrigin: '0 0'}}><div className="scr"><img src="stills/home.jpg" alt="" /></div></div>
    </div>
    <div className="abs" style={{left: 1010, top: 890, display: 'flex', gap: 18}}>
      {['一盒桌游', '一部手机', '同一个游戏'].map((x, i) => <span key={x} className="chip" style={{fontSize: 34, ...(i === 2 ? {background: 'var(--ink)', color: 'var(--sun)'} : {}), ...rise(t, 4.4 + i * 0.75, {y: 16})}}>{x}</span>)}
    </div>
    {wipe < 1 && <div className="abs" style={{left: lx - 3, top: 0, width: 6, height: 1080, background: 'var(--kite)'}} />}
  </div>;
}

export function Blind() {
  const t = useT();
  return <>
    <div className="paper" />
    <Side t={t} kicker="Step 1 · 盲盒" title={'名字和日期\n藏起来'}>
      <div className="body" style={{marginTop: 40, width: 980, ...rise(t, 1.2)}}>只给决定那天之前的走势，和当时的处境。</div>
      <div className="abs" style={{top: 470, left: 0, width: 900, ...rise(t, 2.6)}}>
        <div className="card flat" style={{position: 'relative', width: 900, padding: '26px 34px', background: 'var(--paper-light)', borderRadius: 16}}>
          <div className="stampbox muted">当时能看到的</div>
          <div className="h3" style={{marginTop: 8}}>人人都在借钱买的夏天</div>
          <div className="small" style={{marginTop: 10}}>指数一年多翻了一倍还多 · 你手里已经有货</div>
        </div>
      </div>
      <Stamp t={t} at={4.6} ink rot={-4} size={56} style={{left: 0, top: 690}}>先猜猜：这是哪一年？</Stamp>
    </Side>
    <Ph t={t} />
  </>;
}

export function Clues() {
  const t = useT();
  const step = t < 2.9 ? 0 : t < 4.8 ? 1 : 2;
  const fingerDown = t > 5.85;
  return <>
    <div className="paper" />
    <div className="abs" style={{left: 130, top: 110, display: 'flex', gap: 20}}>
      {['翻线索', '定计划', '出手'].map((x, i) => <span key={x} className="chip" style={{fontSize: 40, padding: '10px 30px', ...(i === step ? {background: 'var(--ink)', color: 'var(--sun)'} : {opacity: .55}), ...rise(t, 0.1 + i * 0.15, {y: 10})}}>{i + 1} · {x}</span>)}
    </div>
    <div className="abs" style={{left: 130, top: 300, width: 1060, ...rise(t, 3.9, {y: 30})}}>
      <div style={{display: 'flex', alignItems: 'center', gap: 46}}>
        <div style={{position: 'relative', width: 230, height: 230, borderRadius: '50%', background: fingerDown ? 'var(--kite)' : 'var(--paper-light)', border: '6px solid var(--ink)', boxShadow: fingerDown ? '0 0 0 26px rgba(212,67,42,.16)' : '6px 6px 0 var(--ink)', transform: `scale(${fingerDown ? 0.94 : 1})`}}>
          <div className="abs h2" style={{inset: 0, display: 'flex', alignItems: 'center', justifyContent: 'center', color: fingerDown ? '#fff' : 'var(--ink)', whiteSpace: 'pre-line', textAlign: 'center', fontSize: 54}}>{fingerDown ? '拿着' : '按住\n买入'}</div>
        </div>
        <div>
          <div className="h1" style={{fontSize: 96}}>按着 = <span className="red">拿着</span></div>
          <div className="h1" style={{fontSize: 96, marginTop: 18}}>松开 = <span className="green">卖掉</span></div>
        </div>
      </div>
      <div className="body muted" style={{marginTop: 50}}>不用点，也不用再按一次：按多久，就拿多久。</div>
    </div>
    <Ph t={t} />
  </>;
}

export function Game() {
  const t = useT();
  const items = [
    {at: 0.4, txt: '涨多了，有人借钱给你', sub: '借 1 倍，涨跌都翻倍'},
    {at: 4.6, txt: '跌停那天，卖不出去', sub: '松手了，也要排到下一天'},
    {at: 6.3, txt: '两位 AI 对手同图买卖', sub: '按桌上 AI 物种牌的打法'},
  ];
  return <>
    <div className="paper" />
    <Side t={t} kicker="Step 2 · 出手 · 2015" title="真实行情，一格一格长出来" at={0.05}>
      {items.map((x, i) => <div key={i} className="abs" style={{left: 0, top: 360 + i * 170, ...rise(t, x.at, {x: -40, y: 0})}}>
        <div className="bubble" style={{position: 'relative', fontSize: 44}}>{x.txt}</div>
        <div className="small muted" style={{marginTop: 10, marginLeft: 8}}>{x.sub}</div>
      </div>)}
    </Side>
    <Ph t={t} />
  </>;
}

export function Reveal() {
  const t = useT();
  const L = LEVELS.s2015;
  return <>
    <div className="paper" />
    <Side t={t} kicker="Step 3 · 揭幕" title={'原来是 2015\n杠杆牛与千股跌停'} at={1.3}>
      <div className="abs" style={{left: 0, top: 380, width: 960, height: 230}}>
        <Chart id="s2015" w={960} h={220} p={eo(prog(t, 1.9, 2.4))} color="var(--kite)" width={6} fill="rgba(212,67,42,.08)" />
      </div>
      <div className="abs card flat" style={{left: 0, top: 650, width: 960, padding: '20px 30px', background: 'var(--paper-light)', borderRadius: 16, ...rise(t, 3.6)}}>
        <div className="stampbox">数据 · Panda Data <span style={{fontFamily: 'monospace'}}>{L.api}</span></div>
        <div className="small" style={{marginTop: 6}}>{L.name} {L.code} · {L.dates[0]} → {L.dates[L.dates.length - 1]} · {L.dates.length} 个交易日 · 按真实日线结算</div>
      </div>
    </Side>
    <Ph t={t} />
  </>;
}

export function Judge() {
  const t = useT();
  const rows = [['在哪儿买的', 1.9], ['扛了多深', 2.6], ['说好跌 5% 就走，走没走', 3.4]];
  return <>
    <div className="paper" />
    <Side t={t} kicker="AI 复盘 · 终局" title={'玩完，\nAI 给你复盘'}>
      <div className="abs" style={{left: 0, top: 420}}>
        {rows.map(([x, at], i) => <div key={x} className="h2" style={{marginBottom: 22, display: 'flex', alignItems: 'center', gap: 22, ...rise(t, at, {x: -30, y: 0})}}>
          <span style={{width: 56, height: 56, borderRadius: 12, background: 'var(--ink)', color: 'var(--sun)', display: 'inline-flex', alignItems: 'center', justifyContent: 'center', fontSize: 40}}>✓</span>{x}</div>)}
      </div>
      <Stamp t={t} at={5.0} rot={-5} size={54} style={{left: 0, top: 720, background: 'rgba(251,244,228,.9)'}}>说好跌 5% 就走 · 结果扛到了 44%</Stamp>
    </Side>
    <Ph t={t} />
  </>;
}

const SEVEN = ['cheetah', 'elephant', 'fox', 'owl', 'meerkat', 'chameleon', 'beaver'];
const CN = {cheetah: '猎豹', elephant: '大象', fox: '狐狸', owl: '猫头鹰', meerkat: '狐獴', chameleon: '变色龙', beaver: '海狸'};
export function Species() {
  const t = useT();
  const pick = eo(prog(t, 1.4, 0.6));
  const two = eio(prog(t, 2.9, 0.6));
  return <>
    <div className="paper" />
    <div className="abs" style={{left: 130, top: 110, opacity: 1 - two}}>
      <div className="kicker" style={rise(t, 0.1)}>七种交易物种</div>
      <div className="abs" style={{left: 0, top: 70, width: 1100, height: 560}}>
        {SEVEN.map((s, i) => {
          const me = s === 'elephant';
          const x = (i % 4) * 270, y = Math.floor(i / 4) * 270;
          return <div key={s} className="abs" style={{left: x, top: y, width: 250, textAlign: 'center', opacity: me ? 1 : lerp(1, 0.28, pick), transform: `scale(${me ? lerp(1, 1.18, pick) : 1})`, ...rise(t, 0.2 + i * 0.08, {y: 20})}}>
            <img src={art('fig_' + s)} alt="" style={{width: 220, height: 220, margin: '0 auto', objectFit: 'contain'}} />
            <div className="h3" style={{fontSize: 38}}>{CN[s]}</div>
          </div>;
        })}
      </div>
    </div>
    <div className="abs" style={{left: 130, top: 120, width: 1060, opacity: two}}>
      <div className="kicker">下一步 · PandaAI</div>
      <div className="h1" style={{marginTop: 18}}>把你的习惯<br />写成一句交易规则</div>
      <div className="abs card flat" style={{left: 0, top: 360, width: 1000, padding: '26px 34px', background: 'var(--paper-light)', borderRadius: 16}}>
        <div className="body" style={{fontSize: 36}}>复制进 PandaAI 的 Qube，拿历史数据回测：<br />“这个习惯，到底灵不灵？”</div>
      </div>
      <Stamp t={t} at={7.2} rot={-6} size={60} style={{left: 560, top: 600}}>一键复制 · 打开 Qube</Stamp>
    </div>
    <Ph t={t} />
  </>;
}

export function Demo() {
  const t = useT();
  return <>
    <div className="paper" />
    <Side t={t} kicker="评委演示台 · /demo" title={'换一个选择\n当场重算'}>
      <div className="body" style={{marginTop: 40, ...rise(t, 0.9)}}>五位模拟玩家，随手改一个选项试试。</div>
      <div className="abs" style={{left: 0, top: 500, ...rise(t, 1.6)}}>
        <div className="h3">“等证据”的玩家，把 924 从 <span className="chip">C 等回调</span> 改成 <span className="chip">A 节后追入</span></div>
        <div className="h3" style={{marginTop: 30, ...rise(t, 2.6)}}>猫头鹰 / 大象 · 待确认 <span className="red">→ 大象 · 比较确定</span></div>
      </div>
    </Side>
    <Ph t={t} />
  </>;
}

export function Handoff() {
  const t = useT();
  const n = Math.round(88 * eo(prog(t, 0.4, 1.6)));
  const cards = ['scene_s2015', 'ev_s2015_price', 'reveal_s2015', 'rule', 'task_hyp'];
  return <>
    <div className="paper" />
    <div className="abs" style={{left: 130, top: 110}}>
      <div className="kicker" style={rise(t, 0.1)}>线下 ⇄ 线上</div>
      <div className="h1" style={{fontSize: 200, marginTop: 6, ...rise(t, 0.3)}}>{n}<span className="h2" style={{marginLeft: 20}}>个二维码</span></div>
      <div className="body" style={{marginTop: 10, ...rise(t, 1.2)}}>扫到名场面，点“在手机上玩这一场”。</div>
    </div>
    {cards.map((c, i) => <div key={c} className="card" style={{left: 160 + i * 190, top: 600 - (i % 2) * 30, width: 230, height: 318, transform: `rotate(${(i - 2) * 5}deg)`, ...rise(t, 0.5 + i * 0.12, {y: 60})}}><img src={pr(c)} alt="" /></div>)}
    <Ph t={t} />
  </>;
}

export function EndCard() {
  const t = useT();
  return <>
    <div className="paper" />
    <div className="abs" style={{left: 0, right: 0, top: 250, textAlign: 'center'}}>
      <div className="kicker" style={rise(t, 0.1)}>The Origin of Trading Species</div>
      <div className="h1" style={{fontSize: 150, marginTop: 16, ...rise(t, 0.2)}}>交易物种起源</div>
      <div className="h2 red" style={{marginTop: 26, ...rise(t, 0.5)}}>不是韭菜，那你是哪一种？</div>
      <div className="h3" style={{marginTop: 50, ...rise(t, 0.8)}}>meetmind.online/ts</div>
      <div className="small muted" style={{marginTop: 26, ...rise(t, 1.0)}}>投资者教育游戏，不构成投资建议 · 行情来自 Panda Data 与标注过的公开接口 · AI 生成内容已标注</div>
    </div>
  </>;
}
