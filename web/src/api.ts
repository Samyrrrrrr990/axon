import type { ExampleInfo, Issue, NodeSpec, PackInfo, RunEventT, WorkflowT } from "./types";

async function req<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(path, {
    headers: init?.body ? { "Content-Type": "application/json" } : undefined,
    ...init,
  });
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = typeof body.detail === "string" ? body.detail : JSON.stringify(body.detail);
    } catch {
      /* keep statusText */
    }
    throw new Error(detail);
  }
  return res.json();
}

export const api = {
  catalog: () => req<{ nodes: NodeSpec[]; packs: Record<string, PackInfo> }>("/api/nodes"),
  listWorkflows: () => req<{ id: string; name: string; node_count: number }[]>("/api/workflows"),
  getWorkflow: (id: string) => req<WorkflowT>(`/api/workflows/${id}`),
  saveWorkflow: (wf: WorkflowT) =>
    wf.id
      ? req<WorkflowT>(`/api/workflows/${wf.id}`, { method: "PUT", body: JSON.stringify(wf) })
      : req<WorkflowT>("/api/workflows", { method: "POST", body: JSON.stringify(wf) }),
  deleteWorkflow: (id: string) => req(`/api/workflows/${id}`, { method: "DELETE" }),
  validate: (wf: WorkflowT) =>
    req<{ issues: Issue[] }>("/api/workflows/validate", { method: "POST", body: JSON.stringify(wf) }),
  run: (wf: WorkflowT) =>
    req<{ run_id: string }>("/api/runs", { method: "POST", body: JSON.stringify({ workflow: wf }) }),
  cancelRun: (runId: string) => req(`/api/runs/${runId}/cancel`, { method: "POST" }),
  getRun: (runId: string) => req<Record<string, any>>(`/api/runs/${runId}`),
  settings: () => req<Record<string, any>>("/api/settings"),
  saveSettings: (s: Record<string, any>) =>
    req<Record<string, any>>("/api/settings", { method: "PUT", body: JSON.stringify(s) }),
  installPack: (name: string) => req(`/api/packs/${name}/install`, { method: "POST" }),
  examples: () => req<ExampleInfo[]>("/api/examples"),
  openExample: (name: string) => req<WorkflowT>(`/api/examples/${name}/open`, { method: "POST" }),
  copilot: (workflow: WorkflowT, messages: { role: string; content: string }[]) =>
    req<{ reply: string; workflow: WorkflowT | null; ops_applied: number }>("/api/copilot/chat", {
      method: "POST",
      body: JSON.stringify({ workflow, messages }),
    }),
};

export function connectWS(onEvent: (e: RunEventT) => void): () => void {
  let ws: WebSocket | null = null;
  let closed = false;

  const open = () => {
    const proto = location.protocol === "https:" ? "wss" : "ws";
    ws = new WebSocket(`${proto}://${location.host}/api/ws`);
    ws.onmessage = (msg) => {
      try {
        onEvent(JSON.parse(msg.data));
      } catch {
        /* ignore malformed frames */
      }
    };
    ws.onclose = () => {
      if (!closed) setTimeout(open, 1500);
    };
  };
  open();
  return () => {
    closed = true;
    ws?.close();
  };
}
