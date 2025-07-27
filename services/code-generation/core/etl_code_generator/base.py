"""
ETL code generation base types and utilities
"""
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass
from enum import Enum
import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class CodeFramework(Enum):
    """Supported code generation frameworks"""
    AIRFLOW = "airflow"
    PREFECT = "prefect" 
    SPARK = "spark"
    DASK = "dask"
    LUIGI = "luigi"
    DAGSTER = "dagster"
    PYTHON = "python"
    SQL = "sql"

class CodeTemplateType(Enum):
    """Types of code templates"""
    MAIN_SCRIPT = "main_script"
    CONFIG_FILE = "config_file"
    DOCKERFILE = "dockerfile"
    REQUIREMENTS = "requirements"
    DEPLOYMENT = "deployment"
    TESTING = "testing"
    MONITORING = "monitoring"

@dataclass
class CodeTemplate:
    """Template for code generation"""
    template_type: CodeTemplateType
    framework: CodeFramework
    content: str
    variables: Dict[str, Any] = None
    filename: str = ""
    
@dataclass
class GeneratedCode:
    """Container for generated code"""
    framework: CodeFramework
    main_code: str
    config_files: Dict[str, str] = None
    requirements: List[str] = None
    docker_config: Optional[str] = None
    deployment_scripts: Dict[str, str] = None
    test_files: Dict[str, str] = None
    metadata: Dict[str, Any] = None

@dataclass
class DataSource:
    """Data source configuration"""
    source_type: str
    connection_config: Dict[str, Any]
    schema_info: Optional[Dict[str, Any]] = None
    authentication: Optional[Dict[str, Any]] = None

@dataclass
class DataTransformation:
    """Data transformation step"""
    transformation_type: str
    operation: str
    parameters: Dict[str, Any] = None
    input_columns: List[str] = None
    output_columns: List[str] = None
    
@dataclass
class DataDestination:
    """Data destination configuration"""
    destination_type: str
    connection_config: Dict[str, Any]
    schema_mapping: Optional[Dict[str, Any]] = None
    write_mode: str = "append"

@dataclass
class ETLPipeline:
    """ETL pipeline definition"""
    pipeline_id: str
    name: str
    description: str
    sources: List[DataSource]
    transformations: List[DataTransformation]
    destinations: List[DataDestination]
    schedule: Optional[str] = None
    dependencies: List[str] = None
    metadata: Dict[str, Any] = None

class CodeGenerationError(Exception):
    """Exception raised during code generation"""
    pass

class TemplateEngine:
    """Template engine for code generation"""
    
    def __init__(self):
        self.templates = {}
        self.variables = {}
    
    def load_template(self, template: CodeTemplate):
        """Load a code template"""
        key = f"{template.framework.value}_{template.template_type.value}"
        self.templates[key] = template
    
    def render_template(
        self,
        framework: CodeFramework,
        template_type: CodeTemplateType,
        variables: Dict[str, Any]
    ) -> str:
        """Render template with variables"""
        key = f"{framework.value}_{template_type.value}"
        
        if key not in self.templates:
            raise CodeGenerationError(f"Template not found: {key}")
        
        template = self.templates[key]
        content = template.content
        
        # Simple variable substitution
        for var_name, var_value in variables.items():
            placeholder = f"{{{var_name}}}"
            if isinstance(var_value, str):
                content = content.replace(placeholder, var_value)
            else:
                content = content.replace(placeholder, str(var_value))
        
        return content

class CodeValidator:
    """Validates generated code"""
    
    def __init__(self):
        self.validation_rules = {}
    
    def validate_code(self, code: GeneratedCode) -> Dict[str, Any]:
        """Validate generated code"""
        results = {
            "valid": True,
            "errors": [],
            "warnings": []
        }
        
        try:
            # Basic syntax validation
            if code.framework == CodeFramework.PYTHON:
                self._validate_python_syntax(code.main_code, results)
            
            # Framework-specific validation
            if code.framework == CodeFramework.AIRFLOW:
                self._validate_airflow_dag(code.main_code, results)
            
            # Check for required files
            self._validate_required_files(code, results)
            
        except Exception as e:
            results["valid"] = False
            results["errors"].append(f"Validation error: {str(e)}")
        
        return results
    
    def _validate_python_syntax(self, code: str, results: Dict[str, Any]):
        """Validate Python syntax"""
        try:
            compile(code, '<generated>', 'exec')
        except SyntaxError as e:
            results["valid"] = False
            results["errors"].append(f"Python syntax error: {str(e)}")
    
    def _validate_airflow_dag(self, code: str, results: Dict[str, Any]):
        """Validate Airflow DAG structure"""
        required_imports = ["from airflow import DAG", "from datetime import datetime"]
        for import_stmt in required_imports:
            if import_stmt not in code:
                results["warnings"].append(f"Missing import: {import_stmt}")
        
        if "dag = DAG(" not in code and "with DAG(" not in code:
            results["errors"].append("No DAG definition found")
            results["valid"] = False
    
    def _validate_required_files(self, code: GeneratedCode, results: Dict[str, Any]):
        """Validate required files are present"""
        if code.framework == CodeFramework.AIRFLOW:
            if not code.requirements:
                results["warnings"].append("No requirements.txt file generated")

class CodeOptimizer:
    """Optimizes generated code"""
    
    def __init__(self):
        self.optimization_rules = {}
    
    def optimize_code(self, code: GeneratedCode) -> GeneratedCode:
        """Apply optimizations to generated code"""
        try:
            # Remove duplicate imports
            if code.framework in [CodeFramework.PYTHON, CodeFramework.AIRFLOW, CodeFramework.PREFECT]:
                code.main_code = self._remove_duplicate_imports(code.main_code)
            
            # Optimize for framework-specific patterns
            if code.framework == CodeFramework.SPARK:
                code.main_code = self._optimize_spark_code(code.main_code)
            
            # Add performance monitoring
            code.main_code = self._add_performance_monitoring(code.main_code, code.framework)
            
        except Exception as e:
            logger.warning(f"Code optimization failed: {str(e)}")
        
        return code
    
    def _remove_duplicate_imports(self, code: str) -> str:
        """Remove duplicate import statements"""
        lines = code.split('\n')
        imports = set()
        result_lines = []
        
        for line in lines:
            stripped = line.strip()
            if stripped.startswith(('import ', 'from ')):
                if stripped not in imports:
                    imports.add(stripped)
                    result_lines.append(line)
            else:
                result_lines.append(line)
        
        return '\n'.join(result_lines)
    
    def _optimize_spark_code(self, code: str) -> str:
        """Optimize Spark-specific code patterns"""
        # Add caching for reused DataFrames
        if "df.filter(" in code and "df.cache()" not in code:
            code = code.replace("df.filter(", "df.cache().filter(")
        
        return code
    
    def _add_performance_monitoring(self, code: str, framework: CodeFramework) -> str:
        """Add performance monitoring code"""
        if framework == CodeFramework.PYTHON:
            monitoring_code = """
import time
import logging

# Performance monitoring
start_time = time.time()
logger = logging.getLogger(__name__)
"""
            
            # Insert at the beginning after imports
            lines = code.split('\n')
            import_end = 0
            
            for i, line in enumerate(lines):
                if not line.strip().startswith(('import ', 'from ', '#')):
                    import_end = i
                    break
            
            lines.insert(import_end, monitoring_code)
            
            # Add end monitoring
            lines.append("""
# Log execution time
execution_time = time.time() - start_time
logger.info(f"Pipeline execution completed in {execution_time:.2f} seconds")
""")
            
            code = '\n'.join(lines)
        
        return code

class DocumentationGenerator:
    """Generates documentation for code"""
    
    def __init__(self):
        self.doc_templates = {}
    
    def generate_documentation(self, code: GeneratedCode, pipeline: ETLPipeline) -> str:
        """Generate documentation for the pipeline"""
        doc_sections = []
        
        # Pipeline overview
        doc_sections.append(f"# {pipeline.name}")
        doc_sections.append(f"\n{pipeline.description}\n")
        
        # Data sources
        if pipeline.sources:
            doc_sections.append("## Data Sources")
            for i, source in enumerate(pipeline.sources, 1):
                doc_sections.append(f"{i}. **{source.source_type}**")
                doc_sections.append(f"   - Configuration: {json.dumps(source.connection_config, indent=2)}")
        
        # Transformations
        if pipeline.transformations:
            doc_sections.append("\n## Transformations")
            for i, transform in enumerate(pipeline.transformations, 1):
                doc_sections.append(f"{i}. **{transform.transformation_type}**: {transform.operation}")
                if transform.parameters:
                    doc_sections.append(f"   - Parameters: {json.dumps(transform.parameters, indent=2)}")
        
        # Destinations
        if pipeline.destinations:
            doc_sections.append("\n## Data Destinations")
            for i, dest in enumerate(pipeline.destinations, 1):
                doc_sections.append(f"{i}. **{dest.destination_type}**")
                doc_sections.append(f"   - Write Mode: {dest.write_mode}")
        
        # Generated code info
        doc_sections.append(f"\n## Generated Code")
        doc_sections.append(f"- Framework: {code.framework.value}")
        doc_sections.append(f"- Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        if code.requirements:
            doc_sections.append(f"\n### Dependencies")
            for req in code.requirements:
                doc_sections.append(f"- {req}")
        
        # Usage instructions
        doc_sections.append(f"\n## Usage Instructions")
        
        if code.framework == CodeFramework.AIRFLOW:
            doc_sections.append("1. Copy the generated DAG file to your Airflow DAGs folder")
            doc_sections.append("2. Install required dependencies")
            doc_sections.append("3. Configure connections in Airflow UI")
            doc_sections.append("4. Enable and trigger the DAG")
        elif code.framework == CodeFramework.PYTHON:
            doc_sections.append("1. Install required dependencies: `pip install -r requirements.txt`")
            doc_sections.append("2. Configure environment variables or config files")
            doc_sections.append("3. Run the script: `python main.py`")
        
        return '\n'.join(doc_sections)

class CodePackager:
    """Packages generated code into deployable artifacts"""
    
    def __init__(self):
        self.package_formats = ['zip', 'tar.gz', 'docker']
    
    def create_package(
        self,
        code: GeneratedCode,
        pipeline: ETLPipeline,
        package_format: str = 'zip'
    ) -> Dict[str, Any]:
        """Create deployment package"""
        
        package_info = {
            "format": package_format,
            "files": {},
            "metadata": {
                "pipeline_id": pipeline.pipeline_id,
                "framework": code.framework.value,
                "created_at": datetime.now().isoformat()
            }
        }
        
        # Main script
        if code.framework == CodeFramework.AIRFLOW:
            package_info["files"]["dags/pipeline.py"] = code.main_code
        else:
            package_info["files"]["main.py"] = code.main_code
        
        # Config files
        if code.config_files:
            for filename, content in code.config_files.items():
                package_info["files"][f"config/{filename}"] = content
        
        # Requirements
        if code.requirements:
            package_info["files"]["requirements.txt"] = '\n'.join(code.requirements)
        
        # Docker configuration
        if code.docker_config:
            package_info["files"]["Dockerfile"] = code.docker_config
        
        # Deployment scripts
        if code.deployment_scripts:
            for filename, content in code.deployment_scripts.items():
                package_info["files"][f"deploy/{filename}"] = content
        
        # Test files
        if code.test_files:
            for filename, content in code.test_files.items():
                package_info["files"][f"tests/{filename}"] = content
        
        # Documentation
        doc_generator = DocumentationGenerator()
        documentation = doc_generator.generate_documentation(code, pipeline)
        package_info["files"]["README.md"] = documentation
        
        return package_info
