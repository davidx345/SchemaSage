"""Shared models for SchemaSage microservices."""

from .base import BaseModel, BaseResponse, ErrorResponse
from .schema import SchemaModel, TableModel, ColumnModel, RelationshipModel, CodeGenerationRequest, CodeGenerationResponse
from .project import ProjectModel, ProjectResponse, ProjectCreateRequest, ProjectUpdateRequest
from .user import UserModel, UserResponse, UserLoginRequest, UserRegisterRequest, AuthTokenResponse
from .file import FileModel, FileResponse, FileUploadRequest, FileProcessingRequest
from .chat import ChatSessionModel, ChatMessageModel, ChatSessionCreateRequest, ChatMessageCreateRequest
from .integration import IntegrationModel, IntegrationCreateRequest, IntegrationUpdateRequest, IntegrationTestResponse

__all__ = [
    # Base models
    "BaseModel",
    "BaseResponse", 
    "ErrorResponse",
    
    # Schema models
    "SchemaModel",
    "TableModel",
    "ColumnModel", 
    "RelationshipModel",
    "CodeGenerationRequest",
    "CodeGenerationResponse",
    
    # Project models
    "ProjectModel",
    "ProjectResponse",
    "ProjectCreateRequest",
    "ProjectUpdateRequest",
    
    # User models
    "UserModel",
    "UserResponse",
    "UserLoginRequest",
    "UserRegisterRequest",
    "AuthTokenResponse",
    
    # File models
    "FileModel",
    "FileResponse",
    "FileUploadRequest",
    "FileProcessingRequest",
    
    # Chat models
    "ChatSessionModel",
    "ChatMessageModel",
    "ChatSessionCreateRequest",
    "ChatMessageCreateRequest",
    
    # Integration models
    "IntegrationModel",
    "IntegrationCreateRequest",
    "IntegrationUpdateRequest",
    "IntegrationTestResponse"
]
