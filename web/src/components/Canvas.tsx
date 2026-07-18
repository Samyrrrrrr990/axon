import { useCallback, useRef } from "react";
import {
  Background,
  BackgroundVariant,
  Controls,
  MiniMap,
  ReactFlow,
  useReactFlow,
  type Edge,
} from "@xyflow/react";
import { useStore } from "../store";
import { SOCKET_COLORS } from "../types";
import AxonNode from "./AxonNode";

const nodeTypes = { axon: AxonNode };

function EmptyState() {
  const setStore = useStore((s) => s.set);
  return (
    <div className="absolute inset-0 flex items-center justify-center pointer-events-none z-10">
      <div className="text-center pointer-events-auto msg-in max-w-sm px-6">
        <svg width="56" height="56" viewBox="0 0 22 22" aria-hidden className="mx-auto mb-4 opacity-90">
          <circle cx="5" cy="11" r="3" fill="var(--accent)" />
          <circle cx="17" cy="5" r="2.4" fill="var(--sock-dataset)" />
          <circle cx="17" cy="17" r="2.4" fill="var(--sock-model)" />
          <path d="M7.5 10L14.8 5.8M7.5 12L14.8 16.2" stroke="var(--line-bright)" strokeWidth="1.2" />
        </svg>
        <div className="font-display text-lg mb-1.5" style={{ color: "var(--text-0)" }}>
          Your canvas is empty
        </div>
        <div className="text-[13px] leading-relaxed mb-5" style={{ color: "var(--text-1)" }}>
          Drag a node from the palette, describe what you want to the copilot, or open a working example.
        </div>
        <button className="btn btn-primary" onClick={() => setStore({ galleryOpen: true })}>
          Open examples
        </button>
      </div>
    </div>
  );
}

export default function Canvas() {
  const nodes = useStore((s) => s.nodes);
  const edges = useStore((s) => s.edges);
  const specById = useStore((s) => s.specById);
  const onNodesChange = useStore((s) => s.onNodesChange);
  const onEdgesChange = useStore((s) => s.onEdgesChange);
  const onConnect = useStore((s) => s.onConnect);
  const addNode = useStore((s) => s.addNode);
  const select = useStore((s) => s.select);
  const { screenToFlowPosition } = useReactFlow();
  const wrapper = useRef<HTMLDivElement>(null);

  const onDrop = useCallback(
    (event: React.DragEvent) => {
      event.preventDefault();
      const type = event.dataTransfer.getData("application/axon-node");
      if (!type) return;
      addNode(type, screenToFlowPosition({ x: event.clientX, y: event.clientY }));
    },
    [addNode, screenToFlowPosition],
  );

  const nodeStatus = useStore((s) => s.run.nodeStatus);
  const coloredEdges: Edge[] = edges.map((e) => {
    const src = nodes.find((n) => n.id === e.source);
    const type = src ? specById[src.data.nodeType as string]?.outputs[e.sourceHandle || ""] : undefined;
    const color = SOCKET_COLORS[type || "any"] || "var(--sock-any)";
    // A wire lights up while its destination node is computing.
    const active = nodeStatus[e.target] === "running";
    return { ...e, animated: active, style: { stroke: color, strokeOpacity: active ? 1 : 0.7 } };
  });

  return (
    <div ref={wrapper} className="relative h-full w-full">
      {nodes.length === 0 && <EmptyState />}
      <ReactFlow
        nodes={nodes}
        edges={coloredEdges}
        nodeTypes={nodeTypes}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onConnect={onConnect}
        onDrop={onDrop}
        onDragOver={(e) => {
          e.preventDefault();
          e.dataTransfer.dropEffect = "move";
        }}
        onSelectionChange={({ nodes: sel }) => select(sel[0]?.id ?? null)}
        deleteKeyCode={["Backspace", "Delete"]}
        fitView
        proOptions={{ hideAttribution: true }}
        colorMode="dark"
      >
        <Background variant={BackgroundVariant.Dots} gap={22} size={1.5} color="#232c3d" />
        <Controls position="bottom-left" />
        <MiniMap
          position="bottom-right"
          nodeColor="#222b3d"
          maskColor="rgba(11, 14, 20, 0.7)"
          pannable
          zoomable
        />
      </ReactFlow>
    </div>
  );
}
