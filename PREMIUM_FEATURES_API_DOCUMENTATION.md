# Premium Features API Documentation

Complete API reference for all 5 premium features with request/response formats for frontend integration.

**Base URLs:**
- Schema Detection Service: `https://schemasage-schema-detection-0cc19b546c3c.herokuapp.com` (or your deployed URL)
- Project Management Service: `https://schemasage-project-management-48496f02644b.herokuapp.com` (or your deployed URL)

remeber all requets passes trhough my api-gatewway
https://schemasage-api-gateway-2da67d920b07.herokuapp.com
**Authentication:** All endpoints require JWT token in Authorization header:
```
Authorization: Bearer YOUR_JWT_TOKEN
```

---

## Feature #1: AI-Powered Data Health Score

**Service:** Schema Detection  
**Base Path:** `/health`

### 1.1 Calculate Health Score

**Endpoint:** `POST /health/analyze`

**Request Body:**
```json
{
  "schema_id": "string",
  "include_recommendations": true
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "health_score": {
      "schema_id": "abc-123",
      "overall_score": 87.5,
      "status": "good",
      "dimensions": {
        "completeness": {
          "score": 95.0,
          "weight": 0.25,
          "weighted_score": 23.75
        },
        "freshness": {
          "score": 80.0,
          "weight": 0.15,
          "weighted_score": 12.0
        },
        "consistency": {
          "score": 90.0,
          "weight": 0.2,
          "weighted_score": 18.0
        },
        "accuracy": {
          "score": 85.0,
          "weight": 0.2,
          "weighted_score": 17.0
        },
        "duplicates": {
          "score": 75.0,
          "weight": 0.1,
          "weighted_score": 7.5
        },
        "validity": {
          "score": 92.0,
          "weight": 0.1,
          "weighted_score": 9.2
        }
      },
      "issues": [
        {
          "category": "duplicates",
          "severity": "medium",
          "description": "Found 250 duplicate records",
          "affected_tables": ["users", "orders"],
          "recommendation": "Run deduplication analysis"
        }
      ],
      "calculated_at": "2025-11-10T10:30:00Z"
    }
  }
}
```

### 1.2 Get Health History

**Endpoint:** `GET /health/history`

**Query Parameters:**
- `schema_id` (required): string
- `days` (optional): integer, default 30

**Request:**
```
GET /health/history?schema_id=abc-123&days=30
```

**Response:**
```json
{
  "success": true,
  "data": {
    "schema_id": "abc-123",
    "period_days": 30,
    "history": [
      {
        "date": "2025-11-10",
        "overall_score": 87.5,
        "status": "good"
      },
      {
        "date": "2025-11-09",
        "overall_score": 85.0,
        "status": "good"
      },
      {
        "date": "2025-11-08",
        "overall_score": 82.0,
        "status": "good"
      }
    ],
    "trend": {
      "direction": "improving",
      "change_percentage": 6.7,
      "summary": "Health score improved by 6.7% over the last 30 days"
    }
  }
}
```

### 1.3 Enable Monitoring

**Endpoint:** `POST /health/monitor`

**Request Body:**
```json
{
  "schema_id": "abc-123",
  "frequency": "daily",
  "alert_threshold": 70.0,
  "notification_channels": ["email", "slack"]
}
```

**Frequency Options:** `"hourly"`, `"daily"`, `"weekly"`

**Response:**
```json
{
  "success": true,
  "data": {
    "monitor_id": "mon-456",
    "schema_id": "abc-123",
    "frequency": "daily",
    "alert_threshold": 70.0,
    "status": "active",
    "next_check": "2025-11-11T10:30:00Z",
    "message": "Health monitoring enabled successfully"
  }
}
```

### 1.4 Get Industry Benchmarks

**Endpoint:** `GET /health/benchmarks`

**Query Parameters:**
- `industry` (required): string - `"e-commerce"`, `"saas"`, `"healthcare"`, `"financial"`

**Request:**
```
GET /health/benchmarks?industry=e-commerce
```

**Response:**
```json
{
  "success": true,
  "data": {
    "industry": "e-commerce",
    "benchmarks": {
      "overall_score": 85.0,
      "completeness": 90.0,
      "freshness": 85.0,
      "consistency": 88.0,
      "accuracy": 82.0,
      "duplicates": 80.0,
      "validity": 85.0
    },
    "percentiles": {
      "p25": 75.0,
      "p50": 85.0,
      "p75": 92.0,
      "p90": 95.0
    },
    "comparison": "Your score of 87.5 is above industry average (85.0)"
  }
}
```

### 1.5 Get Health Alerts

**Endpoint:** `GET /health/alerts`

**Query Parameters:**
- `schema_id` (optional): string
- `severity` (optional): `"critical"`, `"high"`, `"medium"`, `"low"`

**Request:**
```
GET /health/alerts?schema_id=abc-123&severity=high
```

**Response:**
```json
{
  "success": true,
  "data": {
    "total_alerts": 3,
    "alerts": [
      {
        "alert_id": "alert-789",
        "schema_id": "abc-123",
        "severity": "high",
        "category": "freshness",
        "message": "Data has not been updated in 7 days",
        "triggered_at": "2025-11-10T08:00:00Z",
        "acknowledged": false
      },
      {
        "alert_id": "alert-790",
        "schema_id": "abc-123",
        "severity": "medium",
        "category": "duplicates",
        "message": "Duplicate rate increased to 15%",
        "triggered_at": "2025-11-10T09:30:00Z",
        "acknowledged": false
      }
    ]
  }
}
```

---

## Feature #2: Smart Data Relationships Discovery

**Service:** Schema Detection  
**Base Path:** `/insights`

### 2.1 Discover All Insights

**Endpoint:** `POST /insights/discover`

**Request Body:**
```json
{
  "schema_id": "abc-123",
  "insight_types": ["correlations", "patterns", "orphaned", "anomalies"]
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "insights": [
      {
        "insight_id": "ins-001",
        "type": "correlation",
        "title": "High-value customer pattern",
        "description": "Customers who purchase Product A have 73% higher lifetime value",
        "confidence": 0.87,
        "impact": "high",
        "details": {
          "correlation_strength": 0.73,
          "sample_size": 5000,
          "statistical_significance": 0.001
        }
      },
      {
        "insight_id": "ins-002",
        "type": "pattern",
        "title": "Frequently purchased together",
        "description": "Products X and Y are purchased together 45% of the time",
        "confidence": 0.92,
        "impact": "medium"
      }
    ],
    "total_insights": 12,
    "categories": {
      "correlations": 4,
      "patterns": 5,
      "orphaned": 2,
      "anomalies": 1
    }
  }
}
```

### 2.2 Correlation Analysis

**Endpoint:** `POST /insights/correlations`

**Request Body:**
```json
{
  "schema_id": "abc-123",
  "target_metric": "lifetime_value",
  "analyze_columns": ["product_category", "signup_source", "user_tier"]
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "correlations": [
      {
        "column": "product_category",
        "value": "premium",
        "correlation_strength": 0.73,
        "correlation_type": "positive",
        "insight": "Customers who buy premium products have 73% higher lifetime value",
        "sample_size": 5000,
        "confidence": 0.95
      },
      {
        "column": "signup_source",
        "value": "referral",
        "correlation_strength": 0.58,
        "correlation_type": "positive",
        "insight": "Referred customers have 58% higher lifetime value",
        "sample_size": 3200,
        "confidence": 0.92
      },
      {
        "column": "user_tier",
        "value": "free",
        "correlation_strength": -0.45,
        "correlation_type": "negative",
        "insight": "Free tier users have 45% lower lifetime value",
        "sample_size": 8000,
        "confidence": 0.88
      }
    ],
    "business_recommendations": [
      "Focus marketing on premium product categories",
      "Invest in referral program",
      "Create upgrade incentives for free tier users"
    ]
  }
}
```

### 2.3 Find Orphaned Records

**Endpoint:** `GET /insights/orphaned`

**Query Parameters:**
- `schema_id` (required): string

**Request:**
```
GET /insights/orphaned?schema_id=abc-123
```

**Response:**
```json
{
  "success": true,
  "data": {
    "orphaned_records": [
      {
        "table": "orders",
        "foreign_key": "user_id",
        "references": "users",
        "orphaned_count": 800,
        "percentage": 5.2,
        "severity": "high",
        "impact": "Data integrity issue - 800 orders have no matching user",
        "recommendation": "Clean up orphaned orders or restore missing user records"
      },
      {
        "table": "order_items",
        "foreign_key": "product_id",
        "references": "products",
        "orphaned_count": 150,
        "percentage": 1.8,
        "severity": "medium",
        "impact": "150 order items reference non-existent products",
        "recommendation": "Update product references or archive deleted products"
      }
    ],
    "total_issues": 2,
    "overall_integrity_score": 94.8
  }
}
```

### 2.4 Detect Patterns

**Endpoint:** `POST /insights/patterns`

**Request Body:**
```json
{
  "schema_id": "abc-123",
  "pattern_types": ["frequency", "sequence", "temporal", "association"]
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "patterns": [
      {
        "pattern_id": "pat-001",
        "type": "frequency",
        "title": "Weekend shopping spike",
        "description": "Orders increase 40% on weekends",
        "confidence": 0.89,
        "frequency": "weekly",
        "details": {
          "average_weekday_orders": 1200,
          "average_weekend_orders": 1680,
          "increase_percentage": 40
        }
      },
      {
        "pattern_id": "pat-002",
        "type": "sequence",
        "title": "User onboarding sequence",
        "description": "Users who complete profile within 24h are 3x more likely to stay active",
        "confidence": 0.92,
        "details": {
          "step_1": "Sign up",
          "step_2": "Complete profile",
          "time_window": "24 hours",
          "retention_rate": 0.75
        }
      },
      {
        "pattern_id": "pat-003",
        "type": "association",
        "title": "Product bundle opportunity",
        "description": "Products A, B, and C are purchased together 35% of the time",
        "confidence": 0.85,
        "details": {
          "products": ["Product A", "Product B", "Product C"],
          "co_purchase_rate": 0.35,
          "recommendation": "Create bundle discount"
        }
      }
    ],
    "total_patterns": 8
  }
}
```

### 2.5 Get Anomalies

**Endpoint:** `GET /insights/anomalies`

**Query Parameters:**
- `schema_id` (required): string
- `time_period` (optional): integer (days), default 7

**Request:**
```
GET /insights/anomalies?schema_id=abc-123&time_period=7
```

**Response:**
```json
{
  "success": true,
  "data": {
    "anomalies": [
      {
        "anomaly_id": "ano-001",
        "detected_at": "2025-11-10T10:00:00Z",
        "severity": "high",
        "category": "volume",
        "description": "Order volume dropped 60% compared to baseline",
        "details": {
          "expected_value": 1500,
          "actual_value": 600,
          "deviation_percentage": -60,
          "z_score": -3.5
        },
        "possible_causes": [
          "System outage",
          "Marketing campaign ended",
          "Seasonal effect"
        ]
      },
      {
        "anomaly_id": "ano-002",
        "detected_at": "2025-11-09T15:30:00Z",
        "severity": "medium",
        "category": "distribution",
        "description": "Unusual spike in null values for email column",
        "details": {
          "column": "email",
          "normal_null_rate": 0.02,
          "current_null_rate": 0.15,
          "affected_records": 450
        },
        "possible_causes": [
          "Form validation issue",
          "Integration problem"
        ]
      }
    ],
    "total_anomalies": 2
  }
}
```

---

## Feature #9: A/B Testing & Experiment Platform

**Service:** Project Management  
**Base Path:** `/experiments`

### 9.1 Create Experiment

**Endpoint:** `POST /experiments/create`

**Request Body:**
```json
{
  "name": "Homepage CTA Button Test",
  "description": "Testing blue vs green CTA button on homepage",
  "hypothesis": "Green button will increase conversions by 10%",
  "variants": [
    {
      "name": "Control",
      "description": "Current blue button",
      "is_control": true,
      "traffic_allocation": 0.5
    },
    {
      "name": "Treatment",
      "description": "New green button",
      "is_control": false,
      "traffic_allocation": 0.5
    }
  ],
  "success_metric": "conversions",
  "minimum_detectable_effect": 0.1,
  "baseline_conversion_rate": 0.05
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "experiment": {
      "experiment_id": "exp-789",
      "name": "Homepage CTA Button Test",
      "status": "draft",
      "variants": [
        {
          "variant_id": "var-001",
          "name": "Control",
          "is_control": true
        },
        {
          "variant_id": "var-002",
          "name": "Treatment",
          "is_control": false
        }
      ],
      "sample_size_required": 3841,
      "created_at": "2025-11-10T10:00:00Z"
    },
    "message": "Experiment created successfully. Start when ready."
  }
}
```

### 9.2 List Experiments

**Endpoint:** `GET /experiments/list`

**Query Parameters:**
- `status` (optional): `"draft"`, `"running"`, `"completed"`, `"paused"`

**Request:**
```
GET /experiments/list?status=running
```

**Response:**
```json
{
  "success": true,
  "data": {
    "experiments": [
      {
        "experiment_id": "exp-789",
        "name": "Homepage CTA Button Test",
        "status": "running",
        "start_date": "2025-11-08T00:00:00Z",
        "end_date": "2025-11-22T23:59:59Z",
        "progress": {
          "current_sample_size": 2500,
          "required_sample_size": 3841,
          "percentage_complete": 65.1
        },
        "created_at": "2025-11-07T10:00:00Z"
      },
      {
        "experiment_id": "exp-790",
        "name": "Pricing Page Test",
        "status": "running",
        "start_date": "2025-11-09T00:00:00Z",
        "end_date": "2025-11-23T23:59:59Z",
        "progress": {
          "current_sample_size": 1200,
          "required_sample_size": 4000,
          "percentage_complete": 30.0
        },
        "created_at": "2025-11-08T14:00:00Z"
      }
    ],
    "total_count": 2
  }
}
```

### 9.3 Start Experiment

**Endpoint:** `POST /experiments/{experiment_id}/start`

**Request Body:**
```json
{
  "duration_days": 14
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "experiment_id": "exp-789",
    "status": "running",
    "start_date": "2025-11-10T10:00:00Z",
    "end_date": "2025-11-24T10:00:00Z",
    "message": "Experiment started successfully"
  }
}
```

### 9.4 Track Conversion Event

**Endpoint:** `POST /experiments/track`

**Request Body:**
```json
{
  "experiment_id": "exp-789",
  "variant_id": "var-002",
  "user_id": "user-123",
  "event_type": "conversion",
  "metadata": {
    "page": "homepage",
    "button_color": "green",
    "session_id": "sess-456"
  }
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "event_id": "evt-999",
    "tracked_at": "2025-11-10T10:30:00Z",
    "message": "Event tracked successfully"
  }
}
```

### 9.5 Analyze Experiment

**Endpoint:** `POST /experiments/{experiment_id}/analyze`

**Request Body:**
```json
{
  "include_recommendations": true
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "analysis": {
      "experiment_id": "exp-789",
      "statistical_significance": true,
      "p_value": 0.023,
      "confidence_level": 0.95,
      "results": {
        "control": {
          "variant_name": "Control",
          "conversions": 125,
          "total_samples": 2500,
          "conversion_rate": 0.05,
          "confidence_interval": [0.042, 0.058]
        },
        "treatment": {
          "variant_name": "Treatment",
          "conversions": 175,
          "total_samples": 2500,
          "conversion_rate": 0.07,
          "confidence_interval": [0.061, 0.079]
        }
      },
      "winner": "Treatment",
      "lift_percentage": 40.0,
      "recommendation": "Roll out Treatment variant - statistically significant 40% improvement"
    }
  }
}
```

### 9.6 Get Experiment Results

**Endpoint:** `GET /experiments/{experiment_id}/results`

**Request:**
```
GET /experiments/exp-789/results
```

**Response:**
```json
{
  "success": true,
  "data": {
    "experiment": {
      "experiment_id": "exp-789",
      "name": "Homepage CTA Button Test",
      "status": "running"
    },
    "current_results": {
      "control": {
        "variant_name": "Control",
        "conversions": 125,
        "total_samples": 2500,
        "conversion_rate": 0.05
      },
      "treatment": {
        "variant_name": "Treatment",
        "conversions": 175,
        "total_samples": 2500,
        "conversion_rate": 0.07
      }
    },
    "is_conclusive": true,
    "remaining_samples": 0,
    "days_remaining": 12
  }
}
```

### 9.7 Stop Experiment

**Endpoint:** `POST /experiments/{experiment_id}/stop`

**Request Body:**
```json
{
  "declare_winner": true,
  "reason": "Statistical significance achieved"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "experiment_id": "exp-789",
    "status": "completed",
    "winner": "Treatment",
    "stopped_at": "2025-11-10T10:45:00Z",
    "message": "Experiment stopped successfully"
  }
}
```

### 9.8 Delete Experiment

**Endpoint:** `DELETE /experiments/{experiment_id}`

**Request:**
```
DELETE /experiments/exp-789
```

**Response:**
```json
{
  "success": true,
  "data": {
    "message": "Experiment deleted successfully"
  }
}
```

---

## Feature #4a: Data Valuation Engine

**Service:** Project Management  
**Base Path:** `/valuation`

### 4a.1 Analyze Data Value

**Endpoint:** `POST /valuation/analyze`

**Request Body:**
```json
{
  "dataset_name": "Customer Transaction Database",
  "category": "transactional",
  "row_count": 50000,
  "column_count": 25,
  "update_frequency": "daily",
  "data_quality_score": 87.5,
  "has_pii": true,
  "industry": "e-commerce",
  "description": "Complete customer transaction history with product details"
}
```

**Category Options:** `"behavioral"`, `"demographic"`, `"transactional"`, `"location"`, `"sensor"`, `"social"`, `"financial"`, `"healthcare"`

**Response:**
```json
{
  "success": true,
  "data": {
    "valuation": {
      "valuation_id": "val-123",
      "dataset_name": "Customer Transaction Database",
      "estimated_value_low": 17500.00,
      "estimated_value_mid": 25000.00,
      "estimated_value_high": 37500.00,
      "recommended_price_monthly": 3750.00,
      "recommended_price_yearly": 37500.00,
      "recommended_price_per_record": 0.50,
      "confidence_score": 85.0,
      "valuation_factors": {
        "base_price": 0.50,
        "industry_multiplier": 1.5,
        "quality_multiplier": 1.5,
        "freshness_multiplier": 1.5,
        "size_multiplier": 0.9,
        "pii_multiplier": 0.7,
        "final_price_per_record": 0.5292
      },
      "monetization_strategies": [
        {
          "strategy": "subscription",
          "estimated_monthly_revenue": 3750.00,
          "estimated_yearly_revenue": 45000.00,
          "setup_complexity": "medium",
          "time_to_revenue": "1-3 months",
          "recommended_pricing": {
            "monthly": 3750.00,
            "yearly": 37500.00
          },
          "pros": [
            "Recurring revenue stream",
            "Higher lifetime value",
            "Retain data ownership"
          ],
          "cons": [
            "Requires ongoing updates",
            "Customer support needed",
            "Churn risk"
          ],
          "action_items": [
            "Set up automated data refresh",
            "Create tiered pricing plans",
            "Build subscriber portal"
          ]
        },
        {
          "strategy": "api_access",
          "estimated_monthly_revenue": 15000.00,
          "estimated_yearly_revenue": 180000.00,
          "setup_complexity": "high",
          "time_to_revenue": "3-6 months",
          "recommended_pricing": {
            "per_api_call": 0.005,
            "monthly_quota_100k": 1875.00,
            "monthly_quota_1m": 5625.00
          },
          "pros": [
            "Scalable revenue model",
            "Usage-based pricing",
            "Developer-friendly"
          ],
          "cons": [
            "Complex infrastructure",
            "Rate limiting needed",
            "Higher support costs"
          ],
          "action_items": [
            "Build RESTful API",
            "Implement authentication",
            "Create API documentation",
            "Set up billing integration"
          ]
        }
      ],
      "market_comparables": [
        {
          "dataset_type": "transactional data in e-commerce",
          "price_range": "$5,000 - $50,000",
          "typical_buyers": ["Market research firms", "Analytics companies", "Enterprises"],
          "market_size": "Growing 15% YoY"
        }
      ],
      "valued_at": "2025-11-10T10:00:00Z"
    },
    "summary": {
      "estimated_value": "$25,000.00",
      "monthly_potential": "$3,750.00/month",
      "top_strategy": "subscription"
    }
  }
}
```

### 4a.2 Quick Estimate

**Endpoint:** `GET /valuation/estimate`

**Query Parameters:**
- `category` (required): DataCategory enum
- `row_count` (required): integer
- `industry` (optional): string, default "general"

**Request:**
```
GET /valuation/estimate?category=transactional&row_count=50000&industry=e-commerce
```

**Response:**
```json
{
  "success": true,
  "data": {
    "estimated_value": 37500.00,
    "estimated_monthly_revenue": 5625.00,
    "price_per_record": 0.75,
    "note": "This is a quick estimate. Use /analyze for detailed valuation"
  }
}
```

### 4a.3 Get Pricing Recommendations

**Endpoint:** `POST /valuation/pricing`

**Request Body:**
```json
{
  "dataset_value": 25000.00,
  "target_market": "enterprise"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "pricing_tiers": {
      "starter": {
        "price": 2500.00,
        "features": [
          "Limited API calls",
          "Monthly updates",
          "Basic support"
        ],
        "target_customers": "Small businesses, startups"
      },
      "professional": {
        "price": 6250.00,
        "features": [
          "Unlimited API calls",
          "Weekly updates",
          "Priority support",
          "Custom exports"
        ],
        "target_customers": "Medium businesses, agencies"
      },
      "enterprise": {
        "price": 12500.00,
        "features": [
          "Full access",
          "Real-time updates",
          "Dedicated support",
          "Custom integrations",
          "SLA guarantees"
        ],
        "target_customers": "Large enterprises, data brokers"
      }
    },
    "recommended_tier": "professional",
    "upsell_strategy": "Start with Starter, upsell to Professional after 3 months"
  }
}
```

### 4a.4 Get Monetization Recommendations

**Endpoint:** `GET /valuation/recommendations`

**Query Parameters:**
- `dataset_category` (required): DataCategory enum
- `dataset_size` (required): integer

**Request:**
```
GET /valuation/recommendations?dataset_category=transactional&dataset_size=50000
```

**Response:**
```json
{
  "success": true,
  "data": {
    "recommendations": [
      {
        "priority": "high",
        "recommendation": "Build API access with usage-based pricing",
        "reasoning": "Medium datasets ideal for API monetization",
        "expected_revenue": "$2,000 - $10,000/month"
      }
    ],
    "next_steps": [
      "Get detailed valuation analysis",
      "Anonymize sensitive data",
      "List on data marketplace",
      "Set up payment processing"
    ]
  }
}
```

---

## Feature #4b: Data Marketplace

**Service:** Project Management  
**Base Path:** `/marketplace`

### 4b.1 Create Listing

**Endpoint:** `POST /marketplace/list`

**Request Body:**
```json
{
  "title": "E-commerce Customer Behavior Dataset",
  "description": "Comprehensive customer behavior data including purchases, browsing patterns, and demographics. Perfect for ML models and market research.",
  "category": "behavioral",
  "price": 5000.00,
  "pricing_model": "one-time",
  "row_count": 100000,
  "column_count": 30,
  "update_frequency": "monthly",
  "privacy_level": "public",
  "dataset_url": "s3://my-bucket/datasets/customer-behavior.csv",
  "sample_data": {
    "age_group": "25-34",
    "purchase_frequency": "weekly",
    "avg_order_value": 125.50
  },
  "tags": ["e-commerce", "customer-behavior", "marketing", "analytics"]
}
```

**Privacy Level Options:** `"public"`, `"restricted"`, `"private"`, `"confidential"`  
**Pricing Model Options:** `"one-time"`, `"subscription"`, `"usage-based"`

**Response:**
```json
{
  "success": true,
  "data": {
    "listing": {
      "dataset_id": "ds-456",
      "title": "E-commerce Customer Behavior Dataset",
      "status": "draft",
      "created_at": "2025-11-10T10:00:00Z"
    },
    "next_steps": [
      "Your listing is in DRAFT status",
      "Provide sample data for preview",
      "Submit for review to publish",
      "Once approved, it will be visible to buyers"
    ]
  }
}
```

### 4b.2 Search Marketplace

**Endpoint:** `GET /marketplace/search`

**Query Parameters:**
- `category` (optional): string
- `min_price` (optional): float
- `max_price` (optional): float
- `privacy_level` (optional): PrivacyLevel enum
- `tags` (optional): comma-separated string
- `min_rows` (optional): integer

**Request:**
```
GET /marketplace/search?category=behavioral&max_price=10000&tags=e-commerce,marketing
```

**Response:**
```json
{
  "success": true,
  "data": {
    "total_results": 15,
    "listings": [
      {
        "dataset_id": "ds-456",
        "title": "E-commerce Customer Behavior Dataset",
        "description": "Comprehensive customer behavior data...",
        "category": "behavioral",
        "seller_id": "user-789",
        "seller_name": "User_12345678",
        "price": 5000.00,
        "pricing_model": "one-time",
        "row_count": 100000,
        "column_count": 30,
        "last_updated": "2025-11-10T10:00:00Z",
        "update_frequency": "monthly",
        "privacy_level": "public",
        "status": "published",
        "rating": 4.5,
        "purchase_count": 12,
        "tags": ["e-commerce", "customer-behavior", "marketing"]
      }
    ],
    "filters_applied": {
      "category": "behavioral",
      "price_range": "$0 - $10000",
      "privacy_level": null,
      "tags": ["e-commerce", "marketing"],
      "min_rows": null
    }
  }
}
```

### 4b.3 Purchase Dataset

**Endpoint:** `POST /marketplace/purchase`

**Request Body:**
```json
{
  "dataset_id": "ds-456",
  "payment_method": "credit_card",
  "billing_info": {
    "name": "John Doe",
    "email": "john@example.com",
    "company": "Acme Corp"
  }
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "transaction": {
      "transaction_id": "txn-999",
      "dataset_id": "ds-456",
      "buyer_id": "user-123",
      "seller_id": "user-789",
      "amount": 5000.00,
      "status": "completed",
      "payment_method": "credit_card",
      "created_at": "2025-11-10T10:30:00Z",
      "completed_at": "2025-11-10T10:30:15Z",
      "access_url": "/api/marketplace/download/ds-456?token=abc123xyz",
      "access_expires_at": null
    },
    "message": "Purchase completed successfully!",
    "access_info": {
      "download_url": "/api/marketplace/download/ds-456?token=abc123xyz",
      "expires_at": "Never",
      "instructions": "Use the download URL to access your data. Keep this secure."
    }
  }
}
```

### 4b.4 Get My Purchases

**Endpoint:** `GET /marketplace/purchases`

**Request:**
```
GET /marketplace/purchases
```

**Response:**
```json
{
  "success": true,
  "data": {
    "total_purchases": 3,
    "purchases": [
      {
        "transaction": {
          "transaction_id": "txn-999",
          "dataset_id": "ds-456",
          "amount": 5000.00,
          "status": "completed",
          "created_at": "2025-11-10T10:30:00Z",
          "access_url": "/api/marketplace/download/ds-456?token=abc123xyz"
        },
        "dataset": {
          "dataset_id": "ds-456",
          "title": "E-commerce Customer Behavior Dataset",
          "seller_name": "User_12345678"
        }
      }
    ]
  }
}
```

### 4b.5 Get My Sales

**Endpoint:** `GET /marketplace/sales`

**Request:**
```
GET /marketplace/sales
```

**Response:**
```json
{
  "success": true,
  "data": {
    "total_revenue": 15000.00,
    "total_sales": 3,
    "unique_datasets_sold": 2,
    "active_listings": 5,
    "average_sale_price": 5000.00
  }
}
```

### 4b.6 Anonymize Data

**Endpoint:** `POST /marketplace/anonymize`

**Request Body:**
```json
{
  "data_sample": {
    "email": "john@example.com",
    "phone": "+1-555-0123",
    "name": "John Doe",
    "age": 35,
    "purchase_amount": 125.50
  },
  "privacy_level": "public"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "anonymization_result": {
      "success": true,
      "anonymized_rows": 2,
      "techniques_applied": [
        "Removed PII column: email",
        "Removed PII column: phone",
        "Removed PII column: name"
      ],
      "privacy_score": 95.0,
      "pii_removed": ["email", "phone", "name"],
      "warnings": []
    },
    "recommendation": "Safe to share publicly"
  }
}
```

### 4b.7 Get Dataset Details

**Endpoint:** `GET /marketplace/dataset/{dataset_id}`

**Request:**
```
GET /marketplace/dataset/ds-456
```

**Response:**
```json
{
  "success": true,
  "data": {
    "listing": {
      "dataset_id": "ds-456",
      "title": "E-commerce Customer Behavior Dataset",
      "description": "Comprehensive customer behavior data...",
      "price": 5000.00,
      "seller_name": "User_12345678",
      "rating": 4.5,
      "purchase_count": 12,
      "tags": ["e-commerce", "customer-behavior"]
    },
    "has_purchased": false,
    "can_purchase": true
  }
}
```

### 4b.8 Publish Listing

**Endpoint:** `PUT /marketplace/listing/{dataset_id}/publish`

**Request:**
```
PUT /marketplace/listing/ds-456/publish
```

**Response:**
```json
{
  "success": true,
  "data": {
    "listing": {
      "dataset_id": "ds-456",
      "status": "published"
    },
    "message": "Dataset is now live on marketplace!"
  }
}
```

---

## Error Responses

All endpoints follow a consistent error response format:

```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "details": {}
  }
}
```

**Common HTTP Status Codes:**
- `200` - Success
- `400` - Bad Request (invalid input)
- `401` - Unauthorized (missing/invalid JWT token)
- `403` - Forbidden (insufficient permissions)
- `404` - Not Found
- `422` - Unprocessable Entity (validation error)
- `429` - Too Many Requests (rate limit)
- `500` - Internal Server Error

---

## Authentication

All endpoints require JWT authentication. Include the token in the Authorization header:

```javascript
const response = await fetch('http://localhost:8000/health/analyze', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${jwtToken}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    schema_id: 'abc-123',
    include_recommendations: true
  })
});
```

---

## Rate Limiting

**Schema Detection Service:** 100 requests per minute per IP  
**Project Management Service:** Follows same rate limiting policy

When rate limit is exceeded:
```json
{
  "message": "Rate limit exceeded. Please try again later.",
  "status": "error"
}
```

---

## Frontend Integration Examples

### React Example - Health Score

```typescript
import { useState } from 'react';

interface HealthScoreResponse {
  success: boolean;
  data: {
    health_score: {
      overall_score: number;
      status: string;
      dimensions: Record<string, any>;
      issues: any[];
    };
  };
}

const useHealthScore = () => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const analyzeHealth = async (schemaId: string, token: string) => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch('http://localhost:8000/health/analyze', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          schema_id: schemaId,
          include_recommendations: true
        })
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data: HealthScoreResponse = await response.json();
      return data.data.health_score;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
      throw err;
    } finally {
      setLoading(false);
    }
  };

  return { analyzeHealth, loading, error };
};

export default useHealthScore;
```

### React Example - A/B Testing

```typescript
const useExperiment = () => {
  const createExperiment = async (experimentData: any, token: string) => {
    const response = await fetch('http://localhost:8001/experiments/create', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(experimentData)
    });

    return response.json();
  };

  const trackConversion = async (
    experimentId: string,
    variantId: string,
    userId: string,
    token: string
  ) => {
    const response = await fetch('http://localhost:8001/experiments/track', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        experiment_id: experimentId,
        variant_id: variantId,
        user_id: userId,
        event_type: 'conversion'
      })
    });

    return response.json();
  };

  return { createExperiment, trackConversion };
};
```

---

## Summary

**Total Endpoints:** 30  
**Services:** 2 (Schema Detection, Project Management)

**Breakdown by Feature:**
- Health Score: 5 endpoints
- AI Insights: 5 endpoints
- A/B Testing: 8 endpoints
- Data Valuation: 4 endpoints
- Data Marketplace: 8 endpoints

All endpoints are **production-ready** with proper authentication, validation, error handling, and user isolation.
