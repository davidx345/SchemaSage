"""
Universal Compliance Code Generation Router
Generates compliance-ready code templates for all industries
"""

from fastapi import APIRouter, HTTPException, Query, Depends
from typing import List, Dict, Any, Optional
import logging
from datetime import datetime
import httpx
import os

from models.schemas import CodeGenerationRequest, CodeGenerationResponse
from core.compliance_templates import (
    UniversalComplianceTemplates, ComplianceTemplate, IndustryTemplate, DataRecordType
)
from core.code_generator import CodeGenerator

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/compliance-generation", tags=["Universal Compliance Code Generation"])

# Service URLs
WEBSOCKET_SERVICE_URL = os.getenv("WEBSOCKET_SERVICE_URL", "https://schemasage-websocket-realtime.herokuapp.com")

# Initialize components
compliance_templates = UniversalComplianceTemplates()
code_generator = CodeGenerator()


async def send_generation_webhook(webhook_data: dict):
    """Send code generation webhook to WebSocket service"""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            await client.post(f"{WEBSOCKET_SERVICE_URL}/webhooks/code-generated", json=webhook_data)
            logger.info("Code generation webhook sent successfully")
    except Exception as e:
        logger.warning(f"Failed to send generation webhook: {e}")


@router.post("/generate-compliant-schema")
async def generate_compliant_schema(
    request: Dict[str, Any]
):
    """Generate compliance-ready database schema"""
    try:
        template_id = request.get("template_id")
        industry = request.get("industry")
        record_type = request.get("record_type", "general")
        database_type = request.get("database_type", "mysql")
        project_id = request.get("project_id")
        
        if not template_id and not industry:
            raise HTTPException(status_code=400, detail="Either template_id or industry is required")
        
        # Get template by ID or find by industry
        if template_id:
            template = compliance_templates.get_template(template_id)
            if not template:
                raise HTTPException(status_code=404, detail="Template not found")
        else:
            try:
                industry_enum = IndustryTemplate(industry)
                templates = compliance_templates.get_templates_by_industry(industry_enum)
                if not templates:
                    raise HTTPException(status_code=404, detail="No templates found for industry")
                template = templates[0]  # Use first available template
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid industry type")
        
        # Generate SQL from template
        generated_sql = compliance_templates.generate_sql_from_template(template.template_id, database_type)
        
        # Generate additional compliance artifacts
        compliance_artifacts = {
            "data_classification_guide": _generate_data_classification_guide(template),
            "security_controls_checklist": template.security_controls,
            "audit_requirements": template.audit_requirements,
            "access_control_matrix": _generate_access_control_matrix(template),
            "retention_policy_document": template.retention_policies,
            "encryption_implementation_guide": _generate_encryption_guide(template)
        }
        
        # Send webhook notification
        if project_id:
            webhook_data = {
                "project_id": project_id,
                "template_used": template.template_id,
                "industry": template.industry.value,
                "frameworks": template.applicable_frameworks,
                "artifact_count": len(compliance_artifacts),
                "timestamp": datetime.now().isoformat()
            }
            await send_generation_webhook(webhook_data)
        
        return {
            "generation_id": f"gen_{int(datetime.now().timestamp())}",
            "template_info": {
                "template_id": template.template_id,
                "name": template.name,
                "industry": template.industry.value,
                "record_type": template.record_type.value,
                "applicable_frameworks": template.applicable_frameworks
            },
            "generated_schema": {
                "sql": generated_sql,
                "database_type": database_type,
                "table_count": len(template.schema_template)
            },
            "compliance_artifacts": compliance_artifacts,
            "implementation_notes": [
                f"This schema is designed for {template.industry.value} industry compliance",
                f"Supports {', '.join(template.applicable_frameworks)} frameworks",
                "All PII fields are marked for encryption",
                "Comprehensive audit logging is included",
                "Regular compliance assessments recommended"
            ],
            "generated_at": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating compliant schema: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate compliant schema")


@router.get("/templates")
async def get_compliance_templates(
    industry: Optional[IndustryTemplate] = Query(None, description="Filter by industry"),
    framework: Optional[str] = Query(None, description="Filter by compliance framework")
):
    """Get available compliance templates"""
    try:
        if industry:
            templates = compliance_templates.get_templates_by_industry(industry)
        elif framework:
            templates = compliance_templates.get_templates_by_framework(framework)
        else:
            templates = list(compliance_templates.get_all_templates().values())
        
        # Format templates for response
        formatted_templates = []
        for template in templates:
            formatted_templates.append({
                "template_id": template.template_id,
                "name": template.name,
                "industry": template.industry.value,
                "record_type": template.record_type.value,
                "applicable_frameworks": template.applicable_frameworks,
                "table_count": len(template.schema_template),
                "security_controls_count": len(template.security_controls),
                "description": f"Compliance-ready {template.record_type.value} template for {template.industry.value} industry"
            })
        
        return {
            "templates": formatted_templates,
            "total_count": len(formatted_templates),
            "filter_applied": {
                "industry": industry.value if industry else None,
                "framework": framework
            }
        }
        
    except Exception as e:
        logger.error(f"Error fetching templates: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch templates")


@router.get("/templates/{template_id}")
async def get_template_details(template_id: str):
    """Get detailed information about a specific template"""
    try:
        template = compliance_templates.get_template(template_id)
        if not template:
            raise HTTPException(status_code=404, detail="Template not found")
        
        return {
            "template_id": template.template_id,
            "name": template.name,
            "industry": template.industry.value,
            "record_type": template.record_type.value,
            "applicable_frameworks": template.applicable_frameworks,
            "schema_structure": template.schema_template,
            "security_controls": template.security_controls,
            "audit_requirements": template.audit_requirements,
            "access_controls": template.access_controls,
            "encryption_requirements": template.encryption_requirements,
            "retention_policies": template.retention_policies,
            "implementation_complexity": _assess_implementation_complexity(template),
            "estimated_implementation_time": _estimate_implementation_time(template)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching template details: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch template details")


@router.post("/generate-custom-template")
async def generate_custom_template(
    request: Dict[str, Any]
):
    """Generate a custom compliance template based on requirements"""
    try:
        industry = request.get("industry")
        frameworks = request.get("frameworks", [])
        data_types = request.get("data_types", [])
        special_requirements = request.get("special_requirements", [])
        project_id = request.get("project_id")
        
        if not industry or not frameworks:
            raise HTTPException(status_code=400, detail="Industry and frameworks are required")
        
        # Validate industry
        try:
            industry_enum = IndustryTemplate(industry)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid industry type")
        
        # Find base template for industry
        base_templates = compliance_templates.get_templates_by_industry(industry_enum)
        if not base_templates:
            raise HTTPException(status_code=400, detail="No base templates available for industry")
        
        base_template = base_templates[0]
        
        # Create custom template by modifying base template
        custom_schema = dict(base_template.schema_template)
        custom_controls = list(base_template.security_controls)
        custom_audit = list(base_template.audit_requirements)
        
        # Add framework-specific requirements
        for framework in frameworks:
            if framework not in base_template.applicable_frameworks:
                framework_additions = _get_framework_additions(framework)
                custom_controls.extend(framework_additions.get("controls", []))
                custom_audit.extend(framework_additions.get("audit", []))
        
        # Add special requirements
        for requirement in special_requirements:
            if requirement == "biometric_data":
                custom_schema["biometric_data"] = {
                    "biometric_id": {"type": "varchar(50)", "primary_key": True},
                    "biometric_type": {"type": "enum('fingerprint','facial','iris')", "required": True},
                    "biometric_hash": {"type": "varchar(255)", "encrypted": True, "sensitive": True},
                    "created_at": {"type": "timestamp", "default": "CURRENT_TIMESTAMP"}
                }
                custom_controls.append("Biometric data encryption with specialized algorithms")
            elif requirement == "blockchain_audit":
                custom_schema["blockchain_audit"] = {
                    "block_id": {"type": "varchar(64)", "primary_key": True},
                    "transaction_hash": {"type": "varchar(64)", "unique": True},
                    "block_data": {"type": "json", "encrypted": True},
                    "timestamp": {"type": "timestamp", "default": "CURRENT_TIMESTAMP"}
                }
                custom_controls.append("Blockchain-based audit trail for immutability")
        
        # Generate SQL for custom template
        custom_template_data = {
            "schema_template": custom_schema,
            "security_controls": list(set(custom_controls)),
            "audit_requirements": list(set(custom_audit))
        }
        
        generated_sql = _generate_custom_sql(custom_schema, industry, frameworks)
        
        # Send webhook notification
        if project_id:
            webhook_data = {
                "project_id": project_id,
                "custom_template": True,
                "industry": industry,
                "frameworks": frameworks,
                "special_requirements": special_requirements,
                "timestamp": datetime.now().isoformat()
            }
            await send_generation_webhook(webhook_data)
        
        return {
            "custom_template_id": f"custom_{industry}_{int(datetime.now().timestamp())}",
            "industry": industry,
            "frameworks": frameworks,
            "generated_schema": generated_sql,
            "template_data": custom_template_data,
            "special_requirements": special_requirements,
            "implementation_guide": _generate_implementation_guide(industry, frameworks),
            "generated_at": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating custom template: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate custom template")


@router.get("/industry/{industry}/recommendations")
async def get_industry_recommendations(industry: IndustryTemplate):
    """Get compliance recommendations for a specific industry"""
    try:
        templates = compliance_templates.get_templates_by_industry(industry)
        
        if not templates:
            return {
                "industry": industry.value,
                "templates_available": 0,
                "recommendations": ["No specific templates available for this industry"]
            }
        
        # Aggregate recommendations from all templates
        all_frameworks = set()
        all_controls = set()
        all_requirements = set()
        
        for template in templates:
            all_frameworks.update(template.applicable_frameworks)
            all_controls.update(template.security_controls)
            all_requirements.update(template.audit_requirements)
        
        return {
            "industry": industry.value,
            "templates_available": len(templates),
            "recommended_frameworks": list(all_frameworks),
            "essential_security_controls": list(all_controls)[:10],  # Top 10
            "key_audit_requirements": list(all_requirements)[:10],   # Top 10
            "implementation_priority": _get_industry_priority(industry),
            "estimated_compliance_cost": _estimate_compliance_cost(industry),
            "typical_timeline": _get_typical_timeline(industry)
        }
        
    except Exception as e:
        logger.error(f"Error fetching industry recommendations: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch industry recommendations")


@router.get("/health")
async def compliance_generation_health():
    """Health check for compliance code generation"""
    template_summary = compliance_templates.get_template_summary()
    
    return {
        "status": "healthy",
        "service": "Universal Compliance Code Generation",
        "version": "1.0.0",
        "templates_loaded": template_summary["total_templates"],
        "industries_supported": len(template_summary["by_industry"]),
        "frameworks_supported": len(template_summary["by_framework"]),
        "features": {
            "compliant_schema_generation": True,
            "custom_template_creation": True,
            "multi_framework_support": True,
            "industry_specific_templates": True
        },
        "timestamp": datetime.now().isoformat()
    }


# Helper functions
def _generate_data_classification_guide(template: ComplianceTemplate) -> Dict[str, Any]:
    """Generate data classification guide for template"""
    return {
        "classification_levels": ["Public", "Internal", "Confidential", "Restricted"],
        "pii_fields": [field for field, config in template.schema_template.items() 
                      if any("pii" in str(col).lower() for col in config.values())],
        "sensitive_fields": [field for field, config in template.schema_template.items()
                           if any("sensitive" in str(col).lower() for col in config.values())],
        "encryption_required": template.encryption_requirements
    }


def _generate_access_control_matrix(template: ComplianceTemplate) -> Dict[str, Any]:
    """Generate access control matrix"""
    return {
        "roles": ["Admin", "User", "Auditor", "Guest"],
        "permissions": template.access_controls,
        "restrictions": ["Need-to-know", "Minimum necessary", "Segregation of duties"]
    }


def _generate_encryption_guide(template: ComplianceTemplate) -> Dict[str, Any]:
    """Generate encryption implementation guide"""
    return {
        "algorithms": ["AES-256", "RSA-4096", "TLS 1.3"],
        "key_management": "HSM or KMS recommended",
        "rotation_policy": "90 days for high-sensitivity data",
        "requirements": template.encryption_requirements
    }


def _assess_implementation_complexity(template: ComplianceTemplate) -> str:
    """Assess implementation complexity of template"""
    complexity_score = 0
    complexity_score += len(template.schema_template) * 2
    complexity_score += len(template.security_controls) * 3
    complexity_score += len(template.applicable_frameworks) * 5
    
    if complexity_score < 20:
        return "Low"
    elif complexity_score < 50:
        return "Medium"
    else:
        return "High"


def _estimate_implementation_time(template: ComplianceTemplate) -> str:
    """Estimate implementation time for template"""
    weeks = 2  # Base time
    weeks += len(template.schema_template) * 0.5
    weeks += len(template.security_controls) * 0.3
    weeks += len(template.applicable_frameworks) * 2
    
    return f"{int(weeks)}-{int(weeks * 1.5)} weeks"


def _get_framework_additions(framework: str) -> Dict[str, List[str]]:
    """Get additional requirements for specific frameworks"""
    additions = {
        "gdpr": {
            "controls": ["Data minimization", "Consent management", "Right to erasure"],
            "audit": ["Consent tracking", "Data processing records", "Breach notifications"]
        },
        "hipaa": {
            "controls": ["Minimum necessary access", "PHI encryption", "Business associate agreements"],
            "audit": ["PHI access logging", "Risk assessments", "Workforce training records"]
        },
        "sox": {
            "controls": ["Segregation of duties", "IT general controls", "Financial reporting controls"],
            "audit": ["Change management logs", "Access reviews", "Control testing"]
        }
    }
    return additions.get(framework, {"controls": [], "audit": []})


def _generate_custom_sql(schema: Dict[str, Any], industry: str, frameworks: List[str]) -> str:
    """Generate custom SQL for template"""
    sql_lines = [
        f"-- Custom compliance schema for {industry} industry",
        f"-- Frameworks: {', '.join(frameworks)}",
        f"-- Generated: {datetime.now().isoformat()}",
        ""
    ]
    
    for table_name, columns in schema.items():
        sql_lines.append(f"CREATE TABLE {table_name} (")
        
        column_defs = []
        for column_name, config in columns.items():
            column_def = f"    {column_name} {config['type']}"
            if config.get('primary_key'):
                column_def += " PRIMARY KEY"
            if config.get('required'):
                column_def += " NOT NULL"
            if config.get('default'):
                column_def += f" DEFAULT {config['default']}"
            column_defs.append(column_def)
        
        sql_lines.append(",\n".join(column_defs))
        sql_lines.append(");")
        sql_lines.append("")
    
    return "\n".join(sql_lines)


def _generate_implementation_guide(industry: str, frameworks: List[str]) -> List[str]:
    """Generate implementation guide for custom template"""
    return [
        f"1. Review {industry} industry-specific regulations",
        f"2. Implement {', '.join(frameworks)} compliance controls",
        "3. Set up encryption for sensitive data fields",
        "4. Configure audit logging systems",
        "5. Establish access control policies",
        "6. Conduct initial compliance assessment",
        "7. Schedule regular compliance reviews"
    ]


def _get_industry_priority(industry: IndustryTemplate) -> str:
    """Get implementation priority for industry"""
    high_priority = [IndustryTemplate.HEALTHCARE, IndustryTemplate.FINANCIAL, IndustryTemplate.GOVERNMENT]
    return "High" if industry in high_priority else "Medium"


def _estimate_compliance_cost(industry: IndustryTemplate) -> str:
    """Estimate compliance implementation cost"""
    cost_ranges = {
        IndustryTemplate.HEALTHCARE: "$50,000 - $200,000",
        IndustryTemplate.FINANCIAL: "$75,000 - $300,000", 
        IndustryTemplate.GOVERNMENT: "$100,000 - $500,000",
        IndustryTemplate.EDUCATION: "$25,000 - $100,000",
        IndustryTemplate.SAAS: "$30,000 - $150,000"
    }
    return cost_ranges.get(industry, "$20,000 - $100,000")


def _get_typical_timeline(industry: IndustryTemplate) -> str:
    """Get typical implementation timeline"""
    timelines = {
        IndustryTemplate.HEALTHCARE: "6-12 months",
        IndustryTemplate.FINANCIAL: "8-15 months",
        IndustryTemplate.GOVERNMENT: "12-24 months", 
        IndustryTemplate.EDUCATION: "4-8 months",
        IndustryTemplate.SAAS: "3-6 months"
    }
    return timelines.get(industry, "3-9 months")
