import React from "react";
import ReactFlow, { MiniMap, Controls, Background, Node, Edge } from "reactflow";
import "reactflow/dist/style.css";

interface LineageGraphProps {
  nodes: Node[];
  edges: Edge[];
  nodeTypes?: any;
}

export function LineageGraph({ nodes, edges, nodeTypes }: LineageGraphProps) {
  return (
    <div style={{ width: "100%", height: 500 }}>
      <ReactFlow nodes={nodes} edges={edges} nodeTypes={nodeTypes} fitView>
        <MiniMap />
        <Controls />
        <Background />
      </ReactFlow>
    </div>
  );
}
