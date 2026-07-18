import { useEffect } from "react";
import { ReactFlowProvider } from "@xyflow/react";
import { connectWS } from "./api";
import { useStore } from "./store";
import Canvas from "./components/Canvas";
import Copilot from "./components/Copilot";
import Gallery from "./components/Gallery";
import Inspector from "./components/Inspector";
import Palette from "./components/Palette";
import RunLogs from "./components/RunLogs";
import Settings from "./components/Settings";
import Topbar from "./components/Topbar";

function Toast() {
  const toast = useStore((s) => s.toast);
  const setToast = useStore((s) => s.setToast);
  useEffect(() => {
    if (!toast) return;
    const t = setTimeout(() => setToast(null), 3500);
    return () => clearTimeout(t);
  }, [toast, setToast]);
  if (!toast) return null;
  return (
    <div
      className="fixed bottom-5 left-1/2 -translate-x-1/2 z-50 px-4 py-2 rounded-xl text-sm"
      style={{ background: "var(--bg-3)", color: "var(--text-0)", border: "1px solid var(--line-bright)", boxShadow: "0 8px 30px rgb(0 0 0 / 0.5)" }}
    >
      {toast}
    </div>
  );
}

export default function App() {
  const loadCatalog = useStore((s) => s.loadCatalog);
  const loadExamples = useStore((s) => s.loadExamples);
  const loadSettings = useStore((s) => s.loadSettings);
  const handleEvent = useStore((s) => s.handleEvent);
  const setStore = useStore((s) => s.set);

  useEffect(() => {
    loadCatalog();
    loadSettings();
    loadExamples().then(() => {
      // First run: nothing on the canvas → greet with the gallery.
      const s = useStore.getState();
      if (s.nodes.length === 0 && s.examples.length > 0) setStore({ galleryOpen: true });
    });
    return connectWS(handleEvent);
  }, [loadCatalog, loadExamples, loadSettings, handleEvent, setStore]);

  return (
    <div className="h-full flex flex-col" style={{ background: "var(--bg-0)" }}>
      <Topbar />
      <div className="flex-1 flex min-h-0">
        <Palette />
        <div className="flex-1 flex flex-col min-w-0">
          <ReactFlowProvider>
            <Canvas />
          </ReactFlowProvider>
          <RunLogs />
        </div>
        <Inspector />
        <Copilot />
      </div>
      <Gallery />
      <Settings />
      <Toast />
    </div>
  );
}
