import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter, Route, Routes } from "react-router-dom";
import "./styles.css";
import { Home } from "./screens/Intro";
import { Play } from "./screens/Play";
import { About, Atlas } from "./pages/Info";
import { QrResolve, BlindPage, EvidencePage, RevealPage, BreakerPage, RulePage, SpeciesPage, TaskPage, DataPortPage, CardPage, StartPage } from "./pages/Qr";
import { RecordPage } from "./pages/Record";
import { DemoPage } from "./pages/Demo";
import { TermHost } from "./ui/Term";
import { Arcade } from "./arcade/Arcade";

function App() {
  return (
    <div className="frame">
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/play" element={<Play />} />
        <Route path="/go" element={<Arcade />} />
        <Route path="/q/:code" element={<QrResolve />} />
        <Route path="/start" element={<StartPage />} />
        <Route path="/b/:scene" element={<BlindPage />} />
        <Route path="/e/:scene/:kind" element={<EvidencePage />} />
        <Route path="/r/:scene" element={<RevealPage />} />
        <Route path="/ff/:scene" element={<BreakerPage />} />
        <Route path="/rule/:id" element={<RulePage />} />
        <Route path="/sp/:id" element={<SpeciesPage />} />
        <Route path="/task/:id" element={<TaskPage />} />
        <Route path="/dp/:id" element={<DataPortPage />} />
        <Route path="/c/:id" element={<CardPage />} />
        <Route path="/record" element={<RecordPage />} />
        <Route path="/atlas" element={<Atlas />} />
        <Route path="/about" element={<About />} />
        <Route path="/demo" element={<DemoPage />} />
        <Route path="*" element={<Home />} />
      </Routes>
      <TermHost />
    </div>
  );
}

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <BrowserRouter basename="/ts">
      <App />
    </BrowserRouter>
  </React.StrictMode>,
);
