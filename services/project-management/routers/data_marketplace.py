"""
Data Marketplace
Platform for buying and selling datasets with privacy protection
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime, timedelta
from enum import Enum
import logging
from uuid import uuid4
import hashlib

from core.auth import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/marketplace", tags=["Data Marketplace"])


# Models
class DatasetStatus(str, Enum):
    DRAFT = "draft"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    PUBLISHED = "published"
    SUSPENDED = "suspended"
    SOLD = "sold"


class PrivacyLevel(str, Enum):
    PUBLIC = "public"  # No PII, fully anonymized
    RESTRICTED = "restricted"  # Some aggregation required
    PRIVATE = "private"  # Contains PII, strict controls
    CONFIDENTIAL = "confidential"  # Highly sensitive


class TransactionStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"


class DatasetListing(BaseModel):
    dataset_id: str
    title: str
    description: str
    category: str
    seller_id: str
    seller_name: str
    price: float
    pricing_model: str  # one-time, subscription, usage-based
    row_count: int
    column_count: int
    last_updated: datetime
    update_frequency: str
    privacy_level: PrivacyLevel
    status: DatasetStatus
    sample_data_url: Optional[str] = None
    documentation_url: Optional[str] = None
    rating: Optional[float] = Field(None, ge=0, le=5)
    purchase_count: int = 0
    tags: List[str] = []


class CreateListingRequest(BaseModel):
    title: str = Field(..., min_length=10, max_length=200)
    description: str = Field(..., min_length=50)
    category: str
    price: float = Field(..., gt=0)
    pricing_model: str = "one-time"
    row_count: int
    column_count: int
    update_frequency: str = "monthly"
    privacy_level: PrivacyLevel
    dataset_url: str  # Internal reference
    sample_data: Optional[Dict[str, Any]] = None
    tags: List[str] = []


class PurchaseRequest(BaseModel):
    dataset_id: str
    payment_method: str
    billing_info: Dict[str, Any]


class Transaction(BaseModel):
    transaction_id: str
    dataset_id: str
    buyer_id: str
    seller_id: str
    amount: float
    status: TransactionStatus
    payment_method: str
    created_at: datetime
    completed_at: Optional[datetime] = None
    access_url: Optional[str] = None
    access_expires_at: Optional[datetime] = None


class AnonymizationResult(BaseModel):
    success: bool
    anonymized_rows: int
    techniques_applied: List[str]
    privacy_score: float = Field(ge=0, le=100)
    pii_removed: List[str]
    warnings: List[str] = []


# Data Marketplace Engine
class DataMarketplaceEngine:
    """Manage data marketplace listings and transactions"""
    
    def __init__(self):
        # In-memory storage (should be database in production)
        self.listings: Dict[str, DatasetListing] = {}
        self.transactions: Dict[str, Transaction] = {}
        self.user_purchases: Dict[str, List[str]] = {}  # user_id -> [dataset_ids]
    
    def create_listing(
        self,
        request: CreateListingRequest,
        seller_id: str,
        seller_name: str
    ) -> DatasetListing:
        """Create new marketplace listing"""
        
        dataset_id = str(uuid4())
        
        # Validate privacy level matches data
        if request.privacy_level == PrivacyLevel.PUBLIC and request.sample_data:
            # Check for potential PII in sample
            warnings = self._check_pii(request.sample_data)
            if warnings:
                raise ValueError(f"PII detected in PUBLIC dataset: {warnings}")
        
        listing = DatasetListing(
            dataset_id=dataset_id,
            title=request.title,
            description=request.description,
            category=request.category,
            seller_id=seller_id,
            seller_name=seller_name,
            price=request.price,
            pricing_model=request.pricing_model,
            row_count=request.row_count,
            column_count=request.column_count,
            last_updated=datetime.now(),
            update_frequency=request.update_frequency,
            privacy_level=request.privacy_level,
            status=DatasetStatus.DRAFT,
            tags=request.tags,
            purchase_count=0
        )
        
        self.listings[dataset_id] = listing
        
        return listing
    
    def search_listings(
        self,
        category: Optional[str] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        privacy_level: Optional[PrivacyLevel] = None,
        tags: Optional[List[str]] = None,
        min_rows: Optional[int] = None
    ) -> List[DatasetListing]:
        """Search marketplace listings with filters"""
        
        results = []
        
        for listing in self.listings.values():
            # Only show published listings
            if listing.status != DatasetStatus.PUBLISHED:
                continue
            
            # Apply filters
            if category and listing.category != category:
                continue
            
            if min_price is not None and listing.price < min_price:
                continue
            
            if max_price is not None and listing.price > max_price:
                continue
            
            if privacy_level and listing.privacy_level != privacy_level:
                continue
            
            if min_rows and listing.row_count < min_rows:
                continue
            
            if tags:
                # Check if listing has any of the requested tags
                if not any(tag in listing.tags for tag in tags):
                    continue
            
            results.append(listing)
        
        # Sort by purchase count (popularity)
        results.sort(key=lambda x: x.purchase_count, reverse=True)
        
        return results
    
    def purchase_dataset(
        self,
        dataset_id: str,
        buyer_id: str,
        payment_method: str,
        billing_info: Dict[str, Any]
    ) -> Transaction:
        """Process dataset purchase"""
        
        listing = self.listings.get(dataset_id)
        if not listing:
            raise ValueError(f"Dataset {dataset_id} not found")
        
        if listing.status != DatasetStatus.PUBLISHED:
            raise ValueError(f"Dataset is not available for purchase (status: {listing.status})")
        
        # Prevent self-purchase
        if listing.seller_id == buyer_id:
            raise ValueError("Cannot purchase your own dataset")
        
        # Check if already purchased (for one-time purchases)
        if listing.pricing_model == "one-time":
            user_purchases = self.user_purchases.get(buyer_id, [])
            if dataset_id in user_purchases:
                raise ValueError("You have already purchased this dataset")
        
        # Create transaction
        transaction_id = str(uuid4())
        
        # Calculate access expiration
        access_expires_at = None
        if listing.pricing_model == "subscription":
            access_expires_at = datetime.now() + timedelta(days=30)
        
        transaction = Transaction(
            transaction_id=transaction_id,
            dataset_id=dataset_id,
            buyer_id=buyer_id,
            seller_id=listing.seller_id,
            amount=listing.price,
            status=TransactionStatus.PENDING,
            payment_method=payment_method,
            created_at=datetime.now(),
            access_expires_at=access_expires_at
        )
        
        # Simulate payment processing
        transaction.status = TransactionStatus.PROCESSING
        
        # Generate secure access URL
        access_token = hashlib.sha256(
            f"{transaction_id}{buyer_id}{dataset_id}".encode()
        ).hexdigest()
        
        transaction.access_url = f"/api/marketplace/download/{dataset_id}?token={access_token}"
        transaction.status = TransactionStatus.COMPLETED
        transaction.completed_at = datetime.now()
        
        # Store transaction
        self.transactions[transaction_id] = transaction
        
        # Update user purchases
        if buyer_id not in self.user_purchases:
            self.user_purchases[buyer_id] = []
        self.user_purchases[buyer_id].append(dataset_id)
        
        # Update listing stats
        listing.purchase_count += 1
        
        return transaction
    
    def get_purchase_history(self, user_id: str) -> List[Dict[str, Any]]:
        """Get user's purchase history"""
        
        purchases = []
        
        for transaction in self.transactions.values():
            if transaction.buyer_id == user_id:
                listing = self.listings.get(transaction.dataset_id)
                
                purchases.append({
                    "transaction": transaction.dict(),
                    "dataset": listing.dict() if listing else None
                })
        
        # Sort by most recent first
        purchases.sort(key=lambda x: x["transaction"]["created_at"], reverse=True)
        
        return purchases
    
    def get_sales_analytics(self, seller_id: str) -> Dict[str, Any]:
        """Get seller's sales analytics"""
        
        total_revenue = 0
        total_sales = 0
        datasets_sold = set()
        
        for transaction in self.transactions.values():
            if transaction.seller_id == seller_id and transaction.status == TransactionStatus.COMPLETED:
                total_revenue += transaction.amount
                total_sales += 1
                datasets_sold.add(transaction.dataset_id)
        
        # Get active listings
        active_listings = [
            listing for listing in self.listings.values()
            if listing.seller_id == seller_id and listing.status == DatasetStatus.PUBLISHED
        ]
        
        return {
            "total_revenue": round(total_revenue, 2),
            "total_sales": total_sales,
            "unique_datasets_sold": len(datasets_sold),
            "active_listings": len(active_listings),
            "average_sale_price": round(total_revenue / total_sales, 2) if total_sales > 0 else 0
        }
    
    def anonymize_dataset(
        self,
        data_sample: Dict[str, Any],
        privacy_level: PrivacyLevel
    ) -> AnonymizationResult:
        """Anonymize dataset for preview/sharing"""
        
        pii_columns = [
            "email", "phone", "ssn", "address", "name", "first_name", "last_name",
            "credit_card", "passport", "driver_license", "ip_address"
        ]
        
        techniques_applied = []
        pii_removed = []
        warnings = []
        
        anonymized_data = data_sample.copy()
        
        # Detect PII columns
        for key in list(anonymized_data.keys()):
            key_lower = key.lower()
            
            # Check if column name indicates PII
            if any(pii in key_lower for pii in pii_columns):
                pii_removed.append(key)
                
                if privacy_level == PrivacyLevel.PUBLIC:
                    # Remove completely for public datasets
                    del anonymized_data[key]
                    techniques_applied.append(f"Removed PII column: {key}")
                elif privacy_level == PrivacyLevel.RESTRICTED:
                    # Hash or mask
                    anonymized_data[key] = "***REDACTED***"
                    techniques_applied.append(f"Masked column: {key}")
        
        # Calculate privacy score
        original_columns = len(data_sample)
        pii_count = len(pii_removed)
        privacy_score = 100.0
        
        if pii_count > 0:
            if privacy_level == PrivacyLevel.PUBLIC and pii_count > 0:
                privacy_score = 95.0
            elif privacy_level == PrivacyLevel.RESTRICTED:
                privacy_score = 80.0
            elif privacy_level == PrivacyLevel.PRIVATE:
                privacy_score = 60.0
                warnings.append("Dataset contains PII - implement strict access controls")
            elif privacy_level == PrivacyLevel.CONFIDENTIAL:
                privacy_score = 40.0
                warnings.append("Highly sensitive data - requires special licensing")
        
        return AnonymizationResult(
            success=True,
            anonymized_rows=len(anonymized_data),
            techniques_applied=techniques_applied,
            privacy_score=privacy_score,
            pii_removed=pii_removed,
            warnings=warnings
        )
    
    def _check_pii(self, data_sample: Dict[str, Any]) -> List[str]:
        """Check for potential PII in data"""
        pii_indicators = [
            "email", "phone", "ssn", "address", "name", "first_name", "last_name",
            "credit_card", "passport", "driver_license", "ip_address", "dob", "birth"
        ]
        
        found_pii = []
        
        for key in data_sample.keys():
            key_lower = key.lower()
            for indicator in pii_indicators:
                if indicator in key_lower:
                    found_pii.append(key)
                    break
        
        return found_pii


# Initialize engine
marketplace_engine = DataMarketplaceEngine()


# API Endpoints
@router.post("/list")
async def create_marketplace_listing(
    request: CreateListingRequest,
    user_id: str = Depends(get_current_user)
):
    """
    List dataset for sale on marketplace
    
    **Premium Feature**: Monetize your data
    """
    try:
        logger.info(f"Creating marketplace listing for user {user_id}: {request.title}")
        
        # Get seller name (would be from database in production)
        seller_name = f"User_{user_id[:8]}"
        
        listing = marketplace_engine.create_listing(request, user_id, seller_name)
        
        return {
            "success": True,
            "data": {
                "listing": listing.dict(),
                "next_steps": [
                    "Your listing is in DRAFT status",
                    "Provide sample data for preview",
                    "Submit for review to publish",
                    "Once approved, it will be visible to buyers"
                ]
            }
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to create listing: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search")
async def search_marketplace(
    category: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    privacy_level: Optional[PrivacyLevel] = None,
    tags: Optional[str] = Query(None, description="Comma-separated tags"),
    min_rows: Optional[int] = None,
    user_id: str = Depends(get_current_user)
):
    """
    Search marketplace for datasets
    
    **Premium Feature**: Discover valuable datasets
    """
    try:
        # Parse tags
        tag_list = [tag.strip() for tag in tags.split(",")] if tags else None
        
        listings = marketplace_engine.search_listings(
            category=category,
            min_price=min_price,
            max_price=max_price,
            privacy_level=privacy_level,
            tags=tag_list,
            min_rows=min_rows
        )
        
        return {
            "success": True,
            "data": {
                "total_results": len(listings),
                "listings": [listing.dict() for listing in listings[:50]],  # Limit to 50
                "filters_applied": {
                    "category": category,
                    "price_range": f"${min_price or 0} - ${max_price or '∞'}",
                    "privacy_level": privacy_level,
                    "tags": tag_list,
                    "min_rows": min_rows
                }
            }
        }
        
    except Exception as e:
        logger.error(f"Marketplace search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/purchase")
async def purchase_dataset(
    request: PurchaseRequest,
    user_id: str = Depends(get_current_user)
):
    """
    Purchase dataset from marketplace
    
    **Premium Feature**: Buy datasets securely
    """
    try:
        logger.info(f"User {user_id} purchasing dataset {request.dataset_id}")
        
        transaction = marketplace_engine.purchase_dataset(
            dataset_id=request.dataset_id,
            buyer_id=user_id,
            payment_method=request.payment_method,
            billing_info=request.billing_info
        )
        
        return {
            "success": True,
            "data": {
                "transaction": transaction.dict(),
                "message": "Purchase completed successfully!",
                "access_info": {
                    "download_url": transaction.access_url,
                    "expires_at": transaction.access_expires_at.isoformat() if transaction.access_expires_at else "Never",
                    "instructions": "Use the download URL to access your data. Keep this secure."
                }
            }
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Purchase failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/purchases")
async def get_my_purchases(
    user_id: str = Depends(get_current_user)
):
    """Get user's purchase history"""
    try:
        purchases = marketplace_engine.get_purchase_history(user_id)
        
        return {
            "success": True,
            "data": {
                "total_purchases": len(purchases),
                "purchases": purchases
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get purchases: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sales")
async def get_my_sales(
    user_id: str = Depends(get_current_user)
):
    """Get seller's sales analytics"""
    try:
        analytics = marketplace_engine.get_sales_analytics(user_id)
        
        return {
            "success": True,
            "data": analytics
        }
        
    except Exception as e:
        logger.error(f"Failed to get sales analytics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/anonymize")
async def anonymize_data_sample(
    data_sample: Dict[str, Any],
    privacy_level: PrivacyLevel,
    user_id: str = Depends(get_current_user)
):
    """
    Anonymize data for safe sharing/preview
    
    **Premium Feature**: Privacy-safe data sharing
    """
    try:
        result = marketplace_engine.anonymize_dataset(data_sample, privacy_level)
        
        return {
            "success": True,
            "data": {
                "anonymization_result": result.dict(),
                "recommendation": (
                    "Safe to share publicly" if result.privacy_score >= 90
                    else "Use restricted access" if result.privacy_score >= 70
                    else "Requires strict access controls"
                )
            }
        }
        
    except Exception as e:
        logger.error(f"Anonymization failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/dataset/{dataset_id}")
async def get_dataset_details(
    dataset_id: str,
    user_id: str = Depends(get_current_user)
):
    """Get detailed information about a dataset"""
    try:
        listing = marketplace_engine.listings.get(dataset_id)
        
        if not listing:
            raise HTTPException(status_code=404, detail="Dataset not found")
        
        # Check if user has purchased this dataset
        has_purchased = dataset_id in marketplace_engine.user_purchases.get(user_id, [])
        
        return {
            "success": True,
            "data": {
                "listing": listing.dict(),
                "has_purchased": has_purchased,
                "can_purchase": listing.status == DatasetStatus.PUBLISHED and not has_purchased
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get dataset details: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/listing/{dataset_id}/publish")
async def publish_listing(
    dataset_id: str,
    user_id: str = Depends(get_current_user)
):
    """Publish dataset listing (make it live on marketplace)"""
    try:
        listing = marketplace_engine.listings.get(dataset_id)
        
        if not listing:
            raise HTTPException(status_code=404, detail="Dataset not found")
        
        if listing.seller_id != user_id:
            raise HTTPException(status_code=403, detail="You don't own this listing")
        
        if listing.status not in [DatasetStatus.DRAFT, DatasetStatus.APPROVED]:
            raise HTTPException(status_code=400, detail=f"Cannot publish from status: {listing.status}")
        
        listing.status = DatasetStatus.PUBLISHED
        
        return {
            "success": True,
            "data": {
                "listing": listing.dict(),
                "message": "Dataset is now live on marketplace!"
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to publish listing: {e}")
        raise HTTPException(status_code=500, detail=str(e))
