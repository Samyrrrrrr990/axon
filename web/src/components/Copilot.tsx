import { useEffect, useRef, useState } from "react";
import { PaperPlaneRightIcon, SparkleIcon } from "@phosphor-icons/react";
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
      <div className="px-3.5 py-3 border-b flex items-center gap-2" style={{ borderColor: "var(--line)" }}>
        <SparkleIcon size={15} weight="fill" style={{ color: "var(--accent)" }} />
        <span className="panel-title">Copilot</span>
        <span
          className="text-[10px] font-mono truncate ml-auto"
          style={{ color: "var(--text-2)" }}
          title={`${provider} ${model}`}
        >
          {model ? model.split("/").pop()?.split(":")[0] : provider}
        </span>
      </div>

      {!hasKey && (
        <div
          className="m-3 rounded-xl p-3.5 text-xs msg-in"
          style={{ background: "var(--accent-soft)", border: "1px solid rgb(255 178 36 / 0.35)" }}
        >
          <div className="font-medium mb-1" style={{ color: "var(--text-0)" }}>
            The copilot needs an API key
          </div>
          <div className="leading-relaxed mb-2.5" style={{ color: "var(--text-1)" }}>
            A free OpenRouter key works. Create one at openrouter.ai/keys, then paste it in Settings.
          </div>
          <button className="btn btn-primary !py-1.5 !text-xs" onClick={() => setStore({ settingsOpen: true })}>
            Open Settings
          </button>
        </div>
      )}

      <div className="flex-1 overflow-y-auto p-3.5 space-y-2.5">
        {messages.length === 0 && hasKey && (
          <div className="space-y-2 msg-in">
            <div className="text-xs leading-relaxed" style={{ color: "var(--text-1)" }}>
              Describe what you want to build and the copilot adds the nodes, wired and configured. Try:
            </div>
            {SUGGESTIONS.map((s) => (
              <button
                key={s}
                onClick={() => send(s)}
                disabled={busy}
                className="block w-full text-left text-xs rounded-xl px-3 py-2.5 transition-colors"
                style={{ background: "var(--bg-2)", color: "var(--text-0)", border: "1px solid var(--line)" }}
                onMouseEnter={(e) => (e.currentTarget.style.borderColor = "var(--line-bright)")}
                onMouseLeave={(e) => (e.currentTarget.style.borderColor = "var(--line)")}
              >
                {s}
              </button>
            ))}
          </div>
        )}
        {messages.map((m, i) => (
          <div
            key={i}
            className="msg-in rounded-2xl px-3.5 py-2.5 text-[13px] leading-relaxed whitespace-pre-wrap max-w-[92%]"
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
          <div className="flex items-center gap-1.5 text-xs font-mono msg-in" style={{ color: "var(--accent)" }}>
            <SparkleIcon size={12} className="animate-pulse" /> thinking
          </div>
        )}
        <div ref={endRef} />
      </div>

      <div className="p-3 border-t" style={{ borderColor: "var(--line)" }}>
        <div className="relative">
          <textarea
            value={draft}
            onChange={(e) => setDraft(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                submit();
              }
            }}
            placeholder={hasKey ? "e.g. train a classifier on my CSV" : "Add an API key in Settings first"}
            disabled={!hasKey}
            rows={2}
            className="field resize-none !pr-10 !py-2.5"
          />
          <button
            className="btn btn-primary absolute right-2 bottom-2 !p-1.5"
            onClick={submit}
            disabled={busy || !draft.trim() || !hasKey}
            aria-label="Send message"
          >
            <PaperPlaneRightIcon size={13} weight="fill" />
          </button>
        </div>
      </div>
    </aside>
  );
}
