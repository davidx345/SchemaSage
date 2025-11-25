"""
Glossary and Schema Management API Routes

Routes for managing business glossary terms and schema consistency checks.
"""
from fastapi import APIRouter, HTTPException, Body
from typing import List, Dict, Any

from models.schemas import (
    GlossaryTerm, GlossaryRequest, GlossaryResponse,
    SchemaConsistencyCheckRequest, SchemaConsistencyCheckResponse
)

# Router for glossary management
router = APIRouter(tags=["glossary", "schema"])

# Simple in-memory storage for demonstration
glossary_terms = {}


@router.get("/glossary", response_model=GlossaryResponse)
async def list_glossary_terms():
    """List all glossary terms"""
    terms = list(glossary_terms.values())
    return GlossaryResponse(terms=terms, total=len(terms))


@router.post("/glossary")
async def add_glossary_term(term: GlossaryRequest):
    """Add a new glossary term"""
    term_id = f"term_{len(glossary_terms) + 1}"
    glossary_term = GlossaryTerm(
        id=term_id,
        name=term.name,
        definition=term.definition,
        category=term.category,
        tags=term.tags or [],
        examples=term.examples or [],
        related_terms=term.related_terms or []
    )
    glossary_terms[term_id] = glossary_term
    return {"id": term_id, "term": glossary_term}


@router.put("/glossary/{term_id}")
async def update_glossary_term(term_id: str, term: GlossaryRequest):
    """Update an existing glossary term"""
    if term_id not in glossary_terms:
        raise HTTPException(status_code=404, detail="Glossary term not found")
    
    updated_term = GlossaryTerm(
        id=term_id,
        name=term.name,
        definition=term.definition,
        category=term.category,
        tags=term.tags or [],
        examples=term.examples or [],
        related_terms=term.related_terms or []
    )
    glossary_terms[term_id] = updated_term
    return {"id": term_id, "term": updated_term}


@router.delete("/glossary/{term_id}")
async def delete_glossary_term(term_id: str):
    """Delete a glossary term"""
    if term_id not in glossary_terms:
        raise HTTPException(status_code=404, detail="Glossary term not found")
    
    deleted_term = glossary_terms.pop(term_id)
    return {"message": "Glossary term deleted", "deleted_term": deleted_term}


@router.post("/schema/consistency-check", response_model=SchemaConsistencyCheckResponse)
async def check_schema_consistency(request: SchemaConsistencyCheckRequest):
    """Check schema consistency across multiple schemas"""
    issues = []
    warnings = []
    
    # Basic consistency checks
    schemas = request.schemas
    
    # Check for duplicate field names with different types
    field_types = {}
    for schema_name, schema_def in schemas.items():
        if isinstance(schema_def, dict) and "properties" in schema_def:
            for field_name, field_def in schema_def["properties"].items():
                field_type = field_def.get("type", "unknown")
                if field_name in field_types:
                    if field_types[field_name] != field_type:
                        issues.append({
                            "type": "type_mismatch",
                            "field": field_name,
                            "schemas": [s for s in schemas.keys() if field_name in schemas[s].get("properties", {})],
                            "message": f"Field '{field_name}' has different types across schemas"
                        })
                else:
                    field_types[field_name] = field_type
    
    # Check for naming convention issues
    for schema_name, schema_def in schemas.items():
        if isinstance(schema_def, dict) and "properties" in schema_def:
            for field_name in schema_def["properties"].keys():
                # Check for snake_case vs camelCase inconsistency
                if "_" in field_name and any(c.isupper() for c in field_name):
                    warnings.append({
                        "type": "naming_convention",
                        "field": field_name,
                        "schema": schema_name,
                        "message": f"Field '{field_name}' mixes snake_case and camelCase"
                    })
    
    # Calculate consistency score
    total_checks = len(field_types) + sum(len(s.get("properties", {})) for s in schemas.values())
    total_issues = len(issues) + len(warnings)
    consistency_score = max(0, (total_checks - total_issues) / total_checks) if total_checks > 0 else 1.0
    
    return SchemaConsistencyCheckResponse(
        consistent=len(issues) == 0,
        consistency_score=consistency_score,
        issues=issues,
        warnings=warnings,
        summary={
            "total_schemas": len(schemas),
            "total_fields": len(field_types),
            "critical_issues": len(issues),
            "warnings": len(warnings)
        }
    )
