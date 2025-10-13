"""
Additional Code Generation API Routes

Additional routes for alternative code generation methods and scaffolding.
"""
from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Optional, List, Dict, Any
import logging
from datetime import datetime

from models.schemas import CodeGenerationRequest, CodeGenerationResponse
from core.code_generator import CodeGenerator

logger = logging.getLogger(__name__)

# Router for additional generation endpoints
router = APIRouter(prefix="/schema", tags=["schema_generation"])

# Service instance
code_generator = CodeGenerator()


@router.post("/generate-code")
async def generate_code_alternative(
    schema_data: Dict[str, Any],
    format: str = "typescript",
    options: Optional[Dict[str, Any]] = None
):
    """Alternative code generation endpoint for schema-based generation"""
    try:
        # Mock code generation for various formats
        generated_code = ""
        metadata = {}
        
        tables = schema_data.get("tables", [])
        
        if format == "typescript":
            # Generate TypeScript interfaces
            generated_code = "// TypeScript Interfaces\\n\\n"
            for table in tables:
                table_name = table.get("table_name", "UnknownTable")
                class_name = _to_pascal_case(table_name)
                
                generated_code += f"export interface {class_name} {{\\n"
                
                for column in table.get("columns", []):
                    col_name = column.get("column_name", "unknown")
                    col_type = _map_to_typescript_type(column.get("data_type", "string"))
                    nullable = column.get("is_nullable", True)
                    
                    generated_code += f"  {col_name}: {col_type}{'?' if nullable else ''};\\n"
                
                generated_code += f"}}\\n\\n"
                
                # Create type for creating new records (without auto-generated fields)
                generated_code += f"export interface Create{class_name} {{\\n"
                for column in table.get("columns", []):
                    if not column.get("is_primary_key", False):
                        col_name = column.get("column_name", "unknown")
                        col_type = _map_to_typescript_type(column.get("data_type", "string"))
                        nullable = column.get("is_nullable", True)
                        
                        generated_code += f"  {col_name}: {col_type}{'?' if nullable else ''};\\n"
                
                generated_code += f"}}\\n\\n"
            
            metadata = {
                "interfaces_generated": len(tables) * 2,
                "typescript_version": "4.5+",
                "includes_create_types": True
            }
        
        elif format == "python":
            # Generate Python dataclasses
            generated_code = "from dataclasses import dataclass\\nfrom typing import Optional\\nfrom datetime import datetime\\n\\n"
            
            for table in tables:
                table_name = table.get("table_name", "UnknownTable")
                class_name = _to_pascal_case(table_name)
                
                generated_code += f"@dataclass\\nclass {class_name}:\\n"
                
                for column in table.get("columns", []):
                    col_name = column.get("column_name", "unknown")
                    col_type = _map_to_python_type(column.get("data_type", "str"))
                    nullable = column.get("is_nullable", True)
                    
                    if nullable and col_type != "Optional":
                        col_type = f"Optional[{col_type}]"
                    
                    generated_code += f"    {col_name}: {col_type}\\n"
                
                generated_code += f"\\n"
            
            metadata = {
                "classes_generated": len(tables),
                "python_version": "3.7+",
                "uses_dataclasses": True
            }
        
        elif format == "java":
            # Generate Java classes
            generated_code = "// Java Classes\\n\\n"
            
            for table in tables:
                table_name = table.get("table_name", "UnknownTable")
                class_name = _to_pascal_case(table_name)
                
                generated_code += f"public class {class_name} {{\\n"
                
                # Fields
                for column in table.get("columns", []):
                    col_name = column.get("column_name", "unknown")
                    col_type = _map_to_java_type(column.get("data_type", "String"))
                    
                    generated_code += f"    private {col_type} {col_name};\\n"
                
                generated_code += f"\\n"
                
                # Constructor
                generated_code += f"    public {class_name}() {{}}\\n\\n"
                
                # Getters and setters
                for column in table.get("columns", []):
                    col_name = column.get("column_name", "unknown")
                    col_type = _map_to_java_type(column.get("data_type", "String"))
                    getter_name = f"get{_to_pascal_case(col_name)}"
                    setter_name = f"set{_to_pascal_case(col_name)}"
                    
                    generated_code += f"    public {col_type} {getter_name}() {{\\n"
                    generated_code += f"        return {col_name};\\n"
                    generated_code += f"    }}\\n\\n"
                    
                    generated_code += f"    public void {setter_name}({col_type} {col_name}) {{\\n"
                    generated_code += f"        this.{col_name} = {col_name};\\n"
                    generated_code += f"    }}\\n\\n"
                
                generated_code += f"}}\\n\\n"
            
            metadata = {
                "classes_generated": len(tables),
                "java_version": "8+",
                "includes_getters_setters": True
            }
        
        elif format == "csharp":
            # Generate C# classes
            generated_code = "using System;\\nusing System.ComponentModel.DataAnnotations;\\n\\n"
            
            for table in tables:
                table_name = table.get("table_name", "UnknownTable")
                class_name = _to_pascal_case(table_name)
                
                generated_code += f"public class {class_name}\\n{{\\n"
                
                for column in table.get("columns", []):
                    col_name = _to_pascal_case(column.get("column_name", "unknown"))
                    col_type = _map_to_csharp_type(column.get("data_type", "string"))
                    nullable = column.get("is_nullable", True)
                    is_key = column.get("is_primary_key", False)
                    
                    if is_key:
                        generated_code += f"    [Key]\\n"
                    
                    if not nullable:
                        generated_code += f"    [Required]\\n"
                    
                    if nullable and col_type not in ["string"]:
                        col_type += "?"
                    
                    generated_code += f"    public {col_type} {col_name} {{ get; set; }}\\n\\n"
                
                generated_code += f"}}\\n\\n"
            
            metadata = {
                "classes_generated": len(tables),
                "csharp_version": "8.0+",
                "includes_annotations": True
            }
        
        else:
            # Default JSON schema
            generated_code = "{\\n"
            generated_code += f'  "title": "Generated Schema",\\n'
            generated_code += f'  "type": "object",\\n'
            generated_code += f'  "properties": {{\\n'
            
            for i, table in enumerate(tables):
                table_name = table.get("table_name", "UnknownTable")
                generated_code += f'    "{table_name}": {{\\n'
                generated_code += f'      "type": "object",\\n'
                generated_code += f'      "properties": {{\\n'
                
                for j, column in enumerate(table.get("columns", [])):
                    col_name = column.get("column_name", "unknown")
                    col_type = _map_to_json_type(column.get("data_type", "string"))
                    
                    generated_code += f'        "{col_name}": {{"type": "{col_type}"}}'
                    if j < len(table.get("columns", [])) - 1:
                        generated_code += ","
                    generated_code += "\\n"
                
                generated_code += f'      }}\\n'
                generated_code += f'    }}'
                if i < len(tables) - 1:
                    generated_code += ","
                generated_code += "\\n"
            
            generated_code += f'  }}\\n'
            generated_code += f'}}\\n'
            
            metadata = {
                "schema_format": "JSON Schema",
                "objects_generated": len(tables)
            }
        
        return {
            "generated_code": generated_code,
            "format": format,
            "metadata": metadata,
            "options_applied": options or {},
            "generation_stats": {
                "tables_processed": len(tables),
                "total_columns": sum(len(table.get("columns", [])) for table in tables),
                "generation_time_ms": 150,
                "code_lines": len(generated_code.split("\\n"))
            },
            "generated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Alternative code generation error: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate code")


@router.post("/scaffold")
async def generate_api_scaffolding(request_data: Dict[str, Any]):
    """Generate API scaffolding from schema"""
    try:
        # Extract data from request body to match frontend format
        schema_data = request_data.get("schema", {})
        framework = request_data.get("format", "fastapi")  # frontend sends "format", not "framework"
        options = request_data.get("options", {})
        
        tables = schema_data.get("tables", [])
        
        scaffolding_files = []
        
        if framework == "fastapi":
            # Generate FastAPI scaffolding
            
            # Models file
            models_content = _generate_fastapi_models(tables)
            scaffolding_files.append({
                "filename": "models.py",
                "content": models_content,
                "type": "model",
                "description": "Pydantic models for API"
            })
            
            # Router files
            for table in tables:
                table_name = table.get("table_name", "unknown")
                router_content = _generate_fastapi_router(table)
                scaffolding_files.append({
                    "filename": f"routers/{table_name}.py",
                    "content": router_content,
                    "type": "router",
                    "description": f"API routes for {table_name}"
                })
            
            # Main application file
            main_content = _generate_fastapi_main(tables)
            scaffolding_files.append({
                "filename": "main.py",
                "content": main_content,
                "type": "application",
                "description": "Main FastAPI application"
            })
            
            # Requirements file
            requirements_content = _generate_fastapi_requirements()
            scaffolding_files.append({
                "filename": "requirements.txt",
                "content": requirements_content,
                "type": "dependency",
                "description": "Python dependencies"
            })
        
        elif framework == "express":
            # Generate Express.js scaffolding
            
            # Models
            for table in tables:
                table_name = table.get("table_name", "unknown")
                model_content = _generate_express_model(table)
                scaffolding_files.append({
                    "filename": f"models/{table_name}.js",
                    "content": model_content,
                    "type": "model",
                    "description": f"Mongoose model for {table_name}"
                })
            
            # Routes
            for table in tables:
                table_name = table.get("table_name", "unknown")
                routes_content = _generate_express_routes(table)
                scaffolding_files.append({
                    "filename": f"routes/{table_name}.js",
                    "content": routes_content,
                    "type": "router",
                    "description": f"Express routes for {table_name}"
                })
            
            # Main app file
            app_content = _generate_express_app(tables)
            scaffolding_files.append({
                "filename": "app.js",
                "content": app_content,
                "type": "application",
                "description": "Main Express application"
            })
            
            # Package.json
            package_content = _generate_express_package()
            scaffolding_files.append({
                "filename": "package.json",
                "content": package_content,
                "type": "dependency",
                "description": "Node.js dependencies"
            })
        
        elif framework == "spring":
            # Generate Spring Boot scaffolding
            
            # Entity classes
            for table in tables:
                table_name = table.get("table_name", "unknown")
                entity_content = _generate_spring_entity(table)
                class_name = _to_pascal_case(table_name)
                scaffolding_files.append({
                    "filename": f"src/main/java/com/example/entity/{class_name}.java",
                    "content": entity_content,
                    "type": "entity",
                    "description": f"JPA entity for {table_name}"
                })
            
            # Repository interfaces
            for table in tables:
                table_name = table.get("table_name", "unknown")
                repo_content = _generate_spring_repository(table)
                class_name = _to_pascal_case(table_name)
                scaffolding_files.append({
                    "filename": f"src/main/java/com/example/repository/{class_name}Repository.java",
                    "content": repo_content,
                    "type": "repository",
                    "description": f"JPA repository for {table_name}"
                })
            
            # Controller classes
            for table in tables:
                table_name = table.get("table_name", "unknown")
                controller_content = _generate_spring_controller(table)
                class_name = _to_pascal_case(table_name)
                scaffolding_files.append({
                    "filename": f"src/main/java/com/example/controller/{class_name}Controller.java",
                    "content": controller_content,
                    "type": "controller",
                    "description": f"REST controller for {table_name}"
                })
        
        return {
            "framework": framework,
            "scaffolding_files": scaffolding_files,
            "generation_summary": {
                "total_files": len(scaffolding_files),
                "file_types": list(set(f["type"] for f in scaffolding_files)),
                "tables_processed": len(tables),
                "estimated_lines_of_code": sum(len(f["content"].split("\\n")) for f in scaffolding_files)
            },
            "options_applied": options,
            "next_steps": [
                "Review generated files",
                "Install dependencies",
                "Configure database connection",
                "Run and test the application"
            ],
            "generated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"API scaffolding generation error: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate API scaffolding")


def _to_pascal_case(snake_str: str) -> str:
    """Convert snake_case to PascalCase"""
    return ''.join(word.capitalize() for word in snake_str.split('_'))


def _map_to_typescript_type(sql_type: str) -> str:
    """Map SQL types to TypeScript types"""
    type_mapping = {
        'INTEGER': 'number',
        'BIGINT': 'number',
        'DECIMAL': 'number',
        'FLOAT': 'number',
        'DOUBLE': 'number',
        'VARCHAR': 'string',
        'TEXT': 'string',
        'CHAR': 'string',
        'BOOLEAN': 'boolean',
        'TIMESTAMP': 'Date',
        'DATETIME': 'Date',
        'DATE': 'Date',
        'JSON': 'object',
        'JSONB': 'object'
    }
    
    sql_type_upper = sql_type.upper().split('(')[0]  # Remove size specifications
    return type_mapping.get(sql_type_upper, 'string')


def _map_to_python_type(sql_type: str) -> str:
    """Map SQL types to Python types"""
    type_mapping = {
        'INTEGER': 'int',
        'BIGINT': 'int',
        'DECIMAL': 'float',
        'FLOAT': 'float',
        'DOUBLE': 'float',
        'VARCHAR': 'str',
        'TEXT': 'str',
        'CHAR': 'str',
        'BOOLEAN': 'bool',
        'TIMESTAMP': 'datetime',
        'DATETIME': 'datetime',
        'DATE': 'datetime',
        'JSON': 'dict',
        'JSONB': 'dict'
    }
    
    sql_type_upper = sql_type.upper().split('(')[0]
    return type_mapping.get(sql_type_upper, 'str')


def _map_to_java_type(sql_type: str) -> str:
    """Map SQL types to Java types"""
    type_mapping = {
        'INTEGER': 'Integer',
        'BIGINT': 'Long',
        'DECIMAL': 'BigDecimal',
        'FLOAT': 'Float',
        'DOUBLE': 'Double',
        'VARCHAR': 'String',
        'TEXT': 'String',
        'CHAR': 'String',
        'BOOLEAN': 'Boolean',
        'TIMESTAMP': 'LocalDateTime',
        'DATETIME': 'LocalDateTime',
        'DATE': 'LocalDate',
        'JSON': 'String',
        'JSONB': 'String'
    }
    
    sql_type_upper = sql_type.upper().split('(')[0]
    return type_mapping.get(sql_type_upper, 'String')


def _map_to_csharp_type(sql_type: str) -> str:
    """Map SQL types to C# types"""
    type_mapping = {
        'INTEGER': 'int',
        'BIGINT': 'long',
        'DECIMAL': 'decimal',
        'FLOAT': 'float',
        'DOUBLE': 'double',
        'VARCHAR': 'string',
        'TEXT': 'string',
        'CHAR': 'string',
        'BOOLEAN': 'bool',
        'TIMESTAMP': 'DateTime',
        'DATETIME': 'DateTime',
        'DATE': 'DateTime',
        'JSON': 'string',
        'JSONB': 'string'
    }
    
    sql_type_upper = sql_type.upper().split('(')[0]
    return type_mapping.get(sql_type_upper, 'string')


def _map_to_json_type(sql_type: str) -> str:
    """Map SQL types to JSON Schema types"""
    type_mapping = {
        'INTEGER': 'integer',
        'BIGINT': 'integer',
        'DECIMAL': 'number',
        'FLOAT': 'number',
        'DOUBLE': 'number',
        'VARCHAR': 'string',
        'TEXT': 'string',
        'CHAR': 'string',
        'BOOLEAN': 'boolean',
        'TIMESTAMP': 'string',
        'DATETIME': 'string',
        'DATE': 'string',
        'JSON': 'object',
        'JSONB': 'object'
    }
    
    sql_type_upper = sql_type.upper().split('(')[0]
    return type_mapping.get(sql_type_upper, 'string')


def _generate_fastapi_models(tables: List[Dict]) -> str:
    """Generate FastAPI Pydantic models"""
    content = "from pydantic import BaseModel\\nfrom typing import Optional\\nfrom datetime import datetime\\n\\n"
    
    for table in tables:
        table_name = table.get("table_name", "unknown")
        class_name = _to_pascal_case(table_name)
        
        content += f"class {class_name}(BaseModel):\\n"
        
        for column in table.get("columns", []):
            col_name = column.get("column_name", "unknown")
            col_type = _map_to_python_type(column.get("data_type", "str"))
            nullable = column.get("is_nullable", True)
            
            if nullable:
                content += f"    {col_name}: Optional[{col_type}] = None\\n"
            else:
                content += f"    {col_name}: {col_type}\\n"
        
        content += f"\\n    class Config:\\n"
        content += f"        from_attributes = True\\n\\n"
    
    return content


def _generate_fastapi_router(table: Dict) -> str:
    """Generate FastAPI router for a table"""
    table_name = table.get("table_name", "unknown")
    class_name = _to_pascal_case(table_name)
    
    content = f"""from fastapi import APIRouter, HTTPException, Depends
from typing import List
from models import {class_name}

router = APIRouter(prefix="/{table_name}", tags=["{table_name}"])

@router.get("/", response_model=List[{class_name}])
async def get_{table_name}():
    # TODO: Implement get all {table_name}
    return []

@router.get("/{{item_id}}", response_model={class_name})
async def get_{table_name.rstrip('s')}(item_id: int):
    # TODO: Implement get single {table_name.rstrip('s')}
    raise HTTPException(status_code=404, detail="Item not found")

@router.post("/", response_model={class_name})
async def create_{table_name.rstrip('s')}(item: {class_name}):
    # TODO: Implement create {table_name.rstrip('s')}
    return item

@router.put("/{{item_id}}", response_model={class_name})
async def update_{table_name.rstrip('s')}(item_id: int, item: {class_name}):
    # TODO: Implement update {table_name.rstrip('s')}
    return item

@router.delete("/{{item_id}}")
async def delete_{table_name.rstrip('s')}(item_id: int):
    # TODO: Implement delete {table_name.rstrip('s')}
    return {{"message": "Item deleted successfully"}}
"""
    return content


def _generate_fastapi_main(tables: List[Dict]) -> str:
    """Generate FastAPI main application file"""
    content = """from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

"""
    
    # Import routers
    for table in tables:
        table_name = table.get("table_name", "unknown")
        content += f"from routers import {table_name}\\n"
    
    content += """
app = FastAPI(title="Generated API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

"""
    
    # Include routers
    for table in tables:
        table_name = table.get("table_name", "unknown")
        content += f"app.include_router({table_name}.router)\\n"
    
    content += """
@app.get("/")
async def root():
    return {"message": "Generated API is running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
"""
    
    return content


def _generate_fastapi_requirements() -> str:
    """Generate FastAPI requirements.txt"""
    return """fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic==2.5.0
sqlalchemy==2.0.23
psycopg2-binary==2.9.9
python-multipart==0.0.6
"""


def _generate_express_model(table: Dict) -> str:
    """Generate Express/Mongoose model"""
    table_name = table.get("table_name", "unknown")
    
    content = f"""const mongoose = require('mongoose');

const {table_name}Schema = new mongoose.Schema({{
"""
    
    for column in table.get("columns", []):
        col_name = column.get("column_name", "unknown")
        col_type = column.get("data_type", "String")
        required = not column.get("is_nullable", True)
        
        js_type = "String"
        if "INT" in col_type.upper():
            js_type = "Number"
        elif "BOOL" in col_type.upper():
            js_type = "Boolean"
        elif "DATE" in col_type.upper() or "TIME" in col_type.upper():
            js_type = "Date"
        
        content += f"  {col_name}: {{\\n"
        content += f"    type: {js_type},\\n"
        if required:
            content += f"    required: true\\n"
        content += f"  }},\\n"
    
    content += f"""  
}}, {{
  timestamps: true
}});

module.exports = mongoose.model('{_to_pascal_case(table_name)}', {table_name}Schema);
"""
    
    return content


def _generate_express_routes(table: Dict) -> str:
    """Generate Express routes"""
    table_name = table.get("table_name", "unknown")
    model_name = _to_pascal_case(table_name)
    
    content = f"""const express = require('express');
const {model_name} = require('../models/{table_name}');
const router = express.Router();

// Get all {table_name}
router.get('/', async (req, res) => {{
  try {{
    const items = await {model_name}.find();
    res.json(items);
  }} catch (error) {{
    res.status(500).json({{ message: error.message }});
  }}
}});

// Get single {table_name.rstrip('s')}
router.get('/:id', async (req, res) => {{
  try {{
    const item = await {model_name}.findById(req.params.id);
    if (!item) {{
      return res.status(404).json({{ message: 'Item not found' }});
    }}
    res.json(item);
  }} catch (error) {{
    res.status(500).json({{ message: error.message }});
  }}
}});

// Create {table_name.rstrip('s')}
router.post('/', async (req, res) => {{
  try {{
    const item = new {model_name}(req.body);
    const savedItem = await item.save();
    res.status(201).json(savedItem);
  }} catch (error) {{
    res.status(400).json({{ message: error.message }});
  }}
}});

// Update {table_name.rstrip('s')}
router.put('/:id', async (req, res) => {{
  try {{
    const item = await {model_name}.findByIdAndUpdate(
      req.params.id,
      req.body,
      {{ new: true, runValidators: true }}
    );
    if (!item) {{
      return res.status(404).json({{ message: 'Item not found' }});
    }}
    res.json(item);
  }} catch (error) {{
    res.status(400).json({{ message: error.message }});
  }}
}});

// Delete {table_name.rstrip('s')}
router.delete('/:id', async (req, res) => {{
  try {{
    const item = await {model_name}.findByIdAndDelete(req.params.id);
    if (!item) {{
      return res.status(404).json({{ message: 'Item not found' }});
    }}
    res.json({{ message: 'Item deleted successfully' }});
  }} catch (error) {{
    res.status(500).json({{ message: error.message }});
  }}
}});

module.exports = router;
"""
    
    return content


def _generate_express_app(tables: List[Dict]) -> str:
    """Generate Express main app"""
    content = """const express = require('express');
const mongoose = require('mongoose');
const cors = require('cors');
require('dotenv').config();

const app = express();

// Middleware
app.use(cors());
app.use(express.json());

// Database connection
mongoose.connect(process.env.MONGODB_URI || 'mongodb://localhost:27017/generated_db', {
  useNewUrlParser: true,
  useUnifiedTopology: true,
});

// Routes
"""
    
    for table in tables:
        table_name = table.get("table_name", "unknown")
        content += f"app.use('/{table_name}', require('./routes/{table_name}'));\\n"
    
    content += """
app.get('/', (req, res) => {
  res.json({ message: 'Generated Express API is running' });
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
  console.log(`Server is running on port ${PORT}`);
});
"""
    
    return content


def _generate_express_package() -> str:
    """Generate Express package.json"""
    return """{
  "name": "generated-express-api",
  "version": "1.0.0",
  "description": "Generated Express API",
  "main": "app.js",
  "scripts": {
    "start": "node app.js",
    "dev": "nodemon app.js",
    "test": "echo \\"Error: no test specified\\" && exit 1"
  },
  "dependencies": {
    "express": "^4.18.2",
    "mongoose": "^8.0.0",
    "cors": "^2.8.5",
    "dotenv": "^16.3.1"
  },
  "devDependencies": {
    "nodemon": "^3.0.1"
  }
}"""


def _generate_spring_entity(table: Dict) -> str:
    """Generate Spring JPA entity"""
    table_name = table.get("table_name", "unknown")
    class_name = _to_pascal_case(table_name)
    
    content = f"""package com.example.entity;

import javax.persistence.*;
import java.time.LocalDateTime;

@Entity
@Table(name = "{table_name}")
public class {class_name} {{
    
"""
    
    for column in table.get("columns", []):
        col_name = column.get("column_name", "unknown")
        col_type = _map_to_java_type(column.get("data_type", "String"))
        is_primary = column.get("is_primary_key", False)
        
        if is_primary:
            content += f"    @Id\\n"
            if "id" in col_name.lower():
                content += f"    @GeneratedValue(strategy = GenerationType.IDENTITY)\\n"
        
        content += f"    @Column(name = \"{col_name}\")\\n"
        content += f"    private {col_type} {col_name};\\n\\n"
    
    content += f"    // Constructors\\n"
    content += f"    public {class_name}() {{}}\\n\\n"
    
    # Getters and setters
    for column in table.get("columns", []):
        col_name = column.get("column_name", "unknown")
        col_type = _map_to_java_type(column.get("data_type", "String"))
        getter_name = f"get{_to_pascal_case(col_name)}"
        setter_name = f"set{_to_pascal_case(col_name)}"
        
        content += f"    public {col_type} {getter_name}() {{\\n"
        content += f"        return {col_name};\\n"
        content += f"    }}\\n\\n"
        
        content += f"    public void {setter_name}({col_type} {col_name}) {{\\n"
        content += f"        this.{col_name} = {col_name};\\n"
        content += f"    }}\\n\\n"
    
    content += "}"
    
    return content


def _generate_spring_repository(table: Dict) -> str:
    """Generate Spring JPA repository"""
    table_name = table.get("table_name", "unknown")
    class_name = _to_pascal_case(table_name)
    
    content = f"""package com.example.repository;

import com.example.entity.{class_name};
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

@Repository
public interface {class_name}Repository extends JpaRepository<{class_name}, Long> {{
    // Custom query methods can be added here
}}
"""
    
    return content


def _generate_spring_controller(table: Dict) -> str:
    """Generate Spring REST controller"""
    table_name = table.get("table_name", "unknown")
    class_name = _to_pascal_case(table_name)
    
    content = f"""package com.example.controller;

import com.example.entity.{class_name};
import com.example.repository.{class_name}Repository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Optional;

@RestController
@RequestMapping("/api/{table_name}")
@CrossOrigin(origins = "*")
public class {class_name}Controller {{

    @Autowired
    private {class_name}Repository repository;

    @GetMapping
    public List<{class_name}> getAll() {{
        return repository.findAll();
    }}

    @GetMapping("/{{id}}")
    public ResponseEntity<{class_name}> getById(@PathVariable Long id) {{
        Optional<{class_name}> item = repository.findById(id);
        return item.map(ResponseEntity::ok)
                  .orElse(ResponseEntity.notFound().build());
    }}

    @PostMapping
    public {class_name} create(@RequestBody {class_name} item) {{
        return repository.save(item);
    }}

    @PutMapping("/{{id}}")
    public ResponseEntity<{class_name}> update(@PathVariable Long id, @RequestBody {class_name} itemDetails) {{
        Optional<{class_name}> optionalItem = repository.findById(id);
        
        if (optionalItem.isPresent()) {{
            {class_name} item = optionalItem.get();
            // Update fields here
            {class_name} updatedItem = repository.save(item);
            return ResponseEntity.ok(updatedItem);
        }} else {{
            return ResponseEntity.notFound().build();
        }}
    }}

    @DeleteMapping("/{{id}}")
    public ResponseEntity<?> delete(@PathVariable Long id) {{
        return repository.findById(id)
                .map(item -> {{
                    repository.delete(item);
                    return ResponseEntity.ok().build();
                }})
                .orElse(ResponseEntity.notFound().build());
    }}
}}
"""
    
    return content
