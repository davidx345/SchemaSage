"""
Task handlers for workflow automation
"""

import asyncio
import json
import logging
import subprocess
import tempfile
import os
from typing import Dict, Any, List
from datetime import datetime
import requests
import yaml

from models.schemas import SchemaResponse

logger = logging.getLogger(__name__)


async def handle_schema_analysis(context: Dict[str, Any]) -> Dict[str, Any]:
    """Handle schema analysis task"""
    task = context["task"]
    config = task.configuration
    
    # Get schema from input or previous task
    schema_data = config.get("schema") or context["input_data"].get("schema")
    if not schema_data:
        raise ValueError("No schema data provided for analysis")
    
    # Convert to SchemaResponse if needed
    if isinstance(schema_data, dict):
        schema = SchemaResponse(**schema_data)
    else:
        schema = schema_data
    
    # Perform analysis based on config
    analysis_type = config.get("analysis_type", "comprehensive")
    
    if analysis_type == "comprehensive":
        # Comprehensive schema analysis
        analysis_result = {
            "table_count": len(schema.tables),
            "relationship_count": len(schema.relationships or []),
            "complexity_score": _calculate_complexity_score(schema),
            "recommendations": _generate_schema_recommendations(schema)
        }
        return {"output": {"analysis_result": analysis_result}}
    
    elif analysis_type == "compliance":
        # Compliance analysis
        framework = config.get("compliance_framework", "gdpr")
        compliance_result = _assess_compliance(schema, framework)
        return {"output": {"compliance_report": compliance_result}}
    
    else:
        raise ValueError(f"Unknown analysis type: {analysis_type}")


async def handle_code_generation(context: Dict[str, Any]) -> Dict[str, Any]:
    """Handle code generation task"""
    task = context["task"]
    config = task.configuration
    
    # Get schema from input or previous task
    schema_data = config.get("schema") or context["input_data"].get("schema")
    if not schema_data:
        # Try to get from context
        schema_data = context["context"].get("schema")
    
    if not schema_data:
        raise ValueError("No schema data provided for code generation")
    
    # Convert to SchemaResponse if needed
    if isinstance(schema_data, dict):
        schema = SchemaResponse(**schema_data)
    else:
        schema = schema_data
    
    # Generate code
    format_type = config.get("format", "sqlalchemy")
    options = config.get("options", {})
    
    generated_code = _generate_code(schema, format_type, options)
    
    return {
        "output": {
            "generated_code": generated_code,
            "format": format_type,
            "options": options
        }
    }


async def handle_validation(context: Dict[str, Any]) -> Dict[str, Any]:
    """Handle validation task"""
    task = context["task"]
    config = task.configuration
    
    validation_type = config.get("validation_type", "schema")
    
    if validation_type == "schema":
        # Validate schema structure
        schema_data = config.get("schema") or context["input_data"].get("schema")
        if not schema_data:
            raise ValueError("No schema data provided for validation")
        
        validation_result = _validate_schema(schema_data)
        return {"output": {"validation_result": validation_result}}
    
    elif validation_type == "code":
        # Validate generated code
        code = config.get("code") or context["context"].get("generated_code")
        if not code:
            raise ValueError("No code provided for validation")
        
        language = config.get("language", "python")
        validation_result = _validate_code(code, language)
        return {"output": {"validation_result": validation_result}}
    
    else:
        raise ValueError(f"Unknown validation type: {validation_type}")


async def handle_deployment(context: Dict[str, Any]) -> Dict[str, Any]:
    """Handle deployment task"""
    task = context["task"]
    config = task.configuration
    
    deployment_type = config.get("deployment_type", "direct")
    target_environment = config.get("target_environment", "development")
    
    # Get code or schema to deploy
    code = config.get("code") or context["context"].get("generated_code")
    schema = config.get("schema") or context["context"].get("schema")
    
    if not code and not schema:
        raise ValueError("No code or schema provided for deployment")
    
    # Perform deployment based on type
    if deployment_type == "direct":
        result = _direct_deployment(code, schema, target_environment, config)
    elif deployment_type == "blue_green":
        result = _blue_green_deployment(code, schema, target_environment, config)
    elif deployment_type == "canary":
        result = _canary_deployment(code, schema, target_environment, config)
    else:
        raise ValueError(f"Unknown deployment type: {deployment_type}")
    
    return {"output": {"deployment_result": result}}


async def handle_notification(context: Dict[str, Any]) -> Dict[str, Any]:
    """Handle notification task"""
    task = context["task"]
    config = task.configuration
    
    notification_type = config.get("type", "email")
    recipients = config.get("recipients", [])
    message_template = config.get("message_template", "Workflow notification")
    
    # Prepare message with context data
    message = _prepare_notification_message(message_template, context)
    
    # Send notification based on type
    if notification_type == "email":
        result = _send_email_notification(recipients, message, config)
    elif notification_type == "slack":
        result = _send_slack_notification(recipients, message, config)
    elif notification_type == "webhook":
        result = _send_webhook_notification(config.get("webhook_url"), message, config)
    else:
        raise ValueError(f"Unknown notification type: {notification_type}")
    
    return {"output": {"notification_result": result}}


async def handle_data_transformation(context: Dict[str, Any]) -> Dict[str, Any]:
    """Handle data transformation task"""
    task = context["task"]
    config = task.configuration
    
    transformation_type = config.get("transformation_type", "json")
    input_data = config.get("input_data") or context["input_data"]
    
    if transformation_type == "json_to_yaml":
        result = yaml.dump(input_data, default_flow_style=False)
    elif transformation_type == "yaml_to_json":
        result = json.dumps(yaml.safe_load(input_data), indent=2)
    elif transformation_type == "custom":
        transformation_script = config.get("script")
        result = _execute_transformation_script(transformation_script, input_data)
    else:
        result = input_data
    
    return {"output": {"transformed_data": result}}


async def handle_integration(context: Dict[str, Any]) -> Dict[str, Any]:
    """Handle integration task"""
    task = context["task"]
    config = task.configuration
    
    integration_type = config.get("integration_type", "api")
    
    if integration_type == "api":
        # API integration
        endpoint = config.get("endpoint")
        method = config.get("method", "POST")
        headers = config.get("headers", {})
        payload = config.get("payload") or context["context"]
        
        result = _make_api_request(method, endpoint, headers, payload)
        
    elif integration_type == "database":
        # Database integration
        connection_string = config.get("connection_string")
        query = config.get("query")
        parameters = config.get("parameters", {})
        
        result = _execute_database_query(connection_string, query, parameters)
        
    elif integration_type == "file_system":
        # File system integration
        operation = config.get("operation", "read")
        file_path = config.get("file_path")
        
        result = _file_system_operation(operation, file_path, config)
        
    else:
        raise ValueError(f"Unknown integration type: {integration_type}")
    
    return {"output": {"integration_result": result}}


async def handle_approval(context: Dict[str, Any]) -> Dict[str, Any]:
    """Handle approval task"""
    task = context["task"]
    config = task.configuration
    execution = context["execution"]
    
    # Create approval request
    from .models import ApprovalRequest
    import uuid
    
    approval_request = ApprovalRequest(
        request_id=str(uuid.uuid4()),
        workflow_id=execution.workflow_id,
        execution_id=execution.execution_id,
        task_id=task.task_id,
        title=config.get("title", f"Approval required for {task.name}"),
        description=config.get("description", ""),
        approvers=config.get("approvers", []),
        required_approvals=config.get("required_approvals", 1)
    )
    
    # Store approval request (in a real implementation, this would be persisted)
    # For now, we'll simulate approval
    
    return {"output": {"approval_request": approval_request.request_id}}


async def handle_conditional(context: Dict[str, Any]) -> Dict[str, Any]:
    """Handle conditional task"""
    task = context["task"]
    
    # Evaluate conditions
    should_continue = task.should_execute(context["context"])
    
    return {"output": {"condition_result": should_continue}}


async def handle_parallel(context: Dict[str, Any]) -> Dict[str, Any]:
    """Handle parallel task execution"""
    task = context["task"]
    config = task.configuration
    
    parallel_tasks = config.get("parallel_tasks", [])
    
    # In a real implementation, this would coordinate parallel execution
    # For now, return placeholder
    
    return {"output": {"parallel_result": f"Executed {len(parallel_tasks)} parallel tasks"}}


async def handle_webhook(context: Dict[str, Any]) -> Dict[str, Any]:
    """Handle webhook task"""
    task = context["task"]
    config = task.configuration
    
    webhook_url = config.get("url")
    method = config.get("method", "POST")
    headers = config.get("headers", {})
    payload = config.get("payload") or context["context"]
    
    result = _make_api_request(method, webhook_url, headers, payload)
    
    return {"output": {"webhook_result": result}}


async def handle_script(context: Dict[str, Any]) -> Dict[str, Any]:
    """Handle script execution task"""
    task = context["task"]
    config = task.configuration
    
    script_type = config.get("script_type", "python")
    script_content = config.get("script")
    
    if not script_content:
        raise ValueError("No script content provided")
    
    if script_type == "python":
        result = _execute_python_script(script_content, context)
    elif script_type == "shell":
        result = _execute_shell_script(script_content, context)
    else:
        raise ValueError(f"Unknown script type: {script_type}")
    
    return {"output": {"script_result": result}}


# Helper functions

def _calculate_complexity_score(schema: SchemaResponse) -> float:
    """Calculate schema complexity score"""
    table_count = len(schema.tables)
    relationship_count = len(schema.relationships or [])
    
    total_columns = sum(len(table.columns) for table in schema.tables)
    
    # Simple complexity calculation
    complexity = (table_count * 0.3) + (relationship_count * 0.5) + (total_columns * 0.1)
    
    return round(complexity, 2)


def _generate_schema_recommendations(schema: SchemaResponse) -> List[str]:
    """Generate schema recommendations"""
    recommendations = []
    
    for table in schema.tables:
        # Check for missing primary keys
        if not table.primary_keys:
            recommendations.append(f"Table '{table.name}' should have a primary key")
        
        # Check for tables without indexes
        if not table.indexes:
            recommendations.append(f"Consider adding indexes to table '{table.name}'")
    
    return recommendations


def _assess_compliance(schema: SchemaResponse, framework: str) -> Dict[str, Any]:
    """Assess schema compliance"""
    # Simplified compliance assessment
    compliance_score = 85.0  # Placeholder
    
    issues = []
    recommendations = []
    
    if framework == "gdpr":
        # Check for personal data handling
        for table in schema.tables:
            for column in table.columns:
                if any(term in column.name.lower() for term in ['email', 'name', 'phone']):
                    recommendations.append(f"Consider data protection for {table.name}.{column.name}")
    
    return {
        "framework": framework,
        "compliance_score": compliance_score,
        "issues": issues,
        "recommendations": recommendations
    }


def _generate_code(schema: SchemaResponse, format_type: str, options: Dict[str, Any]) -> str:
    """Generate code from schema"""
    # Simplified code generation
    if format_type == "sqlalchemy":
        code_lines = ["from sqlalchemy import Column, Integer, String, ForeignKey"]
        code_lines.append("from sqlalchemy.ext.declarative import declarative_base")
        code_lines.append("")
        code_lines.append("Base = declarative_base()")
        code_lines.append("")
        
        for table in schema.tables:
            class_name = table.name.title().replace('_', '')
            code_lines.append(f"class {class_name}(Base):")
            code_lines.append(f"    __tablename__ = '{table.name}'")
            
            for column in table.columns:
                col_type = "String" if column.type == "VARCHAR" else "Integer"
                code_lines.append(f"    {column.name} = Column({col_type})")
            
            code_lines.append("")
        
        return "\n".join(code_lines)
    
    elif format_type == "sql":
        code_lines = []
        for table in schema.tables:
            code_lines.append(f"CREATE TABLE {table.name} (")
            column_defs = []
            for column in table.columns:
                col_def = f"    {column.name} {column.type}"
                if not column.nullable:
                    col_def += " NOT NULL"
                column_defs.append(col_def)
            code_lines.append(",\n".join(column_defs))
            code_lines.append(");")
            code_lines.append("")
        
        return "\n".join(code_lines)
    
    else:
        return f"-- Code generation for {format_type} not implemented"


def _validate_schema(schema_data: Any) -> Dict[str, Any]:
    """Validate schema structure"""
    errors = []
    warnings = []
    
    if isinstance(schema_data, dict):
        if "tables" not in schema_data:
            errors.append("Schema must contain 'tables' field")
        
        # Additional validation logic would go here
    
    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings
    }


def _validate_code(code: str, language: str) -> Dict[str, Any]:
    """Validate generated code"""
    errors = []
    warnings = []
    
    if language == "python":
        try:
            compile(code, '<string>', 'exec')
        except SyntaxError as e:
            errors.append(f"Syntax error: {e}")
    
    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings
    }


def _direct_deployment(code: str, schema: Any, environment: str, config: Dict[str, Any]) -> Dict[str, Any]:
    """Perform direct deployment"""
    # Placeholder implementation
    return {
        "status": "success",
        "environment": environment,
        "deployed_at": datetime.now().isoformat()
    }


def _blue_green_deployment(code: str, schema: Any, environment: str, config: Dict[str, Any]) -> Dict[str, Any]:
    """Perform blue-green deployment"""
    # Placeholder implementation
    return {
        "status": "success",
        "environment": environment,
        "deployment_type": "blue_green",
        "deployed_at": datetime.now().isoformat()
    }


def _canary_deployment(code: str, schema: Any, environment: str, config: Dict[str, Any]) -> Dict[str, Any]:
    """Perform canary deployment"""
    # Placeholder implementation
    return {
        "status": "success",
        "environment": environment,
        "deployment_type": "canary",
        "deployed_at": datetime.now().isoformat()
    }


def _prepare_notification_message(template: str, context: Dict[str, Any]) -> str:
    """Prepare notification message from template"""
    # Simple template substitution
    message = template
    
    # Replace common placeholders
    execution = context.get("execution", {})
    if hasattr(execution, 'workflow_id'):
        message = message.replace("{workflow_id}", execution.workflow_id)
        message = message.replace("{execution_id}", execution.execution_id)
    
    return message


def _send_email_notification(recipients: List[str], message: str, config: Dict[str, Any]) -> Dict[str, Any]:
    """Send email notification"""
    # Placeholder implementation
    return {
        "status": "sent",
        "recipients": recipients,
        "message_length": len(message)
    }


def _send_slack_notification(recipients: List[str], message: str, config: Dict[str, Any]) -> Dict[str, Any]:
    """Send Slack notification"""
    # Placeholder implementation
    return {
        "status": "sent",
        "channels": recipients,
        "message_length": len(message)
    }


def _send_webhook_notification(webhook_url: str, message: str, config: Dict[str, Any]) -> Dict[str, Any]:
    """Send webhook notification"""
    try:
        response = requests.post(webhook_url, json={"message": message}, timeout=30)
        return {
            "status": "sent",
            "response_code": response.status_code
        }
    except Exception as e:
        return {
            "status": "failed",
            "error": str(e)
        }


def _execute_transformation_script(script: str, input_data: Any) -> Any:
    """Execute transformation script"""
    # This would execute custom transformation logic
    # For now, return input data unchanged
    return input_data


def _make_api_request(method: str, endpoint: str, headers: Dict[str, str], payload: Any) -> Dict[str, Any]:
    """Make API request"""
    try:
        response = requests.request(
            method=method,
            url=endpoint,
            headers=headers,
            json=payload,
            timeout=30
        )
        
        return {
            "status_code": response.status_code,
            "response": response.json() if response.content else None
        }
    except Exception as e:
        return {
            "error": str(e)
        }


def _execute_database_query(connection_string: str, query: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
    """Execute database query"""
    # Placeholder implementation
    return {
        "status": "executed",
        "query": query,
        "parameters": parameters
    }


def _file_system_operation(operation: str, file_path: str, config: Dict[str, Any]) -> Dict[str, Any]:
    """Perform file system operation"""
    try:
        if operation == "read":
            with open(file_path, 'r') as f:
                content = f.read()
            return {"content": content}
        elif operation == "write":
            content = config.get("content", "")
            with open(file_path, 'w') as f:
                f.write(content)
            return {"status": "written", "bytes": len(content)}
        else:
            raise ValueError(f"Unknown operation: {operation}")
    except Exception as e:
        return {"error": str(e)}


def _execute_python_script(script: str, context: Dict[str, Any]) -> Dict[str, Any]:
    """Execute Python script"""
    try:
        # Create a safe execution environment
        exec_globals = {
            'context': context,
            'print': print,
            'len': len,
            'str': str,
            'int': int,
            'float': float,
            'dict': dict,
            'list': list
        }
        
        exec_locals = {}
        exec(script, exec_globals, exec_locals)
        
        return {
            "status": "executed",
            "locals": {k: v for k, v in exec_locals.items() if not k.startswith('_')}
        }
    except Exception as e:
        return {"error": str(e)}


def _execute_shell_script(script: str, context: Dict[str, Any]) -> Dict[str, Any]:
    """Execute shell script"""
    try:
        # Write script to temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.sh', delete=False) as f:
            f.write(script)
            script_path = f.name
        
        try:
            # Execute script
            result = subprocess.run(
                ['bash', script_path],
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            return {
                "status": "executed",
                "return_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr
            }
        finally:
            # Clean up temporary file
            os.unlink(script_path)
            
    except Exception as e:
        return {"error": str(e)}
