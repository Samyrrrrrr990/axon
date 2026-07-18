import { useEffect, useRef } from "react";
import { XIcon } from "@phosphor-icons/react";
import { useStore } from "../store";

const STATUS_COLOR: Record<string, string> = {
  finished: "var(--ok)",
  error: "var(--err)",
  running: "var(--accent)",
  cancelled: "var(--text-1)",
};

export default function RunLogs() {
  const open = useStore((s) => s.logsOpen);
  const setStore = useStore((s) => s.set);
  const logs = useStore((s) => s.run.logs);
  const status = useStore((s) => s.run.status);
  const errors = useStore((s) => s.run.errors);
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [logs.length]);

  if (!open) return null;

  return (
    <div
      className="h-44 shrink-0 border-t flex flex-col msg-in"
      style={{ background: "var(--bg-1)", borderColor: "var(--line)" }}
    >
      <div className="flex items-center gap-2.5 px-3.5 py-2 border-b" style={{ borderColor: "var(--line)" }}>
        <span className="section-label">Run log</span>
        <span className="flex items-center gap-1.5 text-[11px] font-mono" style={{ color: STATUS_COLOR[status] || "var(--text-1)" }}>
          {status === "running" && (
            <span className="w-1.5 h-1.5 rounded-full animate-pulse" style={{ background: "var(--accent)" }} />
          )}
          {status}
        </span>
        <button
          className="btn btn-ghost !px-1 ml-auto"
          onClick={() => setStore({ logsOpen: false })}
          aria-label="Close run log"
        >
          <XIcon size={14} />
        </button>
      </div>
      <div className="flex-1 overflow-y-auto px-3.5 py-2 font-mono text-[11px] leading-relaxed space-y-0.5">
        {logs.map((l, i) => (
          <div key={i}>
            <span style={{ color: "var(--sock-dataset)" }}>{l.nodeId ?? "run"}</span>{" "}
            <span style={{ color: "var(--text-1)" }}>{l.message}</span>
          </div>
        ))}
        {Object.entries(errors).map(([nid, e]) => (
          <div key={nid}>
            <span style={{ color: "var(--err)" }}>{nid}</span>{" "}
            <span style={{ color: "var(--err)" }}>{e.error}</span>
            {e.hint && <span style={{ color: "var(--text-1)" }}> Hint: {e.hint}</span>}
          </div>
        ))}
        {logs.length === 0 && Object.keys(errors).length === 0 && (
          <span style={{ color: "var(--text-2)" }}>Waiting for output</span>
        )}
        <div ref={endRef} />
      </div>
    </div>
  );
}
