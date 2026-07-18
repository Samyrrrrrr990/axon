import { useStore } from "../store";

const DOMAIN_COLORS: Record<string, string> = {
  "classical-ml": "var(--sock-model)",
  "deep-learning": "var(--sock-model)",
  "fine-tuning": "var(--sock-image)",
  llm: "var(--sock-text)",
  agents: "var(--sock-text)",
};

export default function Gallery() {
  const open = useStore((s) => s.galleryOpen);
  const examples = useStore((s) => s.examples);
  const packs = useStore((s) => s.packs);
  const openExample = useStore((s) => s.openExample);
  const setStore = useStore((s) => s.set);

  if (!open) return null;

  return (
    <div
      className="fixed inset-0 z-40 flex items-center justify-center"
      style={{ background: "rgb(0 0 0 / 0.6)" }}
      onClick={() => setStore({ galleryOpen: false })}
    >
      <div
        className="w-[640px] max-h-[80vh] overflow-y-auto rounded-2xl p-5"
        style={{ background: "var(--bg-1)", border: "1px solid var(--line-bright)" }}
        onClick={(e) => e.stopPropagation()}
      >
        <div className="font-display text-lg" style={{ color: "var(--text-0)" }}>
          Start from an example
        </div>
        <div className="text-xs mb-4" style={{ color: "var(--text-1)" }}>
          Open one, press Run, and watch it work. Then change anything.
        </div>
        <div className="grid grid-cols-2 gap-3">
          {examples.map((ex) => {
            const missingPacks = ex.requires_packs.filter((p) => packs[p] && !packs[p].installed);
            return (
              <button
                key={ex.name}
                onClick={() => openExample(ex.name)}
                className="text-left rounded-xl p-4 hover:border-[var(--line-bright)] transition-colors"
                style={{ background: "var(--bg-2)", border: "1px solid var(--line)" }}
              >
                <div className="flex items-center gap-2 mb-1">
                  <span
                    className="w-2 h-2 rounded-full"
                    style={{ background: DOMAIN_COLORS[ex.domain] || "var(--sock-any)" }}
                  />
                  <span className="font-display text-sm font-medium" style={{ color: "var(--text-0)" }}>
                    {ex.title}
                  </span>
                </div>
                <div className="text-xs mb-2" style={{ color: "var(--text-1)" }}>
                  {ex.description}
                </div>
                <div className="flex gap-2 text-[10px] font-mono" style={{ color: "var(--text-1)" }}>
                  <span>{ex.node_count} nodes</span>
                  {missingPacks.length > 0 && (
                    <span style={{ color: "var(--accent)" }}>needs: {missingPacks.join(", ")}</span>
                  )}
                  {ex.requires_keys.length > 0 && (
                    <span style={{ color: "var(--sock-text)" }}>needs API key</span>
                  )}
                </div>
              </button>
            );
          })}
        </div>
        {examples.length === 0 && (
          <div className="text-xs" style={{ color: "var(--text-1)" }}>
            No examples found — they live in the repo's examples/ folder.
          </div>
        )}
      </div>
    </div>
  );
}
