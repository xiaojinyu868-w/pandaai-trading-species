import type { SpeciesId } from "../game/meta";
import type { Run } from "./Game";
import { levelById } from "./levels";
import { describe, ORDER, scores, stampOf, type Verdict } from "./profile";

/** AI 只在服务端调（/ts-api 由 nginx 转给本机的小服务，key 不进前端）；超时或失败就用本地结果 */
const API = "/ts-api";

async function post<T>(path: string, body: unknown, ms: number): Promise<T | null> {
  const c = new AbortController();
  const t = setTimeout(() => c.abort(), ms);
  try {
    const r = await fetch(API + path, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body), signal: c.signal });
    if (!r.ok) return null;
    return (await r.json()) as T;
  } catch {
    return null;
  } finally {
    clearTimeout(t);
  }
}

const clip = (s: unknown, n: number) => {
  if (typeof s !== "string") return "";
  const t = s.trim();
  if (t.length <= n) return t;
  const cut = t.slice(0, n);
  const k = Math.max(...["。", "！", "？", "；"].map((c) => cut.lastIndexOf(c)));
  return k >= n * 0.5 ? cut.slice(0, k + 1) : cut.slice(0, n - 1) + "…";
};

export async function aiLine(r: Run): Promise<string | null> {
  const l = levelById(r.id);
  const st = stampOf(l, r);
  const res = await post<{ line?: string }>("/line", { level: l.reveal.name, did: describe(l, r), stamp: `${st.t}：${st.sub}`, lesson: l.reveal.lesson }, 6000);
  const line = clip(res?.line, 48);
  return line || null;
}

export async function aiJudge(runs: Run[], guess: string | null, local: Verdict): Promise<Verdict> {
  const body = {
    levels: runs.map((r) => {
      const l = levelById(r.id);
      const st = stampOf(l, r);
      return { name: l.reveal.name, did: describe(l, r), stamp: `${st.t}：${st.sub}` };
    }),
    scores: scores(runs),
    guess,
  };
  const res = await post<Partial<Verdict>>("/judge", body, 9000);
  if (!res || !ORDER.includes(res.species as SpeciesId)) return local;
  const moments = Array.isArray(res.moments) ? res.moments.map((m) => clip(m, 40)).filter(Boolean).slice(0, 3) : [];
  return {
    species: res.species as SpeciesId,
    title: clip(res.title, 14) || local.title,
    read: clip(res.read, 110) || local.read,
    moments: moments.length >= 2 ? moments : local.moments,
    gap: clip(res.gap, 100) || local.gap,
    qube: clip(res.qube, 110) || local.qube,
    self: clip(res.self, 44) || local.self,
    model: clip(res.model, 40) || "deepseek-v4.1-flash",
  };
}
