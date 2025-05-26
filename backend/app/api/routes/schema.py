from fastapi import (
    APIRouter,
    HTTPException,
    Response,
    status,
    Request,
    UploadFile,
    File,
    Depends,
    Header,
)
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any

# Assuming ChatService, ChatError, CodeGenerator, CodeGenerationError, SchemaDetector, SchemaValidationError
# will be updated to not rely on MongoDB directly or will use the new DB structure if they need persistence.
from app.services.chat_service import ChatService, ChatError
from app.models.schemas import (
    ChatRequest,  # This might need to be reconciled with the one in chat.py
    ChatResponse,
    SchemaResponse,
    # SchemaRequest, # This was not used in the provided snippet for this file directly
    CodeGenRequest,
    CodeGenResponse,
    SchemaSettings,
)
from ...services.code_generator import CodeGenerator, CodeGenerationError
from ...core.schema_detector import SchemaDetector, SchemaValidationError
from ...config import get_settings

settings = get_settings()

router = APIRouter()
# These services might need to be refactored if they directly used the old MongoDB get_db
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


def create_error_response(
    status_code: int, message: str, details: Optional[Dict[str, Any]] = None
) -> JSONResponse:
    """Create a standardized error response"""
    return JSONResponse(
        status_code=status_code,
        content=ErrorResponse(
            message=message, details=details or {}, status="error"
        ).model_dump(),
    )


def normalize_schema_dict(schema_dict: dict) -> dict:
    # Normalize columns: data_type -> type
    for table in schema_dict.get("tables", []):
        for col in table.get("columns", []):
            if "data_type" in col:
                col["type"] = col.pop("data_type")
    # Normalize relationships: from_table -> source_table, etc.
    rel_key_map = {
        "from_table": "source_table",
        "to_table": "target_table",
        "from_column": "source_column",
        "to_column": "target_column",
    }
    if "relationships" in schema_dict:
        for rel in schema_dict["relationships"]:
            for old, new in rel_key_map.items():
                if old in rel:
                    rel[new] = rel.pop(old)
    return schema_dict


@router.get("/validate-api-key")
async def validate_api_key(x_api_key: Optional[str] = Header(None)):
    """Validate the Gemini API key only (OpenAI removed)"""
    try:
        from ...services.gemini_service import verify_gemini_connection

        api_key = x_api_key or settings.GEMINI_API_KEY
        if settings.USE_GEMINI:
            if not api_key:
                return create_error_response(
                    status.HTTP_400_BAD_REQUEST,
                    "Gemini API key not found or invalid format",
                )
            is_valid, message = await verify_gemini_connection(api_key)
            if is_valid:
                return {
                    "status": "success",
                    "message": message,
                    "ai_provider": "gemini",
                }
            else:
                return create_error_response(
                    status.HTTP_401_UNAUTHORIZED, f"Invalid Gemini API key: {message}"
                )
        else:
            return {
                "status": "success",
                "message": "No AI provider required.",
                "ai_provider": None,
            }
    except Exception as e:
        return create_error_response(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            "Internal error during API key validation",
            {"error": str(e)},
        )


@router.options("/{path:path}")
async def options_route(path: str):
    """Handle CORS preflight requests"""
    return Response(
        status_code=200,
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "POST, GET, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, Authorization",
        },
    )


@router.post("/detect", response_model=SchemaDetectResponse)
async def detect_schema(
    request: SchemaDetectRequest, x_api_key: Optional[str] = Header(None)
):
    """Detect database schema from input data using Gemini AI"""
    if not request.data or not request.data.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Input data cannot be empty"
        )
    try:
        # Assuming schema_detector.detect_from_text is async or can be called in an async context
        # If schema_detector needs to save results, it should be refactored to use the new DB session.
        detected_schema: SchemaResponse = await schema_detector.detect_from_text(
            request.data,
            settings=request.settings,
            api_key=x_api_key,  # Pass API key if needed by the detector
        )
        return SchemaDetectResponse(
            schema=detected_schema, metadata={"source": "text_input"}
        )
    except SchemaValidationError as e:
        return create_error_response(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "Schema validation error",
            {"errors": str(e)},
        )
    except Exception as e:
        # Add logging here
        return create_error_response(
            status.HTTP_500_INTERNAL_SERVER_ERROR, f"Error detecting schema: {str(e)}"
        )


@router.post("/detect-from-file", response_model=SchemaDetectResponse)
async def detect_from_file(
    file: UploadFile = File(...), x_api_key: Optional[str] = Header(None)
):
    """Detect schema from uploaded file (JSON, CSV, etc.)"""
    try:
        contents = await file.read()
        # Assuming schema_detector.detect_from_file_content is async or can be called in an async context
        # If schema_detector needs to save results, it should be refactored.
        detected_schema: SchemaResponse = (
            await schema_detector.detect_from_file_content(
                contents, file.filename, api_key=x_api_key  # Pass API key if needed
            )
        )
        return SchemaDetectResponse(
            schema=detected_schema, metadata={"source_filename": file.filename}
        )
    except SchemaValidationError as e:
        return create_error_response(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "Schema validation error from file",
            {"errors": str(e)},
        )
    except Exception as e:
        # Add logging here
        return create_error_response(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            f"Error detecting schema from file: {str(e)}",
        )


# The /chat endpoint here seems to be a duplicate or older version of the one in chat.py.
# It also uses a ChatRequest model that might differ. For now, I am commenting it out.
# If this is needed, it should be reconciled with app/api/routes/chat.py.
# @router.post("/chat", response_model=ChatResponse)
# async def chat(request: ChatRequest, x_api_key: Optional[str] = Header(None)):
#     """Chat about schema using AI"""
#     try:
#         # response_text, suggestions = await chat_service.chat_with_schema(
#         #     schema_data=request.schema_data.model_dump(),
#         #     messages=[msg.model_dump() for msg in request.messages],
#         #     api_key=x_api_key
#         # )
#         # return ChatResponse(response=response_text, suggestions=suggestions)
#         pass # Placeholder
#     except ChatError as e:
#         return create_error_response(status.HTTP_500_INTERNAL_SERVER_ERROR, f"Chat service error: {str(e)}")
#     except aiohttp.ClientError as e: # aiohttp might not be used directly here anymore
#         return create_error_response(status.HTTP_503_SERVICE_UNAVAILABLE, f"External service error: {str(e)}")
#     except Exception as e:
#         return create_error_response(status.HTTP_500_INTERNAL_SERVER_ERROR, f"Error during chat: {str(e)}")


@router.post("/generate-code", response_model=CodeGenResponse)
async def generate_code(
    request: CodeGenRequest, x_api_key: Optional[str] = Header(None)
) -> CodeGenResponse:
    """Generate code from schema using Gemini AI"""
    try:
        # Assuming code_generator.generate is async or can be called in an async context
        # If code_generator needs to save results or interact with DB, it should be refactored.
        generated_code_response: CodeGenResponse = await code_generator.generate(
            schema_data=request.schema_data,
            target_format=request.format,
            options=request.options,
            api_key=x_api_key,  # Pass API key if needed
        )
        return generated_code_response
    except CodeGenerationError as e:
        return create_error_response(
            status.HTTP_500_INTERNAL_SERVER_ERROR, f"Code generation error: {str(e)}"
        )
    except NotImplementedError as e:
        return create_error_response(status.HTTP_501_NOT_IMPLEMENTED, str(e))
    except Exception as e:
        # Add logging here
        return create_error_response(
            status.HTTP_500_INTERNAL_SERVER_ERROR, f"Error generating code: {str(e)}"
        )
