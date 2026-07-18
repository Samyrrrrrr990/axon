import { useEffect, useRef, useState } from "react";
import { useStore } from "../store";

const SUGGESTIONS = [
  "Build a workflow that trains a model on the iris dataset",
  "Add evaluation and a confusion matrix to my graph",
  "Explain what this workflow does",
];

export default function Copilot() {
  const open = useStore((s) => s.copilotOpen);
  const messages = useStore((s) => s.copilotMessages);
  const busy = useStore((s) => s.copilotBusy);
  const send = useStore((s) => s.sendCopilot);
  const settings = useStore((s) => s.settings);
  const setStore = useStore((s) => s.set);
  const [draft, setDraft] = useState("");
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages.length, busy]);

  if (!open) return null;

  const provider = settings?.copilot?.provider ?? "openrouter";
  const model = settings?.copilot?.model ?? "";
  const hasKey = provider === "ollama" || !!settings?.keys?.[provider];

  const submit = () => {
    const text = draft.trim();
    if (!text || busy) return;
    setDraft("");
    send(text);
  };

  return (
    <aside
      className="w-[330px] shrink-0 border-l flex flex-col overflow-hidden"
      style={{ background: "var(--bg-1)", borderColor: "var(--line)" }}
    >
      <div className="p-3 border-b flex items-center gap-2" style={{ borderColor: "var(--line)" }}>
        <span className="font-display text-sm font-medium" style={{ color: "var(--text-0)" }}>
          Copilot
        </span>
        <span className="text-[10px] font-mono truncate" style={{ color: "var(--text-1)" }} title={model}>
          {provider}
          {model ? ` · ${model.split("/").pop()}` : ""}
        </span>
      </div>

      {!hasKey && (
        <div className="m-3 rounded-lg p-3 text-xs" style={{ background: "var(--bg-2)", border: "1px solid var(--accent)" }}>
          <div style={{ color: "var(--text-0)" }}>The copilot needs a (free) API key.</div>
          <div className="mt-1" style={{ color: "var(--text-1)" }}>
            Create a free key at openrouter.ai/keys, then paste it in Settings.
          </div>
          <button
            onClick={() => setStore({ settingsOpen: true })}
            className="mt-2 px-3 py-1 rounded-lg text-xs font-medium"
            style={{ background: "var(--accent)", color: "#0b0e14" }}
          >
            Open Settings
          </button>
        </div>
      )}

      <div className="flex-1 overflow-y-auto p-3 space-y-3">
        {messages.length === 0 && (
          <div className="space-y-2">
            <div className="text-xs" style={{ color: "var(--text-1)" }}>
              Describe what you want to build and the copilot assembles the nodes. Try:
            </div>
            {SUGGESTIONS.map((s) => (
              <button
                key={s}
                onClick={() => send(s)}
                disabled={busy || !hasKey}
                className="block w-full text-left text-xs rounded-lg px-3 py-2 hover:border-[var(--line-bright)]"
                style={{ background: "var(--bg-2)", color: "var(--text-0)", border: "1px solid var(--line)" }}
              >
                {s}
              </button>
            ))}
          </div>
        )}
        {messages.map((m, i) => (
          <div
            key={i}
            className="rounded-xl px-3 py-2 text-[13px] whitespace-pre-wrap max-w-[95%]"
            style={
              m.role === "user"
                ? { background: "var(--bg-3)", color: "var(--text-0)", marginLeft: "auto" }
                : { background: "var(--bg-2)", color: "var(--text-0)", border: "1px solid var(--line)" }
            }
          >
            {m.content}
          </div>
        ))}
        {busy && (
          <div className="text-xs font-mono" style={{ color: "var(--accent)" }}>
            thinking…
          </div>
        )}
        <div ref={endRef} />
      </div>

      <div className="p-3 border-t" style={{ borderColor: "var(--line)" }}>
        <textarea
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              submit();
            }
          }}
          placeholder={hasKey ? "e.g. train a classifier on my CSV…" : "Add an API key in Settings first"}
          disabled={!hasKey}
          rows={2}
          className="w-full rounded-lg px-3 py-2 text-sm outline-none resize-none"
          style={{ background: "var(--bg-2)", color: "var(--text-0)", border: "1px solid var(--line)" }}
        />
        <button
          onClick={submit}
          disabled={busy || !draft.trim() || !hasKey}
          className="mt-2 w-full py-1.5 rounded-lg text-sm font-medium disabled:opacity-40"
          style={{ background: "var(--accent)", color: "#0b0e14" }}
        >
          Send
        </button>
      </div>
    </aside>
  );
}
