import { useEffect, useRef } from "react";
import { useStore } from "../store";

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

  const statusColor =
    status === "finished" ? "var(--ok)" : status === "error" ? "var(--err)" : status === "running" ? "var(--accent)" : "var(--text-1)";

  return (
    <div
      className="h-44 shrink-0 border-t flex flex-col"
      style={{ background: "var(--bg-1)", borderColor: "var(--line)" }}
    >
      <div className="flex items-center px-3 py-1.5 border-b" style={{ borderColor: "var(--line)" }}>
        <span className="text-[11px] uppercase tracking-wider font-medium" style={{ color: "var(--text-1)" }}>
          Run log
        </span>
        <span className="ml-2 text-[11px] font-mono" style={{ color: statusColor }}>
          {status}
        </span>
        <button
          onClick={() => setStore({ logsOpen: false })}
          className="ml-auto text-xs px-2"
          style={{ color: "var(--text-1)" }}
          aria-label="Close log"
        >
          ✕
        </button>
      </div>
      <div className="flex-1 overflow-y-auto px-3 py-2 font-mono text-[11px] space-y-0.5">
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
            {e.hint && <span style={{ color: "var(--text-1)" }}> — {e.hint}</span>}
          </div>
        ))}
        {logs.length === 0 && Object.keys(errors).length === 0 && (
          <span style={{ color: "var(--text-1)" }}>Waiting for output…</span>
        )}
        <div ref={endRef} />
      </div>
    </div>
  );
}
