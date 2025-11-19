# Phase 1: Backend API Specification

**Purpose:** Complete API endpoints documentation for Phase 1 features to ensure seamless frontend-backend integration.

---



## Phase 1.1: Quick Deploy Cost Analysis

### 1.1.1 Cost Comparison Widget

**Endpoint:** `POST /api/cost/compare`

**Request:**
```json
{
  "database_type": "postgresql",
  "storage_gb": 100,
  "region": "us-east-1",
  "performance_requirements": {
    "qps": 1000,
    "connections": 100,
    "iops": 3000
  }
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "providers": [
      {
        "provider": "aws",
        "instance_type": "db.t3.large",
        "monthly_cost": 127.44,
        "breakdown": {
          "instance": 72.96,
          "storage": 10.00,
          "backup": 15.00,
          "network": 5.00,
          "iops": 24.48
        },
        "specs": {
          "cpu_cores": 2,
          "memory_gb": 8,
          "storage_type": "gp3",
          "iops": 3000
        }
      },
      {
        "provider": "gcp",
        "instance_type": "db-n1-standard-2",
        "monthly_cost": 143.52,
        "breakdown": {
          "instance": 85.32,
          "storage": 10.00,
          "backup": 20.00,
          "network": 8.20,
          "iops": 20.00
        },
        "specs": {
          "cpu_cores": 2,
          "memory_gb": 7.5,
          "storage_type": "pd-ssd",
          "iops": 3000
        }
      },
      {
        "provider": "azure",
        "instance_type": "Standard_D2s_v3",
        "monthly_cost": 156.89,
        "breakdown": {
          "instance": 96.00,
          "storage": 12.00,
          "backup": 22.00,
          "network": 6.89,
          "iops": 20.00
        },
        "specs": {
          "cpu_cores": 2,
          "memory_gb": 8,
          "storage_type": "Premium_LRS",
          "iops": 3200
        }
      }
    ],
    "recommendation": "aws",
    "savings": {
      "vs_gcp": 16.08,
      "vs_azure": 29.45
    }
  }
}
```

---

### 1.1.2 Hidden Cost Calculator

**Endpoint:** `POST /api/cost/hidden-costs`

**Request:**
```json
{
  "provider": "aws",
  "storage_gb": 100,
  "backup_enabled": true,
  "multi_az": false,
  "estimated_monthly_queries": 5000000,
  "data_transfer_gb": 100
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "visible_costs": {
      "instance": 72.96,
      "storage": 10.00
    },
    "hidden_costs": [
      {
        "category": "backup_storage",
        "description": "Automated backup retention (7 days)",
        "monthly_cost": 15.00,
        "details": "100 GB × $0.15/GB"
      },
      {
        "category": "snapshot_storage",
        "description": "Manual snapshots (2 per month, 30 day retention)",
        "monthly_cost": 9.00,
        "details": "200 GB total × $0.045/GB"
      },
      {
        "category": "data_transfer_out",
        "description": "Outbound data transfer",
        "monthly_cost": 9.00,
        "details": "100 GB × $0.09/GB"
      },
      {
        "category": "cross_az_transfer",
        "description": "Cross-AZ data transfer (app to DB)",
        "monthly_cost": 2.00,
        "details": "20 GB × $0.01/GB"
      },
      {
        "category": "cloudwatch_metrics",
        "description": "Enhanced monitoring",
        "monthly_cost": 3.50,
        "details": "7 metrics × $0.50/metric"
      },
      {
        "category": "logs",
        "description": "CloudWatch Logs storage",
        "monthly_cost": 2.50,
        "details": "5 GB × $0.50/GB"
      }
    ],
    "total_visible": 82.96,
    "total_hidden": 41.00,
    "total_monthly_cost": 123.96,
    "hidden_percentage": 33.07
  }
}
```

---

### 1.1.3 Performance Predictor

**Endpoint:** `POST /api/cost/predict-performance`

**Request:**
```json
{
  "instance_type": "db.t3.large",
  "provider": "aws",
  "storage_gb": 100,
  "expected_qps": 1000,
  "expected_connections": 100
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "instance_type": "db.t3.large",
    "cpu_cores": 2,
    "memory_gb": 8,
    "capacity": {
      "max_qps": 2400,
      "max_connections": 400,
      "max_throughput_mbps": 400,
      "recommended_qps": 1680
    },
    "utilization": {
      "cpu_percent": 42,
      "memory_percent": 25,
      "disk_iops": 300
    },
    "scaling_thresholds": {
      "warning_qps": 1680,
      "critical_qps": 2160
    },
    "performance_tier": "medium"
  }
}
```

---

### 1.1.4 Reserved Instance Advisor

**Endpoint:** `POST /api/cost/reserved-instance-analysis`

**Request:**
```json
{
  "provider": "aws",
  "instance_type": "db.t3.large",
  "monthly_ondemand_cost": 127.44,
  "expected_usage_months": 24
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "options": [
      {
        "type": "on_demand",
        "commitment": "none",
        "upfront_cost": 0,
        "monthly_cost": 127.44,
        "total_24_months": 3058.56,
        "savings_vs_ondemand": 0,
        "savings_percent": 0,
        "flexibility": "high"
      },
      {
        "type": "reserved_1year_no_upfront",
        "commitment": "1 year",
        "upfront_cost": 0,
        "monthly_cost": 95.58,
        "total_24_months": 2293.92,
        "savings_vs_ondemand": 764.64,
        "savings_percent": 25,
        "flexibility": "medium"
      },
      {
        "type": "reserved_1year_partial_upfront",
        "commitment": "1 year",
        "upfront_cost": 573.48,
        "monthly_cost": 47.79,
        "total_24_months": 2293.92,
        "savings_vs_ondemand": 764.64,
        "savings_percent": 25,
        "flexibility": "medium"
      },
      {
        "type": "reserved_1year_all_upfront",
        "commitment": "1 year",
        "upfront_cost": 1146.96,
        "monthly_cost": 0,
        "total_24_months": 2293.92,
        "savings_vs_ondemand": 764.64,
        "savings_percent": 25,
        "flexibility": "low"
      },
      {
        "type": "reserved_3year_no_upfront",
        "commitment": "3 years",
        "upfront_cost": 0,
        "monthly_cost": 63.72,
        "total_24_months": 1529.28,
        "savings_vs_ondemand": 1529.28,
        "savings_percent": 50,
        "flexibility": "low"
      },
      {
        "type": "reserved_3year_all_upfront",
        "commitment": "3 years",
        "upfront_cost": 2293.92,
        "monthly_cost": 0,
        "total_24_months": 2293.92,
        "savings_vs_ondemand": 764.64,
        "savings_percent": 25,
        "flexibility": "very_low"
      }
    ],
    "recommendation": "reserved_1year_partial_upfront",
    "break_even_months": 6
  }
}
```

---

### 1.1.5 Multi-Region Cost Analysis

**Endpoint:** `POST /api/cost/multi-region-analysis`

**Request:**
```json
{
  "provider": "aws",
  "instance_type": "db.t3.large",
  "storage_gb": 100,
  "primary_market": "North America",
  "expected_data_transfer_gb": 100
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "regions": [
      {
        "region": "us-east-1",
        "location": "Virginia, USA",
        "market": "North America",
        "monthly_cost": 127.44,
        "breakdown": {
          "instance": 72.96,
          "storage": 10.00,
          "backup": 15.00,
          "network": 5.00,
          "data_transfer": 24.48
        },
        "latency_to_market": 10,
        "compliance": ["SOC2", "HIPAA", "PCI-DSS"]
      },
      {
        "region": "us-west-2",
        "location": "Oregon, USA",
        "market": "North America",
        "monthly_cost": 127.44,
        "breakdown": {
          "instance": 72.96,
          "storage": 10.00,
          "backup": 15.00,
          "network": 5.00,
          "data_transfer": 24.48
        },
        "latency_to_market": 45,
        "compliance": ["SOC2", "HIPAA", "PCI-DSS"]
      },
      {
        "region": "eu-west-1",
        "location": "Ireland",
        "market": "Europe",
        "monthly_cost": 141.17,
        "breakdown": {
          "instance": 80.88,
          "storage": 11.00,
          "backup": 16.50,
          "network": 5.50,
          "data_transfer": 27.29
        },
        "latency_to_market": 85,
        "compliance": ["GDPR", "SOC2", "ISO27001"]
      },
      {
        "region": "ap-southeast-1",
        "location": "Singapore",
        "market": "Asia Pacific",
        "monthly_cost": 152.92,
        "breakdown": {
          "instance": 87.55,
          "storage": 12.00,
          "backup": 18.00,
          "network": 6.00,
          "data_transfer": 29.37
        },
        "latency_to_market": 180,
        "compliance": ["SOC2", "ISO27001"]
      }
    ],
    "recommendation": "us-east-1",
    "savings_vs_most_expensive": 25.48
  }
}
```

---

### 1.1.6 Disaster Recovery Planner

**Endpoint:** `POST /api/cost/disaster-recovery-plan`

**Request:**
```json
{
  "base_monthly_cost": 127.44,
  "provider": "aws",
  "business_criticality": "medium",
  "compliance_requirements": ["SOC2", "GDPR"]
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "plans": [
      {
        "tier": "basic",
        "name": "Backup Only",
        "rpo_hours": 24,
        "rto_hours": 12,
        "monthly_cost": 15.30,
        "features": [
          "Daily automated backups",
          "7-day retention",
          "Point-in-time recovery",
          "Manual restore process"
        ],
        "compliance": ["Basic GDPR"],
        "total_cost": 142.74
      },
      {
        "tier": "standard",
        "name": "Multi-AZ Standby",
        "rpo_hours": 0,
        "rto_hours": 1,
        "monthly_cost": 142.74,
        "features": [
          "Synchronous replication",
          "Automatic failover",
          "Zero data loss",
          "Continuous backups"
        ],
        "compliance": ["SOC2", "GDPR"],
        "total_cost": 270.18
      },
      {
        "tier": "premium",
        "name": "Multi-Region Active-Active",
        "rpo_hours": 0,
        "rto_hours": 0,
        "monthly_cost": 395.76,
        "features": [
          "Active-active deployment",
          "Global load balancing",
          "Zero downtime failover",
          "Cross-region replication"
        ],
        "compliance": ["SOC2", "GDPR", "HIPAA"],
        "total_cost": 523.20
      }
    ],
    "recommendation": "standard",
    "annual_downtime_cost_without_dr": 50000,
    "annual_downtime_cost_with_standard": 500,
    "roi_calculation": {
      "annual_dr_cost": 1716.12,
      "annual_downtime_savings": 49500,
      "net_annual_savings": 47783.88,
      "roi_percentage": 2784
    }
  }
}
```

---

## Phase 1.2: Schema Browser Security & Compliance

### 1.2.1 PII Detection Scanner

**Endpoint:** `POST /api/compliance/detect-pii`

**Request:**
```json
{
  "schema": {
    "database_type": "postgresql",
    "tables": [
      {
        "name": "users",
        "columns": [
          {"name": "id", "type": "integer"},
          {"name": "email", "type": "varchar"},
          {"name": "phone", "type": "varchar"},
          {"name": "ssn", "type": "varchar"},
          {"name": "created_at", "type": "timestamp"}
        ]
      }
    ]
  }
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "pii_fields": [
      {
        "table": "users",
        "column": "email",
        "pii_type": "email_address",
        "confidence": 0.99,
        "severity": "high",
        "affected_records": 125847,
        "compliance_frameworks": ["GDPR", "CCPA"],
        "recommendations": [
          "Enable encryption at rest",
          "Add data retention policy",
          "Implement consent tracking"
        ]
      },
      {
        "table": "users",
        "column": "phone",
        "pii_type": "phone_number",
        "confidence": 0.95,
        "severity": "high",
        "affected_records": 98234,
        "compliance_frameworks": ["GDPR", "CCPA"],
        "recommendations": [
          "Enable encryption at rest",
          "Add opt-out mechanism"
        ]
      },
      {
        "table": "users",
        "column": "ssn",
        "pii_type": "social_security_number",
        "confidence": 0.98,
        "severity": "critical",
        "affected_records": 125847,
        "compliance_frameworks": ["GDPR", "HIPAA", "PCI-DSS"],
        "recommendations": [
          "Enable encryption at rest and in transit",
          "Implement audit logging",
          "Restrict access to authorized personnel only"
        ]
      }
    ],
    "summary": {
      "total_pii_fields": 3,
      "total_affected_records": 125847,
      "compliance_risk": "high",
      "frameworks_affected": ["GDPR", "CCPA", "HIPAA", "PCI-DSS"]
    }
  }
}
```

---

### 1.2.2 Compliance Heatmap

**Endpoint:** `POST /api/compliance/heatmap`

**Request:**
```json
{
  "schema": {
    "database_type": "postgresql",
    "tables": [
      {"name": "users", "row_count": 125847},
      {"name": "orders", "row_count": 543219},
      {"name": "payments", "row_count": 234156}
    ]
  },
  "frameworks": ["GDPR", "SOC2", "HIPAA"]
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "heatmap": [
      {
        "table": "users",
        "gdpr_score": 45,
        "soc2_score": 72,
        "hipaa_score": 38,
        "overall_score": 52,
        "risk_level": "high",
        "issues": [
          {
            "framework": "GDPR",
            "issue": "No encryption on email field",
            "severity": "high"
          },
          {
            "framework": "HIPAA",
            "issue": "Missing audit trail for PHI access",
            "severity": "critical"
          }
        ]
      },
      {
        "table": "orders",
        "gdpr_score": 68,
        "soc2_score": 85,
        "hipaa_score": 92,
        "overall_score": 82,
        "risk_level": "medium",
        "issues": [
          {
            "framework": "GDPR",
            "issue": "No data retention policy",
            "severity": "medium"
          }
        ]
      },
      {
        "table": "payments",
        "gdpr_score": 88,
        "soc2_score": 95,
        "hipaa_score": 90,
        "overall_score": 91,
        "risk_level": "low",
        "issues": []
      }
    ],
    "summary": {
      "overall_compliance_score": 75,
      "total_tables": 3,
      "high_risk_tables": 1,
      "medium_risk_tables": 1,
      "low_risk_tables": 1
    }
  }
}
```

---

### 1.2.3 Retention Policy Manager

**Endpoint:** `POST /api/compliance/retention-policies`

**Request:**
```json
{
  "schema": {
    "database_type": "postgresql",
    "tables": [
      {"name": "users", "has_created_at": true},
      {"name": "audit_logs", "has_created_at": true},
      {"name": "sessions", "has_created_at": true}
    ]
  }
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "policies": [
      {
        "table": "users",
        "current_policy": "none",
        "recommended_policy": {
          "retention_days": 2555,
          "retention_years": 7,
          "reason": "GDPR requires 7 year retention for financial records",
          "auto_delete": true,
          "archive_before_delete": true
        },
        "implementation": {
          "sql": "ALTER TABLE users ADD COLUMN deleted_at TIMESTAMP;\nCREATE INDEX idx_users_deleted_at ON users(deleted_at) WHERE deleted_at IS NOT NULL;",
          "cron": "0 0 * * * DELETE FROM users WHERE created_at < NOW() - INTERVAL '7 years' AND deleted_at IS NULL;",
          "estimated_records_affected": 12500
        }
      },
      {
        "table": "audit_logs",
        "current_policy": "none",
        "recommended_policy": {
          "retention_days": 2555,
          "retention_years": 7,
          "reason": "SOC2 requires audit log retention for 7 years",
          "auto_delete": false,
          "archive_before_delete": true
        },
        "implementation": {
          "sql": "-- No schema changes needed\n-- Implement archive process instead of deletion",
          "cron": "0 2 * * 0 pg_dump --table=audit_logs --where=\"created_at < NOW() - INTERVAL '7 years'\" > archive.sql",
          "estimated_records_affected": 5400000
        }
      },
      {
        "table": "sessions",
        "current_policy": "none",
        "recommended_policy": {
          "retention_days": 90,
          "retention_years": 0.25,
          "reason": "Security best practice: expire old sessions",
          "auto_delete": true,
          "archive_before_delete": false
        },
        "implementation": {
          "sql": "ALTER TABLE sessions ADD COLUMN expires_at TIMESTAMP DEFAULT NOW() + INTERVAL '90 days';",
          "cron": "0 0 * * * DELETE FROM sessions WHERE expires_at < NOW();",
          "estimated_records_affected": 234000
        }
      }
    ],
    "summary": {
      "total_tables": 3,
      "tables_with_policies": 0,
      "tables_needing_policies": 3,
      "total_records_to_cleanup": 5646500
    }
  }
}
```

---

### 1.2.4 Data Quality Dashboard

**Endpoint:** `POST /api/compliance/data-quality`

**Request:**
```json
{
  "schema": {
    "database_type": "postgresql",
    "tables": [
      {
        "name": "users",
        "columns": [
          {"name": "email", "type": "varchar", "nullable": false},
          {"name": "phone", "type": "varchar", "nullable": true}
        ]
      }
    ]
  },
  "connection_string": "postgresql://..."
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "quality_metrics": [
      {
        "table": "users",
        "column": "email",
        "metrics": {
          "completeness": 98.5,
          "validity": 94.2,
          "uniqueness": 100,
          "consistency": 96.8
        },
        "issues": [
          {
            "type": "invalid_format",
            "count": 7234,
            "severity": "medium",
            "examples": ["user@", "invalid.email", "@domain.com"]
          },
          {
            "type": "duplicate_values",
            "count": 0,
            "severity": "low"
          }
        ],
        "overall_quality_score": 97.4
      },
      {
        "table": "users",
        "column": "phone",
        "metrics": {
          "completeness": 72.3,
          "validity": 88.9,
          "uniqueness": 99.2,
          "consistency": 85.6
        },
        "issues": [
          {
            "type": "missing_values",
            "count": 34876,
            "severity": "medium",
            "percentage": 27.7
          },
          {
            "type": "invalid_format",
            "count": 12543,
            "severity": "high",
            "examples": ["123", "abc-defg", "00000000"]
          }
        ],
        "overall_quality_score": 86.5
      }
    ],
    "summary": {
      "overall_quality_score": 92,
      "total_issues": 54653,
      "critical_issues": 0,
      "high_severity_issues": 12543,
      "medium_severity_issues": 42110
    }
  }
}
```

---

## Phase 1.3: Query Cost & Optimization

### 1.3.1 Query Cost Explainer

**Endpoint:** `POST /api/query/analyze-cost`

**Request:**
```json
{
  "query": "SELECT * FROM users WHERE email = 'user@example.com'",
  "provider": "aws",
  "executions_per_day": 10000,
  "database_type": "postgresql"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "per_execution": 0.0023,
    "breakdown": {
      "cpu_time_ms": 450,
      "cpu_cost": 0.0015,
      "io_operations": 85,
      "io_cost": 0.0008,
      "network_transfer_mb": 0.5,
      "network_cost": 0.00001
    },
    "monthly_cost": 690,
    "execution_frequency": 10000,
    "optimization_available": true,
    "optimized_comparison": {
      "current_query": "SELECT * FROM users WHERE email = 'user@example.com'",
      "optimized_query": "SELECT id, email, name FROM users WHERE email = 'user@example.com'",
      "current_cost": {
        "per_execution": 0.0023,
        "monthly_cost": 690
      },
      "optimized_cost": {
        "per_execution": 0.0001,
        "monthly_cost": 30
      },
      "savings_percent": 95.7,
      "performance_improvement": {
        "current_time_ms": 2400,
        "optimized_time_ms": 20,
        "speedup_factor": 120
      },
      "optimization_type": "Add index on email + use specific columns"
    }
  }
}
```

---

### 1.3.2 Index Recommendation Widget

**Endpoint:** `POST /api/query/analyze-indexes`

**Request:**
```json
{
  "schema": {
    "database_type": "postgresql",
    "tables": [
      {
        "name": "orders",
        "columns": ["id", "user_id", "created_at", "status"],
        "indexes": ["PRIMARY KEY (id)"]
      },
      {
        "name": "users",
        "columns": ["id", "email", "created_at"],
        "indexes": ["PRIMARY KEY (id)"]
      }
    ]
  },
  "query_logs": [
    "SELECT * FROM orders WHERE user_id = 123",
    "SELECT * FROM users WHERE email = 'user@example.com'"
  ],
  "provider": "aws"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "recommendations": [
      {
        "table": "orders",
        "columns": ["user_id"],
        "index_type": "btree",
        "reason": "Frequent JOIN and WHERE clauses on user_id column",
        "impact": {
          "current_cost_per_query": 0.0023,
          "estimated_cost_after_index": 0.0001,
          "cost_reduction_percent": 95.7,
          "current_execution_time_ms": 2400,
          "estimated_execution_time_ms": 20,
          "performance_improvement_factor": 120
        },
        "sql": "CREATE INDEX idx_orders_user_id ON orders(user_id);",
        "affected_queries": 847,
        "priority": "critical",
        "size_estimate_mb": 45
      },
      {
        "table": "products",
        "columns": ["category_id", "created_at"],
        "index_type": "btree",
        "reason": "Composite index for category filtering with date sorting",
        "impact": {
          "current_cost_per_query": 0.0015,
          "estimated_cost_after_index": 0.0002,
          "cost_reduction_percent": 86.7,
          "current_execution_time_ms": 850,
          "estimated_execution_time_ms": 35,
          "performance_improvement_factor": 24
        },
        "sql": "CREATE INDEX idx_products_category_created ON products(category_id, created_at DESC);",
        "affected_queries": 523,
        "priority": "high",
        "size_estimate_mb": 28
      },
      {
        "table": "users",
        "columns": ["email"],
        "index_type": "btree",
        "reason": "Unique index for login queries (email lookups)",
        "impact": {
          "current_cost_per_query": 0.0008,
          "estimated_cost_after_index": 0.0001,
          "cost_reduction_percent": 87.5,
          "current_execution_time_ms": 320,
          "estimated_execution_time_ms": 8,
          "performance_improvement_factor": 40
        },
        "sql": "CREATE UNIQUE INDEX idx_users_email ON users(email);",
        "affected_queries": 1250,
        "priority": "critical",
        "size_estimate_mb": 12
      },
      {
        "table": "order_items",
        "columns": ["order_id", "product_id"],
        "index_type": "covering",
        "reason": "Covering index to eliminate table lookups",
        "impact": {
          "current_cost_per_query": 0.0012,
          "estimated_cost_after_index": 0.0003,
          "cost_reduction_percent": 75.0,
          "current_execution_time_ms": 480,
          "estimated_execution_time_ms": 45,
          "performance_improvement_factor": 10.7
        },
        "sql": "CREATE INDEX idx_order_items_covering ON order_items(order_id, product_id) INCLUDE (quantity);",
        "affected_queries": 342,
        "priority": "medium",
        "size_estimate_mb": 18
      }
    ],
    "summary": {
      "total_recommendations": 4,
      "potential_monthly_savings": 1052,
      "average_cost_reduction": 86,
      "total_affected_queries": 2962
    },
    "existing_indexes": [
      {
        "table": "orders",
        "name": "idx_orders_status",
        "columns": ["status"],
        "size_mb": 15,
        "usage_count": 0,
        "is_used": false,
        "recommendation": "Consider dropping - unused for 30+ days"
      }
    ]
  }
}
```

---

### 1.3.3 Query Optimization Tips

**Endpoint:** `POST /api/query/analyze-optimizations`

**Request:**
```json
{
  "queries": [
    "SELECT * FROM users",
    "SELECT COUNT(*) FROM orders WHERE user_id = 123"
  ],
  "schema": {
    "database_type": "postgresql",
    "tables": [
      {"name": "users", "row_count": 125847},
      {"name": "orders", "row_count": 543219}
    ]
  }
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "tips": [
      {
        "category": "n_plus_one",
        "severity": "critical",
        "title": "N+1 Query Detected in User Orders Endpoint",
        "description": "Controller is making N separate queries to fetch user orders in a loop",
        "before_query": "users.forEach(user => {\n  user.orders = await db.query('SELECT * FROM orders WHERE user_id = $1', [user.id]);\n});",
        "after_query": "const usersWithOrders = await db.query(`\n  SELECT u.*, JSON_AGG(o.*) as orders\n  FROM users u\n  LEFT JOIN orders o ON o.user_id = u.id\n  GROUP BY u.id\n`);",
        "impact": {
          "performance_improvement": "50x faster",
          "cost_reduction": "98% cheaper",
          "monthly_savings": 145
        },
        "how_to_fix": [
          "Use JOIN to fetch related data in single query",
          "Implement eager loading with ORM (.include())",
          "Use DataLoader for batch loading in GraphQL",
          "Cache relationship query if data rarely changes"
        ],
        "sql_example": "-- Single query with JSON aggregation\nSELECT u.*, JSON_AGG(o.*) as orders\nFROM users u\nLEFT JOIN orders o ON o.user_id = u.id\nGROUP BY u.id;",
        "affected_routes": ["/api/users", "/api/dashboard"]
      },
      {
        "category": "sql_rewrite",
        "severity": "high",
        "title": "Replace SELECT * with Specific Columns",
        "description": "Selecting all columns increases I/O and network transfer costs",
        "before_query": "SELECT * FROM users WHERE email = 'user@example.com'",
        "after_query": "SELECT id, email, name FROM users WHERE email = 'user@example.com'",
        "impact": {
          "performance_improvement": "3x faster",
          "cost_reduction": "67% cheaper",
          "monthly_savings": 42
        },
        "how_to_fix": [
          "Specify only needed columns in SELECT clause",
          "Avoid SELECT * in production queries",
          "Use covering indexes to eliminate table lookups",
          "Review ORM query projections"
        ],
        "sql_example": "-- Optimized query\nSELECT id, email, name \nFROM users \nWHERE email = 'user@example.com';",
        "affected_routes": ["/api/auth/login"]
      },
      {
        "category": "caching",
        "severity": "high",
        "title": "Cache Frequently Accessed Static Data",
        "description": "Product categories are queried 15,000+ times per day but rarely change",
        "before_query": "SELECT * FROM categories ORDER BY name",
        "after_query": "// Implement Redis cache with 1-hour TTL\nconst categories = await redis.get('categories');\nif (!categories) {\n  categories = await db.query('SELECT * FROM categories ORDER BY name');\n  await redis.set('categories', categories, 3600);\n}",
        "impact": {
          "performance_improvement": "200x faster",
          "cost_reduction": "99.5% cheaper",
          "monthly_savings": 690
        },
        "how_to_fix": [
          "Implement Redis cache with 1-hour TTL",
          "Invalidate cache on category updates (write-through)",
          "Use CDN edge caching for API responses",
          "Consider materialized views for complex aggregations"
        ],
        "sql_example": "-- Cache key: 'categories:all'\n-- TTL: 3600 seconds (1 hour)\n-- Invalidation: ON UPDATE categories trigger",
        "affected_routes": ["/api/categories", "/api/products"]
      },
      {
        "category": "query_plan",
        "severity": "medium",
        "title": "Use EXISTS Instead of COUNT for Boolean Checks",
        "description": "COUNT(*) scans all matching rows when you only need to know if ANY exist",
        "before_query": "SELECT COUNT(*) FROM orders WHERE user_id = 123",
        "after_query": "SELECT EXISTS(SELECT 1 FROM orders WHERE user_id = 123 LIMIT 1)",
        "impact": {
          "performance_improvement": "8x faster",
          "cost_reduction": "87% cheaper",
          "monthly_savings": 28
        },
        "how_to_fix": [
          "Replace COUNT(*) > 0 with EXISTS",
          "Add LIMIT 1 to stop after first match",
          "Use NOT EXISTS for negative checks",
          "Index columns used in EXISTS subqueries"
        ],
        "sql_example": "-- Optimized boolean check\nSELECT EXISTS(\n  SELECT 1 FROM orders \n  WHERE user_id = 123 \n  LIMIT 1\n);",
        "affected_routes": ["/api/users/has-orders"]
      },
      {
        "category": "query_plan",
        "severity": "medium",
        "title": "Optimize Date Range Queries with Partitioning",
        "description": "Large orders table benefits from date-based partitioning",
        "before_query": "SELECT * FROM orders WHERE created_at BETWEEN '2024-01-01' AND '2024-12-31'",
        "after_query": "-- After partitioning by month\nSELECT * FROM orders_2024_01\nUNION ALL\nSELECT * FROM orders_2024_02\n-- ... etc (query planner handles this automatically)",
        "impact": {
          "performance_improvement": "12x faster",
          "cost_reduction": "91% cheaper",
          "monthly_savings": 112
        },
        "how_to_fix": [
          "Create table partitions by month/quarter",
          "Enable partition pruning in query planner",
          "Archive old partitions to cheaper storage",
          "Use BRIN indexes on partition keys"
        ],
        "sql_example": "-- Create partitioned table\nCREATE TABLE orders (\n  id SERIAL,\n  created_at TIMESTAMP NOT NULL,\n  ...\n) PARTITION BY RANGE (created_at);\n\n-- Create monthly partitions\nCREATE TABLE orders_2024_01 PARTITION OF orders\nFOR VALUES FROM ('2024-01-01') TO ('2024-02-01');",
        "affected_routes": ["/api/reports/monthly"]
      },
      {
        "category": "schema_design",
        "severity": "low",
        "title": "Denormalize Frequently Joined Data",
        "description": "Always joining users.name with orders - consider adding user_name to orders",
        "before_query": "SELECT o.*, u.name as user_name\nFROM orders o\nJOIN users u ON u.id = o.user_id",
        "after_query": "-- Add user_name column to orders\nSELECT o.*, o.user_name\nFROM orders o",
        "impact": {
          "performance_improvement": "4x faster",
          "cost_reduction": "75% cheaper",
          "monthly_savings": 35
        },
        "how_to_fix": [
          "Add user_name column to orders table",
          "Update via database trigger on users.name change",
          "Trade-off: More storage for better read performance",
          "Use for read-heavy workloads only"
        ],
        "sql_example": "-- Add denormalized column\nALTER TABLE orders ADD COLUMN user_name VARCHAR(255);\n\n-- Create trigger to keep in sync\nCREATE TRIGGER sync_user_name\nAFTER UPDATE OF name ON users\nFOR EACH ROW\nEXECUTE FUNCTION update_orders_user_name();",
        "affected_routes": ["/api/orders"]
      }
    ],
    "summary": {
      "total_issues": 6,
      "critical_issues": 1,
      "high_issues": 2,
      "medium_issues": 2,
      "low_issues": 1,
      "potential_monthly_savings": 1052,
      "avg_performance_improvement": "40x faster"
    },
    "query_health_score": 62
  }
}
```

---

## Phase 1.4: ROI Calculator

### 1.4.1 ROI Calculation (Client-Side Only)

**Note:** The ROI Calculator in Phase 1.4 is fully client-side JavaScript. No backend API is required for basic functionality.

**Optional Future Endpoints:**

**Endpoint:** `POST /api/roi/generate-report` (for PDF generation)

**Request:**
```json
{
  "calculation": {
    "company_size": 50,
    "database_count": 5,
    "monthly_cloud_spend": 5000,
    "compliance_needs": "basic",
    "current_tools": 3,
    "annual_savings": 114012,
    "roi_percentage": 952
  },
  "user_email": "customer@example.com"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "report_url": "https://schemasage.com/reports/roi-123456.pdf",
    "expires_at": "2024-12-31T23:59:59Z"
  }
}
```

---

**Endpoint:** `POST /api/roi/send-email` (for email reports)

**Request:**
```json
{
  "email": "customer@example.com",
  "calculation": {
    "company_size": 50,
    "annual_savings": 114012,
    "roi_percentage": 952
  }
}
```

**Response:**
```json
{
  "success": true,
  "message": "ROI report sent to customer@example.com"
}
```

---

## Phase 1.5: Demo Video (No Backend APIs)

Phase 1.5 is video production only - no backend endpoints required.

---

## Common API Patterns

### Authentication Header
```typescript
headers: {
  'Authorization': 'Bearer <jwt_token>',
  'Content-Type': 'application/json'
}
```

### Error Response Format
```json
{
  "success": false,
  "error": {
    "code": "INVALID_SCHEMA",
    "message": "Invalid schema format provided",
    "details": {
      "field": "schema.tables",
      "issue": "Expected array of tables"
    }
  }
}
```

### Pagination (for large datasets)
```json
{
  "success": true,
  "data": [...],
  "pagination": {
    "page": 1,
    "per_page": 50,
    "total": 342,
    "total_pages": 7
  }
}
```

---

## Backend Implementation Priority

### Priority 1 (MVP - Week 1):
1. **Cost Comparison** (1.1.1) - Core value prop
2. **PII Detection** (1.2.1) - Compliance differentiation
3. **Query Cost Explainer** (1.3.1) - Performance optimization

### Priority 2 (Week 2):
4. **Hidden Cost Calculator** (1.1.2)
5. **Compliance Heatmap** (1.2.2)
6. **Index Recommendations** (1.3.2)

### Priority 3 (Week 3):
7. **Performance Predictor** (1.1.3)
8. **Retention Policy Manager** (1.2.3)
9. **Query Optimization Tips** (1.3.3)

### Priority 4 (Week 4):
10. **Reserved Instance Advisor** (1.1.4)
11. **Multi-Region Analysis** (1.1.5)
12. **Disaster Recovery Planner** (1.1.6)
13. **Data Quality Dashboard** (1.2.4)

---

## Testing Recommendations

### API Testing Checklist:
- [ ] All endpoints return proper HTTP status codes (200, 400, 401, 500)
- [ ] Error responses follow common format
- [ ] Authentication required for protected endpoints
- [ ] Request validation (schema, types, required fields)
- [ ] Response schema matches TypeScript interfaces
- [ ] Rate limiting implemented (100 requests/minute per user)
- [ ] CORS configured for frontend domain
- [ ] API versioning (v1, v2) for future changes
- [ ] Logging for debugging and monitoring
- [ ] Performance: <500ms response time for 95th percentile

### Example Integration Test:
```typescript
// Frontend test
test('Cost comparison returns valid providers', async () => {
  const response = await api.post('/api/cost/compare', {
    database_type: 'postgresql',
    storage_gb: 100,
    region: 'us-east-1',
    performance_requirements: {
      qps: 1000,
      connections: 100,
      iops: 3000
    }
  });
  
  expect(response.success).toBe(true);
  expect(response.data.providers).toHaveLength(3);
  expect(response.data.providers[0].provider).toBe('aws');
  expect(response.data.providers[0].monthly_cost).toBeGreaterThan(0);
});
```

---

## Summary

**Total Phase 1 API Endpoints:** 13  
**Priority 1 (MVP):** 3 endpoints  
**Priority 2:** 3 endpoints  
**Priority 3:** 3 endpoints  
**Priority 4:** 4 endpoints  

**Estimated Backend Development Time:**
- Priority 1: 3-4 days
- Priority 2: 3-4 days
- Priority 3: 3-4 days
- Priority 4: 4-5 days
- **Total:** 13-17 days for complete Phase 1 backend

All frontend components are ready and waiting for backend integration. Once APIs are deployed, replace TODO comments with actual API calls.
