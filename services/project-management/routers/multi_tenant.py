"""
Multi-Tenant Schema Isolation Router
Manages tenant-specific schema isolation and customization
"""
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum
import json
import uuid
import asyncio
from core.auth import get_current_user

router = APIRouter(prefix="/tenants", tags=["multi-tenant"])

# Enums
class IsolationLevel(str, Enum):
    database = "database"
    schema = "schema"
    row_level = "row_level"

class TenantStatus(str, Enum):
    active = "active"
    inactive = "inactive"
    migrating = "migrating"
    provisioning = "provisioning"

# Models
class CustomField(BaseModel):
    table: str
    field: str
    type: str
    required: bool = False
    default_value: Optional[str] = None

class TenantConfiguration(BaseModel):
    tenant_name: str
    isolation_level: IsolationLevel
    base_template: str
    custom_fields: List[CustomField] = Field(default_factory=list)
    compliance_requirements: List[str] = Field(default_factory=list)
    resource_limits: Optional[Dict[str, Any]] = None

class TenantInfo(BaseModel):
    id: str
    tenant_name: str
    isolation_level: IsolationLevel
    base_template: str
    status: TenantStatus
    created_at: datetime
    last_updated: datetime
    schema_version: str
    custom_fields: List[CustomField]
    compliance_requirements: List[str]
    resource_usage: Dict[str, Any]

class SchemaMigrationRequest(BaseModel):
    target_version: str
    migration_strategy: str = Field(default="rolling", description="rolling, blue_green, maintenance")
    custom_field_mappings: Optional[Dict[str, str]] = None

# Mock storage
TENANTS = {}
TENANT_SCHEMAS = {}
BASE_TEMPLATES = {
    "saas_starter": {
        "version": "1.0.0",
        "tables": {
            "organizations": {
                "columns": {
                    "id": {"type": "uuid", "primary_key": True},
                    "name": {"type": "varchar(255)", "required": True},
                    "tenant_id": {"type": "uuid", "required": True, "indexed": True},
                    "created_at": {"type": "timestamp", "default": "now()"},
                    "updated_at": {"type": "timestamp", "default": "now()"}
                }
            },
            "users": {
                "columns": {
                    "id": {"type": "uuid", "primary_key": True},
                    "email": {"type": "varchar(255)", "required": True, "unique": True},
                    "tenant_id": {"type": "uuid", "required": True, "indexed": True},
                    "organization_id": {"type": "uuid", "foreign_key": "organizations.id"},
                    "role": {"type": "varchar(50)", "default": "user"},
                    "created_at": {"type": "timestamp", "default": "now()"},
                    "updated_at": {"type": "timestamp", "default": "now()"}
                }
            },
            "data_sources": {
                "columns": {
                    "id": {"type": "uuid", "primary_key": True},
                    "name": {"type": "varchar(255)", "required": True},
                    "tenant_id": {"type": "uuid", "required": True, "indexed": True},
                    "connection_string": {"type": "text", "encrypted": True},
                    "created_at": {"type": "timestamp", "default": "now()"}
                }
            }
        }
    },
    "enterprise_suite": {
        "version": "1.0.0",
        "tables": {
            "tenants": {
                "columns": {
                    "id": {"type": "uuid", "primary_key": True},
                    "name": {"type": "varchar(255)", "required": True},
                    "plan": {"type": "varchar(50)", "default": "enterprise"},
                    "settings": {"type": "jsonb"},
                    "created_at": {"type": "timestamp", "default": "now()"}
                }
            },
            "users": {
                "columns": {
                    "id": {"type": "uuid", "primary_key": True},
                    "email": {"type": "varchar(255)", "required": True},
                    "tenant_id": {"type": "uuid", "required": True, "indexed": True},
                    "permissions": {"type": "jsonb"},
                    "sso_enabled": {"type": "boolean", "default": False},
                    "created_at": {"type": "timestamp", "default": "now()"}
                }
            },
            "audit_logs": {
                "columns": {
                    "id": {"type": "uuid", "primary_key": True},
                    "tenant_id": {"type": "uuid", "required": True, "indexed": True},
                    "user_id": {"type": "uuid", "foreign_key": "users.id"},
                    "action": {"type": "varchar(100)", "required": True},
                    "resource": {"type": "varchar(255)"},
                    "timestamp": {"type": "timestamp", "default": "now()"}
                }
            }
        }
    }
}

class TenantManager:
    """Multi-tenant schema management engine"""
    
    def __init__(self):
        self.isolation_strategies = self._load_isolation_strategies()
        self.compliance_mappings = self._load_compliance_mappings()
    
    def _load_isolation_strategies(self) -> Dict[str, Any]:
        """Load tenant isolation strategies"""
        return {
            "database": {
                "description": "Each tenant gets a separate database",
                "pros": ["Complete isolation", "Easy backup/restore", "Independent scaling"],
                "cons": ["Higher resource usage", "Complex management", "Higher costs"],
                "complexity": "high",
                "resource_multiplier": 1.0
            },
            "schema": {
                "description": "Shared database with separate schemas per tenant",
                "pros": ["Good isolation", "Moderate resource usage", "Easier management"],
                "cons": ["Shared database resources", "Cross-tenant queries complex"],
                "complexity": "medium",
                "resource_multiplier": 0.6
            },
            "row_level": {
                "description": "Shared tables with tenant_id column and RLS",
                "pros": ["Low resource usage", "Easy cross-tenant analytics", "Simple management"],
                "cons": ["Risk of data leakage", "Complex queries", "Security concerns"],
                "complexity": "low",
                "resource_multiplier": 0.3
            }
        }
    
    def _load_compliance_mappings(self) -> Dict[str, Any]:
        """Load compliance requirement mappings"""
        return {
            "SOC2": {
                "required_fields": ["audit_log", "access_control", "data_classification"],
                "encryption_required": True,
                "audit_retention_days": 365
            },
            "GDPR": {
                "required_fields": ["data_consent", "retention_period", "data_purpose"],
                "encryption_required": True,
                "audit_retention_days": 1095  # 3 years
            },
            "HIPAA": {
                "required_fields": ["patient_consent", "access_authorization", "phi_classification"],
                "encryption_required": True,
                "audit_retention_days": 2190  # 6 years
            },
            "ISO27001": {
                "required_fields": ["security_classification", "access_matrix", "incident_log"],
                "encryption_required": True,
                "audit_retention_days": 1095
            }
        }
    
    async def create_tenant_schema(self, config: TenantConfiguration) -> Dict[str, Any]:
        """Create tenant-specific schema based on configuration"""
        tenant_id = f"tenant_{uuid.uuid4().hex[:16]}"
        
        # Get base template
        base_template = BASE_TEMPLATES.get(config.base_template)
        if not base_template:
            raise ValueError(f"Base template '{config.base_template}' not found")
        
        # Create tenant-specific schema
        tenant_schema = json.loads(json.dumps(base_template))  # Deep copy
        
        # Add custom fields
        for custom_field in config.custom_fields:
            table_name = custom_field.table
            if table_name in tenant_schema["tables"]:
                tenant_schema["tables"][table_name]["columns"][custom_field.field] = {
                    "type": custom_field.type,
                    "required": custom_field.required,
                    "default": custom_field.default_value
                }
        
        # Add compliance-specific fields
        for compliance in config.compliance_requirements:
            compliance_mapping = self.compliance_mappings.get(compliance, {})
            required_fields = compliance_mapping.get("required_fields", [])
            
            for table_name in tenant_schema["tables"]:
                for field in required_fields:
                    if field not in tenant_schema["tables"][table_name]["columns"]:
                        tenant_schema["tables"][table_name]["columns"][field] = {
                            "type": "varchar(255)",
                            "required": False
                        }
        
        # Add tenant isolation fields based on isolation level
        if config.isolation_level == IsolationLevel.row_level:
            for table_name in tenant_schema["tables"]:
                if "tenant_id" not in tenant_schema["tables"][table_name]["columns"]:
                    tenant_schema["tables"][table_name]["columns"]["tenant_id"] = {
                        "type": "uuid",
                        "required": True,
                        "indexed": True
                    }
        
        return {
            "tenant_id": tenant_id,
            "schema": tenant_schema,
            "isolation_config": self._generate_isolation_config(config.isolation_level, tenant_id),
            "resource_estimate": self._calculate_resource_requirements(tenant_schema, config.isolation_level)
        }
    
    def _generate_isolation_config(self, isolation_level: IsolationLevel, tenant_id: str) -> Dict[str, Any]:
        """Generate isolation configuration"""
        if isolation_level == IsolationLevel.database:
            return {
                "type": "database",
                "database_name": f"tenant_{tenant_id}",
                "connection_string_template": "postgresql://user:pass@host:5432/tenant_{tenant_id}",
                "backup_strategy": "individual"
            }
        elif isolation_level == IsolationLevel.schema:
            return {
                "type": "schema",
                "schema_name": f"tenant_{tenant_id}",
                "connection_string_template": "postgresql://user:pass@host:5432/shared_db?options=-csearch_path=tenant_{tenant_id}",
                "backup_strategy": "schema_level"
            }
        else:  # row_level
            return {
                "type": "row_level",
                "tenant_id": tenant_id,
                "rls_policies": self._generate_rls_policies(tenant_id),
                "backup_strategy": "filtered"
            }
    
    def _generate_rls_policies(self, tenant_id: str) -> List[str]:
        """Generate Row Level Security policies"""
        return [
            f"CREATE POLICY tenant_isolation ON users FOR ALL TO tenant_role USING (tenant_id = '{tenant_id}')",
            f"CREATE POLICY tenant_isolation ON organizations FOR ALL TO tenant_role USING (tenant_id = '{tenant_id}')",
            f"CREATE POLICY tenant_isolation ON data_sources FOR ALL TO tenant_role USING (tenant_id = '{tenant_id}')"
        ]
    
    def _calculate_resource_requirements(self, schema: Dict[str, Any], isolation_level: IsolationLevel) -> Dict[str, Any]:
        """Calculate resource requirements"""
        base_resources = {
            "storage_mb": len(schema["tables"]) * 100,  # Base estimate
            "cpu_cores": 0.5,
            "memory_mb": 512
        }
        
        # Apply isolation multiplier
        multiplier = self.isolation_strategies[isolation_level]["resource_multiplier"]
        
        return {
            "storage_mb": int(base_resources["storage_mb"] * multiplier),
            "cpu_cores": base_resources["cpu_cores"] * multiplier,
            "memory_mb": int(base_resources["memory_mb"] * multiplier),
            "estimated_monthly_cost": self._estimate_monthly_cost(base_resources, multiplier)
        }
    
    def _estimate_monthly_cost(self, base_resources: Dict[str, Any], multiplier: float) -> float:
        """Estimate monthly cost for tenant resources"""
        # Simple cost calculation (in production, use actual cloud pricing)
        storage_cost = (base_resources["storage_mb"] * multiplier / 1024) * 0.10  # $0.10 per GB
        cpu_cost = (base_resources["cpu_cores"] * multiplier) * 20.0  # $20 per core
        memory_cost = (base_resources["memory_mb"] * multiplier / 1024) * 10.0  # $10 per GB
        
        return round(storage_cost + cpu_cost + memory_cost, 2)

# Global tenant manager
tenant_manager = TenantManager()

@router.post("")
async def create_tenant(
    config: TenantConfiguration,
    current_user: dict = Depends(get_current_user)
):
    """Create new tenant with isolated schema"""
    try:
        # Create tenant schema
        tenant_result = await tenant_manager.create_tenant_schema(config)
        tenant_id = tenant_result["tenant_id"]
        
        # Create tenant record
        tenant_info = TenantInfo(
            id=tenant_id,
            tenant_name=config.tenant_name,
            isolation_level=config.isolation_level,
            base_template=config.base_template,
            status=TenantStatus.provisioning,
            created_at=datetime.now(),
            last_updated=datetime.now(),
            schema_version="1.0.0",
            custom_fields=config.custom_fields,
            compliance_requirements=config.compliance_requirements,
            resource_usage=tenant_result["resource_estimate"]
        )
        
        # Store tenant
        TENANTS[tenant_id] = tenant_info
        TENANT_SCHEMAS[tenant_id] = tenant_result["schema"]
        
        return {
            "success": True,
            "data": {
                "tenant_id": tenant_id,
                "tenant_name": config.tenant_name,
                "isolation_level": config.isolation_level,
                "status": "provisioning",
                "schema": tenant_result["schema"],
                "isolation_config": tenant_result["isolation_config"],
                "resource_estimate": tenant_result["resource_estimate"]
            }
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create tenant: {str(e)}")

@router.get("/{tenant_id}")
async def get_tenant(tenant_id: str):
    """Get tenant information"""
    try:
        if tenant_id not in TENANTS:
            raise HTTPException(status_code=404, detail="Tenant not found")
        
        tenant = TENANTS[tenant_id]
        
        return {
            "success": True,
            "data": {
                "tenant": {
                    "id": tenant.id,
                    "tenant_name": tenant.tenant_name,
                    "isolation_level": tenant.isolation_level,
                    "base_template": tenant.base_template,
                    "status": tenant.status,
                    "created_at": tenant.created_at.isoformat(),
                    "last_updated": tenant.last_updated.isoformat(),
                    "schema_version": tenant.schema_version,
                    "custom_fields": [field.dict() for field in tenant.custom_fields],
                    "compliance_requirements": tenant.compliance_requirements,
                    "resource_usage": tenant.resource_usage
                }
            }
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get tenant: {str(e)}")

@router.get("/{tenant_id}/schema")
async def get_tenant_schema(tenant_id: str):
    """Get tenant-specific schema"""
    try:
        if tenant_id not in TENANT_SCHEMAS:
            raise HTTPException(status_code=404, detail="Tenant schema not found")
        
        schema = TENANT_SCHEMAS[tenant_id]
        tenant = TENANTS[tenant_id]
        
        return {
            "success": True,
            "data": {
                "tenant_id": tenant_id,
                "schema_version": tenant.schema_version,
                "isolation_level": tenant.isolation_level,
                "schema": schema,
                "last_updated": tenant.last_updated.isoformat()
            }
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get tenant schema: {str(e)}")

@router.post("/{tenant_id}/migrate")
async def migrate_tenant_schema(
    tenant_id: str,
    migration_request: SchemaMigrationRequest,
    background_tasks: BackgroundTasks
):
    """Migrate tenant to new schema version"""
    try:
        if tenant_id not in TENANTS:
            raise HTTPException(status_code=404, detail="Tenant not found")
        
        tenant = TENANTS[tenant_id]
        
        # Update tenant status
        tenant.status = TenantStatus.migrating
        tenant.last_updated = datetime.now()
        TENANTS[tenant_id] = tenant
        
        # Start migration in background (mock)
        background_tasks.add_task(execute_tenant_migration, tenant_id, migration_request)
        
        return {
            "success": True,
            "data": {
                "tenant_id": tenant_id,
                "migration_status": "started",
                "target_version": migration_request.target_version,
                "strategy": migration_request.migration_strategy,
                "estimated_completion": (datetime.now().timestamp() + 300)  # 5 minutes
            }
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start tenant migration: {str(e)}")

async def execute_tenant_migration(tenant_id: str, migration_request: SchemaMigrationRequest):
    """Execute tenant schema migration"""
    try:
        # Simulate migration work
        await asyncio.sleep(5)
        
        # Update tenant after migration
        tenant = TENANTS[tenant_id]
        tenant.status = TenantStatus.active
        tenant.schema_version = migration_request.target_version
        tenant.last_updated = datetime.now()
        TENANTS[tenant_id] = tenant
        
    except Exception as e:
        # Handle migration failure
        tenant = TENANTS[tenant_id]
        tenant.status = TenantStatus.active  # Rollback to previous state
        TENANTS[tenant_id] = tenant

@router.get("")
async def list_tenants(
    status: Optional[TenantStatus] = None,
    isolation_level: Optional[IsolationLevel] = None,
    limit: int = 20,
    offset: int = 0
):
    """List tenants with filtering"""
    try:
        # Filter tenants
        filtered_tenants = list(TENANTS.values())
        
        if status:
            filtered_tenants = [t for t in filtered_tenants if t.status == status]
        
        if isolation_level:
            filtered_tenants = [t for t in filtered_tenants if t.isolation_level == isolation_level]
        
        # Sort by creation date
        filtered_tenants.sort(key=lambda x: x.created_at, reverse=True)
        
        # Paginate
        paginated_tenants = filtered_tenants[offset:offset + limit]
        
        # Convert to dict
        tenant_summaries = []
        for tenant in paginated_tenants:
            tenant_summaries.append({
                "id": tenant.id,
                "tenant_name": tenant.tenant_name,
                "isolation_level": tenant.isolation_level,
                "status": tenant.status,
                "created_at": tenant.created_at.isoformat(),
                "schema_version": tenant.schema_version,
                "resource_usage": tenant.resource_usage
            })
        
        return {
            "success": True,
            "data": {
                "tenants": tenant_summaries,
                "total_count": len(filtered_tenants),
                "limit": limit,
                "offset": offset
            }
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list tenants: {str(e)}")

@router.put("/{tenant_id}")
async def update_tenant(
    tenant_id: str,
    updates: Dict[str, Any],
    current_user: dict = Depends(get_current_user)
):
    """Update tenant configuration"""
    try:
        if tenant_id not in TENANTS:
            raise HTTPException(status_code=404, detail="Tenant not found")
        
        tenant = TENANTS[tenant_id]
        
        # Update allowed fields
        if "tenant_name" in updates:
            tenant.tenant_name = updates["tenant_name"]
        
        if "compliance_requirements" in updates:
            tenant.compliance_requirements = updates["compliance_requirements"]
        
        tenant.last_updated = datetime.now()
        TENANTS[tenant_id] = tenant
        
        return {
            "success": True,
            "data": {
                "tenant_id": tenant_id,
                "updated_fields": list(updates.keys()),
                "last_updated": tenant.last_updated.isoformat()
            }
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update tenant: {str(e)}")

@router.delete("/{tenant_id}")
async def delete_tenant(
    tenant_id: str,
    confirm: bool = False,
    current_user: dict = Depends(get_current_user)
):
    """Delete tenant and associated data"""
    try:
        if not confirm:
            raise HTTPException(status_code=400, detail="Confirmation required for tenant deletion")
        
        if tenant_id not in TENANTS:
            raise HTTPException(status_code=404, detail="Tenant not found")
        
        # Remove tenant and schema
        del TENANTS[tenant_id]
        if tenant_id in TENANT_SCHEMAS:
            del TENANT_SCHEMAS[tenant_id]
        
        return {
            "success": True,
            "data": {
                "tenant_id": tenant_id,
                "status": "deleted",
                "deleted_at": datetime.now().isoformat()
            }
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete tenant: {str(e)}")

@router.get("/templates")
async def get_base_templates():
    """Get available base templates"""
    try:
        template_summaries = []
        for template_name, template_data in BASE_TEMPLATES.items():
            template_summaries.append({
                "name": template_name,
                "version": template_data["version"],
                "table_count": len(template_data["tables"]),
                "tables": list(template_data["tables"].keys()),
                "description": _get_template_description(template_name)
            })
        
        return {
            "success": True,
            "data": {
                "templates": template_summaries
            }
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get base templates: {str(e)}")

def _get_template_description(template_name: str) -> str:
    """Get description for base template"""
    descriptions = {
        "saas_starter": "Basic SaaS application schema with user management and data sources",
        "enterprise_suite": "Comprehensive enterprise schema with advanced audit and permissions"
    }
    return descriptions.get(template_name, "Schema template")

@router.get("/isolation-strategies")
async def get_isolation_strategies():
    """Get available tenant isolation strategies"""
    try:
        return {
            "success": True,
            "data": {
                "strategies": tenant_manager.isolation_strategies
            }
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get isolation strategies: {str(e)}")

@router.get("/compliance-requirements")
async def get_compliance_requirements():
    """Get available compliance requirements"""
    try:
        return {
            "success": True,
            "data": {
                "compliance_frameworks": tenant_manager.compliance_mappings
            }
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get compliance requirements: {str(e)}")

@router.get("/stats")
async def get_tenant_stats():
    """Get tenant management statistics"""
    try:
        total_tenants = len(TENANTS)
        
        # Count by status
        status_counts = {}
        for tenant in TENANTS.values():
            status = tenant.status
            status_counts[status] = status_counts.get(status, 0) + 1
        
        # Count by isolation level
        isolation_counts = {}
        for tenant in TENANTS.values():
            isolation = tenant.isolation_level
            isolation_counts[isolation] = isolation_counts.get(isolation, 0) + 1
        
        # Calculate total resource usage
        total_storage = sum(tenant.resource_usage.get("storage_mb", 0) for tenant in TENANTS.values())
        total_cost = sum(tenant.resource_usage.get("estimated_monthly_cost", 0) for tenant in TENANTS.values())
        
        return {
            "success": True,
            "data": {
                "total_tenants": total_tenants,
                "status_distribution": status_counts,
                "isolation_distribution": isolation_counts,
                "total_storage_mb": total_storage,
                "total_monthly_cost": round(total_cost, 2),
                "available_templates": len(BASE_TEMPLATES),
                "average_cost_per_tenant": round(total_cost / max(total_tenants, 1), 2)
            }
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get tenant stats: {str(e)}")
