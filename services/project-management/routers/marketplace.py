"""
Schema Marketplace Router
Handles template marketplace functionality including browsing, purchasing, and management
"""
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
import json
import uuid
import os
import httpx
from core.auth import get_current_user

router = APIRouter(prefix="/marketplace", tags=["marketplace"])

# Stripe configuration
STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY", "sk_test_dummy")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "whsec_dummy")

# Models
class MarketplaceTemplate(BaseModel):
    id: str
    name: str
    description: str
    category: str
    price: float
    rating: float
    downloads: int
    preview_tables: List[str]
    compliance_frameworks: List[str]
    author: str
    thumbnail: str
    tags: List[str]
    difficulty: str
    estimated_implementation: str

class TemplateDetail(BaseModel):
    id: str
    name: str
    description: str
    category: str
    price: float
    schema: Dict[str, Any]
    documentation: str
    migration_scripts: Dict[str, str]
    validation_rules: List[Dict[str, Any]]
    sample_data: Optional[Dict[str, Any]] = None
    reviews: List[Dict[str, Any]]

class PurchaseRequest(BaseModel):
    template_id: str
    payment_method: str
    billing_email: str

class TemplateSubmission(BaseModel):
    name: str
    description: str
    category: str
    price: float
    schema: Dict[str, Any]
    documentation: str
    tags: List[str]
    difficulty: str
    compliance_frameworks: List[str]

# Mock data storage (in production, use database)
MOCK_TEMPLATES = [
    {
        "id": "tpl_001",
        "name": "HIPAA Healthcare Schema",
        "description": "Complete HIPAA-compliant healthcare database schema",
        "category": "healthcare",
        "price": 299.0,
        "rating": 4.8,
        "downloads": 1247,
        "preview_tables": ["patients", "medical_records", "audit_logs"],
        "compliance_frameworks": ["HIPAA", "HITECH"],
        "author": "SchemaSage Official",
        "thumbnail": "https://cdn.schemasage.com/templates/hipaa.png",
        "tags": ["healthcare", "compliance", "pii", "audit"],
        "difficulty": "intermediate",
        "estimated_implementation": "2-4 hours"
    },
    {
        "id": "tpl_002",
        "name": "E-commerce Platform Schema",
        "description": "Scalable e-commerce database with inventory, orders, and payments",
        "category": "e-commerce",
        "price": 199.0,
        "rating": 4.9,
        "downloads": 2341,
        "preview_tables": ["products", "orders", "customers", "payments"],
        "compliance_frameworks": ["PCI-DSS", "GDPR"],
        "author": "Commerce Expert",
        "thumbnail": "https://cdn.schemasage.com/templates/ecommerce.png",
        "tags": ["e-commerce", "payments", "inventory", "scalable"],
        "difficulty": "beginner",
        "estimated_implementation": "1-2 hours"
    },
    {
        "id": "tpl_003",
        "name": "Financial Services Schema",
        "description": "Banking and financial services compliant schema",
        "category": "financial",
        "price": 499.0,
        "rating": 4.7,
        "downloads": 856,
        "preview_tables": ["accounts", "transactions", "compliance_logs"],
        "compliance_frameworks": ["SOX", "PCI-DSS", "Basel III"],
        "author": "FinTech Architect",
        "thumbnail": "https://cdn.schemasage.com/templates/finance.png",
        "tags": ["banking", "compliance", "transactions", "audit"],
        "difficulty": "advanced",
        "estimated_implementation": "4-8 hours"
    }
]

MOCK_TEMPLATE_DETAILS = {
    "tpl_001": {
        "id": "tpl_001",
        "name": "HIPAA Healthcare Schema",
        "description": "Complete HIPAA-compliant healthcare database schema with audit trails",
        "category": "healthcare",
        "price": 299.0,
        "schema": {
            "tables": {
                "patients": {
                    "columns": {
                        "id": {"type": "uuid", "primary_key": True},
                        "patient_id": {"type": "varchar(20)", "unique": True, "encrypted": True},
                        "first_name": {"type": "varchar(100)", "encrypted": True},
                        "last_name": {"type": "varchar(100)", "encrypted": True},
                        "ssn": {"type": "varchar(11)", "encrypted": True},
                        "date_of_birth": {"type": "date", "encrypted": True},
                        "created_at": {"type": "timestamp", "default": "now()"},
                        "updated_at": {"type": "timestamp", "default": "now()"}
                    }
                },
                "medical_records": {
                    "columns": {
                        "id": {"type": "uuid", "primary_key": True},
                        "patient_id": {"type": "uuid", "foreign_key": "patients.id"},
                        "diagnosis": {"type": "text", "encrypted": True},
                        "treatment": {"type": "text", "encrypted": True},
                        "created_at": {"type": "timestamp", "default": "now()"}
                    }
                }
            }
        },
        "documentation": "# HIPAA Healthcare Schema\n\nThis schema provides a complete HIPAA-compliant foundation for healthcare applications.\n\n## Features\n- Encrypted PII fields\n- Audit trail tables\n- Compliance validation rules\n\n## Implementation Guide\n1. Deploy schema\n2. Configure encryption keys\n3. Set up audit triggers",
        "migration_scripts": {
            "postgresql": "CREATE TABLE patients (id UUID PRIMARY KEY DEFAULT gen_random_uuid(), patient_id VARCHAR(20) UNIQUE NOT NULL, first_name VARCHAR(100) NOT NULL, last_name VARCHAR(100) NOT NULL, ssn VARCHAR(11) NOT NULL, date_of_birth DATE NOT NULL, created_at TIMESTAMP DEFAULT NOW(), updated_at TIMESTAMP DEFAULT NOW());",
            "mysql": "CREATE TABLE patients (id CHAR(36) PRIMARY KEY DEFAULT (UUID()), patient_id VARCHAR(20) UNIQUE NOT NULL, first_name VARCHAR(100) NOT NULL, last_name VARCHAR(100) NOT NULL, ssn VARCHAR(11) NOT NULL, date_of_birth DATE NOT NULL, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP);",
            "mongodb": "db.createCollection('patients', {validator: {$jsonSchema: {bsonType: 'object', required: ['patient_id', 'first_name', 'last_name', 'ssn', 'date_of_birth'], properties: {patient_id: {bsonType: 'string'}, first_name: {bsonType: 'string'}, last_name: {bsonType: 'string'}, ssn: {bsonType: 'string'}, date_of_birth: {bsonType: 'date'}}}}});"
        },
        "validation_rules": [
            {
                "table": "patients",
                "column": "ssn",
                "rule": "encrypted_pii",
                "description": "SSN must be encrypted at rest"
            },
            {
                "table": "patients",
                "column": "date_of_birth",
                "rule": "date_validation",
                "description": "Birth date must be in the past"
            }
        ],
        "sample_data": {
            "patients": [
                {"patient_id": "P001", "first_name": "John", "last_name": "Doe", "ssn": "***-**-****", "date_of_birth": "1980-01-01"}
            ]
        },
        "reviews": [
            {
                "user": "john_dev",
                "rating": 5,
                "comment": "Excellent template, saved us weeks of work",
                "date": "2025-09-15"
            },
            {
                "user": "healthcare_admin",
                "rating": 4,
                "comment": "Good compliance coverage, minor customization needed",
                "date": "2025-09-10"
            }
        ]
    }
}

USER_PURCHASES = {}  # Mock user purchases storage

@router.get("/templates")
async def browse_templates(
    category: Optional[str] = None,
    page: int = 1,
    per_page: int = 20,
    search: Optional[str] = None,
    sort_by: str = "downloads"
):
    """Browse available schema templates"""
    try:
        # Filter templates
        filtered_templates = MOCK_TEMPLATES.copy()
        
        if category:
            filtered_templates = [t for t in filtered_templates if t["category"] == category]
        
        if search:
            search_lower = search.lower()
            filtered_templates = [
                t for t in filtered_templates 
                if search_lower in t["name"].lower() 
                or search_lower in t["description"].lower()
                or any(search_lower in tag.lower() for tag in t["tags"])
            ]
        
        # Sort templates
        if sort_by == "downloads":
            filtered_templates.sort(key=lambda x: x["downloads"], reverse=True)
        elif sort_by == "rating":
            filtered_templates.sort(key=lambda x: x["rating"], reverse=True)
        elif sort_by == "price_low":
            filtered_templates.sort(key=lambda x: x["price"])
        elif sort_by == "price_high":
            filtered_templates.sort(key=lambda x: x["price"], reverse=True)
        
        # Paginate
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        paginated_templates = filtered_templates[start_idx:end_idx]
        
        categories = list(set(t["category"] for t in MOCK_TEMPLATES))
        
        return {
            "success": True,
            "data": {
                "templates": paginated_templates,
                "categories": categories,
                "total_count": len(filtered_templates),
                "page": page,
                "per_page": per_page
            }
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to browse templates: {str(e)}")

@router.get("/templates/{template_id}")
async def get_template_details(template_id: str):
    """Get detailed template information"""
    try:
        if template_id not in MOCK_TEMPLATE_DETAILS:
            raise HTTPException(status_code=404, detail="Template not found")
        
        template_detail = MOCK_TEMPLATE_DETAILS[template_id]
        
        return {
            "success": True,
            "data": {
                "template": template_detail
            }
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get template details: {str(e)}")

@router.post("/purchase")
async def purchase_template(
    purchase_request: PurchaseRequest,
    current_user: dict = Depends(get_current_user)
):
    """Purchase a template"""
    try:
        # Validate template exists
        template = next((t for t in MOCK_TEMPLATES if t["id"] == purchase_request.template_id), None)
        if not template:
            raise HTTPException(status_code=404, detail="Template not found")
        
        # Mock Stripe payment processing
        payment_intent_id = f"pi_{uuid.uuid4().hex[:24]}"
        
        # Record purchase
        user_id = current_user["sub"]
        if user_id not in USER_PURCHASES:
            USER_PURCHASES[user_id] = []
        
        purchase_record = {
            "id": f"purchase_{uuid.uuid4().hex[:16]}",
            "template_id": purchase_request.template_id,
            "template_name": template["name"],
            "price": template["price"],
            "payment_intent_id": payment_intent_id,
            "billing_email": purchase_request.billing_email,
            "purchased_at": datetime.now().isoformat(),
            "status": "completed"
        }
        
        USER_PURCHASES[user_id].append(purchase_record)
        
        return {
            "success": True,
            "data": {
                "purchase_id": purchase_record["id"],
                "payment_intent_id": payment_intent_id,
                "status": "completed",
                "template": template
            }
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process purchase: {str(e)}")

@router.get("/my-purchases")
async def get_user_purchases(current_user: dict = Depends(get_current_user)):
    """Get user's purchased templates"""
    try:
        user_id = current_user["sub"]
        user_purchases = USER_PURCHASES.get(user_id, [])
        
        return {
            "success": True,
            "data": {
                "purchases": user_purchases,
                "total_count": len(user_purchases)
            }
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get purchases: {str(e)}")

@router.post("/templates")
async def submit_template(
    name: str = Form(...),
    description: str = Form(...),
    category: str = Form(...),
    price: float = Form(...),
    schema: str = Form(...),
    documentation: str = Form(...),
    tags: str = Form(...),
    difficulty: str = Form(...),
    compliance_frameworks: str = Form(...),
    thumbnail: UploadFile = File(None),
    current_user: dict = Depends(get_current_user)
):
    """Submit new template for approval"""
    try:
        # Parse JSON fields
        schema_data = json.loads(schema)
        tags_list = json.loads(tags)
        compliance_list = json.loads(compliance_frameworks)
        
        template_id = f"tpl_{uuid.uuid4().hex[:8]}"
        
        # Handle thumbnail upload (mock)
        thumbnail_url = "https://cdn.schemasage.com/templates/default.png"
        if thumbnail:
            # In production, upload to S3/CDN
            thumbnail_url = f"https://cdn.schemasage.com/templates/{template_id}.png"
        
        new_template = {
            "id": template_id,
            "name": name,
            "description": description,
            "category": category,
            "price": price,
            "rating": 0.0,
            "downloads": 0,
            "preview_tables": list(schema_data.get("tables", {}).keys())[:3],
            "compliance_frameworks": compliance_list,
            "author": current_user.get("email", "Unknown"),
            "thumbnail": thumbnail_url,
            "tags": tags_list,
            "difficulty": difficulty,
            "estimated_implementation": "2-4 hours",
            "status": "pending_approval",
            "submitted_at": datetime.now().isoformat()
        }
        
        return {
            "success": True,
            "data": {
                "template_id": template_id,
                "status": "pending_approval",
                "message": "Template submitted for review"
            }
        }
    
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON in schema, tags, or compliance_frameworks")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to submit template: {str(e)}")

@router.put("/templates/{template_id}")
async def update_template(
    template_id: str,
    template_update: TemplateSubmission,
    current_user: dict = Depends(get_current_user)
):
    """Update existing template"""
    try:
        # Validate template exists and user owns it
        # In production, check database for template ownership
        
        updated_template = {
            "id": template_id,
            "name": template_update.name,
            "description": template_update.description,
            "category": template_update.category,
            "price": template_update.price,
            "schema": template_update.schema,
            "documentation": template_update.documentation,
            "tags": template_update.tags,
            "difficulty": template_update.difficulty,
            "compliance_frameworks": template_update.compliance_frameworks,
            "updated_at": datetime.now().isoformat(),
            "status": "pending_approval"
        }
        
        return {
            "success": True,
            "data": {
                "template": updated_template,
                "message": "Template updated and submitted for review"
            }
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update template: {str(e)}")

@router.get("/my-templates")
async def get_user_templates(current_user: dict = Depends(get_current_user)):
    """Get templates created by current user"""
    try:
        # In production, query database for user's templates
        user_email = current_user.get("email", "")
        user_templates = [t for t in MOCK_TEMPLATES if t["author"] == user_email]
        
        return {
            "success": True,
            "data": {
                "templates": user_templates,
                "total_count": len(user_templates)
            }
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get user templates: {str(e)}")

@router.get("/categories")
async def get_categories():
    """Get all available template categories"""
    try:
        categories = [
            {"id": "healthcare", "name": "Healthcare", "description": "HIPAA and medical compliance schemas"},
            {"id": "financial", "name": "Financial Services", "description": "Banking and fintech schemas"},
            {"id": "e-commerce", "name": "E-commerce", "description": "Online retail and marketplace schemas"},
            {"id": "saas", "name": "SaaS", "description": "Software as a Service application schemas"},
            {"id": "education", "name": "Education", "description": "Educational institution schemas"},
            {"id": "government", "name": "Government", "description": "Public sector and compliance schemas"},
            {"id": "manufacturing", "name": "Manufacturing", "description": "Industrial and supply chain schemas"},
            {"id": "real-estate", "name": "Real Estate", "description": "Property management schemas"}
        ]
        
        return {
            "success": True,
            "data": {
                "categories": categories
            }
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get categories: {str(e)}")

@router.get("/stats")
async def get_marketplace_stats():
    """Get marketplace statistics"""
    try:
        stats = {
            "total_templates": len(MOCK_TEMPLATES),
            "total_downloads": sum(t["downloads"] for t in MOCK_TEMPLATES),
            "total_revenue": 125000.0,
            "average_rating": sum(t["rating"] for t in MOCK_TEMPLATES) / len(MOCK_TEMPLATES),
            "categories_count": len(set(t["category"] for t in MOCK_TEMPLATES)),
            "top_categories": [
                {"category": "e-commerce", "downloads": 2341},
                {"category": "healthcare", "downloads": 1247},
                {"category": "financial", "downloads": 856}
            ]
        }
        
        return {
            "success": True,
            "data": stats
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get marketplace stats: {str(e)}")
