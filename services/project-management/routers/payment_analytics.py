"""
Payment Processing and Analytics Router
Handles Stripe integration for marketplace payments and provides comprehensive analytics
"""
from fastapi import APIRouter, HTTPException, Depends, Request
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime, timedelta
import json
import uuid
import os
import hmac
import hashlib
import httpx
from ..core.auth import get_current_user

router = APIRouter(prefix="/payments", tags=["payments-analytics"])

# Stripe configuration
STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY", "sk_test_dummy")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "whsec_dummy")
STRIPE_API_BASE = "https://api.stripe.com/v1"

# Models
class PaymentIntentRequest(BaseModel):
    amount: int = Field(..., description="Amount in cents")
    currency: str = Field(default="usd")
    template_id: Optional[str] = None
    subscription_plan: Optional[str] = None
    customer_email: str

class PaymentIntent(BaseModel):
    id: str
    client_secret: str
    amount: int
    currency: str
    status: str

class SubscriptionRequest(BaseModel):
    plan_id: str
    customer_email: str
    payment_method_id: str

class AnalyticsQuery(BaseModel):
    start_date: str
    end_date: str
    metrics: List[str] = Field(default_factory=lambda: ["revenue", "users", "conversions"])
    group_by: str = Field(default="day", description="day, week, month")

# Mock payment data
PAYMENT_RECORDS = []
SUBSCRIPTION_RECORDS = []
ANALYTICS_DATA = {
    "marketplace": {
        "total_revenue": 125000.0,
        "total_sales": 486,
        "top_templates": [
            {"template_id": "tpl_001", "name": "HIPAA Healthcare Schema", "sales": 127, "revenue": 37973.0},
            {"template_id": "tpl_002", "name": "E-commerce Platform Schema", "sales": 234, "revenue": 46566.0}
        ],
        "monthly_revenue": [
            {"month": "2025-07", "revenue": 34000.0, "sales": 142},
            {"month": "2025-08", "revenue": 41000.0, "sales": 168},
            {"month": "2025-09", "revenue": 50000.0, "sales": 176}
        ]
    },
    "security": {
        "total_audits": 1247,
        "critical_vulnerabilities_found": 89,
        "average_security_score": 7.3,
        "monthly_audits": [
            {"month": "2025-07", "audits": 389, "avg_score": 7.1},
            {"month": "2025-08", "audits": 428, "avg_score": 7.3},
            {"month": "2025-09", "audits": 430, "avg_score": 7.5}
        ]
    },
    "compliance": {
        "total_alerts": 567,
        "resolved_violations": 523,
        "active_subscriptions": 89,
        "framework_distribution": {
            "GDPR": 34,
            "HIPAA": 23,
            "SOX": 18,
            "PCI_DSS": 14
        }
    }
}

class StripeService:
    """Stripe payment processing service"""
    
    def __init__(self):
        self.api_key = STRIPE_SECRET_KEY
        self.webhook_secret = STRIPE_WEBHOOK_SECRET
    
    async def create_payment_intent(self, request: PaymentIntentRequest) -> PaymentIntent:
        """Create Stripe payment intent"""
        try:
            # Mock Stripe API call
            payment_intent_id = f"pi_{uuid.uuid4().hex[:24]}"
            client_secret = f"{payment_intent_id}_secret_{uuid.uuid4().hex[:16]}"
            
            # In production, make actual Stripe API call:
            # async with httpx.AsyncClient() as client:
            #     response = await client.post(
            #         f"{STRIPE_API_BASE}/payment_intents",
            #         headers={"Authorization": f"Bearer {self.api_key}"},
            #         data={
            #             "amount": request.amount,
            #             "currency": request.currency,
            #             "metadata": {
            #                 "template_id": request.template_id,
            #                 "customer_email": request.customer_email
            #             }
            #         }
            #     )
            #     response_data = response.json()
            
            return PaymentIntent(
                id=payment_intent_id,
                client_secret=client_secret,
                amount=request.amount,
                currency=request.currency,
                status="requires_payment_method"
            )
        
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to create payment intent: {str(e)}")
    
    async def create_subscription(self, request: SubscriptionRequest) -> Dict[str, Any]:
        """Create Stripe subscription"""
        try:
            subscription_id = f"sub_{uuid.uuid4().hex[:24]}"
            customer_id = f"cus_{uuid.uuid4().hex[:24]}"
            
            # Mock subscription creation
            subscription = {
                "id": subscription_id,
                "customer": customer_id,
                "plan": request.plan_id,
                "status": "active",
                "current_period_start": int(datetime.now().timestamp()),
                "current_period_end": int((datetime.now() + timedelta(days=30)).timestamp())
            }
            
            return subscription
        
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to create subscription: {str(e)}")
    
    def verify_webhook_signature(self, payload: bytes, signature: str) -> bool:
        """Verify Stripe webhook signature"""
        try:
            expected_signature = hmac.new(
                self.webhook_secret.encode('utf-8'),
                payload,
                hashlib.sha256
            ).hexdigest()
            
            return hmac.compare_digest(f"sha256={expected_signature}", signature)
        
        except Exception:
            return False

class AnalyticsEngine:
    """Analytics and reporting engine"""
    
    def __init__(self):
        self.data_sources = ANALYTICS_DATA
    
    def get_marketplace_analytics(self, start_date: str, end_date: str, group_by: str = "day") -> Dict[str, Any]:
        """Get marketplace performance analytics"""
        try:
            marketplace_data = self.data_sources["marketplace"]
            
            # Filter data by date range (mock implementation)
            filtered_revenue = marketplace_data["monthly_revenue"]
            
            # Calculate metrics
            total_revenue = sum(month["revenue"] for month in filtered_revenue)
            total_sales = sum(month["sales"] for month in filtered_revenue)
            average_order_value = total_revenue / max(total_sales, 1)
            
            # Calculate growth rate
            if len(filtered_revenue) >= 2:
                current_month = filtered_revenue[-1]["revenue"]
                previous_month = filtered_revenue[-2]["revenue"]
                growth_rate = ((current_month - previous_month) / previous_month) * 100
            else:
                growth_rate = 0
            
            return {
                "total_revenue": total_revenue,
                "total_sales": total_sales,
                "average_order_value": round(average_order_value, 2),
                "growth_rate": round(growth_rate, 2),
                "top_templates": marketplace_data["top_templates"],
                "revenue_trend": filtered_revenue,
                "conversion_rate": 12.5,  # Mock conversion rate
                "refund_rate": 2.1
            }
        
        except Exception as e:
            raise ValueError(f"Failed to get marketplace analytics: {str(e)}")
    
    def get_security_analytics(self, start_date: str, end_date: str) -> Dict[str, Any]:
        """Get security audit analytics"""
        try:
            security_data = self.data_sources["security"]
            
            return {
                "total_audits": security_data["total_audits"],
                "critical_vulnerabilities": security_data["critical_vulnerabilities_found"],
                "average_security_score": security_data["average_security_score"],
                "monthly_trends": security_data["monthly_audits"],
                "vulnerability_distribution": {
                    "critical": 89,
                    "high": 234,
                    "medium": 567,
                    "low": 234
                },
                "compliance_scores": {
                    "GDPR": 8.2,
                    "HIPAA": 8.7,
                    "SOX": 7.9,
                    "PCI_DSS": 8.1
                }
            }
        
        except Exception as e:
            raise ValueError(f"Failed to get security analytics: {str(e)}")
    
    def get_compliance_analytics(self) -> Dict[str, Any]:
        """Get compliance monitoring analytics"""
        try:
            compliance_data = self.data_sources["compliance"]
            
            resolution_rate = (compliance_data["resolved_violations"] / max(compliance_data["total_alerts"], 1)) * 100
            
            return {
                "total_alerts": compliance_data["total_alerts"],
                "resolved_violations": compliance_data["resolved_violations"],
                "resolution_rate": round(resolution_rate, 2),
                "active_subscriptions": compliance_data["active_subscriptions"],
                "framework_distribution": compliance_data["framework_distribution"],
                "alert_trends": [
                    {"week": "2025-W36", "alerts": 23, "resolved": 21},
                    {"week": "2025-W37", "alerts": 18, "resolved": 16},
                    {"week": "2025-W38", "alerts": 15, "resolved": 14}
                ]
            }
        
        except Exception as e:
            raise ValueError(f"Failed to get compliance analytics: {str(e)}")

# Global services
stripe_service = StripeService()
analytics_engine = AnalyticsEngine()

@router.post("/create-intent")
async def create_payment_intent(
    request: PaymentIntentRequest,
    current_user: dict = Depends(get_current_user)
):
    """Create payment intent for marketplace purchases"""
    try:
        payment_intent = await stripe_service.create_payment_intent(request)
        
        # Record payment attempt
        payment_record = {
            "id": payment_intent.id,
            "user_id": current_user["sub"],
            "amount": request.amount,
            "currency": request.currency,
            "template_id": request.template_id,
            "subscription_plan": request.subscription_plan,
            "status": "pending",
            "created_at": datetime.now().isoformat()
        }
        PAYMENT_RECORDS.append(payment_record)
        
        return {
            "success": True,
            "data": {
                "payment_intent": payment_intent.dict(),
                "publishable_key": "pk_test_dummy"  # In production, use real publishable key
            }
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create payment intent: {str(e)}")

@router.post("/create-subscription")
async def create_subscription(
    request: SubscriptionRequest,
    current_user: dict = Depends(get_current_user)
):
    """Create subscription for premium features"""
    try:
        subscription = await stripe_service.create_subscription(request)
        
        # Record subscription
        subscription_record = {
            "id": subscription["id"],
            "user_id": current_user["sub"],
            "plan_id": request.plan_id,
            "customer_email": request.customer_email,
            "status": subscription["status"],
            "created_at": datetime.now().isoformat()
        }
        SUBSCRIPTION_RECORDS.append(subscription_record)
        
        return {
            "success": True,
            "data": {
                "subscription": subscription
            }
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create subscription: {str(e)}")

@router.post("/webhook")
async def handle_stripe_webhook(request: Request):
    """Handle Stripe webhooks"""
    try:
        payload = await request.body()
        signature = request.headers.get("stripe-signature", "")
        
        # Verify webhook signature
        if not stripe_service.verify_webhook_signature(payload, signature):
            raise HTTPException(status_code=400, detail="Invalid signature")
        
        # Parse webhook event
        event = json.loads(payload.decode('utf-8'))
        event_type = event.get("type")
        
        if event_type == "payment_intent.succeeded":
            # Handle successful payment
            payment_intent = event["data"]["object"]
            
            # Update payment record
            for record in PAYMENT_RECORDS:
                if record["id"] == payment_intent["id"]:
                    record["status"] = "completed"
                    record["completed_at"] = datetime.now().isoformat()
                    break
        
        elif event_type == "payment_intent.payment_failed":
            # Handle failed payment
            payment_intent = event["data"]["object"]
            
            # Update payment record
            for record in PAYMENT_RECORDS:
                if record["id"] == payment_intent["id"]:
                    record["status"] = "failed"
                    record["failed_at"] = datetime.now().isoformat()
                    break
        
        return {"success": True}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to handle webhook: {str(e)}")

@router.get("/analytics/marketplace")
async def get_marketplace_analytics(
    start_date: str,
    end_date: str,
    group_by: str = "day"
):
    """Get marketplace performance metrics"""
    try:
        analytics = analytics_engine.get_marketplace_analytics(start_date, end_date, group_by)
        
        return {
            "success": True,
            "data": {
                "analytics": analytics,
                "query_parameters": {
                    "start_date": start_date,
                    "end_date": end_date,
                    "group_by": group_by
                }
            }
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get marketplace analytics: {str(e)}")

@router.get("/analytics/security")
async def get_security_analytics(
    start_date: str,
    end_date: str
):
    """Get security audit statistics"""
    try:
        analytics = analytics_engine.get_security_analytics(start_date, end_date)
        
        return {
            "success": True,
            "data": {
                "analytics": analytics,
                "query_parameters": {
                    "start_date": start_date,
                    "end_date": end_date
                }
            }
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get security analytics: {str(e)}")

@router.get("/analytics/compliance")
async def get_compliance_analytics():
    """Get compliance violation trends"""
    try:
        analytics = analytics_engine.get_compliance_analytics()
        
        return {
            "success": True,
            "data": {
                "analytics": analytics
            }
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get compliance analytics: {str(e)}")

@router.get("/analytics/dashboard")
async def get_dashboard_analytics(current_user: dict = Depends(get_current_user)):
    """Get comprehensive dashboard analytics"""
    try:
        # Get current month data
        current_date = datetime.now()
        start_date = current_date.replace(day=1).strftime("%Y-%m-%d")
        end_date = current_date.strftime("%Y-%m-%d")
        
        # Gather analytics from all sources
        marketplace_analytics = analytics_engine.get_marketplace_analytics(start_date, end_date)
        security_analytics = analytics_engine.get_security_analytics(start_date, end_date)
        compliance_analytics = analytics_engine.get_compliance_analytics()
        
        # Calculate key metrics
        dashboard_data = {
            "overview": {
                "total_revenue": marketplace_analytics["total_revenue"],
                "total_sales": marketplace_analytics["total_sales"],
                "security_score": security_analytics["average_security_score"],
                "compliance_resolution_rate": compliance_analytics["resolution_rate"]
            },
            "trends": {
                "revenue_growth": marketplace_analytics["growth_rate"],
                "security_improvement": 8.5,  # Mock improvement percentage
                "compliance_alerts": compliance_analytics["total_alerts"]
            },
            "quick_stats": {
                "templates_sold": marketplace_analytics["total_sales"],
                "audits_completed": security_analytics["total_audits"],
                "vulnerabilities_found": security_analytics["critical_vulnerabilities"],
                "compliance_violations": compliance_analytics["total_alerts"]
            },
            "charts": {
                "revenue_chart": marketplace_analytics["revenue_trend"],
                "security_chart": security_analytics["monthly_trends"],
                "compliance_chart": compliance_analytics["alert_trends"]
            }
        }
        
        return {
            "success": True,
            "data": {
                "dashboard": dashboard_data,
                "last_updated": datetime.now().isoformat()
            }
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get dashboard analytics: {str(e)}")

@router.get("/payments/history")
async def get_payment_history(
    limit: int = 20,
    offset: int = 0,
    current_user: dict = Depends(get_current_user)
):
    """Get payment history for current user"""
    try:
        user_id = current_user["sub"]
        
        # Filter payments for current user
        user_payments = [p for p in PAYMENT_RECORDS if p["user_id"] == user_id]
        
        # Sort by creation date
        user_payments.sort(key=lambda x: x["created_at"], reverse=True)
        
        # Paginate
        paginated_payments = user_payments[offset:offset + limit]
        
        return {
            "success": True,
            "data": {
                "payments": paginated_payments,
                "total_count": len(user_payments),
                "limit": limit,
                "offset": offset
            }
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get payment history: {str(e)}")

@router.get("/subscriptions")
async def get_user_subscriptions(current_user: dict = Depends(get_current_user)):
    """Get user's active subscriptions"""
    try:
        user_id = current_user["sub"]
        
        # Filter subscriptions for current user
        user_subscriptions = [s for s in SUBSCRIPTION_RECORDS if s["user_id"] == user_id]
        
        return {
            "success": True,
            "data": {
                "subscriptions": user_subscriptions,
                "total_count": len(user_subscriptions)
            }
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get subscriptions: {str(e)}")

@router.get("/pricing")
async def get_pricing_plans():
    """Get available pricing plans"""
    try:
        pricing_plans = [
            {
                "id": "basic",
                "name": "Basic",
                "price": 29.99,
                "currency": "usd",
                "interval": "month",
                "features": [
                    "5 schema templates",
                    "Basic security audits",
                    "Email support",
                    "Standard migration tools"
                ]
            },
            {
                "id": "professional",
                "name": "Professional",
                "price": 99.99,
                "currency": "usd",
                "interval": "month",
                "features": [
                    "Unlimited schema templates",
                    "Advanced security audits",
                    "Compliance monitoring",
                    "Priority support",
                    "Advanced migration tools",
                    "Custom templates"
                ]
            },
            {
                "id": "enterprise",
                "name": "Enterprise",
                "price": 299.99,
                "currency": "usd",
                "interval": "month",
                "features": [
                    "Everything in Professional",
                    "Multi-tenant support",
                    "Dedicated support",
                    "Custom integrations",
                    "Advanced analytics",
                    "SLA guarantee"
                ]
            }
        ]
        
        return {
            "success": True,
            "data": {
                "plans": pricing_plans
            }
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get pricing plans: {str(e)}")

@router.get("/analytics/export")
async def export_analytics(
    format: str = "json",
    include_sensitive: bool = False,
    current_user: dict = Depends(get_current_user)
):
    """Export analytics data"""
    try:
        # Check if user has export permissions (mock)
        user_role = current_user.get("role", "user")
        if user_role not in ["admin", "analyst"]:
            raise HTTPException(status_code=403, detail="Insufficient permissions for data export")
        
        # Gather all analytics
        export_data = {
            "export_info": {
                "generated_at": datetime.now().isoformat(),
                "generated_by": current_user["sub"],
                "format": format,
                "includes_sensitive_data": include_sensitive
            },
            "marketplace": analytics_engine.get_marketplace_analytics("2025-01-01", "2025-12-31"),
            "security": analytics_engine.get_security_analytics("2025-01-01", "2025-12-31"),
            "compliance": analytics_engine.get_compliance_analytics()
        }
        
        if not include_sensitive:
            # Remove sensitive information
            if "customer_emails" in export_data:
                del export_data["customer_emails"]
        
        return {
            "success": True,
            "data": {
                "export": export_data,
                "download_url": f"https://api.schemasage.com/exports/{uuid.uuid4().hex}.{format}"
            }
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to export analytics: {str(e)}")

@router.get("/revenue/forecast")
async def get_revenue_forecast(months_ahead: int = 6):
    """Get revenue forecasting"""
    try:
        # Simple linear forecasting based on recent trends
        marketplace_data = ANALYTICS_DATA["marketplace"]["monthly_revenue"]
        
        if len(marketplace_data) < 2:
            raise HTTPException(status_code=400, detail="Insufficient data for forecasting")
        
        # Calculate growth rate
        recent_growth = []
        for i in range(1, len(marketplace_data)):
            prev_revenue = marketplace_data[i-1]["revenue"]
            curr_revenue = marketplace_data[i]["revenue"]
            growth = (curr_revenue - prev_revenue) / prev_revenue
            recent_growth.append(growth)
        
        avg_growth_rate = sum(recent_growth) / len(recent_growth)
        
        # Generate forecast
        last_month_revenue = marketplace_data[-1]["revenue"]
        current_date = datetime.now()
        
        forecast = []
        for i in range(1, months_ahead + 1):
            future_date = current_date + timedelta(days=30 * i)
            projected_revenue = last_month_revenue * ((1 + avg_growth_rate) ** i)
            
            forecast.append({
                "month": future_date.strftime("%Y-%m"),
                "projected_revenue": round(projected_revenue, 2),
                "confidence": max(90 - (i * 10), 50)  # Decreasing confidence over time
            })
        
        return {
            "success": True,
            "data": {
                "forecast": forecast,
                "methodology": "Linear growth projection",
                "average_growth_rate": round(avg_growth_rate * 100, 2),
                "confidence_note": "Confidence decreases with projection distance"
            }
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate revenue forecast: {str(e)}")
