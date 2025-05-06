from fastapi import APIRouter, HTTPException, Response, status, Request, UploadFile, File
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import aiohttp
from typing import Optional, Dict, Any
import traceback
from ...services.chat_service import ChatService, ChatError
from ...models.schemas import (
    ChatRequest, 
    ChatResponse, 
    SchemaResponse, 
    SchemaRequest,
    CodeGenRequest, 
    CodeGenResponse,
    SchemaSettings
)
from ...services.code_generator import CodeGenerator, CodeGenerationError
from ...core.schema_detector import SchemaDetector, SchemaValidationError
from ...config import get_settings

settings = get_settings()

router = APIRouter()
chat_service = ChatService()
code_generator = CodeGenerator()
schema_detector = SchemaDetector()

class ErrorResponse(BaseModel):
    message: str
    details: Optional[Dict[str, Any]] = None
    status: str = "error"

class SchemaDetectRequest(BaseModel):
    data: str
    settings: Optional[SchemaSettings] = None

class SchemaDetectResponse(BaseModel):
    schema: SchemaResponse
    metadata: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True  # Updated for Pydantic v2

def create_error_response(status_code: int, message: str, details: Optional[Dict[str, Any]] = None) -> JSONResponse:
    """Create a standardized error response"""
    return JSONResponse(
        status_code=status_code,
        content=ErrorResponse(
            message=message,
            details=details or {},
            status="error"
        ).model_dump()
    )

def normalize_schema_dict(schema_dict: dict) -> dict:
    # Normalize columns: data_type -> type
    for table in schema_dict.get('tables', []):
        for col in table.get('columns', []):
            if 'data_type' in col:
                col['type'] = col.pop('data_type')
    # Normalize relationships: from_table -> source_table, etc.
    rel_key_map = {
        'from_table': 'source_table',
        'to_table': 'target_table',
        'from_column': 'source_column',
        'to_column': 'target_column',
    }
    if 'relationships' in schema_dict:
        for rel in schema_dict['relationships']:
            for old, new in rel_key_map.items():
                if old in rel:
                    rel[new] = rel.pop(old)
    return schema_dict

@router.get("/validate-api-key")
async def validate_api_key():
    """Validate the Gemini API key only (OpenAI removed)"""
    try:
        from ...services.gemini_service import verify_gemini_connection
        if settings.USE_GEMINI:
            if not settings.GEMINI_API_KEY:
                return create_error_response(
                    status.HTTP_400_BAD_REQUEST,
                    "Gemini API key not found or invalid format"
                )
            is_valid, message = await verify_gemini_connection()
            if is_valid:
                return {
                    "status": "success",
                    "message": message,
                    "ai_provider": "gemini"
                }
            else:
                return create_error_response(
                    status.HTTP_401_UNAUTHORIZED,
                    f"Invalid Gemini API key: {message}"
                )
        else:
            return {
                "status": "success",
                "message": "No AI provider required.",
                "ai_provider": None
            }
    except Exception as e:
        return create_error_response(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            "Internal error during API key validation",
            {"error": str(e)}
        )

@router.options("/{path:path}")
async def options_route(path: str):
    """Handle CORS preflight requests"""
    return Response(
        status_code=200,
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "POST, GET, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, Authorization"
        }
    )

@router.post('/detect', response_model=SchemaDetectResponse)
async def detect_schema(request: SchemaDetectRequest):
    """Detect database schema from input data using Gemini AI"""
    if not request.data or not request.data.strip():
        return create_error_response(
            status.HTTP_400_BAD_REQUEST,
            "Input data cannot be empty",
            {"error": "Input data cannot be empty"}
        )
    
    try:
        from ...services.gemini_service import detect_schema_with_gemini
        
        # Use Gemini to detect the schema if USE_GEMINI is enabled
        if settings.USE_GEMINI and settings.GEMINI_API_KEY:
            detected_schema = await detect_schema_with_gemini(request.data)
            detected_schema = normalize_schema_dict(detected_schema)
            
            return SchemaDetectResponse(
                schema=SchemaResponse(**detected_schema),
                metadata={
                    "input_size": len(request.data),
                    "settings_used": request.settings.model_dump() if request.settings else None,
                    "ai_provider": "gemini"
                }
            )
        else:
            # Fallback to existing schema detector if Gemini is not configured
            detector = SchemaDetector(
                settings=request.settings.model_dump() if request.settings else None
            )
            
            # Detect schema from input
            detected_schema = await detector.detect_from_text(request.data)
            detected_schema = normalize_schema_dict(detected_schema)
            
            return SchemaDetectResponse(
                schema=detected_schema,
                metadata={
                    "input_size": len(request.data),
                    "settings_used": request.settings.model_dump() if request.settings else None,
                    "ai_provider": "openai"
                }
            )
    except Exception as e:
        return create_error_response(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            "Schema detection failed",
            {"error": str(e)}
        )

@router.post("/detect-from-file", response_model=SchemaDetectResponse)
async def detect_from_file(file: UploadFile = File(...)):
    """Detect schema from uploaded file (JSON, CSV, etc.)"""
    try:
        content = await file.read()
        text = content.decode("utf-8")
        from ...services.gemini_service import detect_schema_with_gemini
        if settings.USE_GEMINI and settings.GEMINI_API_KEY:
            detected_schema = await detect_schema_with_gemini(text)
            detected_schema = normalize_schema_dict(detected_schema)
            return SchemaDetectResponse(
                schema=SchemaResponse(**detected_schema),
                metadata={
                    "input_size": len(text),
                    "filename": file.filename,
                    "ai_provider": "gemini"
                }
            )
        else:
            detector = SchemaDetector()
            detected_schema = await detector.detect_from_text(text)
            detected_schema = normalize_schema_dict(detected_schema)
            return SchemaDetectResponse(
                schema=SchemaResponse(**detected_schema),
                metadata={
                    "input_size": len(text),
                    "filename": file.filename,
                    "ai_provider": "fallback"
                }
            )
    except Exception as e:
        print("[detect-from-file] Exception:", str(e))
        print(traceback.format_exc())
        return create_error_response(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            "Schema detection from file failed",
            {"error": str(e), "traceback": traceback.format_exc()}
        )

@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Chat about schema using AI"""
    try:
        if not request.messages:
            return create_error_response(
                status.HTTP_400_BAD_REQUEST,
                "No messages provided"
            )

        if not request.messages[-1].get("content"):
            return create_error_response(
                status.HTTP_400_BAD_REQUEST,
                "Last message has no content"
            )

        response = await chat_service.get_response(
            schema=request.schema_data,
            messages=request.messages,
            question=request.messages[-1]["content"]
        )
        return response
    except ChatError as e:
        return create_error_response(
            status.HTTP_400_BAD_REQUEST,
            str(e)
        )
    except aiohttp.ClientError as e:
        return create_error_response(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            "AI service is currently unavailable",
            {"error": str(e)}
        )
    except Exception as e:
        return create_error_response(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            "Internal server error in chat service",
            {"error": str(e)}
        )

@router.post("/generate-code", response_model=CodeGenResponse)
async def generate_code(request: CodeGenRequest) -> CodeGenResponse:
    """Generate code from schema using Gemini AI"""
    try:
        if settings.USE_GEMINI and settings.GEMINI_API_KEY:
            # Use Gemini for code generation
            from ...services.gemini_service import generate_code_with_gemini
            
            code = await generate_code_with_gemini(
                schema=request.schema_data,
                format=request.format.value if hasattr(request.format, 'value') else request.format,
                options=request.options
            )
            
            return CodeGenResponse(
                code=code,
                language=request.format.value if hasattr(request.format, 'value') else request.format,
                metadata={
                    "format": request.format,
                    "options": request.options,
                    "ai_provider": "gemini"
                }
            )
        else:
            # Fallback to existing code generator
            code = await code_generator.generate_code(
                schema=request.schema_data,
                format=request.format,
                options=request.options
            )
            return CodeGenResponse(
                code=code,
                language=request.format.value,
                metadata={
                    "format": request.format,
                    "options": request.options,
                    "ai_provider": "openai"
                }
            )
    except CodeGenerationError as e:
        return create_error_response(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            str(e),
            {
                "format": e.format,
                "details": e.details
            }
        )
    except NotImplementedError as e:
        return create_error_response(
            status.HTTP_501_NOT_IMPLEMENTED,
            str(e),
            {"format": request.format}
        )
    except Exception as e:
        return create_error_response(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            "Failed to generate code",
            {"error": str(e)}
        )