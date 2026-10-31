import { useState, type MouseEvent } from "react";
import { useNavigate } from "react-router-dom";
import { ART } from "../data";
import { sp } from "../game/meta";
import { useGame } from "../game/store";
import { sfx } from "../lib/sound";
import { FinalView, JudgeView } from "../arcade/Arcade";
import type { Run } from "../arcade/Game";
import { Ending } from "../screens/Ending";

/** 桌游主线的终局：拿名场面里的真实操作交给 AI 复盘，结果一页一件事；最后一页把结果带回桌上 */
export function LiveEnding() {
  const { g, update, start } = useGame();
  const nav = useNavigate();
  const [archive, setArchive] = useState(false);
  const runs = g!.seasons.map((r) => r.run).filter(Boolean) as Run[];
  if (archive || !runs.length) return <Ending archive={archive} />;
  const quick = g!.mode === "quick";
  if (!g!.verdict) {
    return (
      <div className="screen arc dark">
        <div className="arc-body">
          <JudgeView runs={runs} guess={g!.self || null} onVerdict={(v) => update((x) => void (x.verdict = v))} />
        </div>
      </div>
    );
  }
  const v = g!.verdict;
  const m = sp(v.species);
  function fullGame() {
    sfx.bell();
    const { self, opponents } = g!;
    start();
    update((x) => {
      x.self = self;
      x.opponents = opponents;
      x.aiMoney = Object.fromEntries(opponents.map((id) => [id, 20]));
      x.phase = "map";
    });
  }
  const stop = (fn: () => void) => (e: MouseEvent) => {
    e.stopPropagation();
    fn();
  };
  return (
    <div className="screen arc dark">
      <div className="arc-body">
        <FinalView
          runs={runs}
          verdict={v}
          total={g!.money - 20}
          unit={quick ? "场" : "季"}
          extra={
            <>
              <div className="arc-kicker">带到桌上</div>
              <h2 className="display">桌上那一盒，是同一个游戏</h2>
              <div className="live-table mt12">
                <img src={ART(`species_${m.id}`)} alt="" />
                <div>
                  <b>{m.cn}</b>
                  <span>开局把{m.cn}卡摆在面前，看看桌上的你还是不是它</span>
                </div>
              </div>
              <div className="arc-qube mt12">同样的名场面卡、证据牌和委托单。玩完扫终局档案卡上的码，AI 用同一套方法再读你一次。</div>
            </>
          }
          actions={
            <div className="col gap8 mt16">
              {quick && <button className="btn primary big block" onClick={stop(fullGame)}>继续完整四季 →</button>}
              <div className="row gap8">
                <button className="btn grow" onClick={stop(() => { sfx.tap(); setArchive(true); })}>完整画像档案</button>
                <button className="btn grow" onClick={stop(() => nav("/"))}>回首页</button>
              </div>
            </div>
          }
        />
      </div>
    </div>
  );
}
