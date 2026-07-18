import { useEffect, useState } from "react";
import { api } from "../api";
import { useStore } from "../store";

const KEY_FIELDS = [
  { id: "openrouter", label: "OpenRouter", help: "Free — create a key at openrouter.ai/keys. Powers the copilot by default." },
  { id: "anthropic", label: "Anthropic", help: "Optional — for Claude models." },
  { id: "openai", label: "OpenAI", help: "Optional — for GPT models." },
];

export default function Settings() {
  const open = useStore((s) => s.settingsOpen);
  const setStore = useStore((s) => s.set);
  const packs = useStore((s) => s.packs);
  const installLog = useStore((s) => s.packInstallLog);
  const storeSettings = useStore((s) => s.settings);
  const [form, setForm] = useState<Record<string, any>>({});
  const [installing, setInstalling] = useState<Record<string, boolean>>({});

  useEffect(() => {
    if (open) setForm(JSON.parse(JSON.stringify(storeSettings || {})));
  }, [open, storeSettings]);

  if (!open) return null;

  const save = async () => {
    const saved = await api.saveSettings(form);
    setStore({ settings: saved, settingsOpen: false, toast: "Settings saved" });
  };

  const install = async (name: string) => {
    setInstalling({ ...installing, [name]: true });
    await api.installPack(name);
  };

  return (
    <div
      className="fixed inset-0 z-40 flex items-center justify-center"
      style={{ background: "rgb(0 0 0 / 0.6)" }}
      onClick={() => setStore({ settingsOpen: false })}
    >
      <div
        className="w-[560px] max-h-[80vh] overflow-y-auto rounded-2xl p-5"
        style={{ background: "var(--bg-1)", border: "1px solid var(--line-bright)" }}
        onClick={(e) => e.stopPropagation()}
      >
        <div className="font-display text-lg mb-4" style={{ color: "var(--text-0)" }}>
          Settings
        </div>

        <div className="text-[11px] uppercase tracking-wider mb-2" style={{ color: "var(--text-1)" }}>
          API keys
        </div>
        <div className="space-y-3 mb-6">
          {KEY_FIELDS.map((f) => (
            <div key={f.id}>
              <div className="flex items-baseline justify-between mb-1">
                <span className="text-sm" style={{ color: "var(--text-0)" }}>
                  {f.label}
                </span>
                <span className="text-[11px]" style={{ color: "var(--text-1)" }}>
                  {f.help}
                </span>
              </div>
              <input
                type="password"
                value={form.keys?.[f.id] ?? ""}
                onChange={(e) => setForm({ ...form, keys: { ...form.keys, [f.id]: e.target.value } })}
                placeholder="Paste key…"
                className="w-full rounded-lg px-3 py-1.5 text-sm outline-none font-mono"
                style={{ background: "var(--bg-2)", color: "var(--text-0)", border: "1px solid var(--line)" }}
              />
            </div>
          ))}
        </div>

        <div className="text-[11px] uppercase tracking-wider mb-2" style={{ color: "var(--text-1)" }}>
          Copilot model
        </div>
        <div className="flex gap-2 mb-6">
          <select
            value={form.copilot?.provider ?? "openrouter"}
            onChange={(e) => setForm({ ...form, copilot: { ...form.copilot, provider: e.target.value } })}
            className="rounded-lg px-2 py-1.5 text-sm outline-none"
            style={{ background: "var(--bg-2)", color: "var(--text-0)", border: "1px solid var(--line)" }}
          >
            {["openrouter", "anthropic", "openai", "ollama"].map((p) => (
              <option key={p} value={p}>
                {p}
              </option>
            ))}
          </select>
          <input
            value={form.copilot?.model ?? ""}
            onChange={(e) => setForm({ ...form, copilot: { ...form.copilot, model: e.target.value } })}
            placeholder="model id"
            className="flex-1 rounded-lg px-3 py-1.5 text-sm outline-none font-mono"
            style={{ background: "var(--bg-2)", color: "var(--text-0)", border: "1px solid var(--line)" }}
          />
        </div>

        <div className="text-[11px] uppercase tracking-wider mb-2" style={{ color: "var(--text-1)" }}>
          Capability packs
        </div>
        <div className="space-y-2 mb-6">
          {Object.entries(packs).map(([name, info]) => (
            <div key={name} className="rounded-lg p-3" style={{ background: "var(--bg-2)", border: "1px solid var(--line)" }}>
              <div className="flex items-center gap-2">
                <span className="text-sm" style={{ color: "var(--text-0)" }}>
                  {info.label}
                </span>
                <span className="text-[11px] font-mono" style={{ color: "var(--text-1)" }}>
                  {info.size_hint}
                </span>
                {info.installed ? (
                  <span className="ml-auto text-xs" style={{ color: "var(--ok)" }}>
                    installed
                  </span>
                ) : (
                  <button
                    onClick={() => install(name)}
                    disabled={installing[name]}
                    className="ml-auto px-3 py-1 rounded-lg text-xs font-medium disabled:opacity-50"
                    style={{ background: "var(--accent)", color: "#0b0e14" }}
                  >
                    {installing[name] ? "Installing…" : "Install"}
                  </button>
                )}
              </div>
              {installing[name] && installLog[name] && (
                <pre
                  className="mt-2 text-[10px] font-mono max-h-24 overflow-y-auto whitespace-pre-wrap"
                  style={{ color: "var(--text-1)" }}
                >
                  {installLog[name].slice(-8).join("\n")}
                </pre>
              )}
            </div>
          ))}
        </div>

        <div className="flex justify-end gap-2">
          <button
            onClick={() => setStore({ settingsOpen: false })}
            className="px-4 py-1.5 rounded-lg text-sm"
            style={{ color: "var(--text-1)" }}
          >
            Cancel
          </button>
          <button
            onClick={save}
            className="px-4 py-1.5 rounded-lg text-sm font-medium"
            style={{ background: "var(--accent)", color: "#0b0e14" }}
          >
            Save settings
          </button>
        </div>
      </div>
    </div>
  );
}
