"""
Template engine for code generation
"""
import logging
from typing import Dict, List, Optional, Any
from pathlib import Path

from .base import APIFramework, ComponentType

logger = logging.getLogger(__name__)

class TemplateEngine:
    """Template engine for API scaffolding generation"""
    
    def __init__(self):
        self.templates = {}
        self._load_default_templates()
    
    def _load_default_templates(self):
        """Load default templates for different frameworks"""
        
        # FastAPI templates
        self.templates[APIFramework.FASTAPI] = {
            ComponentType.MODEL: self._get_fastapi_model_template(),
            ComponentType.CONTROLLER: self._get_fastapi_controller_template(),
            ComponentType.SERVICE: self._get_fastapi_service_template(),
            ComponentType.REPOSITORY: self._get_fastapi_repository_template()
        }
        
        # Django templates
        self.templates[APIFramework.DJANGO] = {
            ComponentType.MODEL: self._get_django_model_template(),
            ComponentType.SERIALIZER: self._get_django_serializer_template(),
            ComponentType.VIEW: self._get_django_view_template(),
            ComponentType.URL: self._get_django_url_template()
        }
        
        # Express templates
        self.templates[APIFramework.EXPRESS] = {
            ComponentType.MODEL: self._get_express_model_template(),
            ComponentType.CONTROLLER: self._get_express_controller_template(),
            ComponentType.ROUTE: self._get_express_route_template(),
            ComponentType.MIDDLEWARE: self._get_express_middleware_template()
        }
    
    def get_template(
        self, 
        framework: APIFramework, 
        component_type: ComponentType
    ) -> Optional[str]:
        """Get template for specific framework and component type"""
        return self.templates.get(framework, {}).get(component_type)
    
    def render_template(
        self,
        template: str,
        context: Dict[str, Any]
    ) -> str:
        """Render template with context variables"""
        try:
            return template.format(**context)
        except KeyError as e:
            logger.error(f"Missing template variable: {e}")
            raise
        except Exception as e:
            logger.error(f"Template rendering error: {e}")
            raise
    
    def _get_fastapi_model_template(self) -> str:
        """FastAPI Pydantic model template"""
        return '''"""
{description}
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
import uuid

{imports}

class {class_name}(BaseModel):
    """Pydantic model for {table_name}"""
{fields}
    
    class Config:
        from_attributes = True
        json_encoders = {{
            datetime: lambda v: v.isoformat(),
        }}

class {class_name}Create(BaseModel):
    """Model for creating {table_name}"""
{create_fields}

class {class_name}Update(BaseModel):
    """Model for updating {table_name}"""
{update_fields}
'''
    
    def _get_fastapi_controller_template(self) -> str:
        """FastAPI router template"""
        return '''"""
{description}
"""
from fastapi import APIRouter, HTTPException, Depends, status
from typing import List
{imports}

router = APIRouter()

{endpoints}
'''
    
    def _get_fastapi_service_template(self) -> str:
        """FastAPI service template"""
        return '''"""
{description}
"""
from typing import List, Optional
{imports}

class {class_name}Service:
    """Service layer for {table_name} operations"""
    
    def __init__(self):
        self.repository = {class_name}Repository()
    
{methods}
'''
    
    def _get_fastapi_repository_template(self) -> str:
        """FastAPI repository template"""
        return '''"""
{description}
"""
from typing import List, Optional
from sqlalchemy.orm import Session
{imports}

class {class_name}Repository:
    """Repository for {table_name} data access"""
    
    def __init__(self):
        pass
    
{methods}
'''
    
    def _get_django_model_template(self) -> str:
        """Django model template"""
        return '''"""
{description}
"""
from django.db import models
{imports}

class {class_name}(models.Model):
    """Django model for {table_name} table"""
{fields}
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = '{table_name}'
        ordering = ['-created_at']
        verbose_name = '{class_name}'
        verbose_name_plural = '{class_name}s'
    
    def __str__(self):
        return f"{class_name} {{self.id}}"
'''
    
    def _get_django_serializer_template(self) -> str:
        """Django REST Framework serializer template"""
        return '''"""
{description}
"""
from rest_framework import serializers
{imports}

class {class_name}Serializer(serializers.ModelSerializer):
    """Serializer for {class_name} model"""
    
    class Meta:
        model = {class_name}
        fields = {fields}
        read_only_fields = ('id', 'created_at', 'updated_at')
    
{methods}
'''
    
    def _get_django_view_template(self) -> str:
        """Django REST Framework view template"""
        return '''"""
{description}
"""
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
{imports}

class {class_name}ViewSet(viewsets.ModelViewSet):
    """ViewSet for {class_name} operations"""
    
    queryset = {class_name}.objects.all()
    serializer_class = {class_name}Serializer
{configuration}
    
{methods}
'''
    
    def _get_django_url_template(self) -> str:
        """Django URL configuration template"""
        return '''"""
{description}
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
{imports}

{url_patterns}
'''
    
    def _get_express_model_template(self) -> str:
        """Express Mongoose model template"""
        return '''/**
 * {description}
 */
const mongoose = require('mongoose');
{imports}

const {schema_name} = new Schema({{
{fields}
}}, {{
  timestamps: true,
  collection: '{table_name}'
}});

{middleware}

const {class_name} = mongoose.model('{class_name}', {schema_name});

module.exports = {class_name};
'''
    
    def _get_express_controller_template(self) -> str:
        """Express controller template"""
        return '''/**
 * {description}
 */
{imports}

{methods}

module.exports = {{
{exports}
}};
'''
    
    def _get_express_route_template(self) -> str:
        """Express route template"""
        return '''/**
 * {description}
 */
const express = require('express');
{imports}

const router = express.Router();

{middleware}

{routes}

module.exports = router;
'''
    
    def _get_express_middleware_template(self) -> str:
        """Express middleware template"""
        return '''/**
 * {description}
 */
{imports}

{middleware_functions}

module.exports = {{
{exports}
}};
'''
    
    def generate_file_structure(
        self,
        framework: APIFramework,
        table_names: List[str],
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, List[str]]:
        """Generate recommended file structure for framework"""
        
        structures = {
            APIFramework.FASTAPI: {
                "models": [f"{table}.py" for table in table_names],
                "controllers": [f"{table}_controller.py" for table in table_names],
                "services": [f"{table}_service.py" for table in table_names],
                "repositories": [f"{table}_repository.py" for table in table_names],
                "schemas": ["__init__.py"],
                "utils": ["database.py", "exceptions.py"],
                "config": ["settings.py"],
                "tests": [f"test_{table}.py" for table in table_names]
            },
            APIFramework.DJANGO: {
                "models": [f"{table}.py" for table in table_names],
                "serializers": [f"{table}_serializers.py" for table in table_names],
                "views": [f"{table}_views.py" for table in table_names],
                "urls": [f"{table}_urls.py" for table in table_names] + ["main.py"],
                "admin": [f"{table}_admin.py" for table in table_names],
                "migrations": ["__init__.py"],
                "tests": [f"test_{table}.py" for table in table_names]
            },
            APIFramework.EXPRESS: {
                "models": [f"{table}.js" for table in table_names],
                "controllers": [f"{table}Controller.js" for table in table_names],
                "routes": [f"{table}.js" for table in table_names],
                "middleware": ["auth.js", "errorHandler.js", "rateLimit.js"],
                "utils": ["ApiError.js", "catchAsync.js"],
                "config": ["database.js", "config.js"],
                "tests": [f"{table}.test.js" for table in table_names]
            }
        }
        
        return structures.get(framework, {})
    
    def generate_package_json(
        self,
        framework: APIFramework,
        project_name: str,
        options: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """Generate package.json for Express projects"""
        
        if framework != APIFramework.EXPRESS:
            return None
        
        return {
            "name": project_name.lower().replace(" ", "-"),
            "version": "1.0.0",
            "description": f"API scaffolding for {project_name}",
            "main": "app.js",
            "scripts": {
                "start": "node app.js",
                "dev": "nodemon app.js",
                "test": "jest",
                "test:watch": "jest --watch",
                "lint": "eslint .",
                "lint:fix": "eslint . --fix"
            },
            "dependencies": {
                "express": "^4.18.2",
                "mongoose": "^7.5.0",
                "express-validator": "^7.0.1",
                "express-rate-limit": "^6.10.0",
                "jsonwebtoken": "^9.0.2",
                "bcryptjs": "^2.4.3",
                "cors": "^2.8.5",
                "helmet": "^7.0.0",
                "morgan": "^1.10.0",
                "dotenv": "^16.3.1"
            },
            "devDependencies": {
                "nodemon": "^3.0.1",
                "jest": "^29.6.4",
                "supertest": "^6.3.3",
                "eslint": "^8.47.0"
            },
            "keywords": ["api", "express", "mongodb", "rest"],
            "author": "",
            "license": "MIT"
        }
    
    def generate_requirements_txt(
        self,
        framework: APIFramework,
        options: Optional[Dict[str, Any]] = None
    ) -> Optional[List[str]]:
        """Generate requirements.txt for Python projects"""
        
        if framework == APIFramework.FASTAPI:
            return [
                "fastapi==0.103.1",
                "uvicorn[standard]==0.23.2",
                "pydantic==2.3.0",
                "sqlalchemy==2.0.20",
                "alembic==1.12.0",
                "python-multipart==0.0.6",
                "python-jose[cryptography]==3.3.0",
                "passlib[bcrypt]==1.7.4",
                "python-dotenv==1.0.0",
                "pytest==7.4.2",
                "pytest-asyncio==0.21.1",
                "httpx==0.24.1"
            ]
        elif framework == APIFramework.DJANGO:
            return [
                "Django==4.2.5",
                "djangorestframework==3.14.0",
                "django-filter==23.3",
                "django-cors-headers==4.2.0",
                "djangorestframework-simplejwt==5.3.0",
                "django-extensions==3.2.3",
                "psycopg2-binary==2.9.7",
                "celery==5.3.2",
                "redis==5.0.0",
                "python-dotenv==1.0.0",
                "pytest-django==4.5.2",
                "factory-boy==3.3.0"
            ]
        
        return None
