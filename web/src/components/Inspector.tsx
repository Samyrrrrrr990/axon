import { useState } from "react";
import { useStore } from "../store";
import type { ParamSchema } from "../types";
import LiveMetrics from "./LiveMetrics";
import OutputPreview from "./previews/OutputPreview";

function ParamField({
  name,
  schema,
  value,
  onChange,
}: {
  name: string;
  schema: ParamSchema;
  value: unknown;
  onChange: (v: unknown) => void;
}) {
  const current = value ?? schema.default;
  const inputStyle = {
    background: "var(--bg-2)",
    color: "var(--text-0)",
    border: "1px solid var(--line)",
  } as const;

  return (
    <label className="block">
      <div className="flex items-baseline justify-between mb-1">
        <span className="text-xs font-medium" style={{ color: "var(--text-0)" }}>
          {name}
          {schema.required && <span style={{ color: "var(--accent)" }}> *</span>}
        </span>
        <span className="text-[10px] font-mono" style={{ color: "var(--text-1)" }}>
          {schema.kind}
        </span>
      </div>
      {schema.kind === "choice" ? (
        <select
          value={String(current ?? "")}
          onChange={(e) => onChange(e.target.value)}
          className="w-full rounded-lg px-2 py-1.5 text-sm outline-none"
          style={inputStyle}
        >
          {(schema.options || []).map((o) => (
            <option key={o} value={o}>
              {o}
            </option>
          ))}
        </select>
      ) : schema.kind === "bool" ? (
        <button
          onClick={() => onChange(!current)}
          className="w-10 h-5 rounded-full relative transition-colors"
          style={{ background: current ? "var(--accent)" : "var(--bg-3)" }}
          role="switch"
          aria-checked={!!current}
        >
          <span
            className="absolute top-0.5 w-4 h-4 rounded-full transition-all"
            style={{ background: "var(--bg-0)", left: current ? 22 : 2 }}
          />
        </button>
      ) : schema.kind === "text" || schema.kind === "json" ? (
        <textarea
          value={
            schema.kind === "json" && typeof current !== "string"
              ? JSON.stringify(current ?? {}, null, 2)
              : String(current ?? "")
          }
          onChange={(e) => {
            if (schema.kind === "json") {
              try {
                onChange(JSON.parse(e.target.value));
              } catch {
                onChange(e.target.value);
              }
            } else onChange(e.target.value);
          }}
          rows={Math.min(10, Math.max(3, String(current ?? "").split("\n").length))}
          spellCheck={false}
          className="w-full rounded-lg px-2 py-1.5 text-xs outline-none font-mono resize-y"
          style={inputStyle}
        />
      ) : schema.kind === "int" || schema.kind === "float" ? (
        <input
          type="number"
          value={current === null || current === undefined ? "" : Number(current)}
          min={schema.min ?? undefined}
          max={schema.max ?? undefined}
          step={schema.kind === "float" ? "any" : 1}
          onChange={(e) =>
            onChange(schema.kind === "int" ? parseInt(e.target.value || "0", 10) : parseFloat(e.target.value || "0"))
          }
          className="w-full rounded-lg px-2 py-1.5 text-sm outline-none font-mono"
          style={inputStyle}
        />
      ) : (
        <input
          type={schema.kind === "secret" ? "password" : "text"}
          value={String(current ?? "")}
          placeholder={schema.kind === "filepath" ? "path/to/file" : undefined}
          onChange={(e) => onChange(e.target.value)}
          className="w-full rounded-lg px-2 py-1.5 text-sm outline-none"
          style={inputStyle}
        />
      )}
      {schema.help && (
        <div className="text-[11px] mt-1" style={{ color: "var(--text-1)" }}>
          {schema.help}
        </div>
      )}
    </label>
  );
}

export default function Inspector() {
  const selection = useStore((s) => s.selection);
  const node = useStore((s) => s.nodes.find((n) => n.id === s.selection));
  const spec = useStore((s) => (node ? s.specById[node.data.nodeType as string] : undefined));
  const updateParams = useStore((s) => s.updateParams);
  const preview = useStore((s) => (selection ? s.run.previews[selection] : undefined));
  const error = useStore((s) => (selection ? s.run.errors[selection] : undefined));
  const metrics = useStore((s) => (selection ? s.run.metrics[selection] : undefined));
  const [tab, setTab] = useState<"params" | "output">("params");

  if (!node || !spec) {
    return (
      <aside
        className="w-[300px] shrink-0 border-l p-4 text-sm"
        style={{ background: "var(--bg-1)", borderColor: "var(--line)", color: "var(--text-1)" }}
      >
        Select a node to edit its settings and see its output.
      </aside>
    );
  }

  const params = (node.data.params as Record<string, unknown>) || {};
  const hasOutput = !!preview || !!error || !!metrics?.length;

  return (
    <aside
      className="w-[300px] shrink-0 border-l flex flex-col overflow-hidden"
      style={{ background: "var(--bg-1)", borderColor: "var(--line)" }}
    >
      <div className="p-3 border-b" style={{ borderColor: "var(--line)" }}>
        <div className="font-display text-sm font-medium" style={{ color: "var(--text-0)" }}>
          {spec.name}
        </div>
        <div className="text-xs mt-0.5" style={{ color: "var(--text-1)" }}>
          {spec.description}
        </div>
      </div>
      <div className="flex border-b" style={{ borderColor: "var(--line)" }}>
        {(["params", "output"] as const).map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className="flex-1 py-2 text-xs uppercase tracking-wider font-medium"
            style={{
              color: tab === t ? "var(--accent)" : "var(--text-1)",
              borderBottom: tab === t ? "2px solid var(--accent)" : "2px solid transparent",
            }}
          >
            {t === "params" ? "Settings" : "Output"}
            {t === "output" && hasOutput && (
              <span className="ml-1" style={{ color: error ? "var(--err)" : "var(--ok)" }}>
                •
              </span>
            )}
          </button>
        ))}
      </div>
      <div className="flex-1 overflow-y-auto p-3 space-y-4">
        {tab === "params" ? (
          Object.keys(spec.params).length ? (
            Object.entries(spec.params).map(([name, schema]) => (
              <ParamField
                key={name}
                name={name}
                schema={schema}
                value={params[name]}
                onChange={(v) => updateParams(node.id, { [name]: v })}
              />
            ))
          ) : (
            <div className="text-xs" style={{ color: "var(--text-1)" }}>
              This node has no settings. Wire it up and run.
            </div>
          )
        ) : (
          <div className="space-y-4">
            {error && (
              <div
                className="rounded-lg p-3 text-xs"
                style={{ background: "rgb(248 113 113 / 0.08)", border: "1px solid var(--err)" }}
              >
                <div style={{ color: "var(--err)" }}>{error.error}</div>
                {error.hint && (
                  <div className="mt-2" style={{ color: "var(--text-1)" }}>
                    💡 {error.hint}
                  </div>
                )}
              </div>
            )}
            {metrics && metrics.length > 0 && <LiveMetrics points={metrics} />}
            {preview ? (
              <OutputPreview preview={preview} />
            ) : (
              !error && (
                <div className="text-xs" style={{ color: "var(--text-1)" }}>
                  Run the workflow to see this node's output.
                </div>
              )
            )}
          </div>
        )}
      </div>
    </aside>
  );
}
