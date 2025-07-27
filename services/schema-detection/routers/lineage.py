"""
Data Lineage API Routes

Routes for table and column lineage tracking.
"""
from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
import logging

from ..models.schemas import (
    TableLineageResponse, ColumnLineageResponse, ImpactAnalysisResponse
)
from ..core.lineage import DataLineageGraph

logger = logging.getLogger(__name__)

# Router for lineage endpoints
router = APIRouter(prefix="/lineage", tags=["lineage"])

# Service instance
lineage_graph = DataLineageGraph()


@router.get("/table/{table_name}", response_model=TableLineageResponse)
async def get_table_lineage(table_name: str):
    """Get lineage information for a specific table"""
    try:
        lineage = lineage_graph.get_table_lineage(table_name)
        return lineage
    
    except Exception as e:
        logger.error(f"Table lineage error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/column/{table_name}/{column_name}", response_model=ColumnLineageResponse)
async def get_column_lineage(table_name: str, column_name: str):
    """Get lineage information for a specific column"""
    try:
        lineage = lineage_graph.get_column_lineage(table_name, column_name)
        return lineage
    
    except Exception as e:
        logger.error(f"Column lineage error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/impact-analysis", response_model=ImpactAnalysisResponse)
async def analyze_impact(request: Dict[str, Any]):
    """Analyze the impact of changes to a table or column"""
    try:
        table_name = request.get("table_name")
        column_name = request.get("column_name")
        change_type = request.get("change_type", "modification")
        
        if not table_name:
            raise HTTPException(status_code=400, detail="table_name is required")
        
        impact = lineage_graph.analyze_impact(table_name, column_name, change_type)
        return impact
    
    except Exception as e:
        logger.error(f"Impact analysis error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/add-relationship")
async def add_lineage_relationship(request: Dict[str, Any]):
    """Add a lineage relationship between tables/columns"""
    try:
        source_table = request.get("source_table")
        target_table = request.get("target_table")
        source_column = request.get("source_column")
        target_column = request.get("target_column")
        relationship_type = request.get("relationship_type", "derived_from")
        
        if not all([source_table, target_table]):
            raise HTTPException(
                status_code=400, 
                detail="source_table and target_table are required"
            )
        
        lineage_graph.add_relationship(
            source_table=source_table,
            target_table=target_table,
            source_column=source_column,
            target_column=target_column,
            relationship_type=relationship_type
        )
        
        return {"message": "Lineage relationship added successfully"}
    
    except Exception as e:
        logger.error(f"Add lineage relationship error: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/graph")
async def get_lineage_graph():
    """Get the complete lineage graph"""
    try:
        graph = lineage_graph.get_complete_graph()
        return graph
    
    except Exception as e:
        logger.error(f"Get lineage graph error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/table/{table_name}")
async def remove_table_from_lineage(table_name: str):
    """Remove a table and its relationships from lineage"""
    try:
        lineage_graph.remove_table(table_name)
        return {"message": f"Table {table_name} removed from lineage"}
    
    except Exception as e:
        logger.error(f"Remove table lineage error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
