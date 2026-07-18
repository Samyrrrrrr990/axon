import { useEffect, useRef, useState } from "react";
import { api } from "../api";
import { useStore } from "../store";

function WorkflowMenu() {
  const [open, setOpen] = useState(false);
  const [items, setItems] = useState<{ id: string; name: string; node_count: number }[]>([]);
  const openWorkflow = useStore((s) => s.openWorkflow);
  const newWorkflow = useStore((s) => s.newWorkflow);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const close = (e: MouseEvent) => {
      if (!ref.current?.contains(e.target as Node)) setOpen(false);
    };
    document.addEventListener("mousedown", close);
    return () => document.removeEventListener("mousedown", close);
  }, []);

  return (
    <div className="relative" ref={ref}>
      <button
        onClick={async () => {
          if (!open) setItems(await api.listWorkflows());
          setOpen(!open);
        }}
        className="px-2.5 py-1.5 rounded-lg text-sm"
        style={{ color: "var(--text-1)" }}
        title="Your workflows"
      >
        ☰
      </button>
      {open && (
        <div
          className="absolute left-0 top-10 w-64 rounded-xl p-1.5 z-50 max-h-96 overflow-y-auto"
          style={{ background: "var(--bg-2)", border: "1px solid var(--line-bright)", boxShadow: "0 8px 30px rgb(0 0 0 / 0.5)" }}
        >
          <button
            onClick={() => {
              newWorkflow();
              setOpen(false);
            }}
            className="w-full text-left px-3 py-2 rounded-lg text-sm hover:bg-[var(--bg-3)]"
            style={{ color: "var(--accent)" }}
          >
            + New workflow
          </button>
          {items.map((w) => (
            <button
              key={w.id}
              onClick={() => {
                openWorkflow(w.id);
                setOpen(false);
              }}
              className="w-full text-left px-3 py-2 rounded-lg text-sm hover:bg-[var(--bg-3)] flex justify-between"
              style={{ color: "var(--text-0)" }}
            >
              <span className="truncate">{w.name}</span>
              <span className="font-mono text-xs" style={{ color: "var(--text-1)" }}>
                {w.node_count}
              </span>
            </button>
          ))}
          {items.length === 0 && (
            <div className="px-3 py-2 text-xs" style={{ color: "var(--text-1)" }}>
              No saved workflows yet.
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default function Topbar() {
  const name = useStore((s) => s.workflowName);
  const setName = useStore((s) => s.setWorkflowName);
  const save = useStore((s) => s.saveWorkflow);
  const run = useStore((s) => s.runWorkflow);
  const cancel = useStore((s) => s.cancelRun);
  const status = useStore((s) => s.run.status);
  const dirty = useStore((s) => s.dirty);
  const setStore = useStore((s) => s.set);
  const copilotOpen = useStore((s) => s.copilotOpen);
  const running = status === "running";

  return (
    <header
      className="h-12 shrink-0 flex items-center gap-3 px-3 border-b z-20"
      style={{ background: "var(--bg-1)", borderColor: "var(--line)" }}
    >
      <div className="flex items-center gap-2 select-none">
        <svg width="22" height="22" viewBox="0 0 22 22" aria-hidden>
          <circle cx="5" cy="11" r="3" fill="var(--accent)" />
          <circle cx="17" cy="5" r="2.4" fill="var(--sock-dataset)" />
          <circle cx="17" cy="17" r="2.4" fill="var(--sock-model)" />
          <path d="M7.5 10L14.8 5.8M7.5 12L14.8 16.2" stroke="var(--line-bright)" strokeWidth="1.6" />
        </svg>
        <span className="font-display font-semibold tracking-wide" style={{ color: "var(--text-0)" }}>
          AXON
        </span>
      </div>
      <WorkflowMenu />
      <input
        value={name}
        onChange={(e) => setName(e.target.value)}
        className="bg-transparent outline-none text-sm rounded-lg px-2 py-1 min-w-0 flex-1 max-w-xs focus:bg-[var(--bg-2)]"
        style={{ color: "var(--text-0)" }}
        aria-label="Workflow name"
      />
      {dirty && (
        <span className="text-[10px] font-mono" style={{ color: "var(--text-1)" }}>
          unsaved
        </span>
      )}

      <div className="ml-auto flex items-center gap-2">
        <button
          onClick={() => setStore({ galleryOpen: true })}
          className="px-3 py-1.5 rounded-lg text-sm"
          style={{ color: "var(--text-1)" }}
        >
          Examples
        </button>
        <button
          onClick={save}
          className="px-3 py-1.5 rounded-lg text-sm"
          style={{ color: "var(--text-0)", border: "1px solid var(--line-bright)" }}
        >
          Save
        </button>
        <button
          onClick={() => setStore({ settingsOpen: true })}
          className="px-2.5 py-1.5 rounded-lg text-sm"
          style={{ color: "var(--text-1)" }}
          title="Settings"
          aria-label="Settings"
        >
          ⚙
        </button>
        <button
          onClick={() => setStore({ copilotOpen: !copilotOpen })}
          className="px-3 py-1.5 rounded-lg text-sm font-medium"
          style={{
            color: copilotOpen ? "var(--accent)" : "var(--text-0)",
            border: `1px solid ${copilotOpen ? "var(--accent)" : "var(--line-bright)"}`,
          }}
        >
          Copilot
        </button>
        <button
          onClick={running ? cancel : run}
          className="px-4 py-1.5 rounded-lg text-sm font-semibold font-display tracking-wide"
          style={{
            background: running ? "var(--bg-3)" : "var(--accent)",
            color: running ? "var(--err)" : "#0b0e14",
          }}
        >
          {running ? "■ Stop" : "▶ Run"}
        </button>
      </div>
    </header>
  );
}
