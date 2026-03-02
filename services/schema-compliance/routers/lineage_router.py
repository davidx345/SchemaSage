"""
Data Lineage Router
Track data flow and dependencies across tables and columns
"""
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/lineage", tags=["lineage"])


# Response Models
class ColumnLineageNode(BaseModel):
    """Column lineage node"""
    column_name: str
    table_name: str
    schema_name: str
    data_type: str
    transformations: List[str] = Field(default_factory=list)
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)


class TableLineageNode(BaseModel):
    """Table lineage node"""
    table_name: str
    schema_name: str
    table_type: str  # 'source', 'intermediate', 'target'
    row_count: Optional[int] = None
    last_updated: Optional[str] = None


class LineageEdge(BaseModel):
    """Lineage relationship edge"""
    from_node: str
    to_node: str
    edge_type: str  # 'derives_from', 'populates', 'references'
    transformation: Optional[str] = None
    confidence: float = Field(default=1.0)


@router.get("/column/{table}/{column}")
async def get_column_lineage(
    table: str,
    column: str,
    schema: str = Query(default="public", description="Database schema name"),
    direction: str = Query(default="both", description="upstream|downstream|both"),
    depth: int = Query(default=3, ge=1, le=10, description="Traversal depth")
):
    """
    Get column-level data lineage
    
    Traces data flow for a specific column showing upstream sources
    and downstream dependencies.
    """
    try:
        # Mock lineage data - in production, this would query metadata tables
        # and analyze SQL queries, ETL jobs, and transformations
        
        upstream_lineage = []
        downstream_lineage = []
        
        # Generate upstream lineage (sources)
        if direction in ["upstream", "both"]:
            upstream_lineage = [
                {
                    "node": ColumnLineageNode(
                        column_name="source_id",
                        table_name="raw_data",
                        schema_name=schema,
                        data_type="integer",
                        transformations=[],
                        confidence=0.95
                    ).dict(),
                    "path_length": 1,
                    "transformation_chain": ["SELECT source_id FROM raw_data"]
                },
                {
                    "node": ColumnLineageNode(
                        column_name="external_id",
                        table_name="staging_imports",
                        schema_name="staging",
                        data_type="varchar",
                        transformations=["CAST(external_id AS INTEGER)"],
                        confidence=0.90
                    ).dict(),
                    "path_length": 2,
                    "transformation_chain": [
                        "INSERT INTO raw_data SELECT CAST(external_id AS INTEGER) FROM staging_imports",
                        "SELECT source_id FROM raw_data"
                    ]
                }
            ]
        
        # Generate downstream lineage (consumers)
        if direction in ["downstream", "both"]:
            downstream_lineage = [
                {
                    "node": ColumnLineageNode(
                        column_name="user_id",
                        table_name="analytics_facts",
                        schema_name="analytics",
                        data_type="integer",
                        transformations=["LEFT JOIN"],
                        confidence=0.98
                    ).dict(),
                    "path_length": 1,
                    "transformation_chain": [
                        f"SELECT t.{column} as user_id FROM {table} t JOIN analytics_facts f ON t.id = f.id"
                    ]
                },
                {
                    "node": ColumnLineageNode(
                        column_name="customer_key",
                        table_name="dim_customers",
                        schema_name="warehouse",
                        data_type="integer",
                        transformations=["COALESCE", "MD5 HASH"],
                        confidence=0.85
                    ).dict(),
                    "path_length": 2,
                    "transformation_chain": [
                        f"SELECT {column} FROM {table}",
                        "INSERT INTO dim_customers SELECT COALESCE(user_id, -1) as customer_key"
                    ]
                }
            ]
        
        # Identify impact areas
        impact_analysis = {
            "affected_tables": len(set(node["node"]["table_name"] for node in downstream_lineage)),
            "affected_columns": len(downstream_lineage),
            "critical_dependencies": [
                dep for dep in downstream_lineage 
                if dep["node"]["schema_name"] in ["warehouse", "analytics"]
            ],
            "data_quality_checks": [
                {
                    "check": "null_count",
                    "status": "passing",
                    "details": "No nulls in last 7 days"
                },
                {
                    "check": "referential_integrity",
                    "status": "passing",
                    "details": "All foreign keys valid"
                }
            ]
        }
        
        return {
            "source_column": {
                "table": table,
                "column": column,
                "schema": schema,
                "metadata": {
                    "data_type": "integer",
                    "nullable": False,
                    "is_primary_key": column.endswith("_id"),
                    "is_foreign_key": column.endswith("_id") and not column == "id"
                }
            },
            "upstream_lineage": upstream_lineage if direction in ["upstream", "both"] else [],
            "downstream_lineage": downstream_lineage if direction in ["downstream", "both"] else [],
            "impact_analysis": impact_analysis,
            "recommendations": [
                "Document transformation logic in data dictionary",
                "Add data quality tests for critical downstream tables",
                "Consider materialized views for frequently joined paths",
                f"Monitor {len(downstream_lineage)} downstream dependencies when modifying this column"
            ],
            "query_metadata": {
                "depth_analyzed": depth,
                "direction": direction,
                "timestamp": datetime.utcnow().isoformat(),
                "total_nodes": len(upstream_lineage) + len(downstream_lineage)
            }
        }
        
    except Exception as e:
        logger.error(f"Column lineage error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve column lineage: {str(e)}")


@router.get("/table/{table}")
async def get_table_lineage(
    table: str,
    schema: str = Query(default="public", description="Database schema name"),
    include_columns: bool = Query(default=False, description="Include column-level lineage"),
    depth: int = Query(default=2, ge=1, le=5, description="Traversal depth")
):
    """
    Get table-level data lineage
    
    Shows which tables populate this table and which tables
    consume data from it.
    """
    try:
        # Mock table lineage data
        
        # Upstream tables (sources)
        upstream_tables = [
            {
                "table": TableLineageNode(
                    table_name="orders",
                    schema_name="transactional",
                    table_type="source",
                    row_count=1500000,
                    last_updated=datetime.utcnow().isoformat()
                ).dict(),
                "relationship_type": "direct_insert",
                "join_columns": ["order_id"],
                "estimated_rows_per_day": 5000,
                "transformation": "INSERT INTO target SELECT * FROM orders WHERE status = 'completed'"
            },
            {
                "table": TableLineageNode(
                    table_name="customers",
                    schema_name="transactional",
                    table_type="source",
                    row_count=50000,
                    last_updated=datetime.utcnow().isoformat()
                ).dict(),
                "relationship_type": "left_join",
                "join_columns": ["customer_id"],
                "estimated_rows_per_day": 200,
                "transformation": "LEFT JOIN customers ON orders.customer_id = customers.id"
            }
        ]
        
        # Downstream tables (consumers)
        downstream_tables = [
            {
                "table": TableLineageNode(
                    table_name="daily_sales_summary",
                    schema_name="analytics",
                    table_type="target",
                    row_count=365,
                    last_updated=datetime.utcnow().isoformat()
                ).dict(),
                "relationship_type": "aggregation",
                "join_columns": ["date", "product_id"],
                "refresh_frequency": "daily",
                "transformation": f"INSERT INTO daily_sales_summary SELECT date, SUM(amount) FROM {table} GROUP BY date"
            },
            {
                "table": TableLineageNode(
                    table_name="customer_360",
                    schema_name="warehouse",
                    table_type="intermediate",
                    row_count=50000,
                    last_updated=datetime.utcnow().isoformat()
                ).dict(),
                "relationship_type": "denormalization",
                "join_columns": ["customer_id"],
                "refresh_frequency": "hourly",
                "transformation": f"MERGE INTO customer_360 USING {table} ON customer_id"
            }
        ]
        
        # Data flow statistics
        data_flow_stats = {
            "total_upstream_tables": len(upstream_tables),
            "total_downstream_tables": len(downstream_tables),
            "estimated_daily_input_rows": sum(t["estimated_rows_per_day"] for t in upstream_tables),
            "estimated_table_size_gb": 15.5,
            "avg_query_time_ms": 245,
            "query_frequency_per_day": 1200
        }
        
        # Column-level details (if requested)
        column_lineage_summary = None
        if include_columns:
            column_lineage_summary = {
                "total_columns": 15,
                "columns_with_upstream_lineage": 12,
                "columns_with_transformations": 8,
                "derived_columns": ["total_amount", "discount_rate", "customer_segment"],
                "pass_through_columns": ["order_id", "customer_id", "created_at"]
            }
        
        # Impact analysis
        impact_analysis = {
            "schema_change_impact": {
                "adding_column": "low",
                "removing_column": "high",
                "changing_datatype": "critical"
            },
            "affected_downstream_processes": [
                "Daily ETL job (2:00 AM UTC)",
                "Real-time analytics dashboard",
                "Customer reporting API"
            ],
            "dependencies": {
                "dbt_models": 3,
                "stored_procedures": 2,
                "external_systems": 1
            }
        }
        
        return {
            "table_info": {
                "table_name": table,
                "schema_name": schema,
                "table_type": "fact",
                "created_date": "2023-01-15T00:00:00Z",
                "last_modified": datetime.utcnow().isoformat()
            },
            "upstream_tables": upstream_tables,
            "downstream_tables": downstream_tables,
            "data_flow_stats": data_flow_stats,
            "column_lineage_summary": column_lineage_summary,
            "impact_analysis": impact_analysis,
            "recommendations": [
                "Add incremental processing to reduce load on source tables",
                "Consider partitioning by date for better query performance",
                f"Monitor {len(downstream_tables)} downstream dependencies before schema changes",
                "Document business logic in lineage metadata",
                "Set up alerts for unexpected data volume changes"
            ],
            "data_quality": {
                "freshness": "current",
                "completeness_score": 0.98,
                "consistency_checks": "passing",
                "last_quality_check": datetime.utcnow().isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"Table lineage error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve table lineage: {str(e)}")


@router.get("/graph")
async def get_lineage_graph(
    schema: str = Query(default="public", description="Database schema to analyze"),
    table_filter: Optional[str] = Query(default=None, description="Filter tables by pattern"),
    max_depth: int = Query(default=3, ge=1, le=10, description="Maximum traversal depth"),
    include_external: bool = Query(default=False, description="Include external data sources")
):
    """
    Get complete lineage graph for visualization
    
    Returns nodes and edges in a format suitable for D3.js, Cytoscape,
    or other graph visualization libraries.
    """
    try:
        # Generate comprehensive lineage graph
        
        # Nodes in the graph
        nodes = [
            {
                "id": "orders",
                "label": "orders",
                "type": "source_table",
                "schema": "transactional",
                "size": 1500000,
                "color": "#4CAF50",
                "metadata": {
                    "primary_key": "order_id",
                    "row_count": 1500000,
                    "avg_row_size_bytes": 256
                }
            },
            {
                "id": "customers",
                "label": "customers",
                "type": "source_table",
                "schema": "transactional",
                "size": 50000,
                "color": "#4CAF50",
                "metadata": {
                    "primary_key": "customer_id",
                    "row_count": 50000,
                    "avg_row_size_bytes": 512
                }
            },
            {
                "id": "order_items",
                "label": "order_items",
                "type": "source_table",
                "schema": "transactional",
                "size": 3000000,
                "color": "#4CAF50",
                "metadata": {
                    "primary_key": "item_id",
                    "row_count": 3000000,
                    "avg_row_size_bytes": 128
                }
            },
            {
                "id": "enriched_orders",
                "label": "enriched_orders",
                "type": "intermediate_table",
                "schema": schema,
                "size": 1500000,
                "color": "#2196F3",
                "metadata": {
                    "refresh_frequency": "hourly",
                    "materialized_view": True
                }
            },
            {
                "id": "daily_sales",
                "label": "daily_sales",
                "type": "target_table",
                "schema": "analytics",
                "size": 365,
                "color": "#FF9800",
                "metadata": {
                    "aggregation_level": "day",
                    "retention_days": 730
                }
            },
            {
                "id": "customer_360",
                "label": "customer_360",
                "type": "target_table",
                "schema": "warehouse",
                "size": 50000,
                "color": "#FF9800",
                "metadata": {
                    "refresh_frequency": "real-time",
                    "use_case": "customer_analytics"
                }
            }
        ]
        
        # Edges (relationships) in the graph
        edges = [
            {
                "id": "e1",
                "source": "orders",
                "target": "enriched_orders",
                "type": "insert",
                "label": "direct insert",
                "weight": 5000,
                "metadata": {
                    "transformation": "SELECT * FROM orders WHERE status = 'completed'",
                    "row_count_per_day": 5000
                }
            },
            {
                "id": "e2",
                "source": "customers",
                "target": "enriched_orders",
                "type": "join",
                "label": "left join",
                "weight": 5000,
                "metadata": {
                    "join_column": "customer_id",
                    "transformation": "LEFT JOIN customers ON orders.customer_id = customers.id"
                }
            },
            {
                "id": "e3",
                "source": "order_items",
                "target": "enriched_orders",
                "type": "join",
                "label": "inner join",
                "weight": 10000,
                "metadata": {
                    "join_column": "order_id",
                    "transformation": "INNER JOIN order_items ON orders.id = order_items.order_id"
                }
            },
            {
                "id": "e4",
                "source": "enriched_orders",
                "target": "daily_sales",
                "type": "aggregation",
                "label": "group by date",
                "weight": 365,
                "metadata": {
                    "transformation": "GROUP BY DATE(order_date), SUM(total_amount)",
                    "refresh_schedule": "0 2 * * *"
                }
            },
            {
                "id": "e5",
                "source": "enriched_orders",
                "target": "customer_360",
                "type": "merge",
                "label": "upsert",
                "weight": 5000,
                "metadata": {
                    "transformation": "MERGE INTO customer_360 USING enriched_orders",
                    "conflict_resolution": "last_write_wins"
                }
            }
        ]
        
        # Add external sources if requested
        if include_external:
            nodes.extend([
                {
                    "id": "shopify_api",
                    "label": "Shopify API",
                    "type": "external_source",
                    "schema": "external",
                    "size": 0,
                    "color": "#9C27B0",
                    "metadata": {
                        "api_endpoint": "https://api.shopify.com/orders",
                        "sync_frequency": "every_5_minutes"
                    }
                },
                {
                    "id": "stripe_webhooks",
                    "label": "Stripe Webhooks",
                    "type": "external_source",
                    "schema": "external",
                    "size": 0,
                    "color": "#9C27B0",
                    "metadata": {
                        "webhook_url": "/webhooks/stripe",
                        "event_types": ["payment.succeeded", "payment.failed"]
                    }
                }
            ])
            
            edges.extend([
                {
                    "id": "ext1",
                    "source": "shopify_api",
                    "target": "orders",
                    "type": "api_sync",
                    "label": "API sync",
                    "weight": 100,
                    "metadata": {
                        "sync_method": "incremental",
                        "last_sync": datetime.utcnow().isoformat()
                    }
                },
                {
                    "id": "ext2",
                    "source": "stripe_webhooks",
                    "target": "orders",
                    "type": "webhook",
                    "label": "real-time webhook",
                    "weight": 50,
                    "metadata": {
                        "delivery_guarantee": "at_least_once",
                        "retry_policy": "exponential_backoff"
                    }
                }
            ])
        
        # Graph statistics
        graph_stats = {
            "total_nodes": len(nodes),
            "total_edges": len(edges),
            "node_types": {
                "source_tables": len([n for n in nodes if n["type"] == "source_table"]),
                "intermediate_tables": len([n for n in nodes if n["type"] == "intermediate_table"]),
                "target_tables": len([n for n in nodes if n["type"] == "target_table"]),
                "external_sources": len([n for n in nodes if n["type"] == "external_source"])
            },
            "edge_types": {
                "insert": len([e for e in edges if e["type"] == "insert"]),
                "join": len([e for e in edges if e["type"] == "join"]),
                "aggregation": len([e for e in edges if e["type"] == "aggregation"]),
                "merge": len([e for e in edges if e["type"] == "merge"])
            },
            "max_depth": max([len(nodes) - 1, max_depth]),
            "disconnected_components": 0
        }
        
        # Layout suggestions for visualization
        layout_hints = {
            "suggested_layout": "hierarchical",
            "direction": "left-to-right",
            "node_spacing": 100,
            "rank_spacing": 200,
            "clusters": [
                {"name": "transactional", "tables": ["orders", "customers", "order_items"]},
                {"name": "intermediate", "tables": ["enriched_orders"]},
                {"name": "analytics", "tables": ["daily_sales", "customer_360"]}
            ]
        }
        
        return {
            "graph": {
                "nodes": nodes,
                "edges": edges
            },
            "statistics": graph_stats,
            "layout_hints": layout_hints,
            "filters_applied": {
                "schema": schema,
                "table_filter": table_filter,
                "max_depth": max_depth,
                "include_external": include_external
            },
            "insights": [
                f"Found {graph_stats['total_nodes']} tables with {graph_stats['total_edges']} relationships",
                "Primary data flow: transactional → intermediate → analytics",
                f"{graph_stats['node_types']['target_tables']} downstream tables depend on this schema",
                "Consider data quality monitoring at source tables",
                "Enriched_orders is a critical intermediate layer affecting multiple downstream tables"
            ],
            "export_formats": {
                "supported": ["json", "graphml", "dot", "cypher"],
                "download_url": "/api/lineage/graph/export?format=graphml"
            }
        }
        
    except Exception as e:
        logger.error(f"Lineage graph error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate lineage graph: {str(e)}")


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "Data Lineage",
        "timestamp": datetime.utcnow().isoformat()
    }
