import { useMemo, useState } from "react";
import { useStore } from "../store";
import { CATEGORY_COLORS } from "../types";

const CATEGORY_ORDER = ["Data", "Classical ML", "Deep Learning", "Fine-tuning", "LLM & Agents", "Utility"];

const PACK_FOR_CATEGORY: Record<string, string> = {
  "Deep Learning": "deep",
  "Fine-tuning": "finetune",
};

export default function Palette() {
  const catalog = useStore((s) => s.catalog);
  const packs = useStore((s) => s.packs);
  const setStore = useStore((s) => s.set);
  const [query, setQuery] = useState("");

  const grouped = useMemo(() => {
    const q = query.toLowerCase();
    const filtered = catalog.filter(
      (n) => !q || n.name.toLowerCase().includes(q) || n.description.toLowerCase().includes(q),
    );
    const byCat: Record<string, typeof catalog> = {};
    for (const n of filtered) (byCat[n.category] ||= []).push(n);
    return byCat;
  }, [catalog, query]);

  const categories = [
    ...CATEGORY_ORDER.filter((c) => grouped[c]),
    ...Object.keys(grouped).filter((c) => !CATEGORY_ORDER.includes(c)),
  ];

  return (
    <aside
      className="w-[250px] shrink-0 flex flex-col border-r overflow-hidden"
      style={{ background: "var(--bg-1)", borderColor: "var(--line)" }}
    >
      <div className="p-3 border-b" style={{ borderColor: "var(--line)" }}>
        <input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search nodes…"
          className="w-full rounded-lg px-3 py-1.5 text-sm outline-none"
          style={{ background: "var(--bg-2)", color: "var(--text-0)", border: "1px solid var(--line)" }}
        />
      </div>
      <div className="flex-1 overflow-y-auto p-2 space-y-4">
        {categories.map((cat) => {
          const packName = PACK_FOR_CATEGORY[cat];
          const needsInstall = packName && packs[packName] && !packs[packName].installed;
          return (
            <div key={cat}>
              <div className="flex items-center gap-2 px-1 mb-1.5">
                <span className="w-2 h-2 rounded-full" style={{ background: CATEGORY_COLORS[cat] || "var(--sock-any)" }} />
                <span className="text-[11px] uppercase tracking-wider font-medium" style={{ color: "var(--text-1)" }}>
                  {cat}
                </span>
                {needsInstall && (
                  <button
                    onClick={() => setStore({ settingsOpen: true })}
                    className="ml-auto text-[10px] px-1.5 py-0.5 rounded font-mono"
                    style={{ background: "var(--bg-3)", color: "var(--accent)" }}
                    title={`Needs the ${packs[packName].label} pack — click to install in Settings`}
                  >
                    install
                  </button>
                )}
              </div>
              <div className="space-y-1">
                {grouped[cat].map((n) => (
                  <div
                    key={n.id}
                    draggable
                    onDragStart={(e) => e.dataTransfer.setData("application/axon-node", n.id)}
                    className="px-2.5 py-1.5 rounded-lg cursor-grab text-[13px] select-none hover:translate-x-0.5 transition-transform"
                    style={{ background: "var(--bg-2)", color: "var(--text-0)", border: "1px solid var(--line)" }}
                    title={n.description}
                  >
                    {n.name}
                  </div>
                ))}
              </div>
            </div>
          );
        })}
        {categories.length === 0 && (
          <div className="text-xs p-2" style={{ color: "var(--text-1)" }}>
            No nodes match "{query}".
          </div>
        )}
      </div>
    </aside>
  );
}
