import ChartPreview from "./ChartPreview";

function TablePreview({ p }: { p: any }) {
  const cols: string[] = p.columns || [];
  const rows: Record<string, any>[] = p.rows || [];
  return (
    <div>
      <div className="text-xs mb-1 font-mono" style={{ color: "var(--text-1)" }}>
        {p.shape?.[0]} rows × {p.shape?.[1]} cols
        {p.target && (
          <span>
            {" · target: "}
            <span style={{ color: "var(--sock-dataset)" }}>{p.target}</span>
          </span>
        )}
      </div>
      <div className="overflow-auto max-h-64 rounded border" style={{ borderColor: "var(--line)" }}>
        <table className="text-xs font-mono w-full border-collapse">
          <thead>
            <tr>
              {cols.map((c) => (
                <th
                  key={c}
                  className="text-left px-2 py-1 sticky top-0 whitespace-nowrap"
                  style={{ background: "var(--bg-2)", color: "var(--text-0)" }}
                >
                  {c}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.slice(0, 30).map((r, i) => (
              <tr key={i} style={{ borderTop: "1px solid var(--line)" }}>
                {cols.map((c) => (
                  <td key={c} className="px-2 py-1 whitespace-nowrap" style={{ color: "var(--text-1)" }}>
                    {typeof r[c] === "number" ? +Number(r[c]).toFixed(4) : String(r[c] ?? "")}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function MetricsPreview({ p }: { p: any }) {
  const entries = Object.entries(p.values || {});
  return (
    <div className="grid grid-cols-2 gap-2">
      {entries.map(([k, v]) => (
        <div key={k} className="rounded-lg p-3" style={{ background: "var(--bg-2)" }}>
          <div className="text-[11px] uppercase tracking-wide" style={{ color: "var(--text-1)" }}>
            {k}
          </div>
          <div className="font-display text-lg" style={{ color: "var(--text-0)" }}>
            {typeof v === "number" ? +Number(v).toFixed(4) : String(v)}
          </div>
        </div>
      ))}
    </div>
  );
}

function DocsPreview({ p }: { p: any }) {
  return (
    <div className="space-y-2">
      <div className="text-xs font-mono" style={{ color: "var(--text-1)" }}>
        {p.count} documents
      </div>
      {(p.sample || []).slice(0, 5).map((d: any) => (
        <div key={d.id} className="rounded p-2 text-xs" style={{ background: "var(--bg-2)" }}>
          <span className="font-mono" style={{ color: "var(--sock-docs)" }}>
            [{d.id}]
          </span>{" "}
          <span style={{ color: "var(--text-1)" }}>{d.text}</span>
        </div>
      ))}
    </div>
  );
}

export default function OutputPreview({ preview }: { preview: Record<string, any> }) {
  const sockets = Object.entries(preview);
  if (!sockets.length)
    return (
      <div className="text-xs" style={{ color: "var(--text-1)" }}>
        This node produced no output to preview.
      </div>
    );
  return (
    <div className="space-y-4">
      {sockets.map(([socket, p]) => (
        <div key={socket}>
          {sockets.length > 1 && (
            <div className="text-[11px] uppercase tracking-wider mb-1 font-mono" style={{ color: "var(--text-1)" }}>
              {socket}
            </div>
          )}
          {p.type === "dataset" ? (
            <TablePreview p={p} />
          ) : p.type === "metrics" ? (
            <MetricsPreview p={p} />
          ) : p.type === "chart" ? (
            <ChartPreview chart={p} />
          ) : p.type === "text" ? (
            <pre
              className="text-xs whitespace-pre-wrap rounded p-3 max-h-64 overflow-auto"
              style={{ background: "var(--bg-2)", color: "var(--text-0)" }}
            >
              {p.text}
            </pre>
          ) : p.type === "docs" ? (
            <DocsPreview p={p} />
          ) : p.type === "image" && p.thumbnail ? (
            <img
              src={`data:image/png;base64,${p.thumbnail}`}
              alt={p.caption || "output image"}
              className="rounded max-w-full"
            />
          ) : p.type === "model" ? (
            <div className="text-xs font-mono rounded p-3" style={{ background: "var(--bg-2)", color: "var(--text-1)" }}>
              {p.model_class} · {p.framework} · {p.task}
            </div>
          ) : (
            <pre
              className="text-xs whitespace-pre-wrap rounded p-3 max-h-40 overflow-auto"
              style={{ background: "var(--bg-2)", color: "var(--text-1)" }}
            >
              {p.repr ?? JSON.stringify(p, null, 2)}
            </pre>
          )}
        </div>
      ))}
    </div>
  );
}
