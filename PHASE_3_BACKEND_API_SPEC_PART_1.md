# Phase 3: Backend API Specification - Part 1

**Covers:** Phase 3.1 Migration Center & Phase 3.2 AI Schema Assistant

---

## Phase 3.1: Universal Migration Center

### 3.1.1 Migration Planning

**Endpoint:** `POST /api/migration/plan`

**Description:** Generate comprehensive migration plan for cross-database migrations

**Request:**
```json
{
  "source_url": "postgresql://user:pass@host:5432/sourcedb",
  "target_url": "mongodb://user:pass@host:27017/targetdb",
  "migration_type": "schema_and_data",
  "options": {
    "preserve_relationships": true,
    "handle_incompatible_types": "convert",
    "batch_size": 1000,
    "parallel_workers": 4
  }
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "migration_id": "mig_7x9k2p4m",
    "source_analysis": {
      "database_type": "PostgreSQL 14.5",
      "total_tables": 23,
      "total_records": 2456789,
      "estimated_size": "45.3 GB",
      "compatibility_issues": [
        "Foreign key constraints not supported in MongoDB",
        "SERIAL data type requires conversion to UUID",
        "Stored procedures cannot be migrated automatically"
      ]
    },
    "target_analysis": {
      "database_type": "MongoDB 6.0",
      "estimated_collections": 23,
      "transformation_plan": [
        "Convert relational tables to document collections",
        "Embed one-to-many relationships where appropriate",
        "Create reference relationships for many-to-many",
        "Add compound indexes for foreign key equivalents"
      ]
    },
    "migration_plan": {
      "estimated_duration": "4-6 hours",
      "steps": [
        {
          "step": 1,
          "description": "Create target database structure",
          "estimated_time": "15 minutes",
          "transformations": [
            "Convert users table to users collection",
            "Embed user_profiles into users (1:1 relationship)",
            "Create indexes on email, created_at"
          ]
        },
        {
          "step": 2,
          "description": "Migrate reference data",
          "estimated_time": "30 minutes",
          "transformations": [
            "Migrate categories (500 records)",
            "Migrate products (15,000 records)",
            "Transform product_images to embedded array"
          ]
        },
        {
          "step": 3,
          "description": "Migrate transactional data",
          "estimated_time": "3-4 hours",
          "transformations": [
            "Migrate orders (500,000 records)",
            "Embed order_items into orders (1.5M items)",
            "Transform payment data to embedded documents"
          ]
        },
        {
          "step": 4,
          "description": "Create indexes and verify data integrity",
          "estimated_time": "45 minutes",
          "transformations": [
            "Create compound indexes",
            "Verify record counts match source",
            "Validate embedded relationships"
          ]
        }
      ],
      "warnings": [
        "ACID transactions limited to single documents in MongoDB",
        "JOIN operations require application-level aggregation",
        "Schema validation recommended for production use"
      ],
      "rollback_available": true
    },
    "cross_database_migration": true,
    "migration_type": "PostgreSQL → MongoDB"
  }
}
```

---

### 3.1.2 Migration Execution

**Endpoint:** `POST /api/migration/execute`

**Description:** Execute migration plan with real-time progress tracking

**Request:**
```json
{
  "migration_id": "mig_7x9k2p4m",
  "execution_options": {
    "dry_run": false,
    "stop_on_error": false,
    "verify_after_migration": true,
    "create_rollback_point": true
  }
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "execution_id": "exec_3m8n5k2p",
    "status": "running",
    "progress": {
      "percentage": 0,
      "current_step": "Creating target database structure",
      "records_processed": 0,
      "total_records": 2456789,
      "estimated_remaining": "4 hours 15 minutes"
    },
    "performance_metrics": {
      "records_per_second": 0,
      "error_count": 0,
      "warning_count": 0
    },
    "logs": [
      "[2024-11-20 14:32:00] Migration started",
      "[2024-11-20 14:32:01] Connecting to source database...",
      "[2024-11-20 14:32:02] Connection established",
      "[2024-11-20 14:32:03] Analyzing schema structure..."
    ]
  }
}
```

**WebSocket Updates:** `wss://api.schemasage.com/ws/migration/{execution_id}`

**Real-time Update Format:**
```json
{
  "execution_id": "exec_3m8n5k2p",
  "status": "running",
  "progress": {
    "percentage": 45.3,
    "current_step": "Migrating transactional data",
    "records_processed": 1113456,
    "total_records": 2456789,
    "estimated_remaining": "2 hours 18 minutes"
  },
  "performance_metrics": {
    "records_per_second": 856,
    "error_count": 3,
    "warning_count": 12
  },
  "logs": [
    "[2024-11-20 16:15:23] Processing orders table: 450,000/500,000",
    "[2024-11-20 16:15:28] Embedded 1,350,000 order_items",
    "[2024-11-20 16:15:30] Warning: Skipped 3 invalid records (logged)"
  ]
}
```

---

### 3.1.3 Multi-Cloud Comparison

**Endpoint:** `POST /api/migration/multi-cloud-compare`

**Description:** Compare database offerings across AWS, Azure, and GCP

**Request:**
```json
{
  "database_engine": "postgresql",
  "database_version": "14",
  "vcpu_count": 4,
  "memory_gb": 16,
  "storage_gb": 100,
  "multi_az": false,
  "region_preference": "us-east"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "recommendations": [
      {
        "cloud_provider": "aws",
        "instance_type": "db.m6g.xlarge",
        "vcpu": 4,
        "memory_gb": 16,
        "storage_type": "gp3",
        "iops": 3000,
        "monthly_compute_cost": 234.56,
        "monthly_storage_cost": 11.50,
        "monthly_total_cost": 246.06,
        "annual_cost": 2952.72,
        "features": [
          "Automated backups (7 days retention)",
          "Multi-AZ available (+$234/mo)",
          "Read replicas supported",
          "Enhanced monitoring included",
          "Encryption at rest"
        ],
        "suitability_score": 92
      },
      {
        "cloud_provider": "azure",
        "instance_type": "General Purpose D4s v3",
        "vcpu": 4,
        "memory_gb": 16,
        "storage_type": "Premium SSD",
        "iops": 5000,
        "monthly_compute_cost": 276.48,
        "monthly_storage_cost": 19.20,
        "monthly_total_cost": 295.68,
        "annual_cost": 3548.16,
        "features": [
          "Automated backups (35 days retention)",
          "Zone-redundant available (+$276/mo)",
          "Read replicas supported",
          "Advanced threat protection",
          "Encryption at rest and in transit"
        ],
        "suitability_score": 85
      },
      {
        "cloud_provider": "gcp",
        "instance_type": "db-n1-standard-4",
        "vcpu": 4,
        "memory_gb": 15,
        "storage_type": "SSD",
        "iops": 3000,
        "monthly_compute_cost": 258.72,
        "monthly_storage_cost": 17.00,
        "monthly_total_cost": 275.72,
        "annual_cost": 3308.64,
        "features": [
          "Automated backups (7 days retention)",
          "High availability available (+$258/mo)",
          "Read replicas supported",
          "Cloud SQL Insights included",
          "Encryption by default"
        ],
        "suitability_score": 88
      }
    ],
    "best_value": {
      "provider": "aws",
      "annual_savings_vs_azure": 595.44,
      "annual_savings_vs_gcp": 355.92
    }
  }
}
```

---

### 3.1.4 Pre-Migration Analysis

**Endpoint:** `POST /api/migration/pre-analysis`

**Description:** Analyze migration risks, breaking changes, and performance impact

**Request:**
```json
{
  "source_database": "postgresql",
  "source_version": "12",
  "target_database": "postgresql",
  "target_version": "15",
  "connection_string": "postgresql://user:pass@host:5432/db"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "overall_risk": "medium",
    "confidence_score": 87,
    "breaking_changes": [
      {
        "severity": "critical",
        "type": "Deprecated Function",
        "description": "to_timestamp() behavior changed in PostgreSQL 15",
        "affected_objects": [
          "analytics.daily_reports",
          "billing.invoice_generator"
        ],
        "impact": "Queries may return different results or fail",
        "recommended_action": "Update to use to_timestamp with explicit format parameter",
        "auto_fixable": true,
        "fix_script": "UPDATE ... SET created_at = to_timestamp(timestamp_str, 'YYYY-MM-DD HH24:MI:SS')"
      },
      {
        "severity": "high",
        "type": "Index Type Change",
        "description": "GiST indexes now use different distance operator",
        "affected_objects": ["locations.geo_index"],
        "impact": "Spatial queries 15% slower until reindex",
        "recommended_action": "Rebuild GiST indexes after upgrade",
        "auto_fixable": true,
        "fix_script": "REINDEX INDEX CONCURRENTLY locations.geo_index;"
      },
      {
        "severity": "medium",
        "type": "Permissions Change",
        "description": "Default PUBLIC schema permissions restricted",
        "affected_objects": ["public schema"],
        "impact": "Application users may lose CREATE privilege",
        "recommended_action": "Explicitly grant CREATE on public schema to app roles",
        "auto_fixable": true,
        "fix_script": "GRANT CREATE ON SCHEMA public TO app_user;"
      }
    ],
    "performance_impact": [
      {
        "metric": "Query Performance",
        "current_value": "145ms avg",
        "projected_value": "98ms avg",
        "change_percent": 32.4,
        "status": "improvement"
      },
      {
        "metric": "Index Scan Speed",
        "current_value": "2340 rows/sec",
        "projected_value": "3120 rows/sec",
        "change_percent": 33.3,
        "status": "improvement"
      },
      {
        "metric": "Vacuum Performance",
        "current_value": "12 min",
        "projected_value": "7 min",
        "change_percent": 41.7,
        "status": "improvement"
      }
    ],
    "dependencies": [
      {
        "name": "pg_stat_statements",
        "type": "Extension",
        "current_version": "1.7",
        "required_version": "1.10",
        "compatible": true,
        "upgrade_path": "Automatic during migration"
      },
      {
        "name": "PostGIS",
        "type": "Extension",
        "current_version": "2.5",
        "required_version": "3.3",
        "compatible": true,
        "upgrade_path": "Run: ALTER EXTENSION postgis UPDATE;"
      }
    ],
    "estimated_effort_hours": 8,
    "rollback_difficulty": "easy",
    "recommended_approach": "Blue-green deployment with 1-hour validation period"
  }
}
```

---

### 3.1.5 Smart Rollback

**Endpoint:** `POST /api/migration/rollback`

**Description:** Intelligent rollback with automatic data preservation

**Request:**
```json
{
  "migration_id": "mig_7x9k2p4m",
  "execution_id": "exec_3m8n5k2p",
  "rollback_strategy": "intelligent_reconstruction",
  "preserve_new_data": true
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "rollback_id": "rollback_5k8m3n2p",
    "status": "ready",
    "rollback_plan": {
      "estimated_duration": "12 minutes",
      "risk_assessment": {
        "overall_risk": "low",
        "data_loss_risk": false,
        "complexity_score": 2.3,
        "success_probability": 98.5
      },
      "preservation_plan": {
        "backup_size": "45 GB",
        "recovery_point": "2024-11-20 14:30:00",
        "critical_tables": ["users", "orders", "payments"],
        "validation_checks": 12
      },
      "execution_steps": [
        {
          "step": 1,
          "description": "Validate rollback prerequisites",
          "estimated_time": "30 seconds",
          "action": "Check backup integrity, verify disk space"
        },
        {
          "step": 2,
          "description": "Stop application writes",
          "estimated_time": "1 minute",
          "action": "Set database to read-only mode"
        },
        {
          "step": 3,
          "description": "Restore database from checkpoint",
          "estimated_time": "8 minutes",
          "action": "Restore from backup created at migration start"
        },
        {
          "step": 4,
          "description": "Replay new data (if preserve_new_data=true)",
          "estimated_time": "2 minutes",
          "action": "Apply transactions created during migration"
        },
        {
          "step": 5,
          "description": "Validate data integrity",
          "estimated_time": "30 seconds",
          "action": "Run 12 validation checks, compare record counts"
        }
      ]
    },
    "checkpoints": [
      {
        "name": "Pre-migration snapshot",
        "created_at": "2024-11-20 14:30:00",
        "status": "available",
        "data_snapshot_size": "45 GB",
        "recovery_time_estimate": "8 minutes",
        "validation_score": 100
      }
    ]
  }
}
```

**Execute Rollback:** `POST /api/migration/rollback/{rollback_id}/execute`

**Response:**
```json
{
  "success": true,
  "data": {
    "execution_id": "rollback_exec_7m2k9p",
    "status": "running",
    "progress": {
      "percentage": 0,
      "current_step": "Validating rollback prerequisites",
      "steps_completed": 0,
      "total_steps": 5,
      "estimated_remaining": "12 minutes"
    },
    "performance_metrics": {
      "data_restored_gb": 0,
      "restoration_speed_mbps": 0,
      "validation_checks_passed": 0,
      "issues_detected": 0
    },
    "logs": [
      "[2024-11-20 18:45:00] Rollback initiated",
      "[2024-11-20 18:45:01] Validating backup integrity...",
      "[2024-11-20 18:45:02] Backup validation: PASSED"
    ]
  }
}
```

---

## Phase 3.2: AI Schema Assistant

### 3.2.1 Natural Language Schema Generation

**Endpoint:** `POST /api/ai/generate-schema`

**Description:** Generate database schema from natural language description

**Request:**
```json
{
  "prompt": "I need a database for an e-commerce platform with users, products, orders, and reviews. Users can have multiple addresses. Products belong to categories. Orders contain multiple items.",
  "database_type": "postgresql",
  "options": {
    "include_indexes": true,
    "include_relationships": true,
    "normalization_level": "3NF",
    "use_uuids": true
  }
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "schema_id": "schema_8k3m5p2n",
    "name": "E-commerce Platform",
    "description": "Complete e-commerce system with users, products, orders, and reviews",
    "database_type": "PostgreSQL 15",
    "confidence_score": 92,
    "tables": [
      {
        "name": "users",
        "description": "Customer accounts and authentication",
        "columns": [
          {
            "name": "id",
            "type": "UUID",
            "nullable": false,
            "primary_key": true,
            "description": "Unique user identifier"
          },
          {
            "name": "email",
            "type": "VARCHAR(255)",
            "nullable": false,
            "primary_key": false,
            "description": "User email address (unique)"
          },
          {
            "name": "password_hash",
            "type": "VARCHAR(255)",
            "nullable": false,
            "primary_key": false,
            "description": "Bcrypt hashed password"
          },
          {
            "name": "full_name",
            "type": "VARCHAR(255)",
            "nullable": false,
            "primary_key": false,
            "description": "User's full name"
          },
          {
            "name": "created_at",
            "type": "TIMESTAMP",
            "nullable": false,
            "primary_key": false,
            "description": "Account creation timestamp"
          }
        ],
        "indexes": [
          {
            "name": "idx_users_email",
            "columns": ["email"],
            "unique": true
          },
          {
            "name": "idx_users_created_at",
            "columns": ["created_at"],
            "unique": false
          }
        ]
      },
      {
        "name": "addresses",
        "description": "User shipping and billing addresses",
        "columns": [
          {
            "name": "id",
            "type": "UUID",
            "nullable": false,
            "primary_key": true,
            "description": "Unique address identifier"
          },
          {
            "name": "user_id",
            "type": "UUID",
            "nullable": false,
            "primary_key": false,
            "foreign_key": {
              "table": "users",
              "column": "id"
            },
            "description": "User who owns this address"
          },
          {
            "name": "address_type",
            "type": "VARCHAR(50)",
            "nullable": false,
            "primary_key": false,
            "description": "shipping or billing"
          },
          {
            "name": "street_address",
            "type": "VARCHAR(255)",
            "nullable": false,
            "primary_key": false,
            "description": "Street address"
          },
          {
            "name": "city",
            "type": "VARCHAR(100)",
            "nullable": false,
            "primary_key": false,
            "description": "City name"
          },
          {
            "name": "postal_code",
            "type": "VARCHAR(20)",
            "nullable": false,
            "primary_key": false,
            "description": "ZIP/Postal code"
          }
        ],
        "indexes": [
          {
            "name": "idx_addresses_user_id",
            "columns": ["user_id"],
            "unique": false
          }
        ]
      },
      {
        "name": "categories",
        "description": "Product categories",
        "columns": [
          {
            "name": "id",
            "type": "UUID",
            "nullable": false,
            "primary_key": true,
            "description": "Unique category identifier"
          },
          {
            "name": "name",
            "type": "VARCHAR(100)",
            "nullable": false,
            "primary_key": false,
            "description": "Category name"
          },
          {
            "name": "parent_id",
            "type": "UUID",
            "nullable": true,
            "primary_key": false,
            "foreign_key": {
              "table": "categories",
              "column": "id"
            },
            "description": "Parent category for hierarchy"
          }
        ],
        "indexes": [
          {
            "name": "idx_categories_parent_id",
            "columns": ["parent_id"],
            "unique": false
          }
        ]
      },
      {
        "name": "products",
        "description": "Product catalog",
        "columns": [
          {
            "name": "id",
            "type": "UUID",
            "nullable": false,
            "primary_key": true,
            "description": "Unique product identifier"
          },
          {
            "name": "name",
            "type": "VARCHAR(255)",
            "nullable": false,
            "primary_key": false,
            "description": "Product name"
          },
          {
            "name": "description",
            "type": "TEXT",
            "nullable": true,
            "primary_key": false,
            "description": "Product description"
          },
          {
            "name": "price",
            "type": "DECIMAL(10,2)",
            "nullable": false,
            "primary_key": false,
            "description": "Product price in USD"
          },
          {
            "name": "category_id",
            "type": "UUID",
            "nullable": false,
            "primary_key": false,
            "foreign_key": {
              "table": "categories",
              "column": "id"
            },
            "description": "Product category"
          }
        ],
        "indexes": [
          {
            "name": "idx_products_category_id",
            "columns": ["category_id"],
            "unique": false
          },
          {
            "name": "idx_products_price",
            "columns": ["price"],
            "unique": false
          }
        ]
      },
      {
        "name": "orders",
        "description": "Customer orders",
        "columns": [
          {
            "name": "id",
            "type": "UUID",
            "nullable": false,
            "primary_key": true,
            "description": "Unique order identifier"
          },
          {
            "name": "user_id",
            "type": "UUID",
            "nullable": false,
            "primary_key": false,
            "foreign_key": {
              "table": "users",
              "column": "id"
            },
            "description": "Customer who placed order"
          },
          {
            "name": "status",
            "type": "VARCHAR(50)",
            "nullable": false,
            "primary_key": false,
            "description": "pending, paid, shipped, delivered"
          },
          {
            "name": "total_amount",
            "type": "DECIMAL(10,2)",
            "nullable": false,
            "primary_key": false,
            "description": "Total order amount"
          },
          {
            "name": "created_at",
            "type": "TIMESTAMP",
            "nullable": false,
            "primary_key": false,
            "description": "Order creation timestamp"
          }
        ],
        "indexes": [
          {
            "name": "idx_orders_user_id",
            "columns": ["user_id"],
            "unique": false
          },
          {
            "name": "idx_orders_status",
            "columns": ["status"],
            "unique": false
          }
        ]
      },
      {
        "name": "order_items",
        "description": "Products in each order",
        "columns": [
          {
            "name": "id",
            "type": "UUID",
            "nullable": false,
            "primary_key": true,
            "description": "Unique order item identifier"
          },
          {
            "name": "order_id",
            "type": "UUID",
            "nullable": false,
            "primary_key": false,
            "foreign_key": {
              "table": "orders",
              "column": "id"
            },
            "description": "Order reference"
          },
          {
            "name": "product_id",
            "type": "UUID",
            "nullable": false,
            "primary_key": false,
            "foreign_key": {
              "table": "products",
              "column": "id"
            },
            "description": "Product reference"
          },
          {
            "name": "quantity",
            "type": "INTEGER",
            "nullable": false,
            "primary_key": false,
            "description": "Quantity ordered"
          },
          {
            "name": "unit_price",
            "type": "DECIMAL(10,2)",
            "nullable": false,
            "primary_key": false,
            "description": "Price per unit at time of order"
          }
        ],
        "indexes": [
          {
            "name": "idx_order_items_order_id",
            "columns": ["order_id"],
            "unique": false
          },
          {
            "name": "idx_order_items_product_id",
            "columns": ["product_id"],
            "unique": false
          }
        ]
      },
      {
        "name": "reviews",
        "description": "Product reviews from customers",
        "columns": [
          {
            "name": "id",
            "type": "UUID",
            "nullable": false,
            "primary_key": true,
            "description": "Unique review identifier"
          },
          {
            "name": "product_id",
            "type": "UUID",
            "nullable": false,
            "primary_key": false,
            "foreign_key": {
              "table": "products",
              "column": "id"
            },
            "description": "Product being reviewed"
          },
          {
            "name": "user_id",
            "type": "UUID",
            "nullable": false,
            "primary_key": false,
            "foreign_key": {
              "table": "users",
              "column": "id"
            },
            "description": "User who wrote review"
          },
          {
            "name": "rating",
            "type": "INTEGER",
            "nullable": false,
            "primary_key": false,
            "description": "Rating from 1-5"
          },
          {
            "name": "comment",
            "type": "TEXT",
            "nullable": true,
            "primary_key": false,
            "description": "Review text"
          },
          {
            "name": "created_at",
            "type": "TIMESTAMP",
            "nullable": false,
            "primary_key": false,
            "description": "Review creation timestamp"
          }
        ],
        "indexes": [
          {
            "name": "idx_reviews_product_id",
            "columns": ["product_id"],
            "unique": false
          },
          {
            "name": "idx_reviews_user_id",
            "columns": ["user_id"],
            "unique": false
          }
        ]
      }
    ],
    "relationships": [
      {
        "from_table": "addresses",
        "from_column": "user_id",
        "to_table": "users",
        "to_column": "id",
        "type": "one_to_many"
      },
      {
        "from_table": "products",
        "from_column": "category_id",
        "to_table": "categories",
        "to_column": "id",
        "type": "one_to_many"
      },
      {
        "from_table": "categories",
        "from_column": "parent_id",
        "to_table": "categories",
        "to_column": "id",
        "type": "one_to_many"
      },
      {
        "from_table": "orders",
        "from_column": "user_id",
        "to_table": "users",
        "to_column": "id",
        "type": "one_to_many"
      },
      {
        "from_table": "order_items",
        "from_column": "order_id",
        "to_table": "orders",
        "to_column": "id",
        "type": "one_to_many"
      },
      {
        "from_table": "order_items",
        "from_column": "product_id",
        "to_table": "products",
        "to_column": "id",
        "type": "one_to_many"
      },
      {
        "from_table": "reviews",
        "from_column": "product_id",
        "to_table": "products",
        "to_column": "id",
        "type": "one_to_many"
      },
      {
        "from_table": "reviews",
        "from_column": "user_id",
        "to_table": "users",
        "to_column": "id",
        "type": "one_to_many"
      }
    ],
    "suggestions": [
      "Consider adding a 'wishlists' table for users to save products",
      "Add a 'payment_methods' table to store customer payment info",
      "Create a 'shipping_carriers' table for tracking shipments",
      "Add full-text search indexes on products.name and products.description",
      "Consider partitioning 'orders' table by created_at for better performance"
    ],
    "sql_export": "-- PostgreSQL 15 Schema\n\nCREATE TABLE users (\n  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),\n  email VARCHAR(255) NOT NULL,\n  password_hash VARCHAR(255) NOT NULL,\n  full_name VARCHAR(255) NOT NULL,\n  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP\n);\n\nCREATE UNIQUE INDEX idx_users_email ON users(email);\nCREATE INDEX idx_users_created_at ON users(created_at);\n\n-- ... (remaining tables)"
  }
}
```

---

### 3.2.2 AI Model Selection

**Endpoint:** `GET /api/ai/models`

**Description:** Get available AI models with performance metrics

**Response:**
```json
{
  "success": true,
  "data": {
    "models": [
      {
        "model": "GPT-4o",
        "cost_per_request": 0.03,
        "avg_time_seconds": 2.1,
        "accuracy_score": 0.94,
        "recommended": true,
        "best_for": ["schema-generation", "optimization", "complex-queries"]
      },
      {
        "model": "Claude 3.5 Sonnet",
        "cost_per_request": 0.025,
        "avg_time_seconds": 1.8,
        "accuracy_score": 0.92,
        "recommended": false,
        "best_for": ["code-review", "documentation", "explanation"]
      },
      {
        "model": "Code Llama 70B",
        "cost_per_request": 0.01,
        "avg_time_seconds": 3.2,
        "accuracy_score": 0.88,
        "recommended": false,
        "best_for": ["migration", "transformation", "bulk-operations"]
      },
      {
        "model": "GPT-3.5 Turbo",
        "cost_per_request": 0.002,
        "avg_time_seconds": 1.2,
        "accuracy_score": 0.82,
        "recommended": false,
        "best_for": ["simple-queries", "quick-suggestions", "batch-processing"]
      }
    ],
    "task_recommendations": {
      "schema-generation": "GPT-4o",
      "code-review": "Claude 3.5 Sonnet",
      "optimization": "GPT-4o",
      "migration": "Code Llama 70B",
      "documentation": "Claude 3.5 Sonnet"
    }
  }
}
```

---

### 3.2.3 Best Practices Validation

**Endpoint:** `POST /api/ai/validate-schema`

**Description:** Validate schema against industry best practices

**Request:**
```json
{
  "schema": {
    "database_type": "postgresql",
    "tables": [
      {
        "name": "users",
        "columns": [
          {"name": "id", "type": "SERIAL", "primary_key": true},
          {"name": "email", "type": "VARCHAR(255)"},
          {"name": "password", "type": "VARCHAR(255)"}
        ]
      },
      {
        "name": "products",
        "columns": [
          {"name": "id", "type": "SERIAL", "primary_key": true},
          {"name": "price", "type": "FLOAT"}
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
    "overall_score": 65,
    "total_issues": 8,
    "critical_issues": 2,
    "recommendations": 6,
    "best_practices": [
      {
        "category": "Primary Keys",
        "title": "Consider UUIDs for distributed systems",
        "severity": "recommended",
        "current_implementation": "Using auto-incrementing SERIAL for primary keys",
        "recommended_implementation": "Use UUID (v7) for primary keys in distributed environment",
        "reasoning": "UUIDs prevent ID conflicts across multiple database instances and enable offline-first architectures. UUID v7 maintains time-ordering for better index performance.",
        "performance_impact": "Slightly larger index size (+16 bytes vs 4 bytes per row), but negligible with modern hardware. UUID v7 maintains B-tree locality.",
        "code_example": "-- Before\nCREATE TABLE users (\n  id SERIAL PRIMARY KEY,\n  ...\n);\n\n-- After\nCREATE TABLE users (\n  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),\n  ...\n);",
        "applies_to_tables": ["users", "products"]
      },
      {
        "category": "Security",
        "title": "Never store plaintext passwords",
        "severity": "critical",
        "current_implementation": "Column named 'password' suggests plaintext storage",
        "recommended_implementation": "Use 'password_hash' with bcrypt/argon2",
        "reasoning": "Storing plaintext passwords violates OWASP Top 10, GDPR, PCI-DSS. Use one-way hashing with salt.",
        "performance_impact": "Hashing adds ~100ms per login, negligible for security benefit.",
        "code_example": "-- Before\nCREATE TABLE users (\n  password VARCHAR(255)\n);\n\n-- After\nCREATE TABLE users (\n  password_hash VARCHAR(255) NOT NULL\n);",
        "applies_to_tables": ["users"]
      },
      {
        "category": "Data Types",
        "title": "Use DECIMAL instead of FLOAT for monetary values",
        "severity": "critical",
        "current_implementation": "products.price uses FLOAT",
        "recommended_implementation": "Change to DECIMAL(10,2) for exact precision",
        "reasoning": "FLOAT has rounding errors (0.1 + 0.2 ≠ 0.3). DECIMAL stores exact values, critical for financial calculations.",
        "performance_impact": "Slightly slower arithmetic (~10%), but ensures accuracy. Essential for compliance (SOX, PCI-DSS).",
        "code_example": "-- Before\nCREATE TABLE products (\n  price FLOAT\n);\n\n-- After\nCREATE TABLE products (\n  price DECIMAL(10,2) NOT NULL\n);",
        "applies_to_tables": ["products"]
      },
      {
        "category": "Indexing",
        "title": "Missing index on email for authentication queries",
        "severity": "recommended",
        "current_implementation": "No index on users.email",
        "recommended_implementation": "Add unique index on email column",
        "reasoning": "Login queries filter by email. Without index, performs full table scan O(n). Index reduces to O(log n).",
        "performance_impact": "95% faster login queries. Index size: ~5 MB for 100K users.",
        "code_example": "CREATE UNIQUE INDEX idx_users_email ON users(email);",
        "applies_to_tables": ["users"]
      }
    ],
    "strengths": [
      "Using VARCHAR for variable-length strings (efficient storage)",
      "Proper primary key constraints defined"
    ]
  }
}
```

---

### 3.2.4 Schema Cost Estimation

**Endpoint:** `POST /api/ai/estimate-cost`

**Description:** Estimate cloud costs for schema at different scales

**Request:**
```json
{
  "schema": {
    "database_type": "postgresql",
    "tables": [
      {"name": "users", "estimated_rows": 1000000},
      {"name": "products", "estimated_rows": 50000},
      {"name": "orders", "estimated_rows": 5000000}
    ]
  },
  "cloud_provider": "aws",
  "region": "us-east-1"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "cost_estimates": [
      {
        "scale": "1M users",
        "total_records": 6050000,
        "estimated_storage_gb": 12.5,
        "recommended_instance": "db.t3.large",
        "monthly_cost": 127.44,
        "annual_cost": 1529.28,
        "breakdown": {
          "compute": 72.96,
          "storage": 12.50,
          "backup": 18.75,
          "iops": 15.00,
          "data_transfer": 8.23
        }
      },
      {
        "scale": "10M users",
        "total_records": 60500000,
        "estimated_storage_gb": 125.0,
        "recommended_instance": "db.m5.2xlarge",
        "monthly_cost": 876.32,
        "annual_cost": 10515.84,
        "breakdown": {
          "compute": 584.64,
          "storage": 125.00,
          "backup": 93.75,
          "iops": 45.00,
          "data_transfer": 27.93
        }
      },
      {
        "scale": "100M users",
        "total_records": 605000000,
        "estimated_storage_gb": 1250.0,
        "recommended_instance": "db.r5.8xlarge",
        "monthly_cost": 5234.56,
        "annual_cost": 62814.72,
        "breakdown": {
          "compute": 3504.00,
          "storage": 1250.00,
          "backup": 312.50,
          "iops": 120.00,
          "data_transfer": 48.06
        }
      }
    ],
    "optimization_tips": [
      "Consider partitioning 'orders' table by date at 10M+ scale",
      "Use read replicas to distribute query load (add $73/mo per replica)",
      "Enable query result caching to reduce database load",
      "Archive orders older than 2 years to S3 (save ~$200/mo at 100M scale)"
    ]
  }
}
```

---

### 3.2.5 Alternative Approaches

**Endpoint:** `POST /api/ai/alternative-approaches`

**Description:** Suggest alternative database designs for the same requirements

**Request:**
```json
{
  "prompt": "I need to store real-time user activity events with millions of events per day",
  "current_approach": "PostgreSQL with events table"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "alternatives": [
      {
        "approach": "PostgreSQL with Time-Series Extension (TimescaleDB)",
        "pros": [
          "Automatic data partitioning by time",
          "Optimized for time-range queries",
          "Built-in data retention policies",
          "Compression saves 90% storage"
        ],
        "cons": [
          "Requires TimescaleDB extension",
          "Slightly more complex setup",
          "Not suitable for non-time-series data"
        ],
        "performance": "10x faster for time-range queries",
        "cost_comparison": "40% cheaper storage due to compression",
        "use_when": "Events are time-series data with frequent range queries",
        "suitability_score": 92
      },
      {
        "approach": "ClickHouse (Columnar Database)",
        "pros": [
          "100x faster analytical queries",
          "Handles billions of rows efficiently",
          "Built for high-throughput inserts",
          "Excellent compression (10:1 ratio)"
        ],
        "cons": [
          "No UPDATE/DELETE support (append-only)",
          "Different query syntax (SQL-like)",
          "Steeper learning curve"
        ],
        "performance": "100x faster analytics, 50x faster inserts",
        "cost_comparison": "60% cheaper due to compression + cheaper instances",
        "use_when": "Analytics-heavy workload, append-only events",
        "suitability_score": 88
      },
      {
        "approach": "AWS DynamoDB (NoSQL)",
        "pros": [
          "Serverless, auto-scaling",
          "Single-digit millisecond latency",
          "Pay-per-request pricing",
          "No server management"
        ],
        "cons": [
          "Limited query flexibility (no JOINs)",
          "Expensive for high-throughput",
          "Schema design requires careful planning"
        ],
        "performance": "5ms average latency for point queries",
        "cost_comparison": "30% more expensive at 10M events/day",
        "use_when": "Need serverless, predictable low latency",
        "suitability_score": 75
      },
      {
        "approach": "MongoDB (Document Database)",
        "pros": [
          "Flexible schema for evolving events",
          "Easy horizontal scaling (sharding)",
          "Native JSON support",
          "Good for hierarchical data"
        ],
        "cons": [
          "No ACID transactions across documents",
          "Requires more memory than relational",
          "Complex aggregation queries"
        ],
        "performance": "Similar to PostgreSQL for most queries",
        "cost_comparison": "Similar cost to PostgreSQL",
        "use_when": "Event schema varies significantly over time",
        "suitability_score": 70
      },
      {
        "approach": "Keep PostgreSQL with Optimizations",
        "pros": [
          "Familiar SQL interface",
          "ACID transactions",
          "Rich ecosystem of tools",
          "Good for mixed workloads"
        ],
        "cons": [
          "Slower for pure time-series analytics",
          "Manual partitioning required",
          "Higher storage costs"
        ],
        "performance": "Baseline performance",
        "cost_comparison": "Baseline cost",
        "use_when": "Need relational features, moderate scale",
        "suitability_score": 65,
        "optimizations": [
          "Add BRIN index on timestamp column",
          "Partition table by month",
          "Use JSONB for flexible event metadata",
          "Archive old events to S3"
        ]
      }
    ],
    "recommendation": "TimescaleDB",
    "reasoning": "Best balance of PostgreSQL compatibility, time-series performance, and cost savings. Maintains familiar SQL interface while optimizing for your use case."
  }
}
```

---

## Common Patterns & Best Practices

### Authentication
```typescript
headers: {
  'Authorization': 'Bearer <jwt_token>',
  'Content-Type': 'application/json'
}
```

### Error Handling
```json
{
  "success": false,
  "error": {
    "code": "MIGRATION_FAILED",
    "message": "Migration execution failed at step 3",
    "details": {
      "step": 3,
      "error": "Connection to target database lost",
      "recoverable": true,
      "rollback_available": true
    }
  }
}
```

### Rate Limiting
- **Migration Planning:** 20 requests/hour per user
- **Migration Execution:** 5 concurrent migrations per account
- **AI Schema Generation:** 50 requests/hour per user
- **AI Validation:** 100 requests/hour per user

### WebSocket Authentication
```javascript
const ws = new WebSocket('wss://api.schemasage.com/ws/migration/{execution_id}');
ws.addEventListener('open', () => {
  ws.send(JSON.stringify({
    type: 'auth',
    token: '<jwt_token>'
  }));
});
```

---

## Backend Implementation Priority

### Phase 3.1 - Priority 1 (Week 1-2):
1. **Migration Planning API** (3.1.1) - Core migration workflow
2. **Migration Execution API** (3.1.2) - Execute migrations with progress
3. **WebSocket Real-time Updates** - Critical for user experience

### Phase 3.1 - Priority 2 (Week 3):
4. **Multi-Cloud Comparison API** (3.1.3) - Cost optimization
5. **Pre-Migration Analysis API** (3.1.4) - Risk assessment

### Phase 3.1 - Priority 3 (Week 4):
6. **Smart Rollback API** (3.1.5) - Safety and reliability

### Phase 3.2 - Priority 1 (Week 5-6):
1. **Natural Language Schema Generation** (3.2.1) - Core AI feature
2. **AI Model Selection** (3.2.2) - Performance optimization

### Phase 3.2 - Priority 2 (Week 7):
3. **Best Practices Validation** (3.2.3) - Schema quality
4. **Schema Cost Estimation** (3.2.4) - Business value

### Phase 3.2 - Priority 3 (Week 8):
5. **Alternative Approaches** (3.2.5) - Decision support

---

## Testing Recommendations

### API Testing Checklist:
- [ ] Migration planning handles cross-database scenarios (PostgreSQL → MongoDB)
- [ ] WebSocket connections maintain state during long migrations
- [ ] Rollback preserves data created during migration
- [ ] AI schema generation produces valid SQL for all supported databases
- [ ] Cost estimates match actual cloud provider pricing (±5%)
- [ ] Best practices validation catches security issues (plaintext passwords)
- [ ] Rate limiting prevents abuse
- [ ] Error handling provides actionable rollback options

### Example Integration Test:
```typescript
test('Complete migration workflow', async () => {
  // Plan migration
  const plan = await api.post('/api/migration/plan', {
    source_url: 'postgresql://...',
    target_url: 'mongodb://...',
    migration_type: 'schema_and_data'
  });
  
  expect(plan.success).toBe(true);
  expect(plan.data.cross_database_migration).toBe(true);
  
  // Execute migration
  const execution = await api.post('/api/migration/execute', {
    migration_id: plan.data.migration_id
  });
  
  expect(execution.success).toBe(true);
  expect(execution.data.status).toBe('running');
  
  // Monitor via WebSocket
  const ws = new WebSocket(`wss://api/ws/migration/${execution.data.execution_id}`);
  await new Promise(resolve => {
    ws.on('message', (data) => {
      const update = JSON.parse(data);
      if (update.status === 'completed') {
        expect(update.progress.percentage).toBe(100);
        resolve();
      }
    });
  });
});
```

---

## Summary - Phase 3 Part 1

**Total Endpoints:** 10  
- Phase 3.1 Migration Center: 5 endpoints
- Phase 3.2 AI Schema Assistant: 5 endpoints

**Estimated Development Timeline:**
- Migration Center APIs: 4 weeks
- AI Schema Assistant APIs: 4 weeks
- **Total:** 8 weeks for Part 1

**Key Technologies Required:**
- WebSocket infrastructure for real-time updates
- OpenAI API (GPT-4) / Anthropic API (Claude) integration
- Database migration libraries (pg-migrate, mongo-migrate)
- Cloud provider APIs (AWS Pricing, GCP Billing, Azure Cost)
- ML models for schema analysis and validation

**Next:** Part 2 will cover Phase 3.3 Anonymization and Phase 3.5 Incident Management APIs.
