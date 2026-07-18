import { useEffect, useState } from "react";
import { CheckCircleIcon, XIcon } from "@phosphor-icons/react";
import { api } from "../api";
import { useStore } from "../store";

const KEY_FIELDS = [
  {
    id: "openrouter",
    label: "OpenRouter",
    help: "Free. Create a key at openrouter.ai/keys. Powers the copilot by default.",
  },
  { id: "anthropic", label: "Anthropic", help: "Optional, for Claude models." },
  { id: "openai", label: "OpenAI", help: "Optional, for GPT models." },
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
    <div className="overlay" onClick={() => setStore({ settingsOpen: false })}>
      <div
        className="modal-card w-[580px] max-w-[92vw] max-h-[84vh] overflow-y-auto p-6"
        onClick={(e) => e.stopPropagation()}
        role="dialog"
        aria-label="Settings"
      >
        <div className="flex items-start justify-between mb-5">
          <div className="font-display text-lg font-medium" style={{ color: "var(--text-0)" }}>
            Settings
          </div>
          <button
            className="btn btn-ghost !px-1.5 -mt-1 -mr-2"
            onClick={() => setStore({ settingsOpen: false })}
            aria-label="Close settings"
          >
            <XIcon size={16} />
          </button>
        </div>

        <div className="section-label mb-3">API keys</div>
        <div className="space-y-4 mb-7">
          {KEY_FIELDS.map((f) => (
            <div key={f.id}>
              <div className="flex items-baseline justify-between mb-1.5 gap-4">
                <span className="text-sm font-medium" style={{ color: "var(--text-0)" }}>
                  {f.label}
                </span>
                <span className="text-[11px] text-right" style={{ color: "var(--text-1)" }}>
                  {f.help}
                </span>
              </div>
              <input
                type="password"
                value={form.keys?.[f.id] ?? ""}
                onChange={(e) => setForm({ ...form, keys: { ...form.keys, [f.id]: e.target.value } })}
                placeholder="Paste key"
                className="field font-mono"
                autoComplete="off"
              />
            </div>
          ))}
        </div>

        <div className="section-label mb-3">Copilot model</div>
        <div className="flex gap-2 mb-7">
          <select
            value={form.copilot?.provider ?? "openrouter"}
            onChange={(e) => setForm({ ...form, copilot: { ...form.copilot, provider: e.target.value } })}
            className="field !w-40"
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
            className="field font-mono flex-1"
          />
        </div>

        <div className="section-label mb-3">Capability packs</div>
        <div className="space-y-2 mb-7">
          {Object.entries(packs).map(([name, info]) => (
            <div
              key={name}
              className="rounded-xl p-3.5"
              style={{ background: "var(--bg-2)", border: "1px solid var(--line)" }}
            >
              <div className="flex items-center gap-2.5">
                <span className="text-sm" style={{ color: "var(--text-0)" }}>
                  {info.label}
                </span>
                <span className="text-[11px] font-mono" style={{ color: "var(--text-2)" }}>
                  {info.size_hint}
                </span>
                {info.installed ? (
                  <span
                    className="ml-auto flex items-center gap-1 text-xs"
                    style={{ color: "var(--ok)" }}
                  >
                    <CheckCircleIcon size={14} weight="fill" /> installed
                  </span>
                ) : (
                  <button
                    className="btn btn-primary ml-auto !py-1.5 !text-xs"
                    onClick={() => install(name)}
                    disabled={installing[name]}
                  >
                    {installing[name] ? "Installing" : "Install"}
                  </button>
                )}
              </div>
              {installing[name] && installLog[name] && (
                <pre
                  className="mt-2.5 text-[10px] font-mono max-h-24 overflow-y-auto whitespace-pre-wrap rounded-lg p-2"
                  style={{ color: "var(--text-1)", background: "var(--bg-0)" }}
                >
                  {installLog[name].slice(-8).join("\n")}
                </pre>
              )}
            </div>
          ))}
        </div>

        <div className="flex justify-end gap-2">
          <button className="btn btn-ghost" onClick={() => setStore({ settingsOpen: false })}>
            Cancel
          </button>
          <button className="btn btn-primary" onClick={save}>
            Save settings
          </button>
        </div>
      </div>
    </div>
  );
}
