"""
Universal Compliance API Router
Provides endpoints for universal compliance management across all regulatory frameworks
"""

from fastapi import APIRouter, HTTPException, Query, Depends
from typing import List, Optional, Dict, Any
import logging
from datetime import datetime
import httpx
import os

from models.schemas import ApiHealthResponse
from core.compliance_manager import (
    UniversalComplianceManager, ComplianceFramework, IndustryType,
    UniversalComplianceScore, CrossComplianceMapping
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/compliance", tags=["Universal Compliance"])

# Service URLs
CODE_GENERATION_SERVICE_URL = os.getenv("CODE_GENERATION_SERVICE_URL", "http://localhost:8000")
SCHEMA_DETECTION_SERVICE_URL = os.getenv("SCHEMA_DETECTION_SERVICE_URL", "http://localhost:8001")
WEBSOCKET_SERVICE_URL = os.getenv("WEBSOCKET_SERVICE_URL", "https://schemasage-websocket-realtime.herokuapp.com")

# Initialize compliance manager
compliance_manager = UniversalComplianceManager()


async def send_compliance_webhook(webhook_data: dict):
    """Send compliance update webhook to WebSocket service"""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            await client.post(f"{WEBSOCKET_SERVICE_URL}/webhooks/compliance-updated", json=webhook_data)
            logger.info("Compliance webhook sent successfully")
    except Exception as e:
        logger.warning(f"Failed to send compliance webhook: {e}")


@router.get("/frameworks")
async def get_compliance_frameworks(
    industry: Optional[IndustryType] = Query(None, description="Filter by industry")
):
    """Get available compliance frameworks"""
    try:
        if industry:
            frameworks = compliance_manager.get_industry_frameworks(industry)
            return {
                "industry": industry.value,
                "frameworks": frameworks,
                "count": len(frameworks)
            }
        else:
            all_frameworks = compliance_manager.get_framework_info()
            return {
                "frameworks": all_frameworks,
                "industries": [industry.value for industry in IndustryType],
                "count": len(all_frameworks)
            }
    except Exception as e:
        logger.error(f"Error fetching compliance frameworks: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch compliance frameworks")


@router.get("/frameworks/{framework}")
async def get_framework_details(framework: ComplianceFramework):
    """Get detailed information about a specific compliance framework"""
    try:
        framework_info = compliance_manager.get_framework_info(framework)
        if not framework_info:
            raise HTTPException(status_code=404, detail="Framework not found")
        
        return {
            "framework": framework.value,
            "details": framework_info
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching framework details: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch framework details")


@router.post("/assess")
async def assess_universal_compliance(
    request: Dict[str, Any]
):
    """Assess schema compliance across multiple frameworks"""
    try:
        project_id = request.get("project_id")
        schema_data = request.get("schema_data")
        selected_frameworks = request.get("frameworks", [])
        
        if not project_id or not schema_data:
            raise HTTPException(status_code=400, detail="project_id and schema_data are required")
        
        # Convert framework strings to enums
        framework_enums = []
        for fw in selected_frameworks:
            try:
                framework_enums.append(ComplianceFramework(fw))
            except ValueError:
                logger.warning(f"Unknown framework: {fw}")
        
        # Perform universal compliance assessment
        compliance_score = await compliance_manager.assess_universal_compliance(
            project_id=project_id,
            schema_data=schema_data,
            selected_frameworks=framework_enums if framework_enums else None
        )
        
        # Send webhook notification
        webhook_data = {
            "project_id": project_id,
            "overall_score": compliance_score.overall_score,
            "risk_level": compliance_score.risk_level,
            "frameworks_assessed": list(compliance_score.framework_scores.keys()),
            "timestamp": datetime.now().isoformat()
        }
        await send_compliance_webhook(webhook_data)
        
        return {
            "assessment_id": f"assess_{project_id}_{int(datetime.now().timestamp())}",
            "project_id": compliance_score.project_id,
            "overall_score": compliance_score.overall_score,
            "framework_scores": compliance_score.framework_scores,
            "cross_compliance_coverage": compliance_score.cross_compliance_coverage,
            "risk_level": compliance_score.risk_level,
            "last_assessed": compliance_score.last_assessed.isoformat(),
            "next_assessment_due": compliance_score.next_assessment_due.isoformat(),
            "recommendations": [
                "Implement encryption to improve multiple framework scores",
                "Add audit logging for better compliance coverage",
                "Consider access control improvements"
            ]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error assessing universal compliance: {e}")
        raise HTTPException(status_code=500, detail="Failed to assess compliance")


@router.get("/cross-analysis")
async def get_cross_compliance_analysis(
    frameworks: List[ComplianceFramework] = Query(..., description="Frameworks to analyze")
):
    """Analyze compliance overlaps and conflicts between frameworks"""
    try:
        if len(frameworks) < 2:
            raise HTTPException(status_code=400, detail="At least 2 frameworks required for cross-analysis")
        
        analysis = compliance_manager.get_cross_compliance_analysis(frameworks)
        
        return {
            "analysis_id": f"cross_{int(datetime.now().timestamp())}",
            "analysis": analysis,
            "generated_at": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error performing cross-compliance analysis: {e}")
        raise HTTPException(status_code=500, detail="Failed to perform cross-compliance analysis")


@router.get("/templates")
async def get_compliance_templates(
    industry: IndustryType = Query(..., description="Industry type"),
    data_type: str = Query("general", description="Data type (patient, student, customer, financial)")
):
    """Get industry-specific compliance templates"""
    try:
        template = compliance_manager.generate_compliance_templates(industry, data_type)
        
        return {
            "template_id": f"template_{industry.value}_{data_type}",
            "template": template,
            "generated_at": datetime.now().isoformat(),
            "usage_instructions": [
                "Apply recommended security controls to your schema",
                "Include required fields for compliance",
                "Implement audit requirements as specified",
                "Regular compliance monitoring recommended"
            ]
        }
        
    except Exception as e:
        logger.error(f"Error generating compliance templates: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate compliance templates")


@router.post("/multi-framework-detection")
async def multi_framework_detection(
    request: Dict[str, Any]
):
    """Enhanced schema detection with multi-framework PII detection"""
    try:
        schema_data = request.get("schema_data")
        frameworks = request.get("frameworks", [])
        
        if not schema_data:
            raise HTTPException(status_code=400, detail="schema_data is required")
        
        # Call schema detection service with compliance frameworks
        async with httpx.AsyncClient(timeout=30.0) as client:
            detection_response = await client.post(
                f"{SCHEMA_DETECTION_SERVICE_URL}/api/detect",
                json={
                    "data": schema_data,
                    "compliance_frameworks": frameworks,
                    "enhanced_pii_detection": True
                }
            )
            
            if detection_response.status_code != 200:
                raise HTTPException(status_code=502, detail="Schema detection service error")
            
            detection_result = detection_response.json()
        
        # Enhance with universal compliance insights
        compliance_insights = {
            "detected_pii_types": [],
            "compliance_warnings": [],
            "framework_recommendations": []
        }
        
        # Add framework-specific recommendations
        for framework in frameworks:
            try:
                fw_enum = ComplianceFramework(framework)
                fw_info = compliance_manager.get_framework_info(fw_enum)
                compliance_insights["framework_recommendations"].append({
                    "framework": framework,
                    "requirements": fw_info.get("key_requirements", [])
                })
            except ValueError:
                continue
        
        return {
            "detection_id": f"detect_{int(datetime.now().timestamp())}",
            "schema_analysis": detection_result,
            "compliance_insights": compliance_insights,
            "multi_framework_assessment": True,
            "detected_at": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in multi-framework detection: {e}")
        raise HTTPException(status_code=500, detail="Failed to perform multi-framework detection")


@router.post("/generate-compliant-code")
async def generate_compliant_code(
    request: Dict[str, Any]
):
    """Generate compliance-ready code templates"""
    try:
        schema_data = request.get("schema_data")
        industry = request.get("industry")
        frameworks = request.get("frameworks", [])
        code_type = request.get("code_type", "sql")
        
        if not schema_data or not industry:
            raise HTTPException(status_code=400, detail="schema_data and industry are required")
        
        try:
            industry_enum = IndustryType(industry)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid industry type")
        
        # Get compliance template for the industry
        template = compliance_manager.generate_compliance_templates(industry_enum, "general")
        
        # Call code generation service with compliance requirements
        async with httpx.AsyncClient(timeout=30.0) as client:
            generation_response = await client.post(
                f"{CODE_GENERATION_SERVICE_URL}/api/generate",
                json={
                    "schema": schema_data,
                    "format": code_type,
                    "compliance_template": template,
                    "frameworks": frameworks,
                    "industry_specific": True
                }
            )
            
            if generation_response.status_code != 200:
                raise HTTPException(status_code=502, detail="Code generation service error")
            
            generation_result = generation_response.json()
        
        # Add compliance annotations
        compliance_annotations = {
            "industry": industry,
            "applicable_frameworks": frameworks,
            "security_controls": template.get("security_controls", []),
            "audit_requirements": template.get("audit_requirements", []),
            "compliance_notes": [
                f"Generated for {industry} industry compliance",
                "Includes required security controls",
                "Audit logging enabled",
                "Regular compliance monitoring recommended"
            ]
        }
        
        return {
            "generation_id": f"gen_{int(datetime.now().timestamp())}",
            "generated_code": generation_result.get("code", ""),
            "compliance_annotations": compliance_annotations,
            "template_used": template,
            "generated_at": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating compliant code: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate compliant code")


@router.get("/project/{project_id}/status")
async def get_project_compliance_status(project_id: str):
    """Get comprehensive compliance status for a project"""
    try:
        # In a real implementation, this would fetch from database
        # For now, return mock data with universal compliance structure
        
        mock_status = {
            "project_id": project_id,
            "overall_compliance_score": 78.5,
            "frameworks": {
                "gdpr": {
                    "score": 85.0,
                    "status": "partial",
                    "violations": 2,
                    "last_assessed": datetime.now().isoformat()
                },
                "soc2": {
                    "score": 72.0,
                    "status": "partial", 
                    "violations": 4,
                    "last_assessed": datetime.now().isoformat()
                },
                "hipaa": {
                    "score": 90.0,
                    "status": "compliant",
                    "violations": 0,
                    "last_assessed": datetime.now().isoformat()
                }
            },
            "risk_level": "medium",
            "total_violations": 6,
            "critical_violations": 1,
            "next_assessment_due": (datetime.now()).isoformat(),
            "cross_compliance_coverage": 82.3,
            "recommendations": [
                "Implement additional encryption controls",
                "Enhance access control policies",
                "Improve audit logging coverage"
            ]
        }
        
        return mock_status
        
    except Exception as e:
        logger.error(f"Error fetching project compliance status: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch compliance status")


@router.get("/industry/{industry}/recommendations")
async def get_industry_compliance_recommendations(industry: IndustryType):
    """Get compliance recommendations for a specific industry"""
    try:
        frameworks = compliance_manager.get_industry_frameworks(industry)
        
        recommendations = {
            "industry": industry.value,
            "required_frameworks": [fw for fw in frameworks if fw.get("priority") == "required"],
            "recommended_frameworks": [fw for fw in frameworks if fw.get("priority") == "recommended"],
            "implementation_priority": [],
            "cost_estimates": {},
            "timeline_estimates": {}
        }
        
        # Industry-specific recommendations
        if industry == IndustryType.HEALTHCARE:
            recommendations["implementation_priority"] = [
                "HIPAA compliance (required)",
                "Patient data encryption", 
                "Access control implementation",
                "Audit logging system"
            ]
            recommendations["cost_estimates"] = {
                "initial_setup": "$10,000 - $50,000",
                "annual_maintenance": "$5,000 - $15,000"
            }
        elif industry == IndustryType.EDUCATION:
            recommendations["implementation_priority"] = [
                "FERPA compliance (required)",
                "Student record protection",
                "Parental consent management", 
                "Directory information controls"
            ]
            recommendations["cost_estimates"] = {
                "initial_setup": "$5,000 - $25,000",
                "annual_maintenance": "$2,000 - $8,000"
            }
        elif industry == IndustryType.SAAS:
            recommendations["implementation_priority"] = [
                "SOC 2 Type II (required)",
                "Multi-tenant data isolation",
                "Customer data encryption",
                "Incident response procedures"
            ]
            recommendations["cost_estimates"] = {
                "initial_setup": "$15,000 - $75,000",
                "annual_maintenance": "$10,000 - $30,000"
            }
        
        return recommendations
        
    except Exception as e:
        logger.error(f"Error fetching industry recommendations: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch industry recommendations")


@router.get("/health")
async def health_check():
    """Health check endpoint for compliance service"""
    return ApiHealthResponse(
        status="healthy",
        service="Universal Compliance Manager",
        version="1.0.0",
        timestamp=datetime.now().isoformat(),
        details={
            "supported_frameworks": len(ComplianceFramework),
            "supported_industries": len(IndustryType),
            "cross_mappings_loaded": len(compliance_manager.cross_mappings)
        }
    )
