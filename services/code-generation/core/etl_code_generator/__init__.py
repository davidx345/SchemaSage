"""
ETL code generator module initialization
"""

from .base import (
    CodeFramework,
    CodeTemplateType,
    CodeTemplate,
    GeneratedCode,
    DataSource,
    DataTransformation,
    DataDestination,
    ETLPipeline,
    CodeGenerationError,
    TemplateEngine,
    CodeValidator,
    CodeOptimizer,
    DocumentationGenerator,
    CodePackager
)

from .airflow_generator import AirflowCodeGenerator
from .spark_generator import SparkCodeGenerator

__all__ = [
    # Base types and classes
    "CodeFramework",
    "CodeTemplateType", 
    "CodeTemplate",
    "GeneratedCode",
    "DataSource",
    "DataTransformation",
    "DataDestination",
    "ETLPipeline",
    "CodeGenerationError",
    "TemplateEngine",
    "CodeValidator",
    "CodeOptimizer",
    "DocumentationGenerator",
    "CodePackager",
    
    # Code generators
    "AirflowCodeGenerator",
    "SparkCodeGenerator",
    
    # Main generator class
    "ETLCodeGenerator"
]

class ETLCodeGenerator:
    """Main ETL code generator that orchestrates different framework generators"""
    
    def __init__(self):
        self.generators = {
            CodeFramework.AIRFLOW: AirflowCodeGenerator(),
            CodeFramework.SPARK: SparkCodeGenerator(),
        }
        self.validator = CodeValidator()
        self.optimizer = CodeOptimizer()
        self.packager = CodePackager()
    
    def generate_code(
        self,
        pipeline: ETLPipeline,
        framework: CodeFramework,
        options: dict = None
    ) -> GeneratedCode:
        """
        Generate code for the specified framework
        
        Args:
            pipeline: ETL pipeline definition
            framework: Target framework for code generation
            options: Framework-specific options
            
        Returns:
            GeneratedCode object containing all generated artifacts
            
        Raises:
            CodeGenerationError: If generation fails
        """
        options = options or {}
        
        if framework not in self.generators:
            raise CodeGenerationError(f"Unsupported framework: {framework}")
        
        try:
            # Generate code using appropriate generator
            generator = self.generators[framework]
            
            if framework == CodeFramework.AIRFLOW:
                generated_code = generator.generate_dag(pipeline, options)
            elif framework == CodeFramework.SPARK:
                generated_code = generator.generate_spark_job(pipeline, options)
            else:
                raise CodeGenerationError(f"Generator method not implemented for {framework}")
            
            # Validate generated code
            if options.get("validate", True):
                validation_result = self.validator.validate_code(generated_code)
                generated_code.metadata["validation"] = validation_result
                
                if not validation_result["valid"] and options.get("strict_validation", False):
                    raise CodeGenerationError(f"Code validation failed: {validation_result['errors']}")
            
            # Optimize code
            if options.get("optimize", True):
                generated_code = self.optimizer.optimize_code(generated_code)
            
            return generated_code
            
        except Exception as e:
            raise CodeGenerationError(f"Code generation failed: {str(e)}") from e
    
    def create_deployment_package(
        self,
        generated_code: GeneratedCode,
        pipeline: ETLPipeline,
        package_format: str = "zip"
    ) -> dict:
        """
        Create a deployment package from generated code
        
        Args:
            generated_code: Generated code artifacts
            pipeline: Original pipeline definition
            package_format: Format for the package (zip, tar.gz, docker)
            
        Returns:
            Package information dictionary
        """
        return self.packager.create_package(generated_code, pipeline, package_format)
    
    def get_supported_frameworks(self) -> list:
        """Get list of supported frameworks"""
        return list(self.generators.keys())
    
    def validate_pipeline(self, pipeline: ETLPipeline) -> dict:
        """
        Validate pipeline definition before code generation
        
        Args:
            pipeline: Pipeline to validate
            
        Returns:
            Validation result dictionary
        """
        validation_result = {
            "valid": True,
            "errors": [],
            "warnings": []
        }
        
        # Check required fields
        if not pipeline.pipeline_id:
            validation_result["errors"].append("Pipeline ID is required")
            validation_result["valid"] = False
        
        if not pipeline.name:
            validation_result["errors"].append("Pipeline name is required")
            validation_result["valid"] = False
        
        if not pipeline.sources:
            validation_result["errors"].append("At least one data source is required")
            validation_result["valid"] = False
        
        if not pipeline.destinations:
            validation_result["errors"].append("At least one destination is required")
            validation_result["valid"] = False
        
        # Check source configurations
        for i, source in enumerate(pipeline.sources):
            if not source.source_type:
                validation_result["errors"].append(f"Source {i+1}: source_type is required")
                validation_result["valid"] = False
            
            if not source.connection_config:
                validation_result["warnings"].append(f"Source {i+1}: connection_config is empty")
        
        # Check destination configurations
        for i, dest in enumerate(pipeline.destinations):
            if not dest.destination_type:
                validation_result["errors"].append(f"Destination {i+1}: destination_type is required")
                validation_result["valid"] = False
            
            if not dest.connection_config:
                validation_result["warnings"].append(f"Destination {i+1}: connection_config is empty")
        
        # Check transformation logic
        for i, transform in enumerate(pipeline.transformations):
            if not transform.operation:
                validation_result["errors"].append(f"Transformation {i+1}: operation is required")
                validation_result["valid"] = False
        
        return validation_result
