"""
SQL Dialect Translator Router

Endpoint: POST /api/code/translate-sql
"""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
import logging
from datetime import datetime

from models.translation_models import (
    TranslationRequest,
    TranslationResponse,
    ErrorResponse
)
from core.translation.translator import translate_sql
from core.auth import get_current_user_optional

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/code", tags=["sql-translation"])


@router.post("/translate-sql", response_model=TranslationResponse)
async def translate_sql_dialect(
    request: TranslationRequest,
    user_id: int = Depends(get_current_user_optional)
):
    """
    Translate SQL query between different database dialects
    
    Args:
        request: SQL translation request
        user_id: Optional authenticated user ID
        
    Returns:
        TranslationResponse with translated query, syntax changes, and warnings
    """
    try:
        logger.info(
            f"Translating SQL for user {user_id}: "
            f"{request.source_dialect} -> {request.target_dialect}, "
            f"query length: {len(request.sql_query)}"
        )
        
        # Translate SQL
        translated_query, compatibility_level, statistics, syntax_changes, warnings, notes = translate_sql(request)
        
        # Build response
        response = TranslationResponse(
            success=True,
            original_query=request.sql_query,
            translated_query=translated_query,
            compatibility_level=compatibility_level,
            statistics=statistics,
            syntax_changes=syntax_changes,
            warnings=warnings,
            notes=notes,
            timestamp=datetime.utcnow()
        )
        
        logger.info(
            f"SQL translation complete: {compatibility_level.value}, "
            f"{statistics.syntax_changes} changes, "
            f"{statistics.warnings_count} warnings, "
            f"confidence={statistics.confidence_score}%"
        )
        
        return response
        
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        error_response = ErrorResponse(
            error="Validation error",
            details=str(e)
        )
        return JSONResponse(
            status_code=400,
            content=error_response.dict()
        )
        
    except Exception as e:
        logger.error(f"Error translating SQL: {e}", exc_info=True)
        error_response = ErrorResponse(
            error="Failed to translate SQL",
            details=str(e)
        )
        return JSONResponse(
            status_code=500,
            content=error_response.dict()
        )


@router.get("/translate-sql/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "sql-dialect-translator"}
