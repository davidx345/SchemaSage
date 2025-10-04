"""
Enhanced Schema Detection Router with Universal Compliance
Integrates multi-framework PII detection for universal compliance
"""

from fastapi import APIRouter, HTTPException, Depends, Query, UploadFile, File
from typing import List, Dict, Any, Optional
import logging
import json
from datetime import datetime
import httpx
import os

from models.schemas import DetectionResponse, SchemaResponse
from core.schema_detector import SchemaDetector
from core.universal_pii_detector import (
    UniversalPIIDetector, PIIFramework, PIIType, PIIDetectionResult
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/compliance", tags=["Universal Compliance Detection"])

# Service URLs
WEBSOCKET_SERVICE_URL = os.getenv("WEBSOCKET_SERVICE_URL", "https://schemasage-websocket-realtime.herokuapp.com")

# Initialize detectors
schema_detector = SchemaDetector()
pii_detector = UniversalPIIDetector()


async def send_detection_webhook(webhook_data: dict):
    """Send detection webhook to WebSocket service"""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            await client.post(f"{WEBSOCKET_SERVICE_URL}/webhooks/schema-detected", json=webhook_data)
            logger.info("Schema detection webhook sent successfully")
    except Exception as e:
        logger.warning(f"Failed to send detection webhook: {e}")


@router.post("/multi-framework-detect")
async def multi_framework_schema_detection(
    request: Dict[str, Any]
):
    """Enhanced schema detection with multi-framework PII analysis"""
    try:
        data = request.get("data")
        frameworks = request.get("frameworks", [])
        project_id = request.get("project_id")
        
        if not data:
            raise HTTPException(status_code=400, detail="Data is required")
        
        # Convert framework strings to enums
        target_frameworks = []
        for fw in frameworks:
            try:
                target_frameworks.append(PIIFramework(fw))
            except ValueError:
                logger.warning(f"Unknown framework: {fw}")
        
        # Perform standard schema detection first
        detection_settings = request.get("settings", {})
        schema_detector.configure_settings(detection_settings)
        
        # Parse the data
        parsed_data = schema_detector.data_parser.parse_data(data)
        
        # Analyze schema structure
        schema_analysis = await schema_detector.schema_analyzer.analyze_schema(parsed_data)
        
        # AI enhancement if available
        enhanced_schema = await schema_detector.ai_enhancer.enhance_schema(schema_analysis)
        
        # Build schema data structure for PII detection
        schema_data = {}
        for table in enhanced_schema.tables:
            schema_data[table.table_name] = {
                "columns": [
                    {
                        "name": col.column_name,
                        "type": col.type,
                        "constraints": col.constraints
                    }
                    for col in table.columns
                ]
            }
        
        # Perform universal PII detection
        pii_results = pii_detector.detect_pii_multi_framework(schema_data, target_frameworks)
        
        # Generate compliance summary
        compliance_summary = pii_detector.generate_compliance_summary(pii_results)
        
        # Format PII results for response
        formatted_pii_results = {}
        for field_name, result in pii_results.items():
            formatted_pii_results[field_name] = {
                "detected_pii_types": [pii_type.value for pii_type in result.detected_pii_types],
                "applicable_frameworks": [fw.value for fw in result.applicable_frameworks],
                "confidence_score": result.confidence_score,
                "sensitivity_level": result.sensitivity_level,
                "recommendations": result.recommendations,
                "compliance_notes": result.compliance_notes
            }
        
        # Enhance schema with compliance metadata
        for table in enhanced_schema.tables:
            for column in table.columns:
                field_key = f"{table.table_name}.{column.column_name}"
                if field_key in pii_results:
                    pii_result = pii_results[field_key]
                    column.metadata.update({
                        "pii_detected": True,
                        "pii_types": [t.value for t in pii_result.detected_pii_types],
                        "compliance_frameworks": [f.value for f in pii_result.applicable_frameworks],
                        "sensitivity_level": pii_result.sensitivity_level,
                        "encryption_required": pii_result.sensitivity_level >= 4
                    })
        
        # Send webhook notification
        if project_id:
            webhook_data = {
                "project_id": project_id,
                "schema_name": enhanced_schema.schema_name,
                "table_count": len(enhanced_schema.tables),
                "pii_fields_detected": len(pii_results),
                "frameworks_analyzed": [fw.value for fw in target_frameworks],
                "compliance_risk": compliance_summary.get("compliance_readiness", "unknown"),
                "timestamp": datetime.now().isoformat()
            }
            await send_detection_webhook(webhook_data)
        
        return {
            "detection_id": f"detect_{int(datetime.now().timestamp())}",
            "schema_analysis": enhanced_schema.to_dict(),
            "pii_detection_results": formatted_pii_results,
            "compliance_summary": compliance_summary,
            "frameworks_analyzed": [fw.value for fw in target_frameworks],
            "universal_compliance": True,
            "detected_at": datetime.now().isoformat(),
            "recommendations": [
                "Review detected PII fields for compliance requirements",
                "Implement recommended security controls",
                "Consider encryption for high-sensitivity fields",
                "Establish data retention policies",
                "Regular compliance assessments recommended"
            ]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in multi-framework detection: {e}")
        raise HTTPException(status_code=500, detail="Failed to perform multi-framework detection")


@router.post("/industry-specific-detect")
async def industry_specific_detection(
    request: Dict[str, Any]
):
    """Industry-specific schema detection with tailored compliance analysis"""
    try:
        data = request.get("data")
        industry = request.get("industry")  # healthcare, education, financial, government, saas
        project_id = request.get("project_id")
        
        if not data or not industry:
            raise HTTPException(status_code=400, detail="Data and industry are required")
        
        # Map industry to relevant frameworks
        industry_frameworks = {
            "healthcare": [PIIFramework.HIPAA, PIIFramework.GDPR, PIIFramework.SOC2],
            "education": [PIIFramework.FERPA, PIIFramework.GDPR, PIIFramework.CCPA],
            "financial": [PIIFramework.SOX, PIIFramework.PCI_DSS, PIIFramework.GDPR],
            "government": [PIIFramework.FISMA, PIIFramework.NIST, PIIFramework.ITAR],
            "saas": [PIIFramework.SOC2, PIIFramework.GDPR, PIIFramework.CCPA],
            "manufacturing": [PIIFramework.ITAR, PIIFramework.GDPR],
            "nonprofit": [PIIFramework.GDPR, PIIFramework.CCPA]
        }
        
        target_frameworks = industry_frameworks.get(industry, [PIIFramework.GDPR])
        
        # Use the multi-framework detection with industry-specific frameworks
        enhanced_request = {
            "data": data,
            "frameworks": [fw.value for fw in target_frameworks],
            "project_id": project_id,
            "industry_context": industry
        }
        
        # Call the multi-framework detection
        result = await multi_framework_schema_detection(enhanced_request)
        
        # Add industry-specific recommendations
        industry_recommendations = {
            "healthcare": [
                "Ensure HIPAA minimum necessary compliance",
                "Implement patient consent tracking",
                "Consider PHI de-identification options",
                "Establish breach notification procedures"
            ],
            "education": [
                "Implement FERPA directory opt-out controls",
                "Ensure parental consent for under-18 students",
                "Protect academic records with appropriate access controls",
                "Consider legitimate educational interest documentation"
            ],
            "financial": [
                "Implement SOX segregation of duties",
                "Ensure PCI DSS cardholder data protection",
                "Establish financial reporting audit trails",
                "Consider fraud detection mechanisms"
            ],
            "government": [
                "Implement security classification controls",
                "Ensure continuous monitoring compliance",
                "Establish export control procedures",
                "Consider insider threat protection"
            ],
            "saas": [
                "Implement multi-tenant data isolation",
                "Ensure SOC 2 Type II compliance",
                "Establish customer data processing agreements",
                "Consider data residency requirements"
            ]
        }
        
        result["industry"] = industry
        result["industry_specific_recommendations"] = industry_recommendations.get(industry, [])
        result["compliance_priority"] = "high" if industry in ["healthcare", "financial", "government"] else "medium"
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in industry-specific detection: {e}")
        raise HTTPException(status_code=500, detail="Failed to perform industry-specific detection")


@router.get("/frameworks")
async def get_supported_frameworks():
    """Get list of supported compliance frameworks"""
    framework_info = {}
    
    for framework in PIIFramework:
        framework_info[framework.value] = {
            "name": framework.value.upper(),
            "description": f"{framework.value.upper()} compliance framework",
            "pii_types_covered": [pii_type.value for pii_type in PIIType],
            "industry_focus": _get_framework_industries(framework)
        }
    
    return {
        "supported_frameworks": framework_info,
        "total_frameworks": len(PIIFramework),
        "pii_types": [pii_type.value for pii_type in PIIType],
        "industries_supported": [
            "healthcare", "education", "financial", "government", 
            "saas", "manufacturing", "nonprofit"
        ]
    }


@router.post("/pii-analysis")
async def standalone_pii_analysis(
    request: Dict[str, Any]
):
    """Standalone PII analysis without full schema detection"""
    try:
        schema_data = request.get("schema_data")
        frameworks = request.get("frameworks", [])
        
        if not schema_data:
            raise HTTPException(status_code=400, detail="Schema data is required")
        
        # Convert framework strings to enums
        target_frameworks = []
        for fw in frameworks:
            try:
                target_frameworks.append(PIIFramework(fw))
            except ValueError:
                logger.warning(f"Unknown framework: {fw}")
        
        # Perform PII detection
        pii_results = pii_detector.detect_pii_multi_framework(schema_data, target_frameworks)
        
        # Generate compliance summary
        compliance_summary = pii_detector.generate_compliance_summary(pii_results)
        
        # Format results
        formatted_results = {}
        for field_name, result in pii_results.items():
            formatted_results[field_name] = {
                "detected_pii_types": [pii_type.value for pii_type in result.detected_pii_types],
                "applicable_frameworks": [fw.value for fw in result.applicable_frameworks],
                "confidence_score": result.confidence_score,
                "sensitivity_level": result.sensitivity_level,
                "recommendations": result.recommendations,
                "compliance_notes": result.compliance_notes
            }
        
        return {
            "analysis_id": f"pii_{int(datetime.now().timestamp())}",
            "pii_detection_results": formatted_results,
            "compliance_summary": compliance_summary,
            "frameworks_analyzed": [fw.value for fw in target_frameworks],
            "analyzed_at": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in PII analysis: {e}")
        raise HTTPException(status_code=500, detail="Failed to perform PII analysis")


@router.get("/health")
async def compliance_health_check():
    """Health check for compliance detection features"""
    return {
        "status": "healthy",
        "service": "Universal Compliance Detection",
        "version": "1.0.0",
        "features": {
            "multi_framework_detection": True,
            "industry_specific_analysis": True,
            "pii_pattern_matching": True,
            "compliance_recommendations": True
        },
        "supported_frameworks": len(PIIFramework),
        "supported_pii_types": len(PIIType),
        "timestamp": datetime.now().isoformat()
    }


def _get_framework_industries(framework: PIIFramework) -> List[str]:
    """Get industries that typically use this framework"""
    industry_mapping = {
        PIIFramework.HIPAA: ["healthcare"],
        PIIFramework.FERPA: ["education"],
        PIIFramework.SOX: ["financial"],
        PIIFramework.PCI_DSS: ["financial", "saas"],
        PIIFramework.FISMA: ["government"],
        PIIFramework.ITAR: ["government", "manufacturing"],
        PIIFramework.SOC2: ["saas", "healthcare", "financial"],
        PIIFramework.GDPR: ["all"],
        PIIFramework.CCPA: ["saas", "education", "nonprofit"],
        PIIFramework.NIST: ["government", "healthcare"]
    }
    
    return industry_mapping.get(framework, ["general"])
