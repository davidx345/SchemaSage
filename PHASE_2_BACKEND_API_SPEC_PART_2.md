# Phase 2: Backend API Specification - Part 2

**Covers:** Phase 2.2 (continued) and Phase 2.3

---

## Phase 2.2: Database Health Benchmark (Continued)

### 2.2.3 Slow Query Analyzer

**Endpoint:** `POST /api/monitoring/slow-queries`

**Request:**
```json
{
  "database_type": "postgresql",
  "connection_string": "postgresql://user:pass@host:5432/dbname",
  "threshold_ms": 1000,
  "time_range": "24h",
  "limit": 20
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "slow_queries": [
      {
        "query_id": "q_001",
        "query_text": "SELECT * FROM orders WHERE user_id = $1 AND created_at > $2",
        "avg_execution_time_ms": 2340,
        "total_executions": 847,
        "total_time_seconds": 1982,
        "max_time_ms": 4560,
        "min_time_ms": 890,
        "calls_per_hour": 35,
        "rows_returned_avg": 23,
        "cost_per_execution": 0.0023,
        "total_monthly_cost": 58.50,
        "optimization_potential": {
          "current_time_ms": 2340,
          "optimized_time_ms": 45,
          "speedup_factor": 52,
          "monthly_savings": 56.80,
          "recommendations": [
            "Add composite index on (user_id, created_at)",
            "Replace SELECT * with specific columns",
            "Use LIMIT clause if not fetching all results"
          ],
          "optimized_query": "SELECT id, user_id, total, status FROM orders WHERE user_id = $1 AND created_at > $2 ORDER BY created_at DESC LIMIT 100",
          "sql_fix": "CREATE INDEX idx_orders_user_created ON orders(user_id, created_at DESC);"
        }
      },
      {
        "query_id": "q_002",
        "query_text": "SELECT COUNT(*) FROM users",
        "avg_execution_time_ms": 1890,
        "total_executions": 1250,
        "total_time_seconds": 2362,
        "calls_per_hour": 52,
        "optimization_potential": {
          "current_time_ms": 1890,
          "optimized_time_ms": 5,
          "speedup_factor": 378,
          "monthly_savings": 45.20,
          "recommendations": [
            "Cache count result in Redis (TTL 5 minutes)",
            "Use approximate count from pg_stat_user_tables",
            "Consider materialized view for dashboard metrics"
          ],
          "optimized_query": "SELECT reltuples::bigint FROM pg_class WHERE relname = 'users'"
        }
      }
    ],
    "summary": {
      "total_slow_queries": 47,
      "total_execution_time_hours": 12.5,
      "total_monthly_cost": 342.80,
      "potential_monthly_savings": 287.40,
      "avg_optimization_speedup": 85
    }
  }
}
```

---

## Phase 2.3: Schema Debt Tracker

### 2.3.1 Technical Debt Detection

**Endpoint:** `POST /api/schema/detect-debt`

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
          {"name": "data", "type": "text"}
        ],
        "indexes": ["PRIMARY KEY (id)"]
      }
    ]
  },
  "connection_string": "postgresql://user:pass@host:5432/dbname"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "debt_items": [
      {
        "id": "debt_001",
        "category": "missing_indexes",
        "severity": "high",
        "title": "Missing Index on users.email",
        "description": "Email column used in WHERE clauses 15,000+ times/day without index",
        "affected_tables": ["users"],
        "affected_columns": ["email"],
        "impact": {
          "query_slowdown_factor": 120,
          "affected_queries_per_day": 15000,
          "monthly_cost_impact": 145.00,
          "user_experience_impact": "Login queries taking 2.3s instead of 20ms"
        },
        "detection_method": "Query log analysis",
        "first_detected": "2024-01-10T00:00:00Z",
        "age_days": 8,
        "fix_sql": "CREATE UNIQUE INDEX idx_users_email ON users(email);",
        "fix_effort_hours": 0.5,
        "fix_risk": "low",
        "fix_downtime_required": false
      },
      {
        "id": "debt_002",
        "category": "schema_antipattern",
        "severity": "critical",
        "title": "JSON/Text Blob in users.data Column",
        "description": "Storing structured data in TEXT column prevents indexing and query optimization",
        "affected_tables": ["users"],
        "affected_columns": ["data"],
        "antipattern_type": "entity_attribute_value",
        "impact": {
          "query_slowdown_factor": 50,
          "affected_queries_per_day": 8500,
          "monthly_cost_impact": 320.00,
          "maintenance_overhead": "Unable to add indexes, constraints, or validate data types"
        },
        "recommended_solution": {
          "approach": "Normalize into separate columns",
          "new_schema": [
            {"name": "phone", "type": "varchar(20)"},
            {"name": "address", "type": "text"},
            {"name": "preferences", "type": "jsonb"}
          ],
          "migration_sql": [
            "ALTER TABLE users ADD COLUMN phone VARCHAR(20);",
            "ALTER TABLE users ADD COLUMN address TEXT;",
            "ALTER TABLE users ADD COLUMN preferences JSONB;",
            "UPDATE users SET phone = data->>'phone', address = data->>'address', preferences = data::jsonb - 'phone' - 'address';",
            "ALTER TABLE users DROP COLUMN data;"
          ],
          "fix_effort_hours": 8,
          "fix_risk": "medium",
          "rollback_plan": "Keep data column until migration verified"
        }
      },
      {
        "id": "debt_003",
        "category": "missing_constraints",
        "severity": "medium",
        "title": "No Foreign Key on orders.user_id",
        "description": "Missing FK constraint allows orphaned records and data integrity issues",
        "affected_tables": ["orders"],
        "affected_columns": ["user_id"],
        "impact": {
          "orphaned_records_count": 247,
          "data_integrity_risk": "high",
          "cascading_delete_missing": true
        },
        "fix_sql": [
          "-- Clean up orphaned records first",
          "DELETE FROM orders WHERE user_id NOT IN (SELECT id FROM users);",
          "",
          "-- Add foreign key constraint",
          "ALTER TABLE orders ADD CONSTRAINT fk_orders_user_id FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;"
        ],
        "fix_effort_hours": 2,
        "fix_risk": "low"
      },
      {
        "id": "debt_004",
        "category": "over_normalization",
        "severity": "medium",
        "title": "Excessive JOINs for User Orders Display",
        "description": "Always joining users.name with orders - consider denormalization for read performance",
        "affected_tables": ["orders", "users"],
        "antipattern_type": "over_normalization",
        "impact": {
          "query_slowdown_factor": 4,
          "affected_queries_per_day": 25000,
          "monthly_cost_impact": 85.00
        },
        "recommended_solution": {
          "approach": "Add denormalized user_name column to orders",
          "trade_off": "5% more storage for 75% faster queries",
          "migration_sql": [
            "ALTER TABLE orders ADD COLUMN user_name VARCHAR(255);",
            "UPDATE orders o SET user_name = u.name FROM users u WHERE u.id = o.user_id;",
            "CREATE TRIGGER sync_user_name AFTER UPDATE OF name ON users FOR EACH ROW EXECUTE FUNCTION update_orders_user_name();"
          ],
          "fix_effort_hours": 4
        }
      },
      {
        "id": "debt_005",
        "category": "unused_indexes",
        "severity": "low",
        "title": "15 Unused Indexes Wasting Storage",
        "description": "Indexes created but never used in queries - waste 8.2 GB storage",
        "affected_tables": ["users", "orders", "products"],
        "impact": {
          "storage_waste_gb": 8.2,
          "monthly_cost_impact": 12.30,
          "write_performance_penalty": "5-10% slower INSERTs/UPDATEs"
        },
        "unused_indexes": [
          {"table": "users", "index": "idx_users_old_column", "size_mb": 450, "last_used": null},
          {"table": "orders", "index": "idx_orders_unused", "size_mb": 890, "last_used": null}
        ],
        "fix_sql": [
          "DROP INDEX idx_users_old_column;",
          "DROP INDEX idx_orders_unused;"
        ],
        "fix_effort_hours": 1
      }
    ],
    "summary": {
      "total_debt_items": 5,
      "critical_count": 1,
      "high_count": 1,
      "medium_count": 2,
      "low_count": 1,
      "total_monthly_cost_impact": 562.30,
      "total_fix_effort_hours": 15.5,
      "debt_score": 42,
      "debt_trend": "increasing"
    },
    "debt_categories": {
      "missing_indexes": {"count": 1, "cost_impact": 145.00},
      "schema_antipattern": {"count": 1, "cost_impact": 320.00},
      "missing_constraints": {"count": 1, "cost_impact": 0},
      "over_normalization": {"count": 1, "cost_impact": 85.00},
      "unused_indexes": {"count": 1, "cost_impact": 12.30}
    }
  }
}
```

---

### 2.3.2 Debt Payoff Calculator

**Endpoint:** `POST /api/schema/calculate-payoff`

**Request:**
```json
{
  "debt_items": [
    {"id": "debt_001", "fix_effort_hours": 0.5, "monthly_savings": 145.00},
    {"id": "debt_002", "fix_effort_hours": 8, "monthly_savings": 320.00}
  ],
  "developer_hourly_rate": 150,
  "deployment_risk_tolerance": "medium"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "payoff_scenarios": [
      {
        "debt_id": "debt_001",
        "title": "Fix Missing Index on users.email",
        "fix_cost": {
          "effort_hours": 0.5,
          "labor_cost": 75.00,
          "deployment_cost": 0,
          "total_cost": 75.00
        },
        "monthly_savings": 145.00,
        "annual_savings": 1740.00,
        "roi_timeline": {
          "break_even_days": 16,
          "12_month_roi_percent": 2220,
          "24_month_roi_percent": 4540
        },
        "priority_score": 98,
        "recommendation": "IMMEDIATE FIX - breaks even in 16 days"
      },
      {
        "debt_id": "debt_002",
        "title": "Normalize users.data JSON Column",
        "fix_cost": {
          "effort_hours": 8,
          "labor_cost": 1200.00,
          "deployment_cost": 100.00,
          "testing_cost": 200.00,
          "total_cost": 1500.00
        },
        "monthly_savings": 320.00,
        "annual_savings": 3840.00,
        "roi_timeline": {
          "break_even_days": 141,
          "12_month_roi_percent": 156,
          "24_month_roi_percent": 412
        },
        "priority_score": 85,
        "recommendation": "HIGH PRIORITY - significant long-term savings"
      }
    ],
    "optimal_payoff_plan": {
      "total_items": 2,
      "total_fix_cost": 1575.00,
      "total_monthly_savings": 465.00,
      "total_annual_savings": 5580.00,
      "blended_roi_12_months": 254,
      "execution_order": [
        {"debt_id": "debt_001", "month": 1, "reason": "Quickest ROI"},
        {"debt_id": "debt_002", "month": 1, "reason": "High impact, acceptable risk"}
      ],
      "timeline": {
        "month_1": {"fixes": 2, "cost": 1575.00, "savings": 465.00},
        "month_2": {"fixes": 0, "cost": 0, "savings": 465.00},
        "month_3": {"fixes": 0, "cost": 0, "savings": 465.00},
        "month_12": {"cumulative_savings": 5115.00, "net_profit": 3540.00}
      }
    }
  }
}
```

---

### 2.3.3 Debt Prioritization Matrix

**Endpoint:** `POST /api/schema/prioritize-debt`

**Request:**
```json
{
  "debt_items": [
    {"id": "debt_001", "severity": "high", "fix_effort_hours": 0.5, "monthly_cost_impact": 145.00},
    {"id": "debt_002", "severity": "critical", "fix_effort_hours": 8, "monthly_cost_impact": 320.00},
    {"id": "debt_003", "severity": "medium", "fix_effort_hours": 2, "monthly_cost_impact": 0},
    {"id": "debt_004", "severity": "medium", "fix_effort_hours": 4, "monthly_cost_impact": 85.00},
    {"id": "debt_005", "severity": "low", "fix_effort_hours": 1, "monthly_cost_impact": 12.30}
  ],
  "prioritization_strategy": "roi_focused"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "matrix": {
      "quick_wins": [
        {
          "debt_id": "debt_001",
          "title": "Missing Index on users.email",
          "effort": "low",
          "impact": "high",
          "priority_score": 98,
          "quadrant": "quick_win",
          "recommendation": "DO FIRST - Low effort, high impact"
        },
        {
          "debt_id": "debt_005",
          "title": "Drop Unused Indexes",
          "effort": "low",
          "impact": "medium",
          "priority_score": 75,
          "quadrant": "quick_win",
          "recommendation": "Easy fix with immediate benefits"
        }
      ],
      "major_projects": [
        {
          "debt_id": "debt_002",
          "title": "Normalize users.data Column",
          "effort": "high",
          "impact": "high",
          "priority_score": 85,
          "quadrant": "major_project",
          "recommendation": "PLAN CAREFULLY - High impact justifies effort"
        }
      ],
      "fill_ins": [
        {
          "debt_id": "debt_004",
          "title": "Denormalize user_name in orders",
          "effort": "medium",
          "impact": "medium",
          "priority_score": 60,
          "quadrant": "fill_in",
          "recommendation": "Schedule during sprint with capacity"
        },
        {
          "debt_id": "debt_003",
          "title": "Add Foreign Key Constraint",
          "effort": "low",
          "impact": "medium",
          "priority_score": 55,
          "quadrant": "fill_in",
          "recommendation": "Good for data integrity, moderate impact"
        }
      ],
      "reconsider": []
    },
    "recommended_execution_plan": {
      "sprint_1": {
        "week": 1,
        "items": [
          {"debt_id": "debt_001", "effort_hours": 0.5, "expected_savings": 145.00},
          {"debt_id": "debt_005", "effort_hours": 1, "expected_savings": 12.30}
        ],
        "total_effort_hours": 1.5,
        "total_monthly_savings": 157.30
      },
      "sprint_2": {
        "week": 2,
        "items": [
          {"debt_id": "debt_003", "effort_hours": 2, "expected_savings": 0}
        ],
        "total_effort_hours": 2,
        "focus": "Data integrity improvements"
      },
      "sprint_3": {
        "week": 3,
        "items": [
          {"debt_id": "debt_002", "effort_hours": 8, "expected_savings": 320.00}
        ],
        "total_effort_hours": 8,
        "total_monthly_savings": 320.00,
        "note": "Requires careful planning and testing"
      },
      "sprint_4": {
        "week": 4,
        "items": [
          {"debt_id": "debt_004", "effort_hours": 4, "expected_savings": 85.00}
        ],
        "total_effort_hours": 4,
        "total_monthly_savings": 85.00
      }
    },
    "summary": {
      "total_debt_items": 5,
      "quick_wins": 2,
      "major_projects": 1,
      "fill_ins": 2,
      "reconsider": 0,
      "total_fix_effort_hours": 15.5,
      "total_monthly_savings": 562.30,
      "execution_timeline_weeks": 4
    }
  }
}
```

---

### 2.3.4 Debt Trends Over Time

**Endpoint:** `POST /api/schema/debt-trends`

**Request:**
```json
{
  "database_type": "postgresql",
  "connection_string": "postgresql://user:pass@host:5432/dbname",
  "time_range": "90d"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "time_series": [
      {
        "date": "2023-10-18",
        "debt_score": 72,
        "debt_items_count": 3,
        "total_cost_impact": 245.00
      },
      {
        "date": "2023-11-18",
        "debt_score": 58,
        "debt_items_count": 4,
        "total_cost_impact": 387.00
      },
      {
        "date": "2024-01-18",
        "debt_score": 42,
        "debt_items_count": 5,
        "total_cost_impact": 562.30
      }
    ],
    "trend_analysis": {
      "direction": "worsening",
      "debt_score_change_90d": -30,
      "cost_impact_change_90d": 317.30,
      "avg_new_items_per_month": 0.67,
      "avg_resolved_items_per_month": 0.33,
      "velocity": "negative"
    },
    "category_trends": {
      "missing_indexes": {
        "trend": "stable",
        "count_change_90d": 0
      },
      "schema_antipattern": {
        "trend": "increasing",
        "count_change_90d": 1
      },
      "unused_indexes": {
        "trend": "increasing",
        "count_change_90d": 1
      }
    },
    "forecast_90_days": {
      "predicted_debt_score": 28,
      "predicted_cost_impact": 780.00,
      "confidence": 0.78,
      "recommendation": "URGENT: Debt accumulating faster than resolution - allocate 20% sprint capacity to debt reduction"
    }
  }
}
```

---

## Common Error Responses

```json
{
  "success": false,
  "error": {
    "code": "DATABASE_CONNECTION_FAILED",
    "message": "Unable to connect to database",
    "details": {
      "host": "localhost:5432",
      "database": "production_db"
    }
  }
}
```

---

## Testing Recommendations

### API Testing Checklist:
- [ ] All endpoints validate connection strings
- [ ] Query analysis handles large result sets (pagination)
- [ ] Slow query detection respects configurable thresholds
- [ ] Debt detection works across PostgreSQL, MySQL, SQL Server
- [ ] ROI calculations accurate for different hourly rates
- [ ] Trend analysis requires minimum 7 days of data
- [ ] Error handling for invalid SQL queries
- [ ] Rate limiting: 50 requests/minute per user

---

## Summary - Part 2

**Endpoints Covered:**
- Phase 2.2.3: Slow Query Analyzer (1 endpoint)
- Phase 2.3: Schema Debt Tracker (4 endpoints)

**Total Part 2 Endpoints:** 5

**Next:** Part 3 covers Phase 2.4 Cost Anomaly Detector (3 endpoints)
