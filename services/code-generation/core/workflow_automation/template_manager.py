"""
Template manager for workflow automation
"""

import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import uuid
import os
import yaml

from .models import WorkflowTemplate, WorkflowDefinition, WorkflowTask, WorkflowTrigger, TaskType, TriggerType

logger = logging.getLogger(__name__)


class WorkflowTemplateManager:
    """
    Manages workflow templates for quick workflow creation
    """
    
    def __init__(self, template_directory: str = None):
        """
        Initialize template manager
        
        Args:
            template_directory: Directory to store templates
        """
        self.template_directory = template_directory or "templates/workflows"
        self.templates: Dict[str, WorkflowTemplate] = {}
        
        # Ensure template directory exists
        os.makedirs(self.template_directory, exist_ok=True)
        
        # Load built-in templates
        self._load_builtin_templates()
        
        # Load custom templates from directory
        self._load_templates_from_directory()
    
    def _load_builtin_templates(self):
        """Load built-in workflow templates"""
        
        # Schema Analysis Template
        schema_analysis_template = self._create_schema_analysis_template()
        self.templates[schema_analysis_template.template_id] = schema_analysis_template
        
        # Code Generation Pipeline Template
        code_gen_template = self._create_code_generation_template()
        self.templates[code_gen_template.template_id] = code_gen_template
        
        # Deployment Pipeline Template
        deployment_template = self._create_deployment_template()
        self.templates[deployment_template.template_id] = deployment_template
        
        # Schema Validation Template
        validation_template = self._create_validation_template()
        self.templates[validation_template.template_id] = validation_template
        
        # Data Migration Template
        migration_template = self._create_migration_template()
        self.templates[migration_template.template_id] = migration_template
    
    def _create_schema_analysis_template(self) -> WorkflowTemplate:
        """Create schema analysis workflow template"""
        template_data = {
            "name": "Schema Analysis Workflow",
            "description": "Comprehensive schema analysis and reporting",
            "tasks": [
                {
                    "task_id": "analyze_schema",
                    "name": "Analyze Schema",
                    "task_type": "schema_analysis",
                    "configuration": {
                        "analysis_type": "comprehensive"
                    }
                },
                {
                    "task_id": "generate_report",
                    "name": "Generate Analysis Report",
                    "task_type": "data_transformation",
                    "dependencies": ["analyze_schema"],
                    "configuration": {
                        "transformation_type": "json_to_yaml"
                    }
                },
                {
                    "task_id": "notify_stakeholders",
                    "name": "Notify Stakeholders",
                    "task_type": "notification",
                    "dependencies": ["generate_report"],
                    "configuration": {
                        "type": "email",
                        "recipients": ["${stakeholders}"],
                        "message_template": "Schema analysis completed for ${schema_name}"
                    }
                }
            ],
            "triggers": [
                {
                    "trigger_type": "manual"
                }
            ]
        }
        
        parameters = [
            {
                "name": "stakeholders",
                "type": "list",
                "description": "List of stakeholder email addresses",
                "required": True
            },
            {
                "name": "schema_name",
                "type": "string", 
                "description": "Name of the schema being analyzed",
                "required": True
            }
        ]
        
        return WorkflowTemplate(
            template_id="schema_analysis_v1",
            name="Schema Analysis",
            description="Analyze database schema and generate reports",
            category="Analysis",
            template_data=template_data,
            parameters=parameters,
            tags=["schema", "analysis", "reporting"]
        )
    
    def _create_code_generation_template(self) -> WorkflowTemplate:
        """Create code generation workflow template"""
        template_data = {
            "name": "Code Generation Pipeline",
            "description": "Generate code from schema with validation and deployment",
            "tasks": [
                {
                    "task_id": "validate_schema",
                    "name": "Validate Schema",
                    "task_type": "validation",
                    "configuration": {
                        "validation_type": "schema"
                    }
                },
                {
                    "task_id": "generate_code",
                    "name": "Generate Code",
                    "task_type": "code_generation",
                    "dependencies": ["validate_schema"],
                    "configuration": {
                        "format": "${code_format}",
                        "options": "${generation_options}"
                    }
                },
                {
                    "task_id": "validate_code",
                    "name": "Validate Generated Code",
                    "task_type": "validation",
                    "dependencies": ["generate_code"],
                    "configuration": {
                        "validation_type": "code",
                        "language": "${target_language}"
                    }
                },
                {
                    "task_id": "approval_gate",
                    "name": "Code Review Approval",
                    "task_type": "approval",
                    "dependencies": ["validate_code"],
                    "configuration": {
                        "title": "Code Review Required",
                        "description": "Please review the generated code before deployment",
                        "approvers": ["${reviewers}"],
                        "required_approvals": 1
                    },
                    "conditions": [
                        {
                            "field": "require_approval",
                            "operator": "equals",
                            "value": True
                        }
                    ]
                },
                {
                    "task_id": "deploy_code",
                    "name": "Deploy Code",
                    "task_type": "deployment",
                    "dependencies": ["approval_gate"],
                    "configuration": {
                        "deployment_type": "${deployment_type}",
                        "target_environment": "${target_environment}"
                    }
                }
            ],
            "triggers": [
                {
                    "trigger_type": "schema_change",
                    "configuration": {
                        "change_types": ["table_added", "column_added"],
                        "min_severity": "medium"
                    }
                }
            ]
        }
        
        parameters = [
            {
                "name": "code_format",
                "type": "string",
                "description": "Code generation format (sqlalchemy, django, etc.)",
                "default": "sqlalchemy",
                "required": True
            },
            {
                "name": "target_language",
                "type": "string",
                "description": "Target programming language",
                "default": "python",
                "required": True
            },
            {
                "name": "deployment_type",
                "type": "string",
                "description": "Deployment strategy",
                "default": "direct",
                "required": True
            },
            {
                "name": "target_environment",
                "type": "string",
                "description": "Deployment target environment",
                "default": "development",
                "required": True
            },
            {
                "name": "require_approval",
                "type": "boolean",
                "description": "Whether approval is required before deployment",
                "default": True,
                "required": False
            },
            {
                "name": "reviewers",
                "type": "list",
                "description": "List of code reviewers",
                "required": False
            },
            {
                "name": "generation_options",
                "type": "object",
                "description": "Additional code generation options",
                "default": {},
                "required": False
            }
        ]
        
        return WorkflowTemplate(
            template_id="code_generation_v1",
            name="Code Generation Pipeline",
            description="Generate, validate, and deploy code from database schemas",
            category="Development",
            template_data=template_data,
            parameters=parameters,
            tags=["code-generation", "deployment", "validation"]
        )
    
    def _create_deployment_template(self) -> WorkflowTemplate:
        """Create deployment workflow template"""
        template_data = {
            "name": "Database Deployment Pipeline",
            "description": "Deploy database changes with proper validation and rollback",
            "tasks": [
                {
                    "task_id": "pre_deployment_checks",
                    "name": "Pre-deployment Checks",
                    "task_type": "validation",
                    "configuration": {
                        "validation_type": "schema",
                        "checks": ["syntax", "constraints", "compatibility"]
                    }
                },
                {
                    "task_id": "backup_database",
                    "name": "Backup Current Database",
                    "task_type": "script",
                    "dependencies": ["pre_deployment_checks"],
                    "configuration": {
                        "script_type": "shell",
                        "script": "${backup_script}"
                    }
                },
                {
                    "task_id": "deploy_changes",
                    "name": "Deploy Database Changes",
                    "task_type": "deployment",
                    "dependencies": ["backup_database"],
                    "configuration": {
                        "deployment_type": "${deployment_strategy}",
                        "target_environment": "${environment}",
                        "rollback_enabled": True
                    }
                },
                {
                    "task_id": "post_deployment_tests",
                    "name": "Post-deployment Tests",
                    "task_type": "validation",
                    "dependencies": ["deploy_changes"],
                    "configuration": {
                        "validation_type": "integration",
                        "test_suite": "${test_suite}"
                    }
                },
                {
                    "task_id": "notify_completion",
                    "name": "Notify Deployment Completion",
                    "task_type": "notification",
                    "dependencies": ["post_deployment_tests"],
                    "configuration": {
                        "type": "slack",
                        "channels": ["${notification_channels}"],
                        "message_template": "Database deployment to ${environment} completed successfully"
                    }
                }
            ],
            "triggers": [
                {
                    "trigger_type": "manual"
                },
                {
                    "trigger_type": "scheduled",
                    "configuration": {
                        "cron_expression": "${deployment_schedule}"
                    }
                }
            ]
        }
        
        parameters = [
            {
                "name": "environment",
                "type": "string",
                "description": "Target deployment environment",
                "required": True
            },
            {
                "name": "deployment_strategy",
                "type": "string",
                "description": "Deployment strategy (blue_green, canary, direct)",
                "default": "blue_green",
                "required": True
            },
            {
                "name": "backup_script",
                "type": "string",
                "description": "Database backup script",
                "required": True
            },
            {
                "name": "test_suite",
                "type": "string",
                "description": "Post-deployment test suite",
                "required": False
            },
            {
                "name": "notification_channels",
                "type": "list",
                "description": "Slack channels for notifications",
                "required": False
            },
            {
                "name": "deployment_schedule",
                "type": "string",
                "description": "Cron expression for scheduled deployments",
                "required": False
            }
        ]
        
        return WorkflowTemplate(
            template_id="deployment_v1",
            name="Database Deployment",
            description="Safe database deployment with backup and validation",
            category="Deployment",
            template_data=template_data,
            parameters=parameters,
            tags=["deployment", "database", "backup", "validation"]
        )
    
    def _create_validation_template(self) -> WorkflowTemplate:
        """Create validation workflow template"""
        template_data = {
            "name": "Schema Validation Pipeline",
            "description": "Comprehensive schema validation and quality checks",
            "tasks": [
                {
                    "task_id": "syntax_validation",
                    "name": "Syntax Validation",
                    "task_type": "validation",
                    "configuration": {
                        "validation_type": "syntax"
                    }
                },
                {
                    "task_id": "naming_convention_check",
                    "name": "Naming Convention Check",
                    "task_type": "validation",
                    "dependencies": ["syntax_validation"],
                    "configuration": {
                        "validation_type": "naming_conventions",
                        "rules": "${naming_rules}"
                    }
                },
                {
                    "task_id": "constraint_validation",
                    "name": "Constraint Validation",
                    "task_type": "validation",
                    "dependencies": ["syntax_validation"],
                    "configuration": {
                        "validation_type": "constraints"
                    }
                },
                {
                    "task_id": "generate_validation_report",
                    "name": "Generate Validation Report",
                    "task_type": "data_transformation",
                    "dependencies": ["naming_convention_check", "constraint_validation"],
                    "configuration": {
                        "transformation_type": "json_to_yaml"
                    }
                }
            ]
        }
        
        parameters = [
            {
                "name": "naming_rules",
                "type": "object",
                "description": "Naming convention rules",
                "default": {},
                "required": False
            }
        ]
        
        return WorkflowTemplate(
            template_id="validation_v1",
            name="Schema Validation",
            description="Validate schema syntax, naming, and constraints",
            category="Quality",
            template_data=template_data,
            parameters=parameters,
            tags=["validation", "quality", "standards"]
        )
    
    def _create_migration_template(self) -> WorkflowTemplate:
        """Create data migration workflow template"""
        template_data = {
            "name": "Data Migration Pipeline",
            "description": "Migrate data between schemas with validation",
            "tasks": [
                {
                    "task_id": "validate_source_schema",
                    "name": "Validate Source Schema",
                    "task_type": "validation",
                    "configuration": {
                        "validation_type": "schema",
                        "schema_source": "source"
                    }
                },
                {
                    "task_id": "validate_target_schema",
                    "name": "Validate Target Schema", 
                    "task_type": "validation",
                    "configuration": {
                        "validation_type": "schema",
                        "schema_source": "target"
                    }
                },
                {
                    "task_id": "generate_migration_script",
                    "name": "Generate Migration Script",
                    "task_type": "code_generation",
                    "dependencies": ["validate_source_schema", "validate_target_schema"],
                    "configuration": {
                        "format": "sql",
                        "migration_type": "${migration_type}"
                    }
                },
                {
                    "task_id": "test_migration",
                    "name": "Test Migration",
                    "task_type": "script",
                    "dependencies": ["generate_migration_script"],
                    "configuration": {
                        "script_type": "shell",
                        "script": "${test_script}"
                    }
                },
                {
                    "task_id": "approval_for_migration",
                    "name": "Migration Approval",
                    "task_type": "approval",
                    "dependencies": ["test_migration"],
                    "configuration": {
                        "title": "Data Migration Approval",
                        "description": "Please approve the data migration",
                        "approvers": ["${migration_approvers}"],
                        "required_approvals": 2
                    }
                },
                {
                    "task_id": "execute_migration",
                    "name": "Execute Migration",
                    "task_type": "deployment",
                    "dependencies": ["approval_for_migration"],
                    "configuration": {
                        "deployment_type": "migration",
                        "target_environment": "${target_environment}"
                    }
                }
            ]
        }
        
        parameters = [
            {
                "name": "migration_type",
                "type": "string",
                "description": "Type of migration (schema, data, both)",
                "default": "both",
                "required": True
            },
            {
                "name": "target_environment",
                "type": "string",
                "description": "Target environment for migration",
                "required": True
            },
            {
                "name": "test_script",
                "type": "string",
                "description": "Migration test script",
                "required": True
            },
            {
                "name": "migration_approvers",
                "type": "list",
                "description": "List of migration approvers",
                "required": True
            }
        ]
        
        return WorkflowTemplate(
            template_id="migration_v1",
            name="Data Migration",
            description="Migrate data between schemas with approval gates",
            category="Migration",
            template_data=template_data,
            parameters=parameters,
            tags=["migration", "data", "approval", "validation"]
        )
    
    def _load_templates_from_directory(self):
        """Load custom templates from directory"""
        try:
            for filename in os.listdir(self.template_directory):
                if filename.endswith(('.json', '.yaml', '.yml')):
                    file_path = os.path.join(self.template_directory, filename)
                    template = self._load_template_from_file(file_path)
                    if template:
                        self.templates[template.template_id] = template
        except Exception as e:
            logger.error(f"Error loading templates from directory: {e}")
    
    def _load_template_from_file(self, file_path: str) -> Optional[WorkflowTemplate]:
        """Load template from file"""
        try:
            with open(file_path, 'r') as f:
                if file_path.endswith('.json'):
                    data = json.load(f)
                else:
                    data = yaml.safe_load(f)
            
            return WorkflowTemplate(
                template_id=data['template_id'],
                name=data['name'],
                description=data['description'],
                category=data.get('category', 'Custom'),
                template_data=data['template_data'],
                parameters=data.get('parameters', []),
                tags=data.get('tags', [])
            )
        except Exception as e:
            logger.error(f"Error loading template from {file_path}: {e}")
            return None
    
    def get_template(self, template_id: str) -> Optional[WorkflowTemplate]:
        """Get template by ID"""
        return self.templates.get(template_id)
    
    def list_templates(self, category: str = None) -> List[WorkflowTemplate]:
        """List available templates, optionally filtered by category"""
        templates = list(self.templates.values())
        
        if category:
            templates = [t for t in templates if t.category.lower() == category.lower()]
        
        return sorted(templates, key=lambda t: t.name)
    
    def get_template_categories(self) -> List[str]:
        """Get list of template categories"""
        categories = set(template.category for template in self.templates.values())
        return sorted(list(categories))
    
    def instantiate_template(
        self, 
        template_id: str, 
        parameters: Dict[str, Any],
        workflow_name: str = None
    ) -> WorkflowDefinition:
        """
        Create workflow instance from template
        
        Args:
            template_id: ID of template to instantiate
            parameters: Parameter values for template
            workflow_name: Name for the new workflow
            
        Returns:
            Workflow definition
        """
        template = self.get_template(template_id)
        if not template:
            raise ValueError(f"Template {template_id} not found")
        
        # Validate parameters
        self._validate_template_parameters(template, parameters)
        
        # Substitute parameters in template data
        instantiated_data = self._substitute_parameters(template.template_data, parameters)
        
        # Create workflow definition
        workflow_id = str(uuid.uuid4())
        workflow_name = workflow_name or f"{template.name} Instance"
        
        # Convert task data to WorkflowTask objects
        workflow_tasks = []
        for task_data in instantiated_data.get('tasks', []):
            task = WorkflowTask(
                task_id=task_data['task_id'],
                name=task_data['name'],
                task_type=TaskType(task_data['task_type']),
                description=task_data.get('description', ''),
                dependencies=task_data.get('dependencies', []),
                configuration=task_data.get('configuration', {}),
                timeout=task_data.get('timeout'),
                retry_count=task_data.get('retry_count', 0),
                retry_delay=task_data.get('retry_delay', 60)
            )
            workflow_tasks.append(task)
        
        # Convert trigger data to WorkflowTrigger objects
        workflow_triggers = []
        for trigger_data in instantiated_data.get('triggers', []):
            trigger = WorkflowTrigger(
                trigger_type=TriggerType(trigger_data['trigger_type']),
                configuration=trigger_data.get('configuration', {})
            )
            workflow_triggers.append(trigger)
        
        workflow = WorkflowDefinition(
            workflow_id=workflow_id,
            name=workflow_name,
            description=instantiated_data.get('description', template.description),
            tasks=workflow_tasks,
            triggers=workflow_triggers,
            metadata={
                'template_id': template_id,
                'template_parameters': parameters,
                'instantiated_from': template.name
            },
            tags=template.tags.copy()
        )
        
        return workflow
    
    def _validate_template_parameters(self, template: WorkflowTemplate, parameters: Dict[str, Any]):
        """Validate template parameters"""
        errors = []
        
        for param_def in template.parameters:
            param_name = param_def['name']
            param_type = param_def.get('type', 'string')
            required = param_def.get('required', False)
            
            if required and param_name not in parameters:
                errors.append(f"Required parameter '{param_name}' is missing")
                continue
            
            if param_name in parameters:
                value = parameters[param_name]
                
                # Type validation
                if param_type == 'string' and not isinstance(value, str):
                    errors.append(f"Parameter '{param_name}' must be a string")
                elif param_type == 'list' and not isinstance(value, list):
                    errors.append(f"Parameter '{param_name}' must be a list")
                elif param_type == 'boolean' and not isinstance(value, bool):
                    errors.append(f"Parameter '{param_name}' must be a boolean")
                elif param_type == 'object' and not isinstance(value, dict):
                    errors.append(f"Parameter '{param_name}' must be an object")
        
        if errors:
            raise ValueError(f"Parameter validation errors: {', '.join(errors)}")
    
    def _substitute_parameters(self, data: Any, parameters: Dict[str, Any]) -> Any:
        """Recursively substitute parameters in template data"""
        if isinstance(data, dict):
            return {key: self._substitute_parameters(value, parameters) for key, value in data.items()}
        elif isinstance(data, list):
            return [self._substitute_parameters(item, parameters) for item in data]
        elif isinstance(data, str):
            # Simple parameter substitution
            for param_name, param_value in parameters.items():
                placeholder = f"${{{param_name}}}"
                if placeholder in data:
                    if data == placeholder:
                        # Replace entire string
                        return param_value
                    else:
                        # Replace within string
                        data = data.replace(placeholder, str(param_value))
            return data
        else:
            return data
    
    def save_template(self, template: WorkflowTemplate):
        """Save template to file"""
        file_path = os.path.join(self.template_directory, f"{template.template_id}.yaml")
        
        template_data = {
            'template_id': template.template_id,
            'name': template.name,
            'description': template.description,
            'category': template.category,
            'template_data': template.template_data,
            'parameters': template.parameters,
            'tags': template.tags
        }
        
        try:
            with open(file_path, 'w') as f:
                yaml.dump(template_data, f, default_flow_style=False)
            
            # Add to in-memory collection
            self.templates[template.template_id] = template
            
            logger.info(f"Saved template {template.template_id} to {file_path}")
        except Exception as e:
            logger.error(f"Error saving template: {e}")
            raise
    
    def delete_template(self, template_id: str):
        """Delete template"""
        if template_id in self.templates:
            # Remove from memory
            del self.templates[template_id]
            
            # Remove file if it exists
            file_path = os.path.join(self.template_directory, f"{template_id}.yaml")
            if os.path.exists(file_path):
                os.remove(file_path)
            
            logger.info(f"Deleted template {template_id}")
        else:
            logger.warning(f"Template {template_id} not found for deletion")
