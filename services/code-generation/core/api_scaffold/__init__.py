"""
API scaffolding generator main module
"""
import logging
from typing import Dict, List, Optional, Any, Union
from pathlib import Path

from models.schemas import SchemaResponse, TableInfo
from .base import APIFramework, ComponentType, APIComponent
from .fastapi_generator import FastAPIGenerator
from .django_generator import DjangoGenerator
from .express_generator import ExpressGenerator
from .template_engine import TemplateEngine

logger = logging.getLogger(__name__)

class APIScaffoldGenerator:
    """Main API scaffolding generator"""
    
    def __init__(self):
        self.generators = {
            APIFramework.FASTAPI: FastAPIGenerator(),
            APIFramework.DJANGO: DjangoGenerator(),
            APIFramework.EXPRESS: ExpressGenerator()
        }
        self.template_engine = TemplateEngine()
    
    def generate_api_scaffold(
        self,
        schema: SchemaResponse,
        framework: APIFramework,
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, List[APIComponent]]:
        """Generate complete API scaffolding for a schema"""
        
        if framework not in self.generators:
            raise ValueError(f"Unsupported framework: {framework}")
        
        generator = self.generators[framework]
        components = {
            "models": [],
            "controllers": [],
            "services": [],
            "routes": [],
            "middleware": [],
            "utilities": []
        }
        
        try:
            # Generate models
            if hasattr(generator, 'generate_models'):
                components["models"] = generator.generate_models(schema, options)
            
            # Generate controllers/views
            if hasattr(generator, 'generate_controllers'):
                components["controllers"] = generator.generate_controllers(schema, options)
            elif hasattr(generator, 'generate_views'):
                components["controllers"] = generator.generate_views(schema, options)
            
            # Generate services (FastAPI)
            if hasattr(generator, 'generate_services'):
                components["services"] = generator.generate_services(schema, options)
            
            # Generate serializers (Django)
            if hasattr(generator, 'generate_serializers'):
                components["serializers"] = generator.generate_serializers(schema, options)
            
            # Generate routes/URLs
            if hasattr(generator, 'generate_routes'):
                components["routes"] = generator.generate_routes(schema, options)
            elif hasattr(generator, 'generate_urls'):
                components["routes"] = generator.generate_urls(schema, options)
            
            # Generate repositories (FastAPI)
            if hasattr(generator, 'generate_repositories'):
                components["repositories"] = generator.generate_repositories(schema, options)
            
            # Generate middleware
            if hasattr(generator, 'generate_middleware'):
                components["middleware"] = generator.generate_middleware(schema, options)
            
            # Generate utility files
            components["utilities"] = self._generate_utilities(framework, schema, options)
            
            logger.info(f"Generated {framework} scaffolding with {sum(len(comps) for comps in components.values())} components")
            
        except Exception as e:
            logger.error(f"Error generating {framework} scaffolding: {e}")
            raise
        
        return components
    
    def _generate_utilities(
        self,
        framework: APIFramework,
        schema: SchemaResponse,
        options: Optional[Dict[str, Any]] = None
    ) -> List[APIComponent]:
        """Generate utility files for the API"""
        
        utilities = []
        
        if framework == APIFramework.FASTAPI:
            utilities.extend(self._generate_fastapi_utilities(schema, options))
        elif framework == APIFramework.DJANGO:
            utilities.extend(self._generate_django_utilities(schema, options))
        elif framework == APIFramework.EXPRESS:
            utilities.extend(self._generate_express_utilities(schema, options))
        
        return utilities
    
    def _generate_fastapi_utilities(
        self,
        schema: SchemaResponse,
        options: Optional[Dict[str, Any]] = None
    ) -> List[APIComponent]:
        """Generate FastAPI utility files"""
        
        utilities = []
        
        # Database configuration
        db_config = APIComponent(
            name="DatabaseConfig",
            component_type=ComponentType.UTILITY,
            framework=APIFramework.FASTAPI,
            content='''"""
Database configuration for FastAPI
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./app.db")

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in SQLALCHEMY_DATABASE_URL else {}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
''',
            file_path="database.py",
            dependencies=["sqlalchemy"],
            imports=["from sqlalchemy import create_engine"],
            metadata={"type": "database"}
        )
        utilities.append(db_config)
        
        # Custom exceptions
        exceptions = APIComponent(
            name="CustomExceptions",
            component_type=ComponentType.UTILITY,
            framework=APIFramework.FASTAPI,
            content='''"""
Custom exceptions for FastAPI
"""
from fastapi import HTTPException, status

class BaseAPIException(HTTPException):
    """Base API exception"""
    pass

class NotFoundError(BaseAPIException):
    """Resource not found exception"""
    def __init__(self, detail: str = "Resource not found"):
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail)

class ValidationError(BaseAPIException):
    """Validation error exception"""
    def __init__(self, detail: str = "Validation failed"):
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)

class AuthenticationError(BaseAPIException):
    """Authentication error exception"""
    def __init__(self, detail: str = "Authentication failed"):
        super().__init__(status_code=status.HTTP_401_UNAUTHORIZED, detail=detail)

class AuthorizationError(BaseAPIException):
    """Authorization error exception"""
    def __init__(self, detail: str = "Access denied"):
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail=detail)
''',
            file_path="exceptions.py",
            dependencies=["fastapi"],
            imports=["from fastapi import HTTPException"],
            metadata={"type": "exceptions"}
        )
        utilities.append(exceptions)
        
        return utilities
    
    def _generate_django_utilities(
        self,
        schema: SchemaResponse,
        options: Optional[Dict[str, Any]] = None
    ) -> List[APIComponent]:
        """Generate Django utility files"""
        
        utilities = []
        
        # Custom permissions
        permissions = APIComponent(
            name="CustomPermissions",
            component_type=ComponentType.UTILITY,
            framework=APIFramework.DJANGO,
            content='''"""
Custom permissions for Django REST Framework
"""
from rest_framework import permissions

class IsOwnerOrReadOnly(permissions.BasePermission):
    """Custom permission to only allow owners to edit objects"""
    
    def has_object_permission(self, request, view, obj):
        # Read permissions for any request
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Write permissions only to the owner
        return obj.owner == request.user

class IsAdminOrReadOnly(permissions.BasePermission):
    """Custom permission to only allow admins to edit objects"""
    
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        
        return request.user and request.user.is_staff
''',
            file_path="utils/permissions.py",
            dependencies=["djangorestframework"],
            imports=["from rest_framework import permissions"],
            metadata={"type": "permissions"}
        )
        utilities.append(permissions)
        
        return utilities
    
    def _generate_express_utilities(
        self,
        schema: SchemaResponse,
        options: Optional[Dict[str, Any]] = None
    ) -> List[APIComponent]:
        """Generate Express utility files"""
        
        utilities = []
        
        # API Error class
        api_error = APIComponent(
            name="APIError",
            component_type=ComponentType.UTILITY,
            framework=APIFramework.EXPRESS,
            content='''/**
 * Custom API Error class
 */
class ApiError extends Error {
  constructor(statusCode, message, errors = null) {
    super(message);
    this.statusCode = statusCode;
    this.errors = errors;
    this.name = 'ApiError';
    
    Error.captureStackTrace(this, this.constructor);
  }
}

module.exports = ApiError;
''',
            file_path="utils/ApiError.js",
            dependencies=[],
            imports=[],
            metadata={"type": "error_handling"}
        )
        utilities.append(api_error)
        
        # Async wrapper
        catch_async = APIComponent(
            name="CatchAsync",
            component_type=ComponentType.UTILITY,
            framework=APIFramework.EXPRESS,
            content='''/**
 * Async wrapper to catch errors
 */
const catchAsync = (fn) => (req, res, next) => {
  Promise.resolve(fn(req, res, next)).catch(next);
};

module.exports = catchAsync;
''',
            file_path="utils/catchAsync.js",
            dependencies=[],
            imports=[],
            metadata={"type": "async_wrapper"}
        )
        utilities.append(catch_async)
        
        return utilities
    
    def generate_project_structure(
        self,
        framework: APIFramework,
        table_names: List[str],
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Generate complete project structure"""
        
        structure = self.template_engine.generate_file_structure(
            framework, table_names, options
        )
        
        # Add configuration files
        config_files = {}
        
        if framework == APIFramework.EXPRESS:
            package_json = self.template_engine.generate_package_json(
                framework, options.get('project_name', 'api-project') if options else 'api-project', options
            )
            if package_json:
                config_files['package.json'] = package_json
        
        elif framework in [APIFramework.FASTAPI, APIFramework.DJANGO]:
            requirements = self.template_engine.generate_requirements_txt(framework, options)
            if requirements:
                config_files['requirements.txt'] = requirements
        
        return {
            "structure": structure,
            "config_files": config_files
        }
    
    def validate_schema(self, schema: SchemaResponse) -> List[str]:
        """Validate schema for API generation"""
        
        issues = []
        
        if not schema.tables:
            issues.append("Schema must contain at least one table")
        
        for table in schema.tables:
            if not table.name:
                issues.append(f"Table missing name")
                continue
            
            if not table.columns:
                issues.append(f"Table '{table.name}' has no columns")
                continue
            
            # Check for ID column
            has_id = any(col.name.lower() in ['id', 'pk'] for col in table.columns)
            if not has_id:
                issues.append(f"Table '{table.name}' should have an ID column")
            
            # Check column names
            for column in table.columns:
                if not column.name:
                    issues.append(f"Column in table '{table.name}' missing name")
                
                if not column.type:
                    issues.append(f"Column '{column.name}' in table '{table.name}' missing type")
        
        return issues
    
    def get_supported_frameworks(self) -> List[APIFramework]:
        """Get list of supported frameworks"""
        return list(self.generators.keys())
    
    def get_framework_features(self, framework: APIFramework) -> Dict[str, bool]:
        """Get features supported by a framework"""
        
        features = {
            APIFramework.FASTAPI: {
                "models": True,
                "controllers": True,
                "services": True,
                "repositories": True,
                "middleware": False,
                "authentication": True,
                "validation": True,
                "async_support": True
            },
            APIFramework.DJANGO: {
                "models": True,
                "serializers": True,
                "views": True,
                "urls": True,
                "admin": True,
                "middleware": False,
                "authentication": True,
                "validation": True,
                "async_support": False
            },
            APIFramework.EXPRESS: {
                "models": True,
                "controllers": True,
                "routes": True,
                "middleware": True,
                "authentication": True,
                "validation": True,
                "async_support": True
            }
        }
        
        return features.get(framework, {})
