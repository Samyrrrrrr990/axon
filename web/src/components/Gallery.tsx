import { KeyIcon, PackageIcon, XIcon } from "@phosphor-icons/react";
import { useStore } from "../store";

const DOMAIN_COLORS: Record<string, string> = {
  "classical-ml": "var(--sock-model)",
  "deep-learning": "var(--sock-model)",
  "fine-tuning": "var(--sock-image)",
  llm: "var(--sock-text)",
  agents: "var(--sock-text)",
};

const DOMAIN_LABELS: Record<string, string> = {
  "classical-ml": "Classical ML",
  "deep-learning": "Deep learning",
  "fine-tuning": "Fine-tuning",
  llm: "Retrieval",
  agents: "Agents",
};

export default function Gallery() {
  const open = useStore((s) => s.galleryOpen);
  const examples = useStore((s) => s.examples);
  const packs = useStore((s) => s.packs);
  const openExample = useStore((s) => s.openExample);
  const setStore = useStore((s) => s.set);

  if (!open) return null;

  return (
    <div className="overlay" onClick={() => setStore({ galleryOpen: false })}>
      <div
        className="modal-card w-[660px] max-w-[92vw] max-h-[82vh] overflow-y-auto p-6"
        onClick={(e) => e.stopPropagation()}
        role="dialog"
        aria-label="Example gallery"
      >
        <div className="flex items-start justify-between mb-1">
          <div className="font-display text-lg font-medium" style={{ color: "var(--text-0)" }}>
            Start from an example
          </div>
          <button
            className="btn btn-ghost !px-1.5 -mt-1 -mr-2"
            onClick={() => setStore({ galleryOpen: false })}
            aria-label="Close gallery"
          >
            <XIcon size={16} />
          </button>
        </div>
        <div className="text-[13px] mb-5" style={{ color: "var(--text-1)" }}>
          Open one, press Run, and watch it work. Then change anything you like.
        </div>
        <div className="grid grid-cols-2 gap-3 max-sm:grid-cols-1">
          {examples.map((ex) => {
            const missingPacks = ex.requires_packs.filter((p) => packs[p] && !packs[p].installed);
            const color = DOMAIN_COLORS[ex.domain] || "var(--sock-any)";
            return (
              <button
                key={ex.name}
                onClick={() => openExample(ex.name)}
                className="gallery-card"
                style={{ "--domain-color": color } as React.CSSProperties}
              >
                <div className="flex items-center gap-2 mb-2">
                  <span
                    className="text-[10px] font-mono px-1.5 py-0.5 rounded-md"
                    style={{ color, background: "var(--bg-3)" }}
                  >
                    {DOMAIN_LABELS[ex.domain] || ex.domain}
                  </span>
                  <span className="text-[10px] font-mono ml-auto" style={{ color: "var(--text-2)" }}>
                    {ex.node_count} nodes
                  </span>
                </div>
                <div className="font-display text-[15px] font-medium mb-1" style={{ color: "var(--text-0)" }}>
                  {ex.title}
                </div>
                <div className="text-xs leading-relaxed mb-2" style={{ color: "var(--text-1)" }}>
                  {ex.description}
                </div>
                {(missingPacks.length > 0 || ex.requires_keys.length > 0) && (
                  <div className="flex gap-3 text-[10.5px]" style={{ color: "var(--text-2)" }}>
                    {missingPacks.length > 0 && (
                      <span className="flex items-center gap-1" style={{ color: "var(--accent)" }}>
                        <PackageIcon size={12} /> needs {missingPacks.join(", ")} pack
                      </span>
                    )}
                    {ex.requires_keys.length > 0 && (
                      <span className="flex items-center gap-1">
                        <KeyIcon size={12} /> needs an API key
                      </span>
                    )}
                  </div>
                )}
              </button>
            );
          })}
        </div>
        {examples.length === 0 && (
          <div className="text-xs" style={{ color: "var(--text-1)" }}>
            No examples found. They live in the repository's examples/ folder.
          </div>
        )}
      </div>
    </div>
  );
}
