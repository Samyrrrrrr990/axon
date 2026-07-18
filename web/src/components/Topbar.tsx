import { useEffect, useRef, useState } from "react";
import {
  CaretDownIcon,
  FloppyDiskIcon,
  GearSixIcon,
  PlayIcon,
  PlusIcon,
  SparkleIcon,
  SquaresFourIcon,
  StopIcon,
} from "@phosphor-icons/react";
import { api } from "../api";
import { useStore } from "../store";

function WorkflowMenu() {
  const [open, setOpen] = useState(false);
  const [items, setItems] = useState<{ id: string; name: string; node_count: number }[]>([]);
  const openWorkflow = useStore((s) => s.openWorkflow);
  const newWorkflow = useStore((s) => s.newWorkflow);
  const name = useStore((s) => s.workflowName);
  const setName = useStore((s) => s.setWorkflowName);
  const dirty = useStore((s) => s.dirty);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const close = (e: MouseEvent) => {
      if (!ref.current?.contains(e.target as Node)) setOpen(false);
    };
    document.addEventListener("mousedown", close);
    return () => document.removeEventListener("mousedown", close);
  }, []);

  return (
    <div className="relative flex items-center gap-1 min-w-0" ref={ref}>
      <input
        value={name}
        onChange={(e) => setName(e.target.value)}
        className="bg-transparent outline-none text-sm rounded-lg px-2 py-1.5 min-w-0 w-48 truncate transition-colors hover:bg-[var(--bg-2)] focus:bg-[var(--bg-2)]"
        style={{ color: "var(--text-0)" }}
        aria-label="Workflow name"
      />
      {dirty && (
        <span
          className="w-1.5 h-1.5 rounded-full shrink-0"
          style={{ background: "var(--accent)" }}
          title="Unsaved changes"
        />
      )}
      <button
        className="btn btn-ghost !px-1.5"
        onClick={async () => {
          if (!open) setItems(await api.listWorkflows());
          setOpen(!open);
        }}
        title="Your workflows"
        aria-label="Open workflow list"
      >
        <CaretDownIcon size={14} />
      </button>
      {open && (
        <div
          className="modal-card absolute left-0 top-11 w-72 p-1.5 z-50 max-h-96 overflow-y-auto !rounded-xl"
          style={{ boxShadow: "0 16px 50px rgb(0 0 0 / 0.5)" }}
        >
          <button
            onClick={() => {
              newWorkflow();
              setOpen(false);
            }}
            className="w-full flex items-center gap-2 text-left px-3 py-2 rounded-lg text-sm transition-colors hover:bg-[var(--bg-3)]"
            style={{ color: "var(--accent)" }}
          >
            <PlusIcon size={14} weight="bold" /> New workflow
          </button>
          {items.map((w) => (
            <button
              key={w.id}
              onClick={() => {
                openWorkflow(w.id);
                setOpen(false);
              }}
              className="w-full text-left px-3 py-2 rounded-lg text-sm transition-colors hover:bg-[var(--bg-3)] flex justify-between items-center gap-3"
              style={{ color: "var(--text-0)" }}
            >
              <span className="truncate">{w.name}</span>
              <span className="font-mono text-[11px] shrink-0" style={{ color: "var(--text-2)" }}>
                {w.node_count} nodes
              </span>
            </button>
          ))}
          {items.length === 0 && (
            <div className="px-3 py-2 text-xs" style={{ color: "var(--text-1)" }}>
              Nothing saved yet. Build something and press Save.
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default function Topbar() {
  const save = useStore((s) => s.saveWorkflow);
  const run = useStore((s) => s.runWorkflow);
  const cancel = useStore((s) => s.cancelRun);
  const status = useStore((s) => s.run.status);
  const setStore = useStore((s) => s.set);
  const copilotOpen = useStore((s) => s.copilotOpen);
  const running = status === "running";

  return (
    <header
      className="h-13 shrink-0 flex items-center gap-2 px-3 border-b z-20"
      style={{ background: "var(--bg-1)", borderColor: "var(--line)", height: 52 }}
    >
      <div className="flex items-center gap-2 pr-2 select-none">
        <svg width="24" height="24" viewBox="0 0 22 22" aria-hidden>
          <circle cx="5" cy="11" r="3" fill="var(--accent)" />
          <circle cx="17" cy="5" r="2.4" fill="var(--sock-dataset)" />
          <circle cx="17" cy="17" r="2.4" fill="var(--sock-model)" />
          <path d="M7.5 10L14.8 5.8M7.5 12L14.8 16.2" stroke="var(--line-bright)" strokeWidth="1.6" />
        </svg>
        <span
          className="font-display font-semibold tracking-[0.08em] text-[15px]"
          style={{ color: "var(--text-0)" }}
        >
          AXON
        </span>
      </div>
      <div className="w-px h-6" style={{ background: "var(--line)" }} />
      <WorkflowMenu />

      <div className="ml-auto flex items-center gap-1.5">
        <button className="btn btn-ghost" onClick={() => setStore({ galleryOpen: true })}>
          <SquaresFourIcon size={15} /> Examples
        </button>
        <button className="btn btn-outline" onClick={save} title="Save workflow (Cmd+S)">
          <FloppyDiskIcon size={15} /> Save
        </button>
        <button
          className="btn btn-ghost !px-2"
          onClick={() => setStore({ settingsOpen: true })}
          title="Settings"
          aria-label="Settings"
        >
          <GearSixIcon size={17} />
        </button>
        <button
          className={copilotOpen ? "btn btn-outline" : "btn btn-outline"}
          style={
            copilotOpen
              ? { borderColor: "var(--accent)", color: "var(--accent)", background: "var(--accent-soft)" }
              : undefined
          }
          onClick={() => setStore({ copilotOpen: !copilotOpen })}
        >
          <SparkleIcon size={15} weight={copilotOpen ? "fill" : "regular"} /> Copilot
        </button>
        <button
          className={running ? "btn btn-danger-soft" : "btn btn-primary"}
          onClick={running ? cancel : run}
          title={running ? "Stop the run" : "Run workflow (Cmd+Enter)"}
        >
          {running ? (
            <>
              <StopIcon size={14} weight="fill" /> Stop
            </>
          ) : (
            <>
              <PlayIcon size={14} weight="fill" /> Run
            </>
          )}
        </button>
      </div>
    </header>
  );
}
