"use client";

import { useCallback, useEffect, useRef, useState } from 'react';
import ReactFlowProvider, {
  Connection,
  Panel,
  useNodesState,
  useEdgesState,
  Handle,
  Position,
  Edge,
  Node,
  ReactFlow,
  MarkerType,
  EdgeMarker,
} from 'reactflow';
import { Background } from '@reactflow/background';
import { Controls } from '@reactflow/controls';
import { MiniMap } from '@reactflow/minimap';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Plus, Maximize2, MinusSquare } from 'lucide-react';
import { SchemaResponse, Table, Column } from '@/lib/types';
import 'reactflow/dist/style.css';

interface SchemaVisualizationProps {
  schema: SchemaResponse;
}

// Custom node for table visualization
function TableNode({ data }: { data: Table }) {
  return (
    <>
      <div className="bg-card border rounded-lg shadow-sm min-w-[180px]">
        <div className="bg-muted px-3 py-2 rounded-t-lg border-b">
          <h4 className="font-semibold text-sm">{data.name}</h4>
        </div>
        <div className="p-3 space-y-1">
          {data.columns.map((column: Column) => (
            <div
              key={column.name}
              className="text-xs flex items-center justify-between group hover:bg-muted/50 rounded px-2 py-1"
            >
              <div className="flex items-center gap-2">
                <span className={column.is_primary_key ? "font-bold" : ""}>
                  {column.name}
                </span>
                <span className="text-muted-foreground">
                  {column.data_type}
                </span>
              </div>
              <div className="flex gap-1">
                {column.is_primary_key && (
                  <span className="text-primary text-[10px] font-medium">PK</span>
                )}
                {column.is_foreign_key && (
                  <span className="text-blue-500 text-[10px] font-medium">FK</span>
                )}
                {column.nullable && (
                  <span className="text-muted-foreground text-[10px]">NULL</span>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>
      <Handle type="target" position={Position.Top} />
      <Handle type="source" position={Position.Bottom} />
    </>
  );
}

// Custom node types
const nodeTypes = {
  table: TableNode,
};

// Custom edge options
const edgeOptions = {
  style: { strokeWidth: 2 },
  type: 'smoothstep',
  markerEnd: {
    type: MarkerType.ArrowClosed,
  } as EdgeMarker,
};

function SchemaVisualizationInner({ schema }: SchemaVisualizationProps) {
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const [zoom, setZoom] = useState(1);
  const flowRef = useRef(null);

  // Transform schema into nodes and edges
  useEffect(() => {
    if (!schema) return;

    // Transform tables into nodes with improved positioning
    const newNodes: Node[] = schema.tables.map((table, index) => ({
      id: table.name,
      type: 'table',
      position: { 
        x: (index % 3) * 300 + 50,
        y: Math.floor(index / 3) * 300 + 50
      },
      data: table,
      draggable: true,
      selectable: true,
    }));

    // Transform relationships into edges with improved styling
    const newEdges: Edge[] = schema.relationships?.map((rel) => ({
      id: `${rel.source_table}-${rel.target_table}`,
      source: rel.source_table,
      target: rel.target_table,
      type: 'smoothstep',
      animated: true,
      label: rel.type,
      labelStyle: { fill: 'var(--muted-foreground)', fontSize: 12 },
      style: { stroke: 'var(--primary)', strokeWidth: 2 },
      markerEnd: {
        type: MarkerType.ArrowClosed,
      },
    })) || [];

    setNodes(newNodes);
    setEdges(newEdges);
  }, [schema, setNodes, setEdges]);

  const onConnect = useCallback(
    (connection: Connection) => {
      if (!connection.source || !connection.target) return;
      setEdges((eds) => [
        ...eds,
        {
          ...connection,
          id: `${connection.source}-${connection.target}`,
          ...edgeOptions,
        } as Edge,
      ]);
    },
    [setEdges]
  );

  const handleZoomIn = () => setZoom((z) => Math.min(z * 1.2, 2));
  const handleZoomOut = () => setZoom((z) => Math.max(z / 1.2, 0.5));
  const handleFitView = () => {
    if (flowRef.current) {
      // @ts-expect-error - ReactFlow instance type is not properly exposed
      flowRef.current.fitView();
    }
  };

  if (!schema) {
    return (
      <Card className="p-4 h-[600px] flex items-center justify-center">
        <p className="text-muted-foreground">No schema data available</p>
      </Card>
    );
  }

  return (
    <Card className="p-4 h-[600px]">
      <ReactFlow
        ref={flowRef}
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onConnect={onConnect}
        nodeTypes={nodeTypes}
        defaultEdgeOptions={edgeOptions}
        fitView
        minZoom={0.1}
        maxZoom={4}
        className="bg-background"
      >
        <Panel position="top-right" className="flex items-center gap-2">
          <Button variant="outline" size="icon" onClick={handleZoomOut}>
            <MinusSquare className="h-4 w-4" />
          </Button>
          <span className="text-sm bg-background/80 px-2 py-1 rounded">
            {Math.round(zoom * 100)}%
          </span>
          <Button variant="outline" size="icon" onClick={handleZoomIn}>
            <Plus className="h-4 w-4" />
          </Button>
          <Button variant="outline" size="icon" onClick={handleFitView}>
            <Maximize2 className="h-4 w-4" />
          </Button>
        </Panel>
        <Background />
        <Controls />
        <MiniMap 
          nodeStrokeColor="var(--border)"
          nodeColor="var(--primary)"
          nodeBorderRadius={2}
        />
      </ReactFlow>
    </Card>
  );
}

// Wrap component with ReactFlowProvider
export function SchemaVisualization(props: SchemaVisualizationProps) {
  return (
    <ReactFlowProvider>
      <SchemaVisualizationInner {...props} />
    </ReactFlowProvider>
  );
}