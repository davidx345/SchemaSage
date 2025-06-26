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
  ConnectionLineType,
} from 'reactflow';
import { Background } from '@reactflow/background';
import { Controls } from '@reactflow/controls';
import { MiniMap } from '@reactflow/minimap';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Plus, Maximize2, MinusSquare } from 'lucide-react';
import { SchemaResponse, Table, Column, Relationship } from '@/lib/types';
import { RelationshipSuggestions } from "@/components/schema-detection/RelationshipSuggestions";
import { DocumentationEditor } from "@/components/documentation/DocumentationEditor";
import 'reactflow/dist/style.css';

interface SchemaVisualizationProps {
  schema: SchemaResponse;
}

// Custom node for table visualization
function TableNode({ data }: { data: Table }) {
  // Generate unique handle IDs for each column to allow precise connections
  const columnHandles = data.columns.map(col => ({
    ...col,
    handleId: `${data.name}-${col.name}`
  }));

  return (
    <>
      <div className="bg-card border rounded-lg shadow-sm min-w-[220px]">
        <div className="bg-muted px-3 py-2 rounded-t-lg border-b">
          <h4 className="font-semibold text-sm">{data.name}</h4>
        </div>
        <div className="p-3 space-y-1">
          {columnHandles.map((column) => (
            <div
              key={column.name}
              className="text-xs flex items-center justify-between group hover:bg-muted/50 rounded px-2 py-1 relative"
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
              
              {/* Add column-specific handles for more precise connections */}
              {column.is_primary_key && (
                <Handle 
                  type="source" 
                  position={Position.Right} 
                  id={`${column.handleId}-out`}
                  style={{ 
                    top: '50%', 
                    background: 'var(--primary)',
                    width: 8,
                    height: 8
                  }}
                />
              )}
              {column.is_foreign_key && (
                <Handle 
                  type="target" 
                  position={Position.Left} 
                  id={`${column.handleId}-in`}
                  style={{ 
                    top: '50%', 
                    background: 'var(--blue-500)',
                    width: 8,
                    height: 8
                  }}
                />
              )}
            </div>
          ))}
        </div>
      </div>
      
      {/* Keep the general handles as fallbacks */}
      <Handle type="target" position={Position.Top} />
      <Handle type="source" position={Position.Bottom} />
      <Handle type="target" position={Position.Left} />
      <Handle type="source" position={Position.Right} />
    </>
  );
}

// Custom node types
const nodeTypes = {
  table: TableNode,
};

// Get appropriate styling based on relationship type
const getRelationshipStyle = (type: string): {
  animated: boolean;
  style: React.CSSProperties;
  markerEnd: EdgeMarker;
  type: ConnectionLineType;
} => {
  // Base styles
  const base = {
    animated: false,
    style: { strokeWidth: 2 },
    markerEnd: {
      type: MarkerType.ArrowClosed,
    } as EdgeMarker,
    type: 'smoothstep' as ConnectionLineType,
  };

  // Customize based on relationship type
  switch (type.toLowerCase()) {
    case 'one_to_many':
      return {
        ...base,
        style: { ...base.style, stroke: 'var(--primary)', strokeDasharray: '0' },
        animated: true,
      };
    case 'many_to_many':
      return {
        ...base,
        style: { ...base.style, stroke: 'var(--blue-500)', strokeDasharray: '0' },
        type: 'step' as ConnectionLineType,
      };
    case 'one_to_one':
      return {
        ...base,
        style: { ...base.style, stroke: 'var(--green-500)', strokeDasharray: '0' },
      };
    default:
      return {
        ...base,
        style: { ...base.style, stroke: 'var(--muted-foreground)', strokeDasharray: '5,5' },
      };
  }
};

// Format relationship label
const formatRelationshipLabel = (rel: Relationship): string => {
  const type = rel.type || 'relationship';
  
  switch (type.toLowerCase()) {
    case 'one_to_many':
      return '1:N';
    case 'many_to_many':
      return 'N:M';
    case 'one_to_one':
      return '1:1';
    default:
      return type;
  }
};

// --- Relationship Legend Component ---
function RelationshipLegend() {
  return (
    <div className="mt-4 flex flex-wrap gap-4 text-xs">
      <div className="flex items-center gap-2">
        <span style={{ width: 24, height: 0, borderTop: '3px solid var(--primary)', display: 'inline-block' }} />
        <span>One-to-Many (1:N)</span>
      </div>
      <div className="flex items-center gap-2">
        <span style={{ width: 24, height: 0, borderTop: '3px solid var(--blue-500)', display: 'inline-block' }} />
        <span>Many-to-Many (N:M)</span>
      </div>
      <div className="flex items-center gap-2">
        <span style={{ width: 24, height: 0, borderTop: '3px solid var(--green-500)', display: 'inline-block' }} />
        <span>One-to-One (1:1)</span>
      </div>
      <div className="flex items-center gap-2">
        <span style={{ width: 24, height: 0, borderTop: '3px dashed var(--muted-foreground)', display: 'inline-block' }} />
        <span>Other</span>
      </div>
    </div>
  );
}

function SchemaVisualizationInner({ schema }: SchemaVisualizationProps) {
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const [zoom, setZoom] = useState(1);
  const flowRef = useRef(null);
  const [relationships, setRelationships] = useState<Relationship[]>(schema.relationships || []);
  const [doc, setDoc] = useState<string>("");
  const [loadingDoc, setLoadingDoc] = useState(false);
  const [errorDoc, setErrorDoc] = useState<string | null>(null);

  // Transform schema into nodes and edges
  useEffect(() => {
    if (!schema) return;

    // Calculate optimal grid layout based on number of tables
    const gridSize = Math.ceil(Math.sqrt(schema.tables.length));
    const spacing = Math.max(400, 700 / gridSize); // Increased spacing for clarity

    // Transform tables into nodes with grid positioning
    const newNodes: Node[] = schema.tables.map((table, tableIndex) => ({
      id: table.name,
      type: 'table',
      position: { 
        x: (tableIndex % gridSize) * spacing + 50,
        y: Math.floor(tableIndex / gridSize) * spacing + 50
      },
      data: table,
      draggable: true,
      selectable: true,
    }));

    // Create a map for quick lookup of columns by table and name
    const tableColumnMap: Record<string, Record<string, Column>> = {};
    schema.tables.forEach(table => {
      tableColumnMap[table.name] = {};
      table.columns.forEach(column => {
        tableColumnMap[table.name][column.name] = column;
      });
    });

    // Transform relationships into edges with improved styling and routing
    const edgesList = (schema.relationships || []).map((rel) => {
      const sourceTable = schema.tables.find(t => t.name === rel.source_table);
      const targetTable = schema.tables.find(t => t.name === rel.target_table);
      const sourceColumn = sourceTable?.columns.find(c => c.name === rel.source_column);
      const targetColumn = targetTable?.columns.find(c => c.name === rel.target_column);
      
      // Skip invalid relationships
      if (!rel.source_table || !rel.target_table || !sourceTable || !targetTable) return null;
      if (typeof rel.source_table !== 'string' || typeof rel.target_table !== 'string') return null;
      
      const relationshipStyle = getRelationshipStyle(rel.type || 'default');
      
      // Create edge with explicit types for all properties
      return {
        id: `${rel.source_table}-${rel.source_column}-${rel.target_table}-${rel.target_column}`,
        source: rel.source_table,
        target: rel.target_table,
        sourceHandle: sourceColumn?.is_primary_key ? `${rel.source_table}-${rel.source_column}-out` : undefined,
        targetHandle: targetColumn?.is_foreign_key ? `${rel.target_table}-${rel.target_column}-in` : undefined,
        label: formatRelationshipLabel(rel),
        labelBgPadding: [8, 4] as [number, number],
        labelBgBorderRadius: 4,
        labelBgStyle: { fill: 'var(--background)', fillOpacity: 0.8 },
        labelStyle: { fill: 'var(--foreground)', fontSize: 12, fontWeight: 500 },
        data: { relationshipType: rel.type },
        animated: relationshipStyle.animated ?? false,
        style: relationshipStyle.style,
        markerEnd: relationshipStyle.markerEnd,
        type: relationshipStyle.type,
      };
    });
    
    // Properly filter and type the edges
    const validEdges = edgesList.filter((edge): edge is NonNullable<typeof edge> => edge !== null);
    
    setNodes(newNodes);
    setEdges(validEdges);
  }, [schema, setNodes, setEdges]);

  const onConnect = useCallback(
    (connection: Connection) => {
      if (!connection.source || !connection.target) return;
      
      // Create new edge with appropriate styling and explicit types
      const newEdge: Edge = {
        id: `${connection.source}-${connection.sourceHandle || ''}-${connection.target}-${connection.targetHandle || ''}`,
        source: connection.source,
        target: connection.target,
        sourceHandle: connection.sourceHandle || undefined, // Convert null to undefined
        targetHandle: connection.targetHandle || undefined, // Convert null to undefined
        label: 'relationship',
        labelBgPadding: [8, 4],
        labelBgBorderRadius: 4,
        labelBgStyle: { fill: 'var(--background)', fillOpacity: 0.8 },
        labelStyle: { fill: 'var(--foreground)', fontSize: 12 },
        ...getRelationshipStyle('default'),
      };
      
      setEdges(eds => [...eds, newEdge]);
    },
    [setEdges]
  );

  // Handler to apply suggested relationships
  const handleApplySuggestions = (suggested: Relationship[]) => {
    setRelationships(suggested);
  };

  // UI control handlers
  const handleZoomIn = () => setZoom((z) => Math.min(z * 1.2, 2));
  const handleZoomOut = () => setZoom((z) => Math.max(z / 1.2, 0.5));
  const handleFitView = () => {
    if (flowRef.current) {
      // @ts-expect-error - ReactFlow instance type is not properly exposed
      flowRef.current.fitView({ padding: 0.2 });
    }
  };

  // Auto-fetch or generate documentation for the schema
  useEffect(() => {
    async function fetchDoc() {
      setLoadingDoc(true);
      setErrorDoc(null);
      try {
        const res = await fetch(`/api/schema-detection/documentation/get?object_id=schema`);
        if (res.ok) {
          const data = await res.json();
          setDoc(data.documentation);
        } else if (res.status === 404) {
          // Auto-generate if not found
          const genRes = await fetch(`/api/schema-detection/documentation/generate`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ schema })
          });
          const data = await genRes.json();
          setDoc(data.documentation);
        } else {
          throw new Error("Failed to fetch documentation");
        }
      } catch (e: any) {
        setErrorDoc(e.message);
      } finally {
        setLoadingDoc(false);
      }
    }
    fetchDoc();
  }, [schema]);

  // Export to Markdown
  const handleExportMarkdown = () => {
    const blob = new Blob([doc], { type: "text/markdown" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "schema-documentation.md";
    a.click();
    URL.revokeObjectURL(url);
  };

  if (!schema) {
    return (
      <Card className="p-4 h-[600px] flex items-center justify-center">
        <p className="text-muted-foreground">No schema data available</p>
      </Card>
    );
  }

  return (
    <>
      <Card className="p-4 h-[600px]">
        <ReactFlow
          ref={flowRef}
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onConnect={onConnect}
          nodeTypes={nodeTypes}
          fitView
          minZoom={0.1}
          maxZoom={4}
          className="bg-background"
          connectionLineType={ConnectionLineType.SmoothStep}
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
            <Button variant="outline" size="icon" onClick={handleFitView} title="Fit view">
              <Maximize2 className="h-4 w-4" />
            </Button>
          </Panel>
          <Background gap={12} size={1} />
          <Controls />
          <MiniMap 
            nodeStrokeColor="var(--border)"
            nodeColor="var(--primary)"
            nodeBorderRadius={2}
            maskColor="rgba(240, 240, 240, 0.4)"
          />
        </ReactFlow>
      </Card>
      <RelationshipLegend />
      <RelationshipSuggestions tables={schema.tables} onApply={handleApplySuggestions} />
      <div className="mb-4">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-bold">Schema Documentation</h2>
          <Button size="sm" onClick={handleExportMarkdown} disabled={!doc}>Export Markdown</Button>
        </div>
        {loadingDoc ? (
          <div>Loading documentation...</div>
        ) : errorDoc ? (
          <div className="text-red-500">{errorDoc}</div>
        ) : (
          <DocumentationEditor objectId="schema" initialDoc={doc} />
        )}
      </div>
    </>
  );
}

// Wrap component with ReactFlowProvider
export function SchemaVisualization(props: SchemaVisualizationProps) {
  return (
    <div className="schema-visualization">
      <ReactFlowProvider>
        <SchemaVisualizationInner {...props} />
      </ReactFlowProvider>
    </div>
  );
}