import { Link } from "react-router-dom";
import { ART, DATA_SOURCE, PAYOFF_RULE, SCENES } from "../data";
import { BADGES, SPECIES } from "../game/meta";
import { Glyph } from "../ui/kit";
import { PageShell } from "./Qr";

export function Atlas() {
  return (
    <PageShell kicker="物种图鉴">
      <h2 className="h2">七种交易物种</h2>
      <p className="small muted mt4">物种只表示偏好，不分高低；能力用徽章单独看。海狸是隐藏物种：数据港口答对两次才会出现。</p>
      <div className="col gap12 mt12">
        {SPECIES.map((s) => (
          <Link key={s.id} to={`/sp/${s.id}`} className="card" style={{ textDecoration: "none", padding: 0, overflow: "hidden", display: "grid", gridTemplateColumns: "120px 1fr" }}>
            <img src={ART(`species_${s.id}`)} alt="" style={{ width: "100%", height: 150, objectFit: "cover", objectPosition: "50% 15%", borderRight: "2px solid #2A2A1C" }} />
            <div style={{ padding: 12 }}>
              <div className="row between"><b className="h3">{s.cn}</b>{s.hidden && <span className="pill dark">隐藏</span>}</div>
              <div className="small bold mt4">{s.tagline}</div>
              <div className="tiny mt4">{s.style}</div>
              <div className="tiny mt4">推荐方向：{s.rec}</div>
            </div>
          </Link>
        ))}
      </div>
      <h2 className="h2 mt24">六枚徽章</h2>
      <div className="col gap8 mt12">
        {BADGES.map((b) => (
          <div key={b.id} className="card row gap12"><Glyph ch={b.glyph} color="#D4432A" size={44} /><div><b>{b.cn}</b><div className="small muted">{b.desc}</div></div></div>
        ))}
      </div>
    </PageShell>
  );
}

export function About() {
  return (
    <PageShell kicker="说明">
      <h2 className="h2">数据来源与说明</h2>
      <div className="col gap12 mt12 body">
        <div className="card">
          <b>行情是真实的</b>
          <div className="small mt4">{typeof DATA_SOURCE === "object" ? Object.values(DATA_SOURCE).join(" ") : String(DATA_SOURCE)}</div>
          <div className="small mt4">数据用 Python 脚本从 Panda Data 离线取好、预先算成游戏里的证据和收益表；页面里没有账号，也不直连接口。</div>
        </div>
        <div className="card">
          <b>收益怎么算</b>
          <div className="small mt4">{PAYOFF_RULE}</div>
        </div>
        <div className="card">
          <b>哪些是游戏化处理</b>
          <ul className="small" style={{ margin: "4px 0 0", paddingLeft: 18 }}>
            <li>2015：指数单日跌超 5% 记作“大面积跌停、卖不出去”；强制平仓线是资金低于 5。</li>
            <li>茅台抱团圈、量化出口板：同时离开的人越多，每人多亏 1 资金。</li>
            <li>原油宝：近月产品每份亏 12 资金，资金可以跌破 0。</li>
            <li>AI 物种的选择和台词是按物种性格写的模拟对手，不是真实用户。</li>
            <li>标“公开报道”的数字不是从行情接口算出来的，来自当时的公开报道。</li>
          </ul>
        </div>
        <div className="card">
          <b>推荐里的入口</b>
          <div className="small mt4">PandaAI（Qube、EVO、因子大赛、期货模拟赛、数据接口）和 QuantSkills 的技能、智能体都是真实入口；标“示例”的是示例内容。部分入口登录 PandaAI 后可用。</div>
        </div>
        <div className="card">
          <b>隐私</b>
          <div className="small mt4">游戏记录只保存在这台手机的浏览器里，不上传。分享图只有物种和徽章，不含任何行为记录。</div>
        </div>
        <div className="card">
          <b>名场面</b>
          <ul className="small" style={{ margin: "4px 0 0", paddingLeft: 18 }}>{SCENES.map((s) => <li key={s.id}>{s.season_cn}{s.door} · {s.title}（{s.t_text}）</li>)}</ul>
        </div>
      </div>
      <p className="tiny mt16">投资者教育游戏，不构成投资建议。</p>
    </PageShell>
  );
}
