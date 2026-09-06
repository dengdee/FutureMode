import React from "react";
import { AbsoluteFill, Easing, interpolate, Sequence, spring, useCurrentFrame } from "remotion";

const teal = "#11a892";
const ink = "#10212b";
const muted = "#71808a";
const soft = "#edf7f5";
const navy = "#122a3a";

const scenes = [
  { from: 0, duration: 240, kicker: "PROXIMATE", title: "讓 AI 成為另一位組員", body: "從會前思考，到會中協作，再到會後記憶。", kind: "hero" },
  { from: 240, duration: 540, kicker: "THE GAP", title: "會議不該只發生在開始之後", body: "很多好想法，停在會議前；很多決定，散在會議後。", kind: "problem" },
  { from: 780, duration: 720, kicker: "BEFORE", title: "議前討論，把問題先想深", body: "每位參與者都能和自己的 AI Agent 對話，拆解風險、反例與待決問題。", kind: "prepare" },
  { from: 1500, duration: 720, kicker: "DURING", title: "會中即時協作，不搶走人的決定權", body: "逐字稿、AI 舉手、投票與共識，集中在同一個 Meeting Workspace。", kind: "live" },
  { from: 2220, duration: 660, kicker: "VOICE + DELEGATE", title: "不能出席，也能帶著觀點到場", body: "缺席代理保存個人立場；核准後，LLM 產生發言稿，再轉成語音。", kind: "voice" },
  { from: 2880, duration: 480, kicker: "MEMORY", title: "一次討論，變成團隊可搜尋的記憶", body: "議前文件切成 chunks、建立 embedding，會議中用 RAG 找回脈絡。", kind: "memory" },
  { from: 3360, duration: 240, kicker: "EVALUATION", title: "把協作，做成可累積的能力", body: "Proximate — AI meeting collaboration。", kind: "end" },
];

const easeIn = (frame: number, start = 0, distance = 24) => interpolate(frame, [start, start + 24], [distance, 0], { extrapolateRight: "clamp", easing: Easing.out(Easing.cubic) });
const fade = (frame: number, start = 0) => interpolate(frame, [start, start + 20], [0, 1], { extrapolateRight: "clamp" });

function TextBlock({ scene, local }: { scene: (typeof scenes)[number]; local: number }) {
  return <div style={{ position: "absolute", left: 112, top: 116, width: 780, opacity: fade(local), transform: `translateY(${easeIn(local)}px)` }}>
    <div style={{ color: teal, fontSize: 22, letterSpacing: 6, fontWeight: 800 }}>{scene.kicker}</div>
    <h1 style={{ margin: "22px 0 18px", color: ink, fontSize: 72, lineHeight: 1.08, letterSpacing: -2, fontWeight: 800 }}>{scene.title}</h1>
    <p style={{ margin: 0, color: muted, fontSize: 28, lineHeight: 1.5 }}>{scene.body}</p>
  </div>;
}

function BrowserFrame({ children, dark = false }: { children: React.ReactNode; dark?: boolean }) {
  return <div style={{ position: "absolute", right: 90, top: 174, width: 940, height: 670, borderRadius: 24, overflow: "hidden", background: dark ? "#0d171c" : "#fff", boxShadow: "0 30px 80px rgba(15,40,50,.16)", border: dark ? "1px solid #27404b" : "1px solid #dbe7e5" }}>
    <div style={{ height: 48, display: "flex", alignItems: "center", gap: 8, padding: "0 18px", background: dark ? "#13232a" : "#f7fbfa", borderBottom: dark ? "1px solid #27404b" : "1px solid #e8efed" }}>
      {['#ff6b6b', '#ffc857', '#11a892'].map((color) => <span key={color} style={{ width: 10, height: 10, borderRadius: "50%", background: color }} />)}
      <div style={{ marginLeft: 14, height: 22, flex: 1, borderRadius: 8, background: dark ? "#20363e" : "#eaf2f0" }} />
    </div>
    {children}
  </div>;
}

function HeroVisual({ local }: { local: number }) {
  const scale = spring({ frame: local, fps: 30, config: { damping: 14, stiffness: 90 } });
  return <div style={{ position: "absolute", right: 160, top: 220, width: 720, height: 540, transform: `scale(${scale})`, opacity: fade(local) }}>
    <div style={{ position: "absolute", inset: 0, borderRadius: 36, background: navy, transform: "rotate(-4deg)", boxShadow: "0 30px 70px rgba(18,42,58,.3)" }} />
    <div style={{ position: "absolute", inset: 28, borderRadius: 24, background: "#f8fbfa", padding: 36 }}>
      <div style={{ color: teal, fontSize: 19, letterSpacing: 5, fontWeight: 800 }}>PROXIMATE</div>
      <div style={{ color: ink, fontSize: 52, fontWeight: 800, marginTop: 20 }}>AI meeting<br />collaboration</div>
      <div style={{ display: "flex", gap: 12, marginTop: 48 }}>{["Before", "During", "After"].map((word, i) => <div key={word} style={{ flex: 1, padding: "18px 10px", textAlign: "center", borderRadius: 14, background: i === 1 ? teal : soft, color: i === 1 ? "white" : ink, fontWeight: 700 }}>{word}</div>)}</div>
      <div style={{ marginTop: 35, height: 10, borderRadius: 99, background: "#d8ebe7", overflow: "hidden" }}><div style={{ width: `${Math.min(100, 20 + local / 4)}%`, height: "100%", background: teal }} /></div>
    </div>
  </div>;
}

function ProblemVisual({ local }: { local: number }) {
  const items = ["會前：想法還沒成形", "會中：資訊分散、節奏太快", "會後：決策找不到脈絡"];
  return <div style={{ position: "absolute", right: 108, top: 220, width: 980, display: "flex", flexDirection: "column", gap: 18 }}>{items.map((item, i) => <div key={item} style={{ opacity: fade(local, i * 18), transform: `translateX(${interpolate(local, [i * 18, i * 18 + 24], [80, 0], { extrapolateRight: "clamp" })}px)`, display: "flex", alignItems: "center", gap: 24, padding: "24px 28px", borderRadius: 20, background: i === 1 ? navy : "#fff", color: i === 1 ? "#fff" : ink, border: i === 1 ? "none" : "1px solid #dbe7e5" }}><span style={{ width: 46, height: 46, borderRadius: 14, display: "grid", placeItems: "center", background: i === 1 ? "#294a5b" : soft, color: teal, fontSize: 22, fontWeight: 800 }}>0{i + 1}</span><span style={{ fontSize: 28, fontWeight: 700 }}>{item}</span><span style={{ marginLeft: "auto", color: i === 1 ? "#b9cbd0" : muted, fontSize: 20 }}>→</span></div>)}</div>;
}

function PrepareVisual({ local }: { local: number }) {
  return <BrowserFrame><div style={{ padding: 28 }}><div style={{ color: teal, fontSize: 15, letterSpacing: 3, fontWeight: 800 }}>議前討論</div><div style={{ color: ink, fontSize: 31, fontWeight: 800, marginTop: 8 }}>堅果品種改良大會</div><div style={{ marginTop: 26, display: "flex", flexDirection: "column", gap: 18 }}>{["我們需要討論下個版本的上線風險", "可以先釐清時程、依賴項目與回滾方案。", "還有哪些可能被忽略的反例？", "建議把風險分成技術、流程與溝通三類。"].map((text, i) => <div key={text} style={{ alignSelf: i % 2 === 0 ? "flex-end" : "flex-start", maxWidth: "76%", padding: "16px 20px", borderRadius: 18, borderBottomRightRadius: i % 2 === 0 ? 5 : 18, borderBottomLeftRadius: i % 2 === 1 ? 5 : 18, background: i % 2 === 0 ? teal : soft, color: i % 2 === 0 ? "#fff" : ink, fontSize: 19, lineHeight: 1.45, opacity: fade(local, 20 + i * 24), transform: `translateY(${easeIn(local, 20 + i * 24)}px)` }}>{text}</div>)}</div><div style={{ marginTop: 30, height: 58, border: "1px solid #cadbd8", borderRadius: 16, display: "flex", alignItems: "center", padding: "0 16px", color: "#9aa7aa", fontSize: 17 }}>和 Agent 討論一個問題…<span style={{ marginLeft: "auto", width: 38, height: 38, borderRadius: 12, background: teal, color: "#fff", display: "grid", placeItems: "center" }}>↑</span></div></div></BrowserFrame>;
}

function LiveVisual({ local }: { local: number }) {
  return <BrowserFrame dark><div style={{ padding: 30, color: "#eef7f5" }}><div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}><div><div style={{ color: "#54d4bd", letterSpacing: 3, fontSize: 14, fontWeight: 800 }}>LIVE MEETING</div><div style={{ marginTop: 8, fontSize: 29, fontWeight: 800 }}>目前討論：上線風險</div></div><div style={{ borderRadius: 999, padding: "9px 16px", background: "#183d3d", color: "#67ddc5", fontSize: 15 }}>● 即時連線</div></div><div style={{ display: "grid", gridTemplateColumns: "1.15fr .85fr", gap: 20, marginTop: 32 }}><div style={{ padding: 24, borderRadius: 18, background: "#172a31", border: "1px solid #2b4750" }}><div style={{ color: "#a9bcc1", fontSize: 15 }}>最新逐字稿</div><div style={{ marginTop: 22, fontSize: 22, lineHeight: 1.55 }}>「我們先確認回滾方案，再決定是否在本週上線。」</div><div style={{ marginTop: 32, display: "flex", gap: 8, alignItems: "center", color: "#64d7c1", fontSize: 15 }}>◉ AI 正在整理脈絡</div></div><div style={{ padding: 24, borderRadius: 18, background: "#f1faf7", color: ink }}><div style={{ color: teal, fontSize: 15, fontWeight: 800 }}>AI 舉手</div><div style={{ marginTop: 18, fontSize: 20, lineHeight: 1.45, fontWeight: 700 }}>是否補充監控指標與停機門檻？</div><div style={{ display: "flex", gap: 8, marginTop: 28 }}>{["支持", "稍後", "忽略"].map((x, i) => <span key={x} style={{ padding: "9px 12px", borderRadius: 9, background: i === 0 ? teal : "#fff", color: i === 0 ? "#fff" : muted, border: i === 0 ? "none" : "1px solid #d5e5e1", fontSize: 14 }}>{x}</span>)}</div></div></div></div></BrowserFrame>;
}

function VoiceVisual({ local }: { local: number }) {
  const steps = ["核准發言", "Gemini 生成文字", "Edge TTS", "送入 Meet"];
  return <div style={{ position: "absolute", right: 120, top: 260, width: 980, padding: 34, borderRadius: 24, background: navy, color: "#fff", boxShadow: "0 30px 70px rgba(18,42,58,.24)" }}><div style={{ color: "#76e2cd", letterSpacing: 3, fontSize: 15, fontWeight: 800 }}>VOICE BOT PIPELINE</div><div style={{ display: "flex", alignItems: "center", marginTop: 42 }}>{steps.map((step, i) => <React.Fragment key={step}><div style={{ flex: 1, textAlign: "center", opacity: fade(local, 18 + i * 20), transform: `translateY(${easeIn(local, 18 + i * 20)}px)` }}><div style={{ margin: "auto", width: 82, height: 82, borderRadius: 22, display: "grid", placeItems: "center", background: i === 1 ? teal : "#244453", fontSize: 27 }}>{["✓", "✦", "◉", "↗"][i]}</div><div style={{ marginTop: 16, fontSize: 17, fontWeight: 700 }}>{step}</div></div>{i < steps.length - 1 && <div style={{ color: "#6bcfbd", fontSize: 26 }}>→</div>}</React.Fragment>)}</div><div style={{ marginTop: 44, padding: "18px 22px", borderRadius: 15, background: "#183843", color: "#c7e4df", fontSize: 18 }}>「我建議先確認上線風險，再決定回滾方案。」</div></div>;
}

function MemoryVisual({ local }: { local: number }) {
  return <div style={{ position: "absolute", right: 130, top: 240, width: 920, height: 470 }}><div style={{ position: "absolute", left: 0, top: 130, width: 240, padding: 22, borderRadius: 18, background: "#fff", border: "1px solid #dbe7e5", boxShadow: "0 16px 40px rgba(15,40,50,.1)", opacity: fade(local) }}><div style={{ color: teal, fontSize: 14, fontWeight: 800 }}>DOCUMENT</div><div style={{ marginTop: 12, fontSize: 20, fontWeight: 700, color: ink }}>議前討論摘要.md</div><div style={{ marginTop: 16, height: 8, borderRadius: 99, background: soft }} /><div style={{ marginTop: 8, height: 8, width: "72%", borderRadius: 99, background: soft }} /></div><div style={{ position: "absolute", left: 360, top: 20, width: 240, padding: 22, borderRadius: 18, background: navy, color: "#fff", boxShadow: "0 16px 40px rgba(15,40,50,.16)", opacity: fade(local, 25), transform: `translateY(${easeIn(local, 25)}px)` }}><div style={{ color: "#79e1cf", fontSize: 14, fontWeight: 800 }}>EMBEDDINGS</div><div style={{ marginTop: 12, fontSize: 20, fontWeight: 700 }}>3 個內容 chunks</div><div style={{ marginTop: 16, display: "flex", gap: 5 }}>{Array.from({ length: 7 }).map((_, i) => <span key={i} style={{ width: 18, height: 18, borderRadius: 5, background: i % 2 ? "#2c6774" : teal }} />)}</div></div><div style={{ position: "absolute", right: 0, top: 130, width: 240, padding: 22, borderRadius: 18, background: "#eaf8f5", color: ink, border: "1px solid #b9e2da", opacity: fade(local, 50), transform: `translateY(${easeIn(local, 50)}px)` }}><div style={{ color: teal, fontSize: 14, fontWeight: 800 }}>RAG SEARCH</div><div style={{ marginTop: 12, fontSize: 20, fontWeight: 700 }}>上線風險</div><div style={{ marginTop: 16, color: muted, fontSize: 15 }}>找到 3 段相關脈絡</div></div><div style={{ position: "absolute", left: 240, top: 244, width: 450, height: 2, background: teal, opacity: fade(local, 65) }} /></div>;
}

function Scene({ scene }: { scene: (typeof scenes)[number] }) {
  const frame = useCurrentFrame();
  const local = frame - scene.from;
  return <AbsoluteFill style={{ background: scene.kind === "voice" ? "#f3faf8" : "#fbfdfc", fontFamily: "Arial, 'Microsoft JhengHei', sans-serif" }}><div style={{ position: "absolute", inset: 0, background: "radial-gradient(circle at 82% 20%, #e3f5f1 0, transparent 34%), radial-gradient(circle at 10% 90%, #eef5fa 0, transparent 28%)" }} /><TextBlock scene={scene} local={local} />{scene.kind === "hero" && <HeroVisual local={local} />}{scene.kind === "problem" && <ProblemVisual local={local} />}{scene.kind === "prepare" && <PrepareVisual local={local} />}{scene.kind === "live" && <LiveVisual local={local} />}{scene.kind === "voice" && <VoiceVisual local={local} />}{scene.kind === "memory" && <MemoryVisual local={local} />}{scene.kind === "end" && <div style={{ position: "absolute", right: 170, top: 218, width: 700, opacity: fade(local), transform: `translateY(${easeIn(local)}px)` }}><div style={{ padding: 42, borderRadius: 28, background: navy, color: "#fff", boxShadow: "0 30px 70px rgba(18,42,58,.22)" }}><div style={{ color: "#74dfcb", fontSize: 20, letterSpacing: 4, fontWeight: 800 }}>THE TAKEAWAY</div><div style={{ marginTop: 20, fontSize: 36, lineHeight: 1.3, fontWeight: 800 }}>更好的會議，<br />從更好的準備開始。</div><div style={{ marginTop: 30, display: "flex", flexWrap: "wrap", gap: 10 }}>{[["產品價值", "9.0"], ["AI 協作", "8.5"], ["流程完整", "9.0"], ["展示潛力", "9.0"]].map(([label, score]) => <div key={label} style={{ padding: "10px 13px", borderRadius: 12, background: "#1d4251", color: "#cce8e2", fontSize: 15 }}><span style={{ color: "#74dfcb", fontWeight: 800 }}>{score}</span> {label}</div>)}</div><div style={{ marginTop: 26, color: "#c1d3d6", fontSize: 19 }}>Proximate / FutureMode</div></div></div>}<div style={{ position: "absolute", left: 112, bottom: 62, right: 112, height: 3, background: "#dcebe8" }}><div style={{ height: "100%", width: `${(frame / 3600) * 100}%`, background: teal }} /></div><div style={{ position: "absolute", right: 112, bottom: 78, color: muted, fontSize: 14 }}>{String(Math.floor(frame / 30 / 60)).padStart(2, "0")}:{String(Math.floor((frame / 30) % 60)).padStart(2, "0")}</div></AbsoluteFill>;
}

export const Video: React.FC = () => <AbsoluteFill>{scenes.map((scene) => <Sequence key={scene.kind} from={scene.from} durationInFrames={scene.duration}><Scene scene={scene} /></Sequence>)}</AbsoluteFill>;
