import { useMemo, useState } from "react";
import {
  BrainIcon,
  ChatsCircleIcon,
  DatabaseIcon,
  DownloadSimpleIcon,
  MagnifyingGlassIcon,
  SlidersIcon,
  TreeStructureIcon,
  WrenchIcon,
} from "@phosphor-icons/react";
import { useStore } from "../store";
import { CATEGORY_COLORS } from "../types";

const CATEGORY_ORDER = ["Data", "Classical ML", "Deep Learning", "Fine-tuning", "LLM & Agents", "Utility"];

const CATEGORY_ICONS: Record<string, React.ReactNode> = {
  Data: <DatabaseIcon size={13} />,
  "Classical ML": <TreeStructureIcon size={13} />,
  "Deep Learning": <BrainIcon size={13} />,
  "Fine-tuning": <SlidersIcon size={13} />,
  "LLM & Agents": <ChatsCircleIcon size={13} />,
  Utility: <WrenchIcon size={13} />,
};

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
      className="w-[248px] shrink-0 flex flex-col border-r overflow-hidden"
      style={{ background: "var(--bg-1)", borderColor: "var(--line)" }}
    >
      <div className="p-3 border-b" style={{ borderColor: "var(--line)" }}>
        <div className="relative">
          <MagnifyingGlassIcon
            size={14}
            className="absolute left-2.5 top-1/2 -translate-y-1/2 pointer-events-none"
            style={{ color: "var(--text-2)" }}
          />
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search nodes"
            className="field !pl-8"
            aria-label="Search nodes"
          />
        </div>
      </div>
      <div className="flex-1 overflow-y-auto p-2.5 space-y-5">
        {categories.map((cat) => {
          const packName = PACK_FOR_CATEGORY[cat];
          const needsInstall = packName && packs[packName] && !packs[packName].installed;
          const color = CATEGORY_COLORS[cat] || "var(--sock-any)";
          return (
            <div key={cat}>
              <div className="flex items-center gap-1.5 px-1 mb-2">
                <span style={{ color }}>{CATEGORY_ICONS[cat]}</span>
                <span className="section-label">{cat}</span>
                {needsInstall && (
                  <button
                    onClick={() => setStore({ settingsOpen: true })}
                    className="ml-auto flex items-center gap-1 text-[10px] font-mono px-1.5 py-0.5 rounded-md transition-colors"
                    style={{ background: "var(--accent-soft)", color: "var(--accent)" }}
                    title={`Needs the ${packs[packName].label} pack. Click to install in Settings.`}
                  >
                    <DownloadSimpleIcon size={11} /> install
                  </button>
                )}
              </div>
              <div className="space-y-1">
                {grouped[cat].map((n) => (
                  <div
                    key={n.id}
                    draggable
                    onDragStart={(e) => e.dataTransfer.setData("application/axon-node", n.id)}
                    className="palette-node"
                    style={{ "--cat-color": color } as React.CSSProperties}
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
            No nodes match "{query}". Try a shorter search.
          </div>
        )}
      </div>
      <div
        className="px-3 py-2 border-t text-[11px]"
        style={{ borderColor: "var(--line)", color: "var(--text-2)" }}
      >
        Drag a node onto the canvas
      </div>
    </aside>
  );
}
