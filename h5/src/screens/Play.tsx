import { useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useGame } from "../game/store";
import { LiveEnding } from "../scenes/LiveEnd";
import { Prologue, SelfPick } from "./Intro";
import { MapScreen } from "./MapScreen";
import { QuickPick } from "./Quick";
import { SceneFlow } from "./Scene";
import { Station } from "./Station";

export function Play() {
  const { g, update, start } = useGame();
  const nav = useNavigate();
  useEffect(() => {
    if (!g) start();
  }, [g]);
  useEffect(() => {
    window.scrollTo({ top: 0 });
  }, [g?.phase, g?.seasonIdx]);
  if (!g) return null;
  const station = () => update((x) => void (x.phase = "station"));
  const quick = g.mode === "quick";
  switch (g.phase) {
    case "home":
    case "prologue":
      return <Prologue onDone={() => update((x) => void (x.phase = "self"))} />;
    case "self":
      return (
        <SelfPick quick={quick} onDone={(self, opp) => update((x) => {
          x.self = self;
          x.opponents = opp;
          x.aiMoney = Object.fromEntries(opp.map((id) => [id, 20]));
          x.phase = x.mode === "quick" ? "pick" : "map";
        })} />
      );
    case "map":
      return <MapScreen onEnterScene={() => {}} />;
    case "pick":
      return <QuickPick />;
    case "scene":
      return <SceneFlow onStation={station} />;
    case "station":
      return <Station onNext={() => {}} />;
    case "ending":
      return <LiveEnding />;
    default:
      nav("/");
      return null;
  }
}
