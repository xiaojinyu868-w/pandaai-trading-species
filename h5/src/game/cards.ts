import { DECKS } from "../data";
import type { SpeciesId, TaskType } from "./meta";

export interface ChanceCard { id: string; dimension: string; q: string; a: { text: string; species: SpeciesId }[] }
export interface RetestCard { id: string; q: string; a: { text: string; species: SpeciesId | "other" }[]; pair?: string[]; why?: string }
export interface RuleCard { id: string; name: string; text: string; does: string; real?: { name: string; url: string } | null; logic?: any; spoils?: string; qube?: string }
export interface DataPortCard { id: string; title: string; code: string; q: string; a: string[]; correct: number; explain: string; variant?: { param: string; from: string; to: string; what_you_see: string }; functions?: string[] }
export interface TaskCard {
  id: string;
  type: TaskType;
  level: "basic" | "adv";
  cn: string;
  who: string;
  now: string;
  resources: { name: string; url: string; kind: string; note?: string; example?: boolean }[];
}

const CHANCE_BASE: ChanceCard[] = [
  { id: "chance-01", dimension: "时间尺度", q: "一只股票，你通常打算拿多久？", a: [{ text: "趋势一坏就走，几天到几周", species: "cheetah" }, { text: "公司没变就一直拿，一年以上", species: "elephant" }] },
  { id: "chance-02", dimension: "证据使用", q: "朋友发来截图：“某公司下季度利润翻倍”。你先做什么？", a: [{ text: "去查公告和财报的日期", species: "fox" }, { text: "看看群里其他人怎么说", species: "meerkat" }] },
  { id: "chance-03", dimension: "人群与消息", q: "饭桌上大家都在聊同一只股票。你的第一反应是？", a: [{ text: "人人都知道了，可能已经涨过了", species: "owl" }, { text: "这么多人看好，总有原因", species: "meerkat" }] },
  { id: "chance-04", dimension: "规则化", q: "你更相信哪一种？", a: [{ text: "写下来的规则，到时候照做", species: "fox" }, { text: "每次具体情况具体看", species: "chameleon" }] },
  { id: "chance-05", dimension: "风险姿态", q: "账户里多了一笔意外收入，你会？", a: [{ text: "先放一半，等更好的价格再加", species: "owl" }, { text: "趁行情好，全部投进去", species: "cheetah" }] },
  { id: "chance-06", dimension: "等待理由", q: "你决定先不买，最可能是因为？", a: [{ text: "还在等一个具体的信号", species: "owl" }, { text: "价格还不够便宜", species: "elephant" }] },
  { id: "chance-07", dimension: "证据使用", q: "一张 K 线图和一张财务报表，只能看一张，你选？", a: [{ text: "K 线图：价格说明一切", species: "cheetah" }, { text: "财务报表：先看它赚不赚钱", species: "elephant" }] },
  { id: "chance-08", dimension: "规则化", q: "你的方法连续亏了三次，你会？", a: [{ text: "拿历史数据查一查，是不是规则失效了", species: "fox" }, { text: "换一种更适合现在市场的方法", species: "chameleon" }] },
];

const RETEST_BASE: RetestCard[] = [
  { id: "retest-01", q: "如果明天开盘就跌 10%，你最先看什么？", a: [{ text: "走势和成交量", species: "cheetah" }, { text: "现在的估值", species: "elephant" }, { text: "发生了什么新闻", species: "meerkat" }, { text: "我事先写好的规则", species: "fox" }] },
  { id: "retest-02", q: "你最后悔的一次交易，是因为？", a: [{ text: "追得太晚", species: "cheetah" }, { text: "听了别人的", species: "meerkat" }, { text: "等得太久", species: "owl" }, { text: "没按自己的规则做", species: "fox" }] },
  { id: "retest-03", q: "挑一个最像你的口头禅：", a: [{ text: "“先上车再说”", species: "cheetah" }, { text: "“好东西不怕等”", species: "elephant" }, { text: "“数据呢？”", species: "fox" }, { text: "“再看看”", species: "owl" }] },
  { id: "retest-04", q: "市场风格突然变了，你会？", a: [{ text: "跟着换打法", species: "chameleon" }, { text: "坚持原来的，长期看没问题", species: "elephant" }, { text: "先停下，等看清楚", species: "owl" }, { text: "去看大家都在买什么", species: "meerkat" }] },
  { id: "retest-05", q: "你更愿意花一小时做什么？", a: [{ text: "写一段代码自己跑数据", species: "fox" }, { text: "读一份年报", species: "elephant" }, { text: "刷一遍今天的新闻", species: "meerkat" }, { text: "盯盘看走势", species: "cheetah" }] },
  { id: "retest-06", q: "一个“稳赚”的机会摆在面前，你会？", a: [{ text: "先找它哪里会亏", species: "fox" }, { text: "等更多证据", species: "owl" }, { text: "小试一下", species: "chameleon" }, { text: "赶紧上，机会不等人", species: "cheetah" }] },
];

const RULES_BASE: RuleCard[] = [
  { id: "rule-ma520", name: "5/20 双均线", text: "5 日均线在 20 日均线上方就拿着，跌破就卖。", does: "趋势跟随", real: { name: "Qube 首页模板「茅台 5/20 双均线」", url: "https://www.pandaaiquant.com/agent_quant/" } },
  { id: "rule-ma52060", name: "MA5/20/60 多均线", text: "5、20、60 日均线从上到下排好才持有，其余时间空仓。", does: "趋势过滤", real: { name: "Qube 模板「多均线趋势过滤」", url: "https://www.pandaaiquant.com/agent_quant/" } },
  { id: "rule-mom20", name: "20 日动量", text: "过去 20 个交易日涨了就持有，跌了就空仓。", does: "动量", real: { name: "Qube 模板「20 日动量」", url: "https://www.pandaaiquant.com/agent_quant/" } },
  { id: "rule-lowpb-roe", name: "低 PB + 高 ROE", text: "只买又便宜（市净率低）又赚钱（净资产收益率高）的公司。", does: "价值筛选", real: { name: "Qube 模板「低 PB + 高 ROE 复合」", url: "https://www.pandaaiquant.com/agent_quant/" } },
  { id: "rule-stop10", name: "跌 10% 止损", text: "从买入价跌 10% 就全部卖出，不找理由。", does: "止损" },
  { id: "rule-dip", name: "跌多了就抄底", text: "从高点跌了 15% 以上，就加 1 份。", does: "逆势" },
  { id: "rule-cap2", name: "仓位上限", text: "任何时候最多 2 份，不加杠杆。", does: "风控" },
  { id: "rule-wait3", name: "大事等三天", text: "出大事之后先等 3 个交易日，再做决定。", does: "等待" },
];

const DATAPORT_BASE: DataPortCard[] = [
  { id: "dp-01", title: "拿一段日线", code: `import panda_data\n\ndf = panda_data.get_index_daily(\n    symbol="000001.SH",\n    start_date="20240923",\n    end_date="20240930")\nprint(len(df))`, q: "这段代码拿到的是什么？", a: ["上证指数 9 月 23—30 日的日线", "茅台这几天的分钟线", "整个 9 月的成交额"], correct: 0, explain: "get_index_daily 取指数日线，symbol 是上证指数，日期是 9 月 23 日到 30 日，一共 6 个交易日。" },
  { id: "dp-02", title: "算一个涨跌幅", code: `last = df["close"].iloc[-1]\nprev = df["close"].iloc[-2]\nprint(last / prev - 1)`, q: "打印出来的是什么？", a: ["最后一天的成交量", "最后一天相对前一天的涨跌幅", "这几天的平均价格"], correct: 1, explain: "最后一天收盘价 ÷ 前一天收盘价 − 1，就是最后一天的涨跌幅。924 那天是 +8.1%。" },
  { id: "dp-03", title: "画一条均线", code: `df["ma20"] = df["close"].rolling(20).mean()\nsignal = df["close"] > df["ma20"]`, q: "signal 为 True 表示什么？", a: ["收盘价在 20 日均线上方", "成交量比 20 天前大", "股价 20 天里涨了 20%"], correct: 0, explain: "rolling(20).mean() 是 20 日均线；收盘价高过它，signal 就是 True。这就是趋势规则的第一步。" },
  { id: "dp-04", title: "找出暴跌日", code: `df = panda_data.get_stock_daily(\n    symbol="600519.SH",\n    start_date="20210101",\n    end_date="20211231")\nbig = df[df["pct_chg"] < -5]\nprint(len(big))`, q: "big 里是哪些天？", a: ["茅台 2021 年涨超 5% 的日子", "茅台 2021 年跌超 5% 的日子", "茅台 2021 年停牌的日子"], correct: 1, explain: "pct_chg < -5 筛出单日跌幅超过 5% 的交易日。" },
];

const TASKS_BASE: TaskCard[] = [
  { id: "task-hypo-basic", type: "hypo", level: "basic", cn: "假设检验 · 入门", who: "有交易直觉、还没验证过", now: "挑一条规则，放回你走过的名场面，看它会怎么做、结果如何。", resources: [
    { name: "Qube 首页模板「5/20 双均线」", url: "https://www.pandaaiquant.com/agent_quant/", kind: "PandaAI 产品", note: "登录 PandaAI 后可用" },
    { name: "QuantSkills · 均线交叉信号分析", url: "https://www.quantskills.ai/skills/skill-ma-crossover-signal", kind: "QuantSkills 技能" }] },
  { id: "task-hypo-adv", type: "hypo", level: "adv", cn: "假设检验 · 进阶", who: "有规则、想知道它是不是运气", now: "把规则拉长到十年历史，再查一遍有没有未来函数和过度拟合。", resources: [
    { name: "Qube 模板「多均线趋势过滤 MA5/20/60」", url: "https://www.pandaaiquant.com/agent_quant/", kind: "PandaAI 产品", note: "登录 PandaAI 后可用" },
    { name: "QuantSkills · 回测偏差规避", url: "https://www.quantskills.ai/skills/skill-backtesting-bias-avoidance", kind: "QuantSkills 技能" },
    { name: "QuantSkills · 回测过拟合检测", url: "https://www.quantskills.ai/skills/skill-backtest-overfit", kind: "QuantSkills 技能" }] },
  { id: "task-verify-basic", type: "verify", level: "basic", cn: "证据核查 · 入门", who: "容易被结论和人群带走", now: "三条当时流传的说法，用公告日期和数据逐条核实。", resources: [
    { name: "PandaAI · EVO 对抗复核", url: "https://www.pandaaiquant.com/evo", kind: "PandaAI 产品", note: "登录 PandaAI 后可用" },
    { name: "QuantSkills · 新闻情绪分析", url: "https://www.quantskills.ai/skills/skill-news-sentiment-analyst", kind: "QuantSkills 技能" }] },
  { id: "task-verify-adv", type: "verify", level: "adv", cn: "证据核查 · 进阶", who: "会查资料，想查得更快更全", now: "给一只股票建一份档案：公告、财务、资金和舆情放在一起对照。", resources: [
    { name: "QuantSkills · A股个股档案", url: "https://www.quantskills.ai/skills/skill-a-share-stock-dossier", kind: "QuantSkills 技能" },
    { name: "QuantSkills · Serenity 投研模型", url: "https://www.quantskills.ai/skills/skill-serenity-research-model", kind: "QuantSkills 技能" },
    { name: "PandaAI · EVO 对抗复核", url: "https://www.pandaaiquant.com/evo", kind: "PandaAI 产品", note: "登录 PandaAI 后可用" }] },
  { id: "task-explore-basic", type: "explore", level: "basic", cn: "数据自主探索 · 入门", who: "会写一点代码、喜欢自己动手", now: "改一行 panda_data 调用：换一个标的或日期，自己重跑一个名场面。", resources: [
    { name: "Panda Data 数据接口文档", url: "https://www.pandaaiquant.com/docs/api", kind: "PandaAI 数据" },
    { name: "QuantSkills · pandadata-api 技能", url: "https://www.quantskills.ai/skills/skill-pandadata-api", kind: "QuantSkills 技能" }] },
  { id: "task-explore-adv", type: "explore", level: "adv", cn: "数据自主探索 · 进阶", who: "能自己写因子", now: "评估“小市值”因子 2021—2024 年的表现和衰减，再去因子大赛试一试。", resources: [
    { name: "QuantSkills · B10 因子评估系统", url: "https://www.quantskills.ai/skills/skill-build-b10-factor-evaluation", kind: "QuantSkills 技能" },
    { name: "QuantStudio（开源）", url: "https://github.com/quantskills/QuantStudio", kind: "QuantSkills 开源" },
    { name: "PandaAI · 第四届因子大赛", url: "https://www.pandaaiquant.com/factorhub/fourthFactorCompetition/", kind: "PandaAI 活动" }] },
  { id: "task-regime-basic", type: "regime", level: "basic", cn: "状态判断 · 入门", who: "观望是因为在等证据", now: "写下你在等的三个信号，看看现在的市场满足了几个。", resources: [
    { name: "QuantSkills · 市场状态监测智能体", url: "https://www.quantskills.ai/agents/agent-market-regime-monitor", kind: "QuantSkills 智能体" },
    { name: "QuantSkills · 市场状态分析", url: "https://www.quantskills.ai/skills/skill-market-regime-analysis", kind: "QuantSkills 技能" }] },
  { id: "task-regime-adv", type: "regime", level: "adv", cn: "状态判断 · 进阶", who: "想把“等什么”变成可以监测的指标", now: "把等待的信号变成每天自动检查的雷达：风险、拥挤度、融资盘。", resources: [
    { name: "QuantSkills · A股市场风险雷达", url: "https://www.quantskills.ai/skills/skill-a-share-market-risk-radar", kind: "QuantSkills 技能" },
    { name: "QuantSkills · 拥挤度风险监测智能体", url: "https://www.quantskills.ai/agents/agent-crowding-risk-monitor", kind: "QuantSkills 智能体" }] },
  { id: "task-chart-basic", type: "chart", level: "basic", cn: "读图入门 · 入门", who: "观望是因为看不懂", now: "30 秒读图练习：从三张走势图里认出放量、破位和反弹。", resources: [
    { name: "PandaAI 学习中心（具体课程待选）", url: "https://www.pandaaiquant.com/learninghub/newcourse", kind: "PandaAI 课程", example: true },
    { name: "QuantSkills · K 线形态识别", url: "https://www.quantskills.ai/skills/skill-kline-pattern-vision", kind: "QuantSkills 技能" }] },
  { id: "task-chart-adv", type: "chart", level: "adv", cn: "读图入门 · 进阶", who: "看得懂图，想看得更准", now: "用风险收益指标读一张净值曲线：回撤、波动、夏普分别在说什么。", resources: [
    { name: "QuantSkills · 风险收益指标", url: "https://www.quantskills.ai/skills/skill-risk-return-metrics", kind: "QuantSkills 技能" },
    { name: "PandaAI 学习中心（具体课程待选）", url: "https://www.pandaaiquant.com/learninghub/newcourse", kind: "PandaAI 课程", example: true }] },
  { id: "task-risk-basic", type: "risk", level: "basic", cn: "风险校准 · 入门", who: "游戏里激进、现实里保守，或者对期货感兴趣", now: "游戏里没有真钱。去模拟盘看看，接近真实的压力下你会怎么做。", resources: [
    { name: "PandaAI · 巅峰交易者 S1 全国期货模拟赛", url: "https://www.pandaaiquant.com/contest/", kind: "PandaAI 活动" },
    { name: "QuantSkills · 交易行为诊断", url: "https://www.quantskills.ai/skills/skill-trading-behavior-diagnostics", kind: "QuantSkills 技能" }] },
  { id: "task-risk-adv", type: "risk", level: "adv", cn: "风险校准 · 进阶", who: "想给自己的交易定一套止损止盈", now: "把止损止盈写成规则，在模拟盘里跑一个月，再做一次行为诊断。", resources: [
    { name: "QuantSkills · B11 自动止损止盈", url: "https://www.quantskills.ai/skills/skill-b11-auto-stop-loss-take-profit", kind: "QuantSkills 技能" },
    { name: "PandaAI · 巅峰交易者 S1 全国期货模拟赛", url: "https://www.pandaaiquant.com/contest/", kind: "PandaAI 活动" },
    { name: "QuantSkills · 交易行为诊断", url: "https://www.quantskills.ai/skills/skill-trading-behavior-diagnostics", kind: "QuantSkills 技能" }] },
];

function normAnswers(x: any): { text: string; species: SpeciesId }[] | null {
  const arr = x.answers || x.options || x.a || x.choices;
  if (!Array.isArray(arr)) return null;
  return arr.map((o: any) => ({ text: o.text || o.label || String(o), species: (o.species || o.icon || "owl") as SpeciesId }));
}

export const CHANCE: ChanceCard[] = Array.isArray(DECKS.chance) && DECKS.chance.length
  ? DECKS.chance.map((c: any) => ({ id: c.id, dimension: c.dimension || "", q: c.q || c.question || c.prompt || c.title, a: normAnswers(c) || [] })).filter((c: ChanceCard) => c.a.length >= 2)
  : CHANCE_BASE;
export const RETEST: RetestCard[] = Array.isArray(DECKS.retest) && DECKS.retest.length
  ? DECKS.retest.map((c: any) => ({ id: c.id, q: c.q || c.question || c.prompt || c.title, a: normAnswers(c) || [], pair: c.pair, why: c.why })).filter((c: RetestCard) => c.a.length >= 2)
  : RETEST_BASE;

/** 规则书：平局抽写着这两种物种的那张，没有就用“变色龙 / 任意”；不同意时抽写着你主张那种的；没有图标抽牌堆顶 */
export function retestFor(mode: "tie" | "none" | "claim", species: string[]): RetestCard {
  const fallback = RETEST.find((c) => c.pair?.includes("other")) || RETEST[RETEST.length - 1];
  if (mode === "tie") return RETEST.find((c) => c.pair && c.pair.every((s) => species.includes(s))) || fallback;
  if (mode === "claim") {
    const hits = RETEST.filter((c) => c.pair?.includes(species[0]));
    return hits.length ? pickN(hits, 1)[0] : fallback;
  }
  return pickN(RETEST.filter((c) => !c.pair?.includes("other")), 1)[0] || fallback;
}
const RULE_DOES: Record<string, string> = {
  ma_cross: "趋势跟随", ma_trend: "趋势过滤", momentum: "动量", fundamental_screen: "价值筛选", stop_loss: "止损",
  buy_dip: "逆势加仓", wait: "等待", position_cap: "仓位上限", volume_breakout: "放量追涨", valuation: "估值",
};
const QUBE_URL = "https://www.pandaaiquant.com/agent_quant/";
export const RULES: RuleCard[] = Array.isArray(DECKS.rules) && DECKS.rules.length
  ? DECKS.rules.map((r: any) => ({
      id: r.id, name: r.name || r.title, text: r.text || r.desc || r.rule || "",
      does: r.does || RULE_DOES[r.logic?.type] || r.family || "规则",
      real: r.real || (r.url ? { name: r.real_name || r.name, url: r.url } : r.is_real_template ? { name: "Qube 首页的真实策略模板", url: QUBE_URL } : null),
      logic: r.logic, spoils: r.spoils || undefined, qube: r.qube_prompt || undefined,
    }))
  : RULES_BASE;
/** 对应名场面揭幕前，规则牌名字里不出现标的名，回测提示也先不给 */
export function ruleView(r: RuleCard, revealed: string[]): { name: string; qube?: string } {
  const hide = !!r.spoils && !revealed.includes(r.spoils);
  return { name: hide ? r.name.replace(/^(贵州)?茅台\s*/, "") : r.name, qube: hide ? undefined : r.qube };
}
function keyIndex(x: any, opts: any[]): number {
  if (typeof x === "number") return x;
  const k = String(x ?? "A").trim();
  const i = opts.findIndex((o) => o && typeof o === "object" && o.key === k);
  return i >= 0 ? i : Math.max(0, "ABCD".indexOf(k));
}
export const DATAPORT: DataPortCard[] = Array.isArray(DECKS.dataport) && DECKS.dataport.length
  ? DECKS.dataport.map((d: any) => {
      const opts: any[] = d.answers || d.options || d.a || [];
      return {
        id: d.id, title: d.title || "", code: Array.isArray(d.code) ? d.code.join("\n") : d.code || "", q: d.q || d.question || "",
        a: opts.map((o) => (typeof o === "string" ? o : o.text || o.label || "")), correct: keyIndex(d.correct ?? d.answer, opts),
        explain: d.explain || d.explanation || "", variant: d.variant, functions: d.functions,
      };
    }).filter((d: DataPortCard) => d.code && d.a.length)
  : DATAPORT_BASE;
export const TASKS: TaskCard[] = TASKS_BASE;
export const taskOf = (type: TaskType, level: "basic" | "adv") => TASKS.find((t) => t.type === type && t.level === level)!;

export function pickN<T>(arr: T[], n: number, seed = Math.random()): T[] {
  const a = [...arr];
  let s = Math.floor(seed * 1e9) || 1;
  for (let i = a.length - 1; i > 0; i--) {
    s = (s * 16807) % 2147483647;
    const j = s % (i + 1);
    [a[i], a[j]] = [a[j], a[i]];
  }
  return a.slice(0, n);
}
