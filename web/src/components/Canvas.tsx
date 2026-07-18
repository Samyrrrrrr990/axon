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
      <div className="text-center pointer-events-auto">
        <div className="font-display text-xl mb-2" style={{ color: "var(--text-1)" }}>
          An empty bench.
        </div>
        <div className="text-sm mb-4" style={{ color: "var(--text-1)" }}>
          Drag a node from the palette, ask the copilot, or start from an example.
        </div>
        <button
          onClick={() => setStore({ galleryOpen: true })}
          className="px-4 py-2 rounded-lg text-sm font-medium"
          style={{ background: "var(--accent)", color: "#0b0e14" }}
        >
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

  const coloredEdges: Edge[] = edges.map((e) => {
    const src = nodes.find((n) => n.id === e.source);
    const type = src ? specById[src.data.nodeType as string]?.outputs[e.sourceHandle || ""] : undefined;
    const color = SOCKET_COLORS[type || "any"] || "var(--sock-any)";
    return { ...e, style: { stroke: color, strokeOpacity: 0.75 } };
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
