"""
FastAPI scaffolding generator
"""
import logging
from typing import Dict, List, Optional, Any

from models.schemas import SchemaResponse, TableInfo, ColumnInfo
from .base import APIComponent, ComponentType, APIFramework, TypeMapper, CodeTemplateEngine

logger = logging.getLogger(__name__)

class FastAPIGenerator:
    """Generates FastAPI scaffolding"""
    
    def __init__(self):
        self.type_mapper = TypeMapper()
        self.template_engine = CodeTemplateEngine()
    
    def generate_models(
        self, 
        schema: SchemaResponse, 
        options: Optional[Dict[str, Any]] = None
    ) -> List[APIComponent]:
        """Generate Pydantic models"""
        components = []
        
        for table in schema.tables:
            model_component = self._generate_pydantic_model(table, schema, options)
            components.append(model_component)
        
        return components
    
    def _generate_pydantic_model(
        self, 
        table: TableInfo, 
        schema: SchemaResponse, 
        options: Optional[Dict[str, Any]] = None
    ) -> APIComponent:
        """Generate a single Pydantic model"""
        
        class_name = self.template_engine.generate_class_name(table.name)
        imports = [
            "from pydantic import BaseModel, Field",
            "from typing import Optional",
            "from datetime import datetime, date, time",
            "import uuid"
        ]
        
        # Generate fields
        fields = []
        for column in table.columns:
            python_type = self.type_mapper.get_python_type(column.type)
            
            # Handle optional fields
            if not getattr(column, 'required', True):
                python_type = f"Optional[{python_type}]"
            
            # Generate field definition
            field_def = f"    {column.name}: {python_type}"
            
            # Add Field validation if needed
            field_constraints = []
            if hasattr(column, 'max_length') and column.max_length:
                field_constraints.append(f"max_length={column.max_length}")
            
            if field_constraints:
                field_def += f" = Field({', '.join(field_constraints)})"
            
            fields.append(field_def)
        
        # Generate model content
        content = f'''"""
{class_name} model for {table.name} table
"""
{self.template_engine.generate_imports(imports)}


class {class_name}(BaseModel):
    """Pydantic model for {table.name}"""
{chr(10).join(fields)}
    
    class Config:
        from_attributes = True
        json_encoders = {{
            datetime: lambda v: v.isoformat(),
            date: lambda v: v.isoformat(),
            time: lambda v: v.isoformat(),
        }}


class {class_name}Create(BaseModel):
    """Model for creating {table.name}"""
{chr(10).join([f for f in fields if not 'id' in f.split(':')[0].strip()])}


class {class_name}Update(BaseModel):
    """Model for updating {table.name}"""
{chr(10).join([f.replace(': ', ': Optional[') + ' = None' if 'Optional' not in f else f + ' = None' for f in fields if not 'id' in f.split(':')[0].strip()])}
'''
        
        return APIComponent(
            name=f"{class_name}Model",
            component_type=ComponentType.MODEL,
            framework=APIFramework.FASTAPI,
            content=content,
            file_path=f"models/{table.name}.py",
            dependencies=["pydantic", "typing"],
            imports=imports,
            metadata={
                "table_name": table.name,
                "class_name": class_name,
                "fields_count": len(table.columns)
            }
        )
    
    def generate_controllers(
        self, 
        schema: SchemaResponse, 
        options: Optional[Dict[str, Any]] = None
    ) -> List[APIComponent]:
        """Generate FastAPI controllers (routers)"""
        components = []
        
        for table in schema.tables:
            controller_component = self._generate_fastapi_controller(table, schema, options)
            components.append(controller_component)
        
        return components
    
    def _generate_fastapi_controller(
        self, 
        table: TableInfo, 
        schema: SchemaResponse, 
        options: Optional[Dict[str, Any]] = None
    ) -> APIComponent:
        """Generate a single FastAPI controller"""
        
        class_name = self.template_engine.generate_class_name(table.name)
        router_name = table.name.lower()
        route_path = self.template_engine.generate_route_path(table.name)
        
        imports = [
            "from fastapi import APIRouter, HTTPException, Depends, status",
            "from typing import List",
            f"from models.{table.name} import {class_name}, {class_name}Create, {class_name}Update",
            f"from services.{table.name}_service import {class_name}Service"
        ]
        
        content = f'''"""
{class_name} API routes
"""
{self.template_engine.generate_imports(imports)}

router = APIRouter()
service = {class_name}Service()


@router.get("{route_path}", response_model=List[{class_name}])
async def get_{router_name}(
    skip: int = 0,
    limit: int = 100
):
    """Get all {table.name} records"""
    try:
        return await service.get_all(skip=skip, limit=limit)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("{route_path}/{{item_id}}", response_model={class_name})
async def get_{router_name}_by_id(item_id: int):
    """Get {table.name} by ID"""
    try:
        item = await service.get_by_id(item_id)
        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"{class_name} not found"
            )
        return item
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("{route_path}", response_model={class_name}, status_code=status.HTTP_201_CREATED)
async def create_{router_name}(item: {class_name}Create):
    """Create new {table.name}"""
    try:
        return await service.create(item)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.put("{route_path}/{{item_id}}", response_model={class_name})
async def update_{router_name}(item_id: int, item: {class_name}Update):
    """Update {table.name}"""
    try:
        updated_item = await service.update(item_id, item)
        if not updated_item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"{class_name} not found"
            )
        return updated_item
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.delete("{route_path}/{{item_id}}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_{router_name}(item_id: int):
    """Delete {table.name}"""
    try:
        success = await service.delete(item_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"{class_name} not found"
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
'''
        
        return APIComponent(
            name=f"{class_name}Controller",
            component_type=ComponentType.CONTROLLER,
            framework=APIFramework.FASTAPI,
            content=content,
            file_path=f"controllers/{table.name}_controller.py",
            dependencies=["fastapi", "typing"],
            imports=imports,
            metadata={
                "table_name": table.name,
                "class_name": class_name,
                "route_path": route_path
            }
        )
    
    def generate_services(
        self, 
        schema: SchemaResponse, 
        options: Optional[Dict[str, Any]] = None
    ) -> List[APIComponent]:
        """Generate service layer components"""
        components = []
        
        for table in schema.tables:
            service_component = self._generate_fastapi_service(table, schema, options)
            components.append(service_component)
        
        return components
    
    def _generate_fastapi_service(
        self, 
        table: TableInfo, 
        schema: SchemaResponse, 
        options: Optional[Dict[str, Any]] = None
    ) -> APIComponent:
        """Generate a single FastAPI service"""
        
        class_name = self.template_engine.generate_class_name(table.name)
        
        imports = [
            "from typing import List, Optional",
            f"from models.{table.name} import {class_name}, {class_name}Create, {class_name}Update",
            f"from repositories.{table.name}_repository import {class_name}Repository"
        ]
        
        content = f'''"""
{class_name} service layer
"""
{self.template_engine.generate_imports(imports)}


class {class_name}Service:
    """Service layer for {table.name} operations"""
    
    def __init__(self):
        self.repository = {class_name}Repository()
    
    async def get_all(self, skip: int = 0, limit: int = 100) -> List[{class_name}]:
        """Get all {table.name} records"""
        return await self.repository.get_all(skip=skip, limit=limit)
    
    async def get_by_id(self, item_id: int) -> Optional[{class_name}]:
        """Get {table.name} by ID"""
        return await self.repository.get_by_id(item_id)
    
    async def create(self, item_data: {class_name}Create) -> {class_name}:
        """Create new {table.name}"""
        return await self.repository.create(item_data)
    
    async def update(self, item_id: int, item_data: {class_name}Update) -> Optional[{class_name}]:
        """Update {table.name}"""
        return await self.repository.update(item_id, item_data)
    
    async def delete(self, item_id: int) -> bool:
        """Delete {table.name}"""
        return await self.repository.delete(item_id)
    
    async def search(self, query: str) -> List[{class_name}]:
        """Search {table.name} records"""
        return await self.repository.search(query)
    
    async def count(self) -> int:
        """Count total {table.name} records"""
        return await self.repository.count()
'''
        
        return APIComponent(
            name=f"{class_name}Service",
            component_type=ComponentType.SERVICE,
            framework=APIFramework.FASTAPI,
            content=content,
            file_path=f"services/{table.name}_service.py",
            dependencies=["typing"],
            imports=imports,
            metadata={
                "table_name": table.name,
                "class_name": class_name
            }
        )
    
    def generate_repositories(
        self, 
        schema: SchemaResponse, 
        options: Optional[Dict[str, Any]] = None
    ) -> List[APIComponent]:
        """Generate repository layer components"""
        components = []
        
        for table in schema.tables:
            repo_component = self._generate_repository(table, schema, options)
            components.append(repo_component)
        
        return components
    
    def _generate_repository(
        self, 
        table: TableInfo, 
        schema: SchemaResponse, 
        options: Optional[Dict[str, Any]] = None
    ) -> APIComponent:
        """Generate a single repository"""
        
        class_name = self.template_engine.generate_class_name(table.name)
        
        imports = [
            "from typing import List, Optional",
            "from sqlalchemy.orm import Session",
            "from sqlalchemy import select, update, delete",
            f"from models.{table.name} import {class_name}, {class_name}Create, {class_name}Update",
            "from database import get_db"
        ]
        
        content = f'''"""
{class_name} repository layer
"""
{self.template_engine.generate_imports(imports)}


class {class_name}Repository:
    """Repository for {table.name} data access"""
    
    def __init__(self):
        pass
    
    async def get_all(self, skip: int = 0, limit: int = 100) -> List[{class_name}]:
        """Get all {table.name} records"""
        # TODO: Implement database query
        pass
    
    async def get_by_id(self, item_id: int) -> Optional[{class_name}]:
        """Get {table.name} by ID"""
        # TODO: Implement database query
        pass
    
    async def create(self, item_data: {class_name}Create) -> {class_name}:
        """Create new {table.name}"""
        # TODO: Implement database insert
        pass
    
    async def update(self, item_id: int, item_data: {class_name}Update) -> Optional[{class_name}]:
        """Update {table.name}"""
        # TODO: Implement database update
        pass
    
    async def delete(self, item_id: int) -> bool:
        """Delete {table.name}"""
        # TODO: Implement database delete
        pass
    
    async def search(self, query: str) -> List[{class_name}]:
        """Search {table.name} records"""
        # TODO: Implement search functionality
        pass
    
    async def count(self) -> int:
        """Count total {table.name} records"""
        # TODO: Implement count query
        pass
'''
        
        return APIComponent(
            name=f"{class_name}Repository",
            component_type=ComponentType.REPOSITORY,
            framework=APIFramework.FASTAPI,
            content=content,
            file_path=f"repositories/{table.name}_repository.py",
            dependencies=["sqlalchemy", "typing"],
            imports=imports,
            metadata={
                "table_name": table.name,
                "class_name": class_name
            }
        )
