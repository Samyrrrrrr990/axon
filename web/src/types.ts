export interface ParamSchema {
  kind: string;
  default: unknown;
  help: string;
  required: boolean;
  min?: number | null;
  max?: number | null;
  options?: string[];
  path_kind?: string;
  must_exist?: boolean;
}

export interface NodeSpec {
  id: string;
  name: string;
  category: string;
  description: string;
  pack: string;
  cacheable: boolean;
  inputs: Record<string, string>;
  outputs: Record<string, string>;
  params: Record<string, ParamSchema>;
}

export interface PackInfo {
  installed: boolean;
  label: string;
  size_hint: string;
}

export interface WfNode {
  id: string;
  type: string;
  params: Record<string, unknown>;
  position: { x: number; y: number };
  label?: string | null;
}

export interface WfEdge {
  id: string;
  source: string;
  source_socket: string;
  target: string;
  target_socket: string;
}

export interface WorkflowT {
  format: string;
  id: string;
  name: string;
  nodes: WfNode[];
  edges: WfEdge[];
  meta: Record<string, unknown>;
}

export interface RunEventT {
  type: string;
  run_id: string;
  node_id: string | null;
  data: Record<string, any>;
  ts: number;
}

export type NodeStatus = "idle" | "running" | "finished" | "failed" | "skipped";

export interface MetricPoint {
  [k: string]: number;
}

export interface ExampleInfo {
  name: string;
  title: string;
  description: string;
  domain: string;
  requires_packs: string[];
  requires_keys: string[];
  node_count: number;
}

export interface Issue {
  level: "error" | "warning";
  node_id: string | null;
  message: string;
}

export const SOCKET_COLORS: Record<string, string> = {
  dataset: "var(--sock-dataset)",
  model: "var(--sock-model)",
  text: "var(--sock-text)",
  metrics: "var(--sock-metrics)",
  chart: "var(--sock-chart)",
  docs: "var(--sock-docs)",
  embeddings: "var(--sock-embeddings)",
  vectorstore: "var(--sock-vectorstore)",
  image: "var(--sock-image)",
  any: "var(--sock-any)",
};

export const CATEGORY_COLORS: Record<string, string> = {
  Data: "var(--sock-dataset)",
  "Classical ML": "var(--sock-model)",
  "Deep Learning": "var(--sock-model)",
  "Fine-tuning": "var(--sock-image)",
  "LLM & Agents": "var(--sock-text)",
  Utility: "var(--sock-any)",
};
