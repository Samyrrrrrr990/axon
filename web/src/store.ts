import { create } from "zustand";
import {
  applyEdgeChanges,
  applyNodeChanges,
  type Connection,
  type Edge,
  type EdgeChange,
  type Node,
  type NodeChange,
} from "@xyflow/react";
import { api } from "./api";
import type {
  ExampleInfo,
  MetricPoint,
  NodeSpec,
  NodeStatus,
  PackInfo,
  RunEventT,
  WorkflowT,
} from "./types";

export interface RunState {
  runId: string | null;
  status: "idle" | "running" | "finished" | "error" | "cancelled";
  nodeStatus: Record<string, NodeStatus>;
  cached: Record<string, boolean>;
  previews: Record<string, Record<string, any>>;
  errors: Record<string, { error: string; hint?: string }>;
  metrics: Record<string, MetricPoint[]>;
  logs: { nodeId: string | null; message: string; ts: number }[];
}

const emptyRun = (): RunState => ({
  runId: null,
  status: "idle",
  nodeStatus: {},
  cached: {},
  previews: {},
  errors: {},
  metrics: {},
  logs: [],
});

interface ChatMessage {
  role: "user" | "assistant";
  content: string;
}

interface AxonState {
  catalog: NodeSpec[];
  specById: Record<string, NodeSpec>;
  packs: Record<string, PackInfo>;
  examples: ExampleInfo[];
  workflowId: string;
  workflowName: string;
  workflowMeta: Record<string, unknown>;
  nodes: Node[];
  edges: Edge[];
  selection: string | null;
  run: RunState;
  settings: Record<string, any>;
  copilotOpen: boolean;
  copilotBusy: boolean;
  copilotMessages: ChatMessage[];
  galleryOpen: boolean;
  settingsOpen: boolean;
  logsOpen: boolean;
  packInstallLog: Record<string, string[]>;
  toast: string | null;
  dirty: boolean;

  loadCatalog: () => Promise<void>;
  loadExamples: () => Promise<void>;
  loadSettings: () => Promise<void>;
  newWorkflow: () => void;
  openWorkflow: (id: string) => Promise<void>;
  openExample: (name: string) => Promise<void>;
  saveWorkflow: () => Promise<void>;
  setWorkflowName: (name: string) => void;
  addNode: (type: string, position: { x: number; y: number }) => void;
  updateParams: (nodeId: string, params: Record<string, unknown>) => void;
  onNodesChange: (changes: NodeChange[]) => void;
  onEdgesChange: (changes: EdgeChange[]) => void;
  onConnect: (conn: Connection) => void;
  select: (id: string | null) => void;
  runWorkflow: () => Promise<void>;
  cancelRun: () => Promise<void>;
  handleEvent: (e: RunEventT) => void;
  applyServerWorkflow: (wf: WorkflowT) => void;
  sendCopilot: (text: string) => Promise<void>;
  toWorkflow: () => WorkflowT;
  setToast: (t: string | null) => void;
  set: (partial: Partial<AxonState>) => void;
}

function toFlowNodes(wf: WorkflowT): Node[] {
  return wf.nodes.map((n) => ({
    id: n.id,
    type: "axon",
    position: n.position,
    data: { nodeType: n.type, params: n.params },
  }));
}

function toFlowEdges(wf: WorkflowT): Edge[] {
  return wf.edges.map((e) => ({
    id: e.id,
    source: e.source,
    sourceHandle: e.source_socket,
    target: e.target,
    targetHandle: e.target_socket,
  }));
}

let idCounter = 0;
const freshId = (prefix: string) =>
  `${prefix}_${Date.now().toString(36)}${(idCounter++).toString(36)}`;

export const useStore = create<AxonState>((set, get) => ({
  catalog: [],
  specById: {},
  packs: {},
  examples: [],
  workflowId: "",
  workflowName: "Untitled",
  workflowMeta: {},
  nodes: [],
  edges: [],
  selection: null,
  run: emptyRun(),
  settings: {},
  copilotOpen: false,
  copilotBusy: false,
  copilotMessages: [],
  galleryOpen: false,
  settingsOpen: false,
  logsOpen: false,
  packInstallLog: {},
  toast: null,
  dirty: false,

  set: (partial) => set(partial),
  setToast: (t) => set({ toast: t }),

  loadCatalog: async () => {
    const { nodes, packs } = await api.catalog();
    set({
      catalog: nodes,
      packs,
      specById: Object.fromEntries(nodes.map((n) => [n.id, n])),
    });
  },

  loadExamples: async () => set({ examples: await api.examples() }),
  loadSettings: async () => set({ settings: await api.settings() }),

  newWorkflow: () =>
    set({
      workflowId: "",
      workflowName: "Untitled",
      workflowMeta: {},
      nodes: [],
      edges: [],
      selection: null,
      run: emptyRun(),
      copilotMessages: [],
      dirty: false,
    }),

  openWorkflow: async (id) => {
    const wf = await api.getWorkflow(id);
    get().applyServerWorkflow(wf);
    set({ run: emptyRun(), copilotMessages: [], dirty: false });
  },

  openExample: async (name) => {
    const wf = await api.openExample(name);
    get().applyServerWorkflow(wf);
    set({ galleryOpen: false, run: emptyRun(), dirty: false });
  },

  saveWorkflow: async () => {
    const saved = await api.saveWorkflow(get().toWorkflow());
    set({ workflowId: saved.id, dirty: false, toast: "Saved" });
  },

  setWorkflowName: (name) => set({ workflowName: name, dirty: true }),

  addNode: (type, position) => {
    const node: Node = {
      id: freshId(type.split(".").pop() || "node"),
      type: "axon",
      position,
      data: { nodeType: type, params: {} },
    };
    set({ nodes: [...get().nodes, node], selection: node.id, dirty: true });
  },

  updateParams: (nodeId, params) =>
    set({
      nodes: get().nodes.map((n) =>
        n.id === nodeId
          ? { ...n, data: { ...n.data, params: { ...(n.data.params as object), ...params } } }
          : n,
      ),
      dirty: true,
    }),

  onNodesChange: (changes) =>
    set({ nodes: applyNodeChanges(changes, get().nodes), dirty: true }),
  onEdgesChange: (changes) =>
    set({ edges: applyEdgeChanges(changes, get().edges), dirty: true }),

  onConnect: (conn) => {
    const { specById, nodes } = get();
    const srcNode = nodes.find((n) => n.id === conn.source);
    const dstNode = nodes.find((n) => n.id === conn.target);
    if (!srcNode || !dstNode || !conn.sourceHandle || !conn.targetHandle) return;
    const srcType = specById[srcNode.data.nodeType as string]?.outputs[conn.sourceHandle];
    const dstType = specById[dstNode.data.nodeType as string]?.inputs[conn.targetHandle];
    if (srcType && dstType && srcType !== dstType && srcType !== "any" && dstType !== "any") {
      set({ toast: `Can't connect ${srcType} to ${dstType}` });
      return;
    }
    const edge: Edge = {
      id: freshId("e"),
      source: conn.source,
      sourceHandle: conn.sourceHandle,
      target: conn.target,
      targetHandle: conn.targetHandle,
    };
    // one wire per input socket
    const edges = get().edges.filter(
      (e) => !(e.target === edge.target && e.targetHandle === edge.targetHandle),
    );
    set({ edges: [...edges, edge], dirty: true });
  },

  select: (id) => set({ selection: id }),

  toWorkflow: () => {
    const s = get();
    return {
      format: "axon-workflow/1",
      id: s.workflowId,
      name: s.workflowName,
      meta: s.workflowMeta,
      nodes: s.nodes.map((n) => ({
        id: n.id,
        type: n.data.nodeType as string,
        params: (n.data.params as Record<string, unknown>) || {},
        position: { x: Math.round(n.position.x), y: Math.round(n.position.y) },
      })),
      edges: s.edges.map((e) => ({
        id: e.id,
        source: e.source,
        source_socket: e.sourceHandle || "",
        target: e.target,
        target_socket: e.targetHandle || "",
      })),
    };
  },

  applyServerWorkflow: (wf) =>
    set({
      workflowId: wf.id,
      workflowName: wf.name,
      workflowMeta: wf.meta || {},
      nodes: toFlowNodes(wf),
      edges: toFlowEdges(wf),
      dirty: true,
    }),

  runWorkflow: async () => {
    const wf = get().toWorkflow();
    if (wf.nodes.length === 0) {
      set({ toast: "Add some nodes first — try an example from the gallery." });
      return;
    }
    try {
      const { run_id } = await api.run(wf);
      set({ run: { ...emptyRun(), runId: run_id, status: "running" }, logsOpen: true });
    } catch (err: any) {
      let message = String(err.message || err);
      try {
        const parsed = JSON.parse(message);
        if (parsed.issues) message = parsed.issues.map((i: any) => i.message).join("; ");
      } catch {
        /* plain message */
      }
      set({ toast: `Can't run: ${message}` });
    }
  },

  cancelRun: async () => {
    const { runId } = get().run;
    if (runId) await api.cancelRun(runId);
  },

  handleEvent: (e) => {
    const s = get();
    if (e.type === "pack_install_progress") {
      const pack = e.data.pack as string;
      const log = { ...s.packInstallLog };
      log[pack] = [...(log[pack] || []), e.data.line || ""].slice(-200);
      set({ packInstallLog: log });
      if (e.data.done) {
        s.loadCatalog();
        set({ toast: e.data.success ? `${pack} installed` : `${pack} install failed — see Settings` });
      }
      return;
    }
    if (e.run_id !== s.run.runId) return;
    const run = { ...s.run };
    switch (e.type) {
      case "node_started":
        run.nodeStatus = { ...run.nodeStatus, [e.node_id!]: "running" };
        break;
      case "node_finished":
        run.nodeStatus = { ...run.nodeStatus, [e.node_id!]: "finished" };
        run.cached = { ...run.cached, [e.node_id!]: !!e.data.cached };
        run.previews = { ...run.previews, [e.node_id!]: e.data.preview || {} };
        break;
      case "node_failed":
        run.nodeStatus = {
          ...run.nodeStatus,
          [e.node_id!]: e.data.skipped ? "skipped" : "failed",
        };
        if (!e.data.skipped)
          run.errors = { ...run.errors, [e.node_id!]: { error: e.data.error, hint: e.data.hint } };
        break;
      case "node_log":
        run.logs = [...run.logs, { nodeId: e.node_id, message: e.data.message, ts: e.ts }].slice(-500);
        break;
      case "node_progress":
        if (e.data.metrics)
          run.metrics = {
            ...run.metrics,
            [e.node_id!]: [...(run.metrics[e.node_id!] || []), e.data.metrics],
          };
        break;
      case "run_finished":
        run.status = e.data.status === "error" ? "error" : "finished";
        break;
      case "run_cancelled":
        run.status = "cancelled";
        break;
      case "run_failed":
        run.status = "error";
        break;
    }
    set({ run });
  },

  sendCopilot: async (text) => {
    const s = get();
    const messages = [...s.copilotMessages, { role: "user" as const, content: text }];
    set({ copilotMessages: messages, copilotBusy: true });
    try {
      const out = await api.copilot(
        s.toWorkflow(),
        messages.map((m) => ({ role: m.role, content: m.content })),
      );
      if (out.workflow) {
        get().applyServerWorkflow(out.workflow);
        set({ toast: "Copilot updated your graph" });
      }
      set({
        copilotMessages: [...messages, { role: "assistant", content: out.reply }],
        copilotBusy: false,
      });
    } catch (err: any) {
      set({
        copilotMessages: [
          ...messages,
          { role: "assistant", content: `Something went wrong: ${err.message}` },
        ],
        copilotBusy: false,
      });
    }
  },
}));
