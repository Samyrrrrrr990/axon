import { Handle, Position, type NodeProps } from "@xyflow/react";
import { CheckIcon, LightningIcon, SkipForwardIcon, SpinnerGapIcon, XIcon } from "@phosphor-icons/react";
import { useStore } from "../store";
import { CATEGORY_COLORS, SOCKET_COLORS } from "../types";

function StatusBadge({ status, cached }: { status: string; cached: boolean }) {
  if (status === "running")
    return <SpinnerGapIcon size={13} className="animate-spin" style={{ color: "var(--accent)" }} />;
  if (status === "finished")
    return cached ? (
      <span title="Loaded from cache">
        <LightningIcon size={13} weight="fill" style={{ color: "var(--sock-dataset)" }} />
      </span>
    ) : (
      <CheckIcon size={13} weight="bold" style={{ color: "var(--ok)" }} />
    );
  if (status === "failed") return <XIcon size={13} weight="bold" style={{ color: "var(--err)" }} />;
  if (status === "skipped")
    return <SkipForwardIcon size={13} style={{ color: "var(--text-2)" }} />;
  return null;
}

export default function AxonNode({ id, data, selected }: NodeProps) {
  const spec = useStore((s) => s.specById[data.nodeType as string]);
  const status = useStore((s) => s.run.nodeStatus[id] || "idle");
  const cached = useStore((s) => s.run.cached[id]);
  const error = useStore((s) => s.run.errors[id]);

  if (!spec) {
    return (
      <div
        className="rounded-lg px-3 py-2 text-xs"
        style={{ background: "var(--bg-2)", color: "var(--err)", border: "1px solid var(--err)" }}
      >
        Unknown node: {String(data.nodeType)}
      </div>
    );
  }

  const inputs = Object.entries(spec.inputs);
  const outputs = Object.entries(spec.outputs);
  const rows = Math.max(inputs.length, outputs.length);
  const catColor = CATEGORY_COLORS[spec.category] || "var(--sock-any)";

  return (
    <div
      className={["axon-node", selected ? "selected" : "", status !== "idle" ? `status-${status}` : ""].join(" ")}
      title={error ? `${error.error}${error.hint ? `\n\n${error.hint}` : ""}` : spec.description}
    >
      <div
        className="flex items-center gap-2 px-3 py-2"
        style={{ borderBottom: rows ? "1px solid var(--line)" : undefined }}
      >
        <span className="inline-block w-2 h-2 rounded-full shrink-0" style={{ background: catColor }} />
        <span className="font-display text-[13px] font-medium" style={{ color: "var(--text-0)" }}>
          {spec.name}
        </span>
        <span className="ml-auto flex items-center">
          <StatusBadge status={status} cached={!!cached} />
        </span>
      </div>
      {rows > 0 && (
        <div className="relative py-1.5" style={{ minHeight: rows * 23 }}>
          {inputs.map(([name, type], i) => (
            <div key={name} className="absolute flex items-center" style={{ top: 6 + i * 23, left: 0 }}>
              <Handle
                type="target"
                id={name}
                position={Position.Left}
                style={{
                  background: SOCKET_COLORS[type] || "var(--sock-any)",
                  position: "relative",
                  transform: "none",
                  left: -6,
                }}
                title={`${name}: ${type}`}
              />
              <span className="text-[11px] ml-1" style={{ color: "var(--text-1)" }}>
                {name}
              </span>
            </div>
          ))}
          {outputs.map(([name, type], i) => (
            <div
              key={name}
              className="absolute flex items-center flex-row-reverse"
              style={{ top: 6 + i * 23, right: 0 }}
            >
              <Handle
                type="source"
                id={name}
                position={Position.Right}
                style={{
                  background: SOCKET_COLORS[type] || "var(--sock-any)",
                  position: "relative",
                  transform: "none",
                  right: -6,
                }}
                title={`${name}: ${type}`}
              />
              <span className="text-[11px] mr-1" style={{ color: "var(--text-1)" }}>
                {name}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
