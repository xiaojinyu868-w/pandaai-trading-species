import { DECKS, type SceneId, type OptKey } from "../data";

export type SpeciesId = "cheetah" | "elephant" | "fox" | "owl" | "meerkat" | "chameleon" | "beaver";
export type Reason = "price" | "data" | "news" | "follow" | "gut" | "lost" | "rule";
export type Plan = "cut" | "add" | "none";
export type TaskType = "chart" | "explore" | "regime" | "verify" | "hypo" | "risk";

export interface SpeciesMeta {
  id: SpeciesId;
  cn: string;
  glyph: string;
  tagline: string;
  style: string;
  behavior: string;
  strength: string;
  watch: string;
  rec: string;
  color: string;
  hidden?: boolean;
  one?: string;
  looks?: string[];
  /** 自评卡上的一句人话：这种人平时是什么样 */
  plain?: string;
}

const PLAIN: Record<SpeciesId, string> = {
  cheetah: "看到涨势就想上车，进出都快",
  elephant: "只买便宜的好东西，买了拿很久",
  fox: "不轻信说法，先拿历史数据验一验",
  owl: "没看清就不动，宁可错过也不追",
  meerkat: "消息最灵通，大家在聊的我先知道",
  chameleon: "行情变了，打法也跟着变",
  beaver: "想自己动手，改参数、跑数据",
};

const SPECIES_BASE: SpeciesMeta[] = [
  { id: "cheetah", cn: "猎豹", glyph: "豹", tagline: "看见趋势就出发", style: "趋势信号、快节奏", behavior: "先看量价，持有期短，理由多是“趋势”", strength: "反应快，敢跟随趋势", watch: "趋势反转时容易接最后一棒。上车前先写好什么时候下车。", rec: "Qube 均线与动量模板", color: "#D4432A" },
  { id: "elephant", cn: "大象", glyph: "象", tagline: "便宜才买，买了就拿", style: "价值、长周期", behavior: "先看估值和位置，计划拿得很久", strength: "不被短期波动带走", watch: "便宜还可能更便宜。耐心之外，也要有认错的条件。", rec: "Qube「低 PB + 高 ROE」、A股个股档案", color: "#77745A" },
  { id: "fox", cn: "狐狸", glyph: "狐", tagline: "先怀疑，再检验", style: "找规律，先怀疑再检验", behavior: "常看历史统计，愿意把想法写成规则", strength: "愿意把直觉交给数据检验", watch: "历史规律会失效。回测好看，不等于以后有效。", rec: "B10 因子评估、因子大赛", color: "#C98A2E" },
  { id: "owl", cn: "猫头鹰", glyph: "鹰", tagline: "证据不够，就再等等", style: "证据门槛高，愿意等待", behavior: "观望，并且说得出自己在等什么", strength: "不追热点，等待有理由", watch: "等待也有代价。信号真的来了，要敢出手。", rec: "市场状态判断智能体", color: "#2D5F6B" },
  { id: "meerkat", cn: "狐獴", glyph: "獴", tagline: "最先听见风声", style: "对消息和人群情绪敏感", behavior: "先看消息，决定常随叙事改变", strength: "消息灵通，嗅觉快", watch: "人人都知道的消息，往往已经在价格里了。先核查，再行动。", rec: "证据核查任务、EVO 对抗复核", color: "#B07D3F" },
  { id: "chameleon", cn: "变色龙", glyph: "变", tagline: "跟着市场换打法", style: "依据随市场状态切换", behavior: "每一季的依据都不同，但各自说得通", strength: "能分辨不同的市场环境", watch: "换得太勤会两头挨打。每次切换都记下理由。", rec: "市场状态 / 风格切换智能体", color: "#3C7A4E" },
  { id: "beaver", cn: "海狸", glyph: "狸", tagline: "自己动手造工具", style: "喜欢自己造工具（隐藏物种）", behavior: "打开数据港口，读代码、改参数", strength: "能读代码、自己验证", watch: "工具不是目的。先想清楚要回答什么问题。", rec: "panda_data quickstart、QuantStudio", color: "#4A4A33", hidden: true },
];

function mergeSpecies(): SpeciesMeta[] {
  const d = DECKS.species;
  if (!Array.isArray(d)) return SPECIES_BASE.map((s) => ({ ...s, plain: PLAIN[s.id] }));
  return SPECIES_BASE.map((s) => {
    const x = d.find((y: any) => y.id === s.id);
    if (!x) return { ...s, plain: PLAIN[s.id] };
    return {
      ...s,
      plain: PLAIN[s.id],
      tagline: x.tagline || x.motto || s.tagline,
      strength: x.strength || s.strength,
      watch: x.watch || x.caution || x.blind_spot || s.watch,
      one: x.one_liner || s.one,
      looks: Array.isArray(x.looks_like) ? x.looks_like : s.looks,
    };
  });
}
export const SPECIES = mergeSpecies();
export const sp = (id: string) => SPECIES.find((s) => s.id === id)!;
export const PICKABLE = SPECIES.filter((s) => !s.hidden);

export const REASONS: { id: Reason; cn: string; sub: string; species: SpeciesId | null; ev?: string }[] = [
  { id: "price", cn: "量价", sub: "走势和成交量", species: "cheetah", ev: "price" },
  { id: "data", cn: "数据", sub: "估值和统计", species: "elephant", ev: "data" },
  { id: "news", cn: "消息", sub: "新闻和说法", species: "meerkat", ev: "news" },
  { id: "follow", cn: "跟别人", sub: "大家都这么做", species: "meerkat" },
  { id: "gut", cn: "直觉", sub: "就是感觉", species: null },
  { id: "lost", cn: "看不懂", sub: "说实话没看懂", species: null },
  { id: "rule", cn: "规则牌", sub: "按我留的规则", species: "fox" },
];
export const reasonCn = (r?: Reason) => REASONS.find((x) => x.id === r)?.cn || "";

export const PLANS: { id: Plan; cn: string; desc: string }[] = [
  { id: "cut", cn: "跌了就走", desc: "跌 5% 就卖出" },
  { id: "add", cn: "跌了就加", desc: "跌 5% 就加 1 份" },
  { id: "none", cn: "不定计划", desc: "到时候再说" },
];

/** 哪些选项算“等 / 观望” */
export const WAIT_OPTIONS: Partial<Record<SceneId, OptKey[]>> = { s924: ["C", "D"], soil: ["C", "D"] };

export interface Badge { id: string; cn: string; desc: string; glyph: string }
export const BADGES: Badge[] = [
  { id: "evidence", cn: "证据控", desc: "至少 2 场看了两张以上不同的证据，并且至少 3 场理由和证据一致", glyph: "证" },
  { id: "keepword", cn: "说到做到", desc: "定了计划、到时候照做，至少 2 场", glyph: "信" },
  { id: "history", cn: "金融史达人", desc: "认出并写对事件名，至少 2 场", glyph: "史" },
  { id: "datahand", cn: "数据手", desc: "数据港口答对至少 2 次", glyph: "码" },
  { id: "rulefan", cn: "规则派", desc: "用规则牌做决定并照做，至少 1 场", glyph: "规" },
  { id: "riskaware", cn: "看懂风险", desc: "看过风险类证据（融资余额、产品说明书等）至少 2 次", glyph: "险" },
];
export const badge = (id: string) => BADGES.find((b) => b.id === id)!;

/* ---------------- AI 对手 ---------------- */
export type FFAction = "hold" | "sell" | "add" | "enter";
export interface AiPick { option: OptKey; reason: Reason; ff: FFAction; line: string; second?: "add" | "stop" | "ignore"; plan?: Plan }
type AiTable = Record<string, Partial<Record<SceneId, AiPick>>>;

const AI_BASE: AiTable = {
  cheetah: {
    s924: { option: "A", reason: "price", ff: "hold", line: "放量突破，先上车再说。" },
    s2015: { option: "B", reason: "price", ff: "sell", line: "趋势还在，杠杆先不动。" },
    smt: { option: "B", reason: "price", ff: "hold", line: "双均线还是绿灯，拿着。" },
    scb: { option: "C", reason: "price", ff: "sell", line: "趋势破了，先砍一半。", second: "stop" },
    squant: { option: "B", reason: "rule", ff: "hold", line: "规则说继续，那就继续。" },
    soil: { option: "A", reason: "price", ff: "hold", line: "跌成这样，反弹就在眼前。" },
  },
  meerkat: {
    s924: { option: "A", reason: "follow", ff: "hold", line: "门口都排队了，我也去开户。" },
    s2015: { option: "B", reason: "news", ff: "sell", line: "评论都说行情才刚开始。" },
    smt: { option: "A", reason: "follow", ff: "hold", line: "顶流基金都在买，我也加。" },
    scb: { option: "D", reason: "news", ff: "hold", line: "新闻太吓人，先全卖了。", second: "ignore" },
    squant: { option: "D", reason: "follow", ff: "sell", line: "群里都在说先停掉。" },
    soil: { option: "A", reason: "follow", ff: "hold", line: "银行的产品，大家都在抄底。" },
  },
  owl: {
    s924: { option: "C", reason: "data", ff: "enter", line: "涨太快了，等第一次回调。" },
    s2015: { option: "C", reason: "data", ff: "hold", line: "融资余额太高，先把借的钱还了。" },
    smt: { option: "C", reason: "data", ff: "sell", line: "估值到了历史最高，先卖一半。" },
    scb: { option: "B", reason: "data", ff: "hold", line: "历史上大跌后多数会反弹，但先不加。", second: "add" },
    squant: { option: "D", reason: "data", ff: "sell", line: "先停下来，查清楚为什么亏。" },
    soil: { option: "C", reason: "data", ff: "hold", line: "说明书里的移仓规则没看懂，不碰。" },
  },
  elephant: {
    s924: { option: "D", reason: "data", ff: "hold", line: "已经不便宜了，不追。" },
    s2015: { option: "D", reason: "data", ff: "hold", line: "估值太高，全部卖出。" },
    smt: { option: "D", reason: "data", ff: "hold", line: "市盈率 73 倍，太贵了。" },
    scb: { option: "A", reason: "data", ff: "add", line: "好东西打折，分批买。", second: "add" },
    squant: { option: "B", reason: "rule", ff: "hold", line: "长期有效的规则，不该因为一周就改。" },
    soil: { option: "B", reason: "data", ff: "hold", line: "远月合约更稳，换远月。" },
  },
  fox: {
    s924: { option: "B", reason: "price", ff: "sell", line: "小仓位试试，跌 5% 就走。", plan: "cut" },
    s2015: { option: "C", reason: "data", ff: "hold", line: "杠杆先降掉，留着子弹。" },
    smt: { option: "C", reason: "rule", ff: "hold", line: "信号还没坏，但先锁一半利润。" },
    scb: { option: "B", reason: "data", ff: "hold", line: "统计上大跌后 20 天多数上涨，持有。", second: "ignore" },
    squant: { option: "C", reason: "rule", ff: "sell", line: "规则要改：加一条流动性过滤。" },
    soil: { option: "B", reason: "data", ff: "hold", line: "近月有交割风险，换远月。" },
  },
  chameleon: {
    s924: { option: "B", reason: "price", ff: "hold", line: "政策市来了，换成趋势打法。" },
    s2015: { option: "C", reason: "data", ff: "sell", line: "杠杆市要看融资数据，降一档。" },
    smt: { option: "C", reason: "news", ff: "sell", line: "风格要切换了，先减一半。" },
    scb: { option: "B", reason: "data", ff: "hold", line: "危机市看统计，先不动。", second: "add" },
    squant: { option: "C", reason: "rule", ff: "sell", line: "市场状态变了，规则也要变。" },
    soil: { option: "D", reason: "data", ff: "hold", line: "看不清的市场，先观望。" },
  },
};

export const AI_STARS: Record<string, number> = { cheetah: 2, meerkat: 1, owl: 3, elephant: 2, fox: 3, chameleon: 2 };

export function aiPick(id: string, scene: SceneId): AiPick {
  const d = DECKS.ai_species;
  const fromDeck = Array.isArray(d) ? d.find((x: any) => x.id === id || x.species === id) : null;
  const s = fromDeck?.scenes?.[scene];
  const base = AI_BASE[id]?.[scene] || { option: "B", reason: "gut", ff: "hold", line: "先拿着看看。" };
  if (!s) return base as AiPick;
  return {
    option: (s.option || base.option) as OptKey,
    reason: (s.reason || base.reason) as Reason,
    ff: (s.ff_action || s.ff || base.ff) as FFAction,
    line: s.line || base.line,
    second: (s.second || base.second) as any,
    plan: (s.plan || base.plan) as Plan,
  };
}
export function aiStars(id: string, scene?: string): number {
  const d = DECKS.ai_species;
  const x = Array.isArray(d) ? d.find((y: any) => y.species === id || y.id === id) : null;
  const ms = x?.method_stars ?? x?.stars;
  if (ms && typeof ms === "object") {
    if (scene && ms[scene] != null) return Number(ms[scene]);
    const vals = Object.values(ms).map(Number).filter((v) => !isNaN(v));
    return vals.length ? Math.round(vals.reduce((a, b) => a + b, 0) / vals.length) : AI_STARS[id] ?? 2;
  }
  const n = Number(ms ?? AI_STARS[id] ?? 2);
  return isNaN(n) ? AI_STARS[id] ?? 2 : n;
}

export const OPPONENT_SETS = [
  { id: "easy", cn: "入门", ids: ["cheetah", "meerkat"], desc: "一只追趋势，一只听消息：最容易被情绪带走的两种对手" },
  { id: "hard", cn: "进阶", ids: ["owl", "elephant"], desc: "一只等证据，一只看估值：方法星很难赢它们" },
  { id: "mirror", cn: "镜像", ids: ["fox", "chameleon"], desc: "一只信规则，一只看环境：比谁的理由更自洽" },
];
