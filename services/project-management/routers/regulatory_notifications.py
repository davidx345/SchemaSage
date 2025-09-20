"""
Regulatory Change Notifications Router
Monitors and notifies about regulatory changes affecting database schemas
"""
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime, timedelta
import json
import uuid
import asyncio
from ..core.auth import get_current_user

router = APIRouter(prefix="/compliance", tags=["regulatory-notifications"])

# Models
class RegulatoryUpdate(BaseModel):
    regulation: str
    change_type: str = Field(..., description="amendment, new_requirement, clarification")
    effective_date: str
    description: str
    impact_assessment: str = Field(..., description="low, medium, high, critical")
    affected_schemas: List[str] = Field(default_factory=list)
    required_actions: List[str] = Field(default_factory=list)
    deadline: Optional[str] = None

class ComplianceSubscription(BaseModel):
    frameworks: List[str]
    notification_method: str = Field(..., description="email, webhook, dashboard")
    urgency_filter: str = Field(default="high", description="all, high, critical")

class RegulatoryChangeImpact(BaseModel):
    project_id: str
    regulation: str
    impact_level: str
    required_changes: List[str]
    estimated_effort: str
    deadline: Optional[str] = None

# Mock regulatory database
REGULATORY_UPDATES = [
    {
        "id": "reg_001",
        "regulation": "GDPR",
        "change_type": "amendment",
        "effective_date": "2025-12-01",
        "description": "New requirements for AI system data processing transparency and consent management",
        "impact_assessment": "medium",
        "affected_schemas": ["proj_123", "proj_456"],
        "required_actions": [
            "Add AI processing consent field to user tables",
            "Implement automated deletion for AI training data",
            "Add data processing purpose tracking",
            "Update privacy policy consent mechanisms"
        ],
        "deadline": "2025-11-15",
        "source": "European Data Protection Board",
        "reference_url": "https://edpb.europa.eu/our-work-tools/our-documents/guidelines/guidelines-32025-ai-and-data-protection_en",
        "published_date": "2025-09-15"
    },
    {
        "id": "reg_002",
        "regulation": "CCPA",
        "change_type": "new_requirement",
        "effective_date": "2026-01-01",
        "description": "Enhanced data minimization requirements for consumer data collection",
        "impact_assessment": "high",
        "affected_schemas": ["proj_789"],
        "required_actions": [
            "Implement data retention policies",
            "Add data collection purpose limitation",
            "Update consumer rights management",
            "Implement automated data deletion"
        ],
        "deadline": "2025-12-01",
        "source": "California Consumer Privacy Act",
        "reference_url": "https://oag.ca.gov/privacy/ccpa",
        "published_date": "2025-09-10"
    },
    {
        "id": "reg_003",
        "regulation": "HIPAA",
        "change_type": "clarification",
        "effective_date": "2025-10-15",
        "description": "Updated guidance on cloud storage encryption requirements for PHI",
        "impact_assessment": "critical",
        "affected_schemas": ["proj_health_001"],
        "required_actions": [
            "Upgrade encryption standards to AES-256",
            "Implement key management best practices",
            "Add audit logging for all PHI access",
            "Update Business Associate Agreements"
        ],
        "deadline": "2025-10-10",
        "source": "HHS Office for Civil Rights",
        "reference_url": "https://www.hhs.gov/hipaa/for-professionals/security/guidance/index.html",
        "published_date": "2025-09-01"
    },
    {
        "id": "reg_004",
        "regulation": "SOX",
        "change_type": "amendment",
        "effective_date": "2026-04-01",
        "description": "Enhanced financial data integrity requirements for automated systems",
        "impact_assessment": "high",
        "affected_schemas": ["proj_finance_001", "proj_finance_002"],
        "required_actions": [
            "Implement automated data validation",
            "Add change management controls",
            "Enhance audit trail capabilities",
            "Update financial reporting processes"
        ],
        "deadline": "2026-03-01",
        "source": "Securities and Exchange Commission",
        "reference_url": "https://www.sec.gov/rules/final.shtml",
        "published_date": "2025-09-05"
    },
    {
        "id": "reg_005",
        "regulation": "PCI_DSS",
        "change_type": "new_requirement",
        "effective_date": "2025-11-30",
        "description": "Enhanced tokenization requirements for payment data processing",
        "impact_assessment": "critical",
        "affected_schemas": ["proj_payment_001"],
        "required_actions": [
            "Implement end-to-end tokenization",
            "Upgrade cardholder data encryption",
            "Add real-time fraud detection",
            "Update payment processing workflows"
        ],
        "deadline": "2025-11-20",
        "source": "PCI Security Standards Council",
        "reference_url": "https://www.pcisecuritystandards.org/",
        "published_date": "2025-08-30"
    }
]

USER_SUBSCRIPTIONS = {}

class RegulatoryMonitor:
    """Regulatory change monitoring and analysis engine"""
    
    def __init__(self):
        self.framework_mappings = self._load_framework_mappings()
        self.schema_analyzers = self._load_schema_analyzers()
    
    def _load_framework_mappings(self) -> Dict[str, Any]:
        """Load regulatory framework to schema element mappings"""
        return {
            "GDPR": {
                "keywords": ["personal_data", "consent", "privacy", "data_subject", "processing_purpose"],
                "required_fields": ["consent_status", "data_retention_period", "processing_purpose"],
                "table_patterns": ["users", "customers", "profiles", "personal_info"]
            },
            "CCPA": {
                "keywords": ["consumer_data", "personal_information", "sale_opt_out", "data_categories"],
                "required_fields": ["opt_out_status", "data_collection_purpose", "third_party_sharing"],
                "table_patterns": ["consumers", "customers", "user_data", "marketing_data"]
            },
            "HIPAA": {
                "keywords": ["phi", "medical", "health", "patient", "diagnosis", "treatment"],
                "required_fields": ["patient_consent", "hipaa_authorization", "access_log"],
                "table_patterns": ["patients", "medical_records", "health_data", "diagnoses"]
            },
            "SOX": {
                "keywords": ["financial", "revenue", "transactions", "accounting", "audit"],
                "required_fields": ["created_by", "approved_by", "audit_trail", "change_log"],
                "table_patterns": ["transactions", "financial_records", "accounting", "revenue"]
            },
            "PCI_DSS": {
                "keywords": ["payment", "card", "cardholder", "transaction", "cvv", "pan"],
                "required_fields": ["encryption_status", "tokenization", "access_control"],
                "table_patterns": ["payments", "cards", "transactions", "billing"]
            }
        }
    
    def _load_schema_analyzers(self) -> Dict[str, Any]:
        """Load schema analysis patterns for compliance impact"""
        return {
            "data_fields": {
                "personal_identifiers": ["email", "phone", "ssn", "name", "address"],
                "financial_data": ["account_number", "routing_number", "card_number", "amount"],
                "health_data": ["diagnosis", "treatment", "medication", "medical_record"],
                "sensitive_data": ["password", "token", "key", "secret", "credential"]
            },
            "encryption_indicators": ["encrypted", "hashed", "tokenized", "cipher"],
            "audit_indicators": ["created_at", "updated_at", "created_by", "audit_log"]
        }
    
    async def analyze_regulatory_impact(self, project_schemas: List[Dict[str, Any]], regulation_update: Dict[str, Any]) -> List[RegulatoryChangeImpact]:
        """Analyze impact of regulatory changes on project schemas"""
        impacts = []
        regulation = regulation_update["regulation"]
        framework_mapping = self.framework_mappings.get(regulation, {})
        
        for schema in project_schemas:
            project_id = schema.get("project_id", "unknown")
            tables = schema.get("schema", {}).get("tables", {})
            
            # Check if this schema is affected by the regulation
            is_affected = self._is_schema_affected(tables, framework_mapping)
            
            if is_affected:
                required_changes = self._identify_required_changes(tables, regulation_update, framework_mapping)
                impact_level = self._assess_impact_level(required_changes, regulation_update)
                estimated_effort = self._estimate_implementation_effort(required_changes)
                
                impact = RegulatoryChangeImpact(
                    project_id=project_id,
                    regulation=regulation,
                    impact_level=impact_level,
                    required_changes=required_changes,
                    estimated_effort=estimated_effort,
                    deadline=regulation_update.get("deadline")
                )
                impacts.append(impact)
        
        return impacts
    
    def _is_schema_affected(self, tables: Dict[str, Any], framework_mapping: Dict[str, Any]) -> bool:
        """Check if schema is affected by regulatory framework"""
        keywords = framework_mapping.get("keywords", [])
        table_patterns = framework_mapping.get("table_patterns", [])
        
        # Check table names
        for table_name in tables.keys():
            if any(pattern in table_name.lower() for pattern in table_patterns):
                return True
        
        # Check column names
        for table in tables.values():
            columns = table.get("columns", {})
            for column_name in columns.keys():
                if any(keyword in column_name.lower() for keyword in keywords):
                    return True
        
        return False
    
    def _identify_required_changes(self, tables: Dict[str, Any], regulation_update: Dict[str, Any], framework_mapping: Dict[str, Any]) -> List[str]:
        """Identify specific changes required for compliance"""
        required_changes = []
        required_fields = framework_mapping.get("required_fields", [])
        
        # Check for missing required fields
        for table_name, table in tables.items():
            columns = table.get("columns", {})
            
            for required_field in required_fields:
                if required_field not in columns:
                    required_changes.append(f"Add {required_field} field to {table_name} table")
        
        # Add regulation-specific requirements
        regulation_actions = regulation_update.get("required_actions", [])
        for action in regulation_actions:
            if not any(action.lower() in change.lower() for change in required_changes):
                required_changes.append(action)
        
        return required_changes
    
    def _assess_impact_level(self, required_changes: List[str], regulation_update: Dict[str, Any]) -> str:
        """Assess impact level based on changes and regulation severity"""
        base_impact = regulation_update.get("impact_assessment", "medium")
        change_count = len(required_changes)
        
        if change_count == 0:
            return "low"
        elif change_count <= 2:
            return base_impact
        elif change_count <= 5:
            # Increase impact level
            impact_levels = ["low", "medium", "high", "critical"]
            current_index = impact_levels.index(base_impact)
            return impact_levels[min(current_index + 1, len(impact_levels) - 1)]
        else:
            return "critical"
    
    def _estimate_implementation_effort(self, required_changes: List[str]) -> str:
        """Estimate implementation effort"""
        change_count = len(required_changes)
        
        if change_count == 0:
            return "No changes required"
        elif change_count <= 2:
            return "1-2 days"
        elif change_count <= 5:
            return "1-2 weeks"
        else:
            return "2-4 weeks"

# Global regulatory monitor
regulatory_monitor = RegulatoryMonitor()

@router.get("/regulations/updates")
async def get_regulatory_updates(
    regulation: Optional[str] = None,
    impact_level: Optional[str] = None,
    limit: int = 20
):
    """Get recent regulatory changes"""
    try:
        # Filter updates
        filtered_updates = REGULATORY_UPDATES.copy()
        
        if regulation:
            filtered_updates = [u for u in filtered_updates if u["regulation"].lower() == regulation.lower()]
        
        if impact_level:
            filtered_updates = [u for u in filtered_updates if u["impact_assessment"] == impact_level]
        
        # Sort by published date
        filtered_updates.sort(key=lambda x: x["published_date"], reverse=True)
        
        # Limit results
        limited_updates = filtered_updates[:limit]
        
        return {
            "success": True,
            "data": {
                "updates": limited_updates,
                "total_count": len(filtered_updates)
            }
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get regulatory updates: {str(e)}")

@router.post("/regulations/subscribe")
async def subscribe_to_regulatory_updates(
    subscription: ComplianceSubscription,
    current_user: dict = Depends(get_current_user)
):
    """Subscribe to regulatory updates"""
    try:
        user_id = current_user["sub"]
        subscription_id = f"sub_{uuid.uuid4().hex[:16]}"
        
        subscription_data = subscription.dict()
        subscription_data["id"] = subscription_id
        subscription_data["user_id"] = user_id
        subscription_data["created_at"] = datetime.now().isoformat()
        subscription_data["active"] = True
        
        if user_id not in USER_SUBSCRIPTIONS:
            USER_SUBSCRIPTIONS[user_id] = []
        
        USER_SUBSCRIPTIONS[user_id].append(subscription_data)
        
        return {
            "success": True,
            "data": {
                "subscription_id": subscription_id,
                "status": "active",
                "frameworks": subscription.frameworks,
                "notification_method": subscription.notification_method
            }
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to subscribe to updates: {str(e)}")

@router.get("/regulations/subscriptions")
async def get_user_subscriptions(current_user: dict = Depends(get_current_user)):
    """Get user's regulatory subscriptions"""
    try:
        user_id = current_user["sub"]
        user_subscriptions = USER_SUBSCRIPTIONS.get(user_id, [])
        
        return {
            "success": True,
            "data": {
                "subscriptions": user_subscriptions,
                "total_count": len(user_subscriptions)
            }
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get subscriptions: {str(e)}")

@router.delete("/regulations/subscriptions/{subscription_id}")
async def unsubscribe_from_updates(
    subscription_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Unsubscribe from regulatory updates"""
    try:
        user_id = current_user["sub"]
        user_subscriptions = USER_SUBSCRIPTIONS.get(user_id, [])
        
        # Find and remove subscription
        subscription_index = next((i for i, s in enumerate(user_subscriptions) if s["id"] == subscription_id), None)
        if subscription_index is None:
            raise HTTPException(status_code=404, detail="Subscription not found")
        
        removed_subscription = user_subscriptions.pop(subscription_index)
        
        return {
            "success": True,
            "data": {
                "subscription_id": subscription_id,
                "status": "unsubscribed"
            }
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to unsubscribe: {str(e)}")

@router.post("/regulations/impact-analysis")
async def analyze_regulatory_impact(
    project_schemas: List[Dict[str, Any]],
    regulation_id: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Analyze impact of regulatory changes on project schemas"""
    try:
        impacts = []
        
        # Get regulations to analyze
        regulations_to_check = REGULATORY_UPDATES.copy()
        if regulation_id:
            regulations_to_check = [u for u in regulations_to_check if u["id"] == regulation_id]
        
        # Analyze impact for each regulation
        for regulation_update in regulations_to_check:
            regulation_impacts = await regulatory_monitor.analyze_regulatory_impact(project_schemas, regulation_update)
            impacts.extend(regulation_impacts)
        
        # Group impacts by project
        impacts_by_project = {}
        for impact in impacts:
            project_id = impact.project_id
            if project_id not in impacts_by_project:
                impacts_by_project[project_id] = []
            impacts_by_project[project_id].append(impact.dict())
        
        return {
            "success": True,
            "data": {
                "impact_analysis": impacts_by_project,
                "total_impacts": len(impacts),
                "critical_impacts": len([i for i in impacts if i.impact_level == "critical"]),
                "high_impacts": len([i for i in impacts if i.impact_level == "high"]),
                "analysis_date": datetime.now().isoformat()
            }
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to analyze regulatory impact: {str(e)}")

@router.get("/regulations/frameworks")
async def get_supported_frameworks():
    """Get list of supported regulatory frameworks"""
    try:
        frameworks = []
        for framework, mapping in regulatory_monitor.framework_mappings.items():
            framework_info = {
                "name": framework,
                "description": _get_framework_description(framework),
                "keywords": mapping["keywords"],
                "required_fields": mapping["required_fields"],
                "applicable_tables": mapping["table_patterns"]
            }
            frameworks.append(framework_info)
        
        return {
            "success": True,
            "data": {
                "frameworks": frameworks,
                "total_count": len(frameworks)
            }
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get frameworks: {str(e)}")

def _get_framework_description(framework: str) -> str:
    """Get description for regulatory framework"""
    descriptions = {
        "GDPR": "General Data Protection Regulation - EU privacy and data protection law",
        "CCPA": "California Consumer Privacy Act - California state privacy law",
        "HIPAA": "Health Insurance Portability and Accountability Act - US healthcare privacy law",
        "SOX": "Sarbanes-Oxley Act - US financial reporting and corporate disclosure law",
        "PCI_DSS": "Payment Card Industry Data Security Standard - Payment card data protection standard"
    }
    return descriptions.get(framework, "Regulatory compliance framework")

@router.get("/regulations/compliance-checklist/{regulation}")
async def get_compliance_checklist(regulation: str):
    """Get compliance checklist for specific regulation"""
    try:
        framework_mapping = regulatory_monitor.framework_mappings.get(regulation.upper())
        if not framework_mapping:
            raise HTTPException(status_code=404, detail="Regulation not supported")
        
        checklist = {
            "regulation": regulation.upper(),
            "description": _get_framework_description(regulation.upper()),
            "requirements": [
                {
                    "category": "Data Fields",
                    "items": [f"Implement {field} field" for field in framework_mapping["required_fields"]]
                },
                {
                    "category": "Table Structure",
                    "items": [f"Review {pattern} tables for compliance" for pattern in framework_mapping["table_patterns"]]
                },
                {
                    "category": "Data Protection",
                    "items": [
                        "Implement encryption for sensitive data",
                        "Add access control mechanisms",
                        "Set up audit logging"
                    ]
                },
                {
                    "category": "User Rights",
                    "items": [
                        "Implement data subject access rights",
                        "Add data deletion capabilities",
                        "Provide data portability options"
                    ]
                }
            ],
            "keywords_to_monitor": framework_mapping["keywords"]
        }
        
        return {
            "success": True,
            "data": {
                "checklist": checklist
            }
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get compliance checklist: {str(e)}")

@router.get("/regulations/deadlines")
async def get_upcoming_deadlines(days_ahead: int = 90):
    """Get upcoming regulatory compliance deadlines"""
    try:
        current_date = datetime.now()
        cutoff_date = current_date + timedelta(days=days_ahead)
        
        upcoming_deadlines = []
        for update in REGULATORY_UPDATES:
            if update.get("deadline"):
                deadline_date = datetime.fromisoformat(update["deadline"])
                if current_date <= deadline_date <= cutoff_date:
                    days_remaining = (deadline_date - current_date).days
                    
                    deadline_info = {
                        "regulation": update["regulation"],
                        "description": update["description"],
                        "deadline": update["deadline"],
                        "days_remaining": days_remaining,
                        "impact_assessment": update["impact_assessment"],
                        "required_actions": update["required_actions"],
                        "urgency": "critical" if days_remaining <= 30 else "high" if days_remaining <= 60 else "medium"
                    }
                    upcoming_deadlines.append(deadline_info)
        
        # Sort by deadline
        upcoming_deadlines.sort(key=lambda x: x["deadline"])
        
        return {
            "success": True,
            "data": {
                "deadlines": upcoming_deadlines,
                "total_count": len(upcoming_deadlines),
                "critical_deadlines": len([d for d in upcoming_deadlines if d["urgency"] == "critical"])
            }
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get upcoming deadlines: {str(e)}")

@router.get("/regulations/stats")
async def get_regulatory_stats():
    """Get regulatory monitoring statistics"""
    try:
        total_subscriptions = sum(len(subs) for subs in USER_SUBSCRIPTIONS.values())
        active_regulations = len(set(update["regulation"] for update in REGULATORY_UPDATES))
        
        # Count updates by impact level
        impact_counts = {}
        for update in REGULATORY_UPDATES:
            impact = update["impact_assessment"]
            impact_counts[impact] = impact_counts.get(impact, 0) + 1
        
        # Count recent updates (last 30 days)
        thirty_days_ago = (datetime.now() - timedelta(days=30)).isoformat()
        recent_updates = len([u for u in REGULATORY_UPDATES if u["published_date"] >= thirty_days_ago])
        
        return {
            "success": True,
            "data": {
                "total_updates": len(REGULATORY_UPDATES),
                "recent_updates": recent_updates,
                "active_regulations": active_regulations,
                "total_subscriptions": total_subscriptions,
                "impact_distribution": impact_counts,
                "supported_frameworks": list(regulatory_monitor.framework_mappings.keys())
            }
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get regulatory stats: {str(e)}")
