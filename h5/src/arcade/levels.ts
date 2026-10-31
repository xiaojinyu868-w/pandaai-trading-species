import PATHS from "./paths.json";

/**
 * 主线四关：每一关是一段真实行情 + 一个只属于这一场的机关。
 * 手势全程只有一个：按住 = 拿着，松手 = 卖出。
 */

export type LevelId = "s924" | "s2015" | "smt" | "scb";
export type Twist = "holiday" | "leverage" | "circle" | "halt";

interface Series { code: string; name: string; api: string; dates: string[]; open: number[]; close: number[] }
const P = (PATHS as unknown as { levels: Record<LevelId, Series> }).levels;

export interface Level {
  id: LevelId;
  n: number;
  season: "spring" | "summer" | "autumn" | "winter";
  seasonCn: string;
  twist: Twist;
  /** 开局就拿着（按住才算继续拿着） */
  startIn: boolean;
  /** 不算慢放，整段大约多少秒 */
  sec: number;
  /** 慢放区间：从哪天到哪天，速度乘多少 */
  slow: [string, string, number][];
  cold: { title: string; line: string };
  /** 开局前那一句机关说明 */
  rule: string;
  /** 这一场的弹幕：按行情情绪分组 */
  pool: Partial<Record<"flat" | "up" | "hot" | "down" | "fear" | "rebound", string[]>>;
  reveal: { name: string; when: string; big: string; unit: string; label: string; lesson: string; source: string };
  series: Series;
  holiday?: { close: string; open: string };
  lev?: { at: number; floor: number };
  lock?: string[];
  halts?: string[];
}

export const LEVELS: Level[] = [
  {
    id: "s924", n: 1, season: "spring", seasonCn: "春", twist: "holiday", startIn: false, sec: 22,
    slow: [["2024-09-24", "2024-10-09", 0.42]],
    cold: { title: "长假前夜，人人都在排队", line: "你现在空仓。" },
    rule: "中途会放长假：休市那几天，谁都动不了。",
    pool: {
      flat: ["又是横盘", "割肉离场了", "没救了", "等一个信号"],
      up: ["营业部排长队", "开户排了三小时", "这次是真牛市", "楼下大妈都在问"],
      hot: ["借钱也要上", "全仓杀入", "闭眼买都赚", "节后必涨停"],
      down: ["开盘就是最高点？", "被套了", "早知道节前就卖", "只是回调吧"],
      fear: ["割了割了", "又回去了"],
      rebound: ["又涨回来了", "抄到了"],
    },
    reveal: {
      name: "924 · 国庆全民开户", when: "2024 年 9 月 2 日 — 11 月 11 日 · 上证指数",
      big: "3.45", unit: "万亿", label: "节后第一天的成交额：开盘约 20 分钟就破万亿，创历史纪录（公开报道）",
      lesson: "排队进场的那一刻，最该想清楚的是：什么时候走。", source: "真实收盘价 · Panda Data 指数日线",
    },
    series: P.s924,
    holiday: { close: "2024-09-30", open: "2024-10-08" },
  },
  {
    id: "s2015", n: 2, season: "summer", seasonCn: "夏", twist: "leverage", startIn: true, sec: 24,
    slow: [["2015-06-12", "2015-07-09", 0.4]],
    cold: { title: "人人都在借钱买的夏天", line: "你手里已经有货。" },
    rule: "涨多了会有人借钱给你；跌停那天，卖不出去。",
    pool: {
      flat: ["稳住", "等风来"],
      up: ["又红了", "今天吃肉", "目标一万点", "辞职炒股了"],
      hot: ["配资 1 比 5", "借钱也要上", "人人都是股神", "满仓还嫌少"],
      down: ["千股跌停", "卖不掉！", "排队卖出中", "要不要跑？"],
      fear: ["强平了", "一夜回到解放前", "卸载软件了", "再也不碰股票了"],
      rebound: ["救市了！", "抄底抄在半山腰？"],
    },
    reveal: {
      name: "2015 · 杠杆牛与千股跌停", when: "2015 年 3 月 2 日 — 7 月 20 日 · 上证指数",
      big: "35", unit: "%", label: "6 月 12 日见顶后不到一个月的跌幅：盘中 5178 点跌到 3374 点",
      lesson: "借来的钱，会在你最需要时间的时候，逼你离场。", source: "真实收盘价 · Panda Data 指数日线",
    },
    series: P.s2015,
    lev: { at: 0.38, floor: 5 },
    lock: ["2015-06-19", "2015-06-26", "2015-07-01", "2015-07-03", "2015-07-08"],
  },
  {
    id: "smt", n: 3, season: "autumn", seasonCn: "秋", twist: "circle", startIn: true, sec: 24,
    slow: [["2021-02-08", "2021-03-10", 0.45]],
    cold: { title: "人人都抱着同一样东西", line: "你也在圈里。" },
    rule: "圈里的人越来越多。有人松手的时候，你会看见。",
    pool: {
      flat: ["拿住别动", "长期主义"],
      up: ["永远涨", "基金经理都在买", "抱紧了", "买了就不卖"],
      hot: ["新基金一天卖光", "核心资产", "这辈子拿着", "贵有贵的道理"],
      down: ["有人跑了", "只是回调", "抱团松动？", "手好抖"],
      fear: ["出口只有一个", "都在卖", "割了"],
      rebound: ["反弹了", "又回来了？"],
    },
    reveal: {
      name: "茅台与顶流基金 · 抱团瓦解", when: "2020 年 11 月 — 2021 年 3 月 · 贵州茅台（前复权）",
      big: "28", unit: "%", label: "春节后见顶，之后一个月里的最大跌幅",
      lesson: "抱团的时候人人都是长期主义者；松动的时候，出口只有一个。", source: "真实收盘价 · Panda Data 个股日线（前复权）",
    },
    series: P.smt,
  },
  {
    id: "scb", n: 4, season: "winter", seasonCn: "冬", twist: "halt", startIn: true, sec: 22,
    slow: [["2020-03-09", "2020-03-24", 0.5]],
    cold: { title: "跌到交易所按下暂停键", line: "你手里有货。" },
    rule: "跌得太快，市场会暂停：暂停的时候，谁都动不了。",
    pool: {
      flat: ["观望观望", "还会跌吗"],
      up: ["反弹了", "V 回来了", "抄到底了"],
      hot: ["新高见", "买买买"],
      down: ["又熔断了", "这次真的不一样", "清仓了", "现金为王"],
      fear: ["末日来了", "全卖了", "再也不看了", "跌穿了"],
      rebound: ["暴力反弹", "卖早了", "没上车"],
    },
    reveal: {
      name: "2020 · 美股十天四次熔断", when: "2020 年 3 月 2 日 — 4 月 14 日 · 纳斯达克 100",
      big: "4", unit: "次", label: "十天里熔断的次数；3 月 23 日见底后，一路涨回去",
      lesson: "最恐慌的十天里，卖出和买入的人都觉得自己清醒。区别在于：有没有提前写好计划。", source: "真实收盘价 · 纳斯达克 100 日线（公开接口）",
    },
    series: P.scb,
    halts: ["2020-03-09", "2020-03-12", "2020-03-16", "2020-03-18"],
  },
];

export const levelById = (id: string) => LEVELS.find((l) => l.id === id)!;

/** 每天两个点：开盘、收盘。跳空（长假、熔断后的开盘）就是一根竖线 */
export function ticksOf(l: Level) {
  const s = l.series;
  const p: number[] = [];
  const day: number[] = [];
  s.close.forEach((c, i) => {
    p.push(s.open[i] || c, c);
    day.push(i, i);
  });
  return { p, day, dates: s.dates };
}
