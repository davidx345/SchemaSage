"""
Base types and configuration for ERD generation
"""
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any, Tuple
import math

class LayoutAlgorithm(Enum):
    """Available layout algorithms for ERD positioning"""
    FORCE_DIRECTED = "force_directed"
    HIERARCHICAL = "hierarchical"
    CIRCULAR = "circular"
    GRID = "grid"
    ORGANIC = "organic"

class NodeShape(Enum):
    """Available node shapes"""
    RECTANGLE = "rectangle"
    ROUNDED_RECTANGLE = "rounded_rectangle"
    ELLIPSE = "ellipse"
    HEXAGON = "hexagon"

class EdgeStyle(Enum):
    """Available edge styles"""
    STRAIGHT = "straight"
    CURVED = "curved"
    ORTHOGONAL = "orthogonal"
    BEZIER = "bezier"

class RelationshipType(Enum):
    """Types of database relationships"""
    ONE_TO_ONE = "one_to_one"
    ONE_TO_MANY = "one_to_many"
    MANY_TO_MANY = "many_to_many"
    SELF_REFERENCING = "self_referencing"

@dataclass
class Point:
    """2D coordinate point"""
    x: float
    y: float
    
    def distance_to(self, other: 'Point') -> float:
        """Calculate distance to another point"""
        return math.sqrt((self.x - other.x)**2 + (self.y - other.y)**2)
    
    def add(self, other: 'Point') -> 'Point':
        """Add another point to this point"""
        return Point(self.x + other.x, self.y + other.y)
    
    def subtract(self, other: 'Point') -> 'Point':
        """Subtract another point from this point"""
        return Point(self.x - other.x, self.y - other.y)
    
    def scale(self, factor: float) -> 'Point':
        """Scale the point by a factor"""
        return Point(self.x * factor, self.y * factor)

@dataclass
class Size:
    """2D size dimensions"""
    width: float
    height: float

@dataclass
class Bounds:
    """Bounding rectangle"""
    x: float
    y: float
    width: float
    height: float
    
    @property
    def center(self) -> Point:
        """Get center point of bounds"""
        return Point(self.x + self.width / 2, self.y + self.height / 2)
    
    @property
    def min_x(self) -> float:
        return self.x
    
    @property
    def max_x(self) -> float:
        return self.x + self.width
    
    @property
    def min_y(self) -> float:
        return self.y
    
    @property
    def max_y(self) -> float:
        return self.y + self.height

@dataclass
class ERDNode:
    """Node representing a database table in ERD"""
    id: str
    table_name: str
    display_name: str
    columns: List[Dict[str, Any]]
    position: Point
    size: Size
    shape: NodeShape = NodeShape.ROUNDED_RECTANGLE
    color: str = "#ffffff"
    border_color: str = "#333333"
    text_color: str = "#000000"
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def bounds(self) -> Bounds:
        """Get bounding rectangle of the node"""
        return Bounds(self.position.x, self.position.y, self.size.width, self.size.height)
    
    @property
    def center(self) -> Point:
        """Get center point of the node"""
        return Point(
            self.position.x + self.size.width / 2,
            self.position.y + self.size.height / 2
        )

@dataclass
class ERDEdge:
    """Edge representing a relationship between tables"""
    id: str
    source_node_id: str
    target_node_id: str
    source_column: str
    target_column: str
    relationship_type: RelationshipType
    style: EdgeStyle = EdgeStyle.STRAIGHT
    color: str = "#666666"
    width: float = 2.0
    label: Optional[str] = None
    control_points: List[Point] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ERDConfig:
    """Configuration for ERD generation"""
    # Node settings
    node_width: float = 200
    node_height: float = 120
    node_padding: float = 10
    column_height: float = 20
    
    # Layout settings
    min_distance: float = 250
    margin: float = 50
    canvas_padding: float = 20
    
    # Visual settings
    show_column_types: bool = True
    show_primary_keys: bool = True
    show_foreign_keys: bool = True
    show_indexes: bool = False
    
    # Color scheme
    primary_key_color: str = "#ffd700"
    foreign_key_color: str = "#87ceeb"
    regular_column_color: str = "#f0f0f0"
    
    # Relationship settings
    show_relationship_labels: bool = True
    relationship_label_size: int = 12
    
    # Performance settings
    max_nodes: int = 50
    max_edges: int = 100
    enable_clustering: bool = True

@dataclass
class LayoutForce:
    """Force vector for force-directed layout"""
    force: Point
    applied_to: str  # node ID

@dataclass
class ClusterInfo:
    """Information about a cluster of related tables"""
    id: str
    table_ids: List[str]
    center: Point
    bounds: Bounds
    color: str = "#e6f3ff"

def calculate_node_size(
    table_name: str, 
    columns: List[Dict[str, Any]], 
    config: ERDConfig
) -> Size:
    """Calculate the size needed for a table node"""
    
    # Base size
    width = max(config.node_width, len(table_name) * 8 + config.node_padding * 2)
    
    # Add height for each column
    column_count = len(columns)
    content_height = (column_count * config.column_height) + (config.node_padding * 2)
    
    # Add header height
    header_height = 30
    height = max(config.node_height, header_height + content_height)
    
    return Size(width, height)

def calculate_canvas_bounds(nodes: List[ERDNode], margin: float = 50) -> Bounds:
    """Calculate the total canvas bounds needed for all nodes"""
    
    if not nodes:
        return Bounds(0, 0, 800, 600)  # Default size
    
    min_x = min(node.position.x for node in nodes) - margin
    min_y = min(node.position.y for node in nodes) - margin
    max_x = max(node.position.x + node.size.width for node in nodes) + margin
    max_y = max(node.position.y + node.size.height for node in nodes) + margin
    
    return Bounds(min_x, min_y, max_x - min_x, max_y - min_y)

def get_default_colors() -> Dict[str, str]:
    """Get default color scheme for ERD elements"""
    return {
        "node_background": "#ffffff",
        "node_border": "#333333",
        "node_text": "#000000",
        "header_background": "#f8f9fa",
        "primary_key": "#ffd700",
        "foreign_key": "#87ceeb",
        "regular_column": "#f0f0f0",
        "relationship_line": "#666666",
        "relationship_label": "#333333",
        "cluster_background": "#e6f3ff",
        "cluster_border": "#b3d9ff"
    }

def validate_erd_data(erd_data: Dict[str, Any]) -> List[str]:
    """Validate ERD data structure"""
    issues = []
    
    # Check required fields
    required_fields = ["nodes", "edges", "metadata"]
    for field in required_fields:
        if field not in erd_data:
            issues.append(f"Missing required field: {field}")
    
    if "nodes" in erd_data:
        nodes = erd_data["nodes"]
        if not isinstance(nodes, list):
            issues.append("Nodes must be a list")
        else:
            # Validate each node
            for i, node in enumerate(nodes):
                if not isinstance(node, dict):
                    issues.append(f"Node {i} must be a dictionary")
                    continue
                
                required_node_fields = ["id", "table_name", "position"]
                for field in required_node_fields:
                    if field not in node:
                        issues.append(f"Node {i} missing required field: {field}")
    
    if "edges" in erd_data:
        edges = erd_data["edges"]
        if not isinstance(edges, list):
            issues.append("Edges must be a list")
        else:
            # Validate each edge
            for i, edge in enumerate(edges):
                if not isinstance(edge, dict):
                    issues.append(f"Edge {i} must be a dictionary")
                    continue
                
                required_edge_fields = ["id", "source_node_id", "target_node_id"]
                for field in required_edge_fields:
                    if field not in edge:
                        issues.append(f"Edge {i} missing required field: {field}")
    
    return issues

def optimize_layout_performance(
    nodes: List[ERDNode], 
    edges: List[ERDEdge], 
    config: ERDConfig
) -> Tuple[List[ERDNode], List[ERDEdge]]:
    """Optimize layout for performance by limiting complexity"""
    
    optimized_nodes = nodes
    optimized_edges = edges
    
    # Limit number of nodes
    if len(nodes) > config.max_nodes:
        optimized_nodes = nodes[:config.max_nodes]
        # Update edges to only include edges between remaining nodes
        remaining_node_ids = {node.id for node in optimized_nodes}
        optimized_edges = [
            edge for edge in edges 
            if edge.source_node_id in remaining_node_ids and edge.target_node_id in remaining_node_ids
        ]
    
    # Limit number of edges
    if len(optimized_edges) > config.max_edges:
        optimized_edges = optimized_edges[:config.max_edges]
    
    return optimized_nodes, optimized_edges
