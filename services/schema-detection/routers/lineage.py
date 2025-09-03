"""
Data Lineage API Routes
Provides table and column-level data lineage tracking
"""
from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging
import uuid

from models.schemas import TableInfo, ColumnInfo, Relationship

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/lineage", tags=["Data Lineage"])

# Sample lineage data store
lineage_store = {
    "tables": {},
    "columns": {}
}

def initialize_sample_lineage():
    """Initialize sample lineage data"""
    # Sample table lineage
    lineage_store["tables"] = {
        "users": {
            "upstream": [],
            "downstream": [
                {
                    "table": "user_analytics",
                    "transformation": "aggregation",
                    "description": "Aggregated user behavior metrics"
                },
                {
                    "table": "customer_segments",
                    "transformation": "classification",
                    "description": "User segmentation based on behavior"
                }
            ]
        },
        "orders": {
            "upstream": [
                {
                    "table": "users",
                    "transformation": "join",
                    "description": "User information joined with orders"
                },
                {
                    "table": "products",
                    "transformation": "join",
                    "description": "Product details joined with orders"
                }
            ],
            "downstream": [
                {
                    "table": "revenue_analytics",
                    "transformation": "aggregation",
                    "description": "Revenue calculations and analytics"
                },
                {
                    "table": "order_fulfillment",
                    "transformation": "status_tracking",
                    "description": "Order fulfillment and shipping tracking"
                }
            ]
        },
        "products": {
            "upstream": [
                {
                    "table": "product_catalog",
                    "transformation": "normalization",
                    "description": "Normalized product information"
                }
            ],
            "downstream": [
                {
                    "table": "inventory_analytics",
                    "transformation": "aggregation",
                    "description": "Inventory levels and movement analytics"
                },
                {
                    "table": "recommendation_engine",
                    "transformation": "feature_extraction",
                    "description": "Product features for recommendations"
                }
            ]
        }
    }
    
    # Sample column lineage
    lineage_store["columns"] = {
        "users.email": {
            "upstream": [
                {
                    "column": "raw_users.email_address",
                    "transformation": "standardization",
                    "description": "Email standardization and validation"
                }
            ],
            "downstream": [
                {
                    "column": "user_analytics.user_email",
                    "transformation": "direct_copy",
                    "description": "Direct copy for analytics"
                },
                {
                    "column": "email_campaigns.recipient_email",
                    "transformation": "direct_copy",
                    "description": "Email for marketing campaigns"
                }
            ]
        },
        "orders.total_amount": {
            "upstream": [
                {
                    "column": "order_items.quantity",
                    "transformation": "calculation",
                    "description": "Calculated from quantity * unit_price"
                },
                {
                    "column": "order_items.unit_price",
                    "transformation": "calculation",
                    "description": "Unit price from product catalog"
                }
            ],
            "downstream": [
                {
                    "column": "revenue_analytics.daily_revenue",
                    "transformation": "aggregation",
                    "description": "Daily revenue aggregation"
                },
                {
                    "column": "customer_segments.avg_order_value",
                    "transformation": "aggregation",
                    "description": "Average order value calculation"
                }
            ]
        },
        "products.category": {
            "upstream": [
                {
                    "column": "product_catalog.category_name",
                    "transformation": "normalization",
                    "description": "Category name standardization"
                }
            ],
            "downstream": [
                {
                    "column": "category_analytics.category",
                    "transformation": "direct_copy",
                    "description": "Category-based analytics"
                },
                {
                    "column": "recommendation_engine.product_category",
                    "transformation": "encoding",
                    "description": "Category encoding for ML model"
                }
            ]
        }
    }

# Initialize sample data
initialize_sample_lineage()

@router.post("/table")
async def get_table_lineage(request: Dict[str, Any]):
    """Get table-level data lineage"""
    try:
        schema = request.get("schema", {})
        table_name = request.get("table")
        depth = request.get("depth", 3)
        direction = request.get("direction", "both")  # "upstream", "downstream", "both"
        
        if not table_name:
            raise HTTPException(status_code=400, detail="table name is required")
        
        logger.info(f"Getting table lineage for: {table_name}, depth: {depth}, direction: {direction}")
        
        # Get lineage data for the table
        table_lineage = lineage_store["tables"].get(table_name, {"upstream": [], "downstream": []})
        
        def build_lineage_tree(table: str, current_depth: int, max_depth: int, direction: str, visited: set = None) -> Dict[str, Any]:
            """Recursively build lineage tree"""
            if visited is None:
                visited = set()
            
            if current_depth >= max_depth or table in visited:
                return {"table": table, "children": []}
            
            visited.add(table)
            
            lineage_data = lineage_store["tables"].get(table, {"upstream": [], "downstream": []})
            children = []
            
            if direction in ["upstream", "both"]:
                for upstream in lineage_data.get("upstream", []):
                    child = build_lineage_tree(
                        upstream["table"], 
                        current_depth + 1, 
                        max_depth, 
                        "upstream", 
                        visited.copy()
                    )
                    child.update({
                        "relationship": "upstream",
                        "transformation": upstream.get("transformation", "unknown"),
                        "description": upstream.get("description", "")
                    })
                    children.append(child)
            
            if direction in ["downstream", "both"]:
                for downstream in lineage_data.get("downstream", []):
                    child = build_lineage_tree(
                        downstream["table"], 
                        current_depth + 1, 
                        max_depth, 
                        "downstream", 
                        visited.copy()
                    )
                    child.update({
                        "relationship": "downstream",
                        "transformation": downstream.get("transformation", "unknown"),
                        "description": downstream.get("description", "")
                    })
                    children.append(child)
            
            return {
                "table": table,
                "children": children
            }
        
        # Build the lineage tree
        lineage_tree = build_lineage_tree(table_name, 0, depth, direction)
        
        # Calculate lineage metrics
        all_related_tables = set()
        
        def collect_tables(node: Dict[str, Any]):
            all_related_tables.add(node["table"])
            for child in node.get("children", []):
                collect_tables(child)
        
        collect_tables(lineage_tree)
        
        # Get impact analysis
        impact_tables = len([t for t in lineage_store["tables"].get(table_name, {}).get("downstream", [])])
        dependency_tables = len([t for t in lineage_store["tables"].get(table_name, {}).get("upstream", [])])
        
        return {
            "table": table_name,
            "lineage_tree": lineage_tree,
            "summary": {
                "total_related_tables": len(all_related_tables) - 1,  # Exclude the source table
                "direct_dependencies": dependency_tables,
                "direct_impacts": impact_tables,
                "lineage_depth": depth,
                "direction_analyzed": direction
            },
            "transformations": {
                "types_found": list(set([
                    rel.get("transformation", "unknown") 
                    for table_data in lineage_store["tables"].values()
                    for rel in table_data.get("upstream", []) + table_data.get("downstream", [])
                ])),
                "complexity_score": min(100, len(all_related_tables) * 10 + depth * 5)
            },
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "schema_context": bool(schema),
                "lineage_id": str(uuid.uuid4())
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting table lineage: {e}")
        raise HTTPException(status_code=500, detail="Failed to get table lineage")

@router.post("/column")
async def get_column_lineage(request: Dict[str, Any]):
    """Get column-level data lineage"""
    try:
        schema = request.get("schema", {})
        table_name = request.get("table")
        column_name = request.get("column")
        depth = request.get("depth", 3)
        direction = request.get("direction", "both")  # "upstream", "downstream", "both"
        
        if not table_name or not column_name:
            raise HTTPException(status_code=400, detail="table and column names are required")
        
        column_key = f"{table_name}.{column_name}"
        logger.info(f"Getting column lineage for: {column_key}, depth: {depth}, direction: {direction}")
        
        def build_column_lineage_tree(column: str, current_depth: int, max_depth: int, direction: str, visited: set = None) -> Dict[str, Any]:
            """Recursively build column lineage tree"""
            if visited is None:
                visited = set()
            
            if current_depth >= max_depth or column in visited:
                table, col = column.split(".", 1) if "." in column else (column, "unknown")
                return {"table": table, "column": col, "children": []}
            
            visited.add(column)
            
            lineage_data = lineage_store["columns"].get(column, {"upstream": [], "downstream": []})
            children = []
            
            if direction in ["upstream", "both"]:
                for upstream in lineage_data.get("upstream", []):
                    child = build_column_lineage_tree(
                        upstream["column"], 
                        current_depth + 1, 
                        max_depth, 
                        "upstream", 
                        visited.copy()
                    )
                    child.update({
                        "relationship": "upstream",
                        "transformation": upstream.get("transformation", "unknown"),
                        "description": upstream.get("description", "")
                    })
                    children.append(child)
            
            if direction in ["downstream", "both"]:
                for downstream in lineage_data.get("downstream", []):
                    child = build_column_lineage_tree(
                        downstream["column"], 
                        current_depth + 1, 
                        max_depth, 
                        "downstream", 
                        visited.copy()
                    )
                    child.update({
                        "relationship": "downstream",
                        "transformation": downstream.get("transformation", "unknown"),
                        "description": downstream.get("description", "")
                    })
                    children.append(child)
            
            table, col = column.split(".", 1) if "." in column else (column, "unknown")
            return {
                "table": table,
                "column": col,
                "children": children
            }
        
        # Build the column lineage tree
        lineage_tree = build_column_lineage_tree(column_key, 0, depth, direction)
        
        # Calculate column lineage metrics
        all_related_columns = set()
        transformation_types = set()
        
        def collect_columns(node: Dict[str, Any]):
            column_ref = f"{node['table']}.{node['column']}"
            all_related_columns.add(column_ref)
            for child in node.get("children", []):
                if "transformation" in child:
                    transformation_types.add(child["transformation"])
                collect_columns(child)
        
        collect_columns(lineage_tree)
        
        # Get column-specific metrics
        column_lineage_data = lineage_store["columns"].get(column_key, {"upstream": [], "downstream": []})
        direct_dependencies = len(column_lineage_data.get("upstream", []))
        direct_impacts = len(column_lineage_data.get("downstream", []))
        
        # Data quality impact analysis
        quality_impact = {
            "risk_level": "high" if direct_impacts > 5 else "medium" if direct_impacts > 2 else "low",
            "affected_columns": direct_impacts,
            "transformation_complexity": len(transformation_types),
            "data_propagation_score": min(100, direct_impacts * 15 + len(transformation_types) * 10)
        }
        
        return {
            "table": table_name,
            "column": column_name,
            "lineage_tree": lineage_tree,
            "summary": {
                "total_related_columns": len(all_related_columns) - 1,  # Exclude the source column
                "direct_dependencies": direct_dependencies,
                "direct_impacts": direct_impacts,
                "lineage_depth": depth,
                "direction_analyzed": direction
            },
            "transformations": {
                "types_found": list(transformation_types),
                "most_common": max(transformation_types, key=lambda x: x) if transformation_types else "none",
                "complexity_score": len(transformation_types) * 20
            },
            "data_quality_impact": quality_impact,
            "usage_patterns": {
                "is_source_column": direct_dependencies == 0,
                "is_calculated_column": any(t in transformation_types for t in ["calculation", "aggregation"]),
                "is_derived_column": direct_dependencies > 0,
                "propagation_factor": max(1, direct_impacts / max(1, direct_dependencies))
            },
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "schema_context": bool(schema),
                "lineage_id": str(uuid.uuid4())
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting column lineage: {e}")
        raise HTTPException(status_code=500, detail="Failed to get column lineage")

@router.get("/tables/{table_name}/summary")
async def get_table_lineage_summary(table_name: str):
    """Get a quick summary of table lineage"""
    try:
        table_lineage = lineage_store["tables"].get(table_name, {"upstream": [], "downstream": []})
        
        upstream_count = len(table_lineage.get("upstream", []))
        downstream_count = len(table_lineage.get("downstream", []))
        
        return {
            "table": table_name,
            "dependencies": {
                "count": upstream_count,
                "tables": [rel["table"] for rel in table_lineage.get("upstream", [])]
            },
            "impacts": {
                "count": downstream_count,
                "tables": [rel["table"] for rel in table_lineage.get("downstream", [])]
            },
            "complexity_level": (
                "high" if upstream_count + downstream_count > 10 
                else "medium" if upstream_count + downstream_count > 5 
                else "low"
            ),
            "total_connections": upstream_count + downstream_count
        }
        
    except Exception as e:
        logger.error(f"Error getting table lineage summary: {e}")
        raise HTTPException(status_code=500, detail="Failed to get table lineage summary")

@router.get("/columns/{table_name}/{column_name}/summary")
async def get_column_lineage_summary(table_name: str, column_name: str):
    """Get a quick summary of column lineage"""
    try:
        column_key = f"{table_name}.{column_name}"
        column_lineage = lineage_store["columns"].get(column_key, {"upstream": [], "downstream": []})
        
        upstream_count = len(column_lineage.get("upstream", []))
        downstream_count = len(column_lineage.get("downstream", []))
        
        # Get transformation types
        transformations = set()
        for rel in column_lineage.get("upstream", []) + column_lineage.get("downstream", []):
            transformations.add(rel.get("transformation", "unknown"))
        
        return {
            "table": table_name,
            "column": column_name,
            "dependencies": {
                "count": upstream_count,
                "columns": [rel["column"] for rel in column_lineage.get("upstream", [])]
            },
            "impacts": {
                "count": downstream_count,
                "columns": [rel["column"] for rel in column_lineage.get("downstream", [])]
            },
            "transformations": list(transformations),
            "data_flow_type": (
                "source" if upstream_count == 0 
                else "derived" if upstream_count > 0 and downstream_count > 0 
                else "sink"
            ),
            "impact_level": (
                "high" if downstream_count > 5 
                else "medium" if downstream_count > 2 
                else "low"
            ),
            "total_connections": upstream_count + downstream_count
        }
        
    except Exception as e:
        logger.error(f"Error getting column lineage summary: {e}")
        raise HTTPException(status_code=500, detail="Failed to get column lineage summary")

@router.get("/search")
async def search_lineage(
    query: str = Query(..., description="Search query for tables/columns"),
    entity_type: str = Query("both", description="Search type: 'table', 'column', or 'both'")
):
    """Search across lineage data"""
    try:
        results = {
            "tables": [],
            "columns": [],
            "total_results": 0
        }
        
        query_lower = query.lower()
        
        if entity_type in ["table", "both"]:
            # Search tables
            for table_name, lineage_data in lineage_store["tables"].items():
                if query_lower in table_name.lower():
                    upstream_count = len(lineage_data.get("upstream", []))
                    downstream_count = len(lineage_data.get("downstream", []))
                    
                    results["tables"].append({
                        "table": table_name,
                        "type": "table",
                        "dependencies": upstream_count,
                        "impacts": downstream_count,
                        "total_connections": upstream_count + downstream_count
                    })
        
        if entity_type in ["column", "both"]:
            # Search columns
            for column_key, lineage_data in lineage_store["columns"].items():
                table_name, column_name = column_key.split(".", 1) if "." in column_key else (column_key, "")
                
                if (query_lower in table_name.lower() or 
                    query_lower in column_name.lower() or 
                    query_lower in column_key.lower()):
                    
                    upstream_count = len(lineage_data.get("upstream", []))
                    downstream_count = len(lineage_data.get("downstream", []))
                    
                    results["columns"].append({
                        "table": table_name,
                        "column": column_name,
                        "type": "column",
                        "dependencies": upstream_count,
                        "impacts": downstream_count,
                        "total_connections": upstream_count + downstream_count
                    })
        
        results["total_results"] = len(results["tables"]) + len(results["columns"])
        
        # Sort by total connections (most connected first)
        results["tables"].sort(key=lambda x: x["total_connections"], reverse=True)
        results["columns"].sort(key=lambda x: x["total_connections"], reverse=True)
        
        return results
        
    except Exception as e:
        logger.error(f"Error searching lineage: {e}")
        raise HTTPException(status_code=500, detail="Failed to search lineage data")

@router.get("/stats")
async def get_lineage_statistics():
    """Get overall lineage statistics"""
    try:
        # Calculate statistics
        total_tables = len(lineage_store["tables"])
        total_columns = len(lineage_store["columns"])
        
        # Count relationships
        total_table_relationships = sum(
            len(data.get("upstream", [])) + len(data.get("downstream", []))
            for data in lineage_store["tables"].values()
        )
        
        total_column_relationships = sum(
            len(data.get("upstream", [])) + len(data.get("downstream", []))
            for data in lineage_store["columns"].values()
        )
        
        # Get transformation types
        transformation_types = set()
        for data in lineage_store["tables"].values():
            for rel in data.get("upstream", []) + data.get("downstream", []):
                transformation_types.add(rel.get("transformation", "unknown"))
        
        for data in lineage_store["columns"].values():
            for rel in data.get("upstream", []) + data.get("downstream", []):
                transformation_types.add(rel.get("transformation", "unknown"))
        
        # Find most connected entities
        table_connections = {}
        for table, data in lineage_store["tables"].items():
            table_connections[table] = len(data.get("upstream", [])) + len(data.get("downstream", []))
        
        column_connections = {}
        for column, data in lineage_store["columns"].items():
            column_connections[column] = len(data.get("upstream", [])) + len(data.get("downstream", []))
        
        most_connected_table = max(table_connections.items(), key=lambda x: x[1]) if table_connections else ("none", 0)
        most_connected_column = max(column_connections.items(), key=lambda x: x[1]) if column_connections else ("none", 0)
        
        return {
            "overview": {
                "total_tables_tracked": total_tables,
                "total_columns_tracked": total_columns,
                "total_table_relationships": total_table_relationships,
                "total_column_relationships": total_column_relationships,
                "total_transformations": len(transformation_types)
            },
            "complexity_metrics": {
                "avg_table_connections": round(total_table_relationships / max(1, total_tables), 2),
                "avg_column_connections": round(total_column_relationships / max(1, total_columns), 2),
                "lineage_density": round((total_table_relationships + total_column_relationships) / max(1, total_tables + total_columns), 2)
            },
            "transformation_analysis": {
                "types_available": list(transformation_types),
                "most_complex_transformations": ["calculation", "aggregation", "join"] if transformation_types else []
            },
            "top_connected": {
                "table": {
                    "name": most_connected_table[0],
                    "connections": most_connected_table[1]
                },
                "column": {
                    "name": most_connected_column[0],
                    "connections": most_connected_column[1]
                }
            },
            "health_metrics": {
                "lineage_coverage": round((total_tables + total_columns) / max(1, 100) * 100, 2),  # Assuming 100 total entities
                "relationship_quality": round(total_table_relationships / max(1, total_tables * 2) * 100, 2),
                "documentation_completeness": 85.0  # Mock percentage
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting lineage statistics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get lineage statistics")
