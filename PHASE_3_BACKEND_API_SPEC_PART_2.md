# Phase 3: Backend API Specification - Part 2

**Covers:** Phase 3.3 Production Data Anonymizer & Phase 3.5 Database Incident Timeline

---

## Phase 3.3: Production Data Anonymizer

### 3.3.1 PII Detection Scan

**Endpoint:** `POST /api/anonymization/scan-pii`

**Description:** ML-powered detection of Personally Identifiable Information across database

**Request:**
```json
{
  "connection_string": "postgresql://user:pass@host:5432/db",
  "scan_options": {
    "tables": ["users", "orders", "payments"],
    "confidence_threshold": 75,
    "include_samples": true,
    "max_sample_size": 3
  }
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "scan_id": "scan_9k2m5p3n",
    "total_tables_scanned": 12,
    "total_columns_scanned": 87,
    "pii_fields_detected": 18,
    "total_records_affected": 2345678,
    "compliance_violations": [
      "GDPR Article 17 (Right to erasure)",
      "CCPA § 1798.105"
    ],
    "scan_duration_seconds": 23,
    "fields": [
      {
        "table": "users",
        "column": "email",
        "pii_type": "email",
        "confidence": 100,
        "sample_values": [
          "j***@example.com",
          "s***@gmail.com",
          "a***@company.org"
        ],
        "records_affected": 145623,
        "severity": "critical",
        "compliance_impact": ["GDPR", "CCPA", "CAN-SPAM"]
      },
      {
        "table": "users",
        "column": "phone",
        "pii_type": "phone",
        "confidence": 98,
        "sample_values": [
          "(555) ***-****",
          "+1-***-***-****",
          "***-***-1234"
        ],
        "records_affected": 128934,
        "severity": "high",
        "compliance_impact": ["GDPR", "CCPA", "TCPA"]
      },
      {
        "table": "users",
        "column": "ssn",
        "pii_type": "ssn",
        "confidence": 100,
        "sample_values": [
          "***-**-6789",
          "***-**-1234",
          "***-**-5678"
        ],
        "records_affected": 89234,
        "severity": "critical",
        "compliance_impact": ["GDPR", "CCPA", "HIPAA", "SOX"]
      },
      {
        "table": "payments",
        "column": "card_number",
        "pii_type": "credit_card",
        "confidence": 100,
        "sample_values": [
          "****-****-****-1234",
          "****-****-****-5678",
          "****-****-****-9012"
        ],
        "records_affected": 234567,
        "severity": "critical",
        "compliance_impact": ["PCI-DSS", "GDPR"]
      },
      {
        "table": "users",
        "column": "date_of_birth",
        "pii_type": "dob",
        "confidence": 95,
        "sample_values": [
          "****-**-15",
          "****-**-23",
          "****-**-08"
        ],
        "records_affected": 145623,
        "severity": "high",
        "compliance_impact": ["GDPR", "CCPA", "COPPA"]
      },
      {
        "table": "orders",
        "column": "shipping_address",
        "pii_type": "address",
        "confidence": 88,
        "sample_values": [
          "*** Main St, ***",
          "*** Oak Ave, ***",
          "*** 5th St, ***"
        ],
        "records_affected": 456789,
        "severity": "medium",
        "compliance_impact": ["GDPR", "CCPA"]
      },
      {
        "table": "sessions",
        "column": "ip_address",
        "pii_type": "ip_address",
        "confidence": 100,
        "sample_values": [
          "192.168.*.*",
          "10.0.*.*",
          "172.16.*.*"
        ],
        "records_affected": 1234567,
        "severity": "low",
        "compliance_impact": ["GDPR"]
      }
    ],
    "recommendations": [
      "Implement anonymization for 7 critical PII fields before deploying to staging",
      "Add encryption-at-rest for payments.card_number (PCI-DSS requirement)",
      "Set up automated PII detection in CI/CD pipeline",
      "Review data retention policies for GDPR compliance (max 2 years for user data)",
      "Implement GDPR Article 17 deletion workflow"
    ]
  }
}
```

---

### 3.3.2 Anonymization Strategy Configuration

**Endpoint:** `POST /api/anonymization/create-rules`

**Description:** Configure anonymization strategies per field

**Request:**
```json
{
  "scan_id": "scan_9k2m5p3n",
  "rules": [
    {
      "table": "users",
      "column": "email",
      "strategy": "fake_data",
      "options": {
        "maintain_domain": true,
        "preserve_uniqueness": true
      }
    },
    {
      "table": "users",
      "column": "ssn",
      "strategy": "masking",
      "options": {
        "mask_pattern": "***-**-####",
        "preserve_last_n": 4
      }
    },
    {
      "table": "payments",
      "column": "card_number",
      "strategy": "tokenization",
      "options": {
        "token_format": "****-****-****-####",
        "preserve_last_n": 4,
        "reversible": false
      }
    },
    {
      "table": "users",
      "column": "password_hash",
      "strategy": "hashing",
      "options": {
        "algorithm": "SHA256",
        "salt": "random"
      }
    }
  ]
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "rule_set_id": "ruleset_7k3m9p2n",
    "total_rules": 4,
    "estimated_processing_time": "12 minutes",
    "rules": [
      {
        "rule_id": "rule_001",
        "table": "users",
        "column": "email",
        "strategy": "fake_data",
        "estimated_records": 145623,
        "reversible": false,
        "maintains_format": true,
        "performance_impact": "medium",
        "example_transformation": {
          "before": "john.doe@company.com",
          "after": "alice.johnson@company.com"
        }
      },
      {
        "rule_id": "rule_002",
        "table": "users",
        "column": "ssn",
        "strategy": "masking",
        "estimated_records": 89234,
        "reversible": false,
        "maintains_format": true,
        "performance_impact": "low",
        "example_transformation": {
          "before": "123-45-6789",
          "after": "***-**-6789"
        }
      },
      {
        "rule_id": "rule_003",
        "table": "payments",
        "column": "card_number",
        "strategy": "tokenization",
        "estimated_records": 234567,
        "reversible": false,
        "maintains_format": true,
        "performance_impact": "medium",
        "example_transformation": {
          "before": "4532-1234-5678-9010",
          "after": "****-****-****-9010"
        }
      },
      {
        "rule_id": "rule_004",
        "table": "users",
        "column": "password_hash",
        "strategy": "hashing",
        "estimated_records": 145623,
        "reversible": false,
        "maintains_format": false,
        "performance_impact": "low",
        "example_transformation": {
          "before": "bcrypt_hash_original",
          "after": "5d41402abc4b2a76b9719d911017c592"
        }
      }
    ],
    "validation_warnings": [
      "Fake data generation may create duplicate emails - consider adding uniqueness check",
      "Masking SSN preserves last 4 digits - ensure this meets your compliance requirements"
    ]
  }
}
```

---

### 3.3.3 Data Anonymization Execution

**Endpoint:** `POST /api/anonymization/apply-masking`

**Description:** Execute anonymization rules on target database

**Request:**
```json
{
  "rule_set_id": "ruleset_7k3m9p2n",
  "target_connection": "postgresql://user:pass@staging-host:5432/staging_db",
  "execution_options": {
    "dry_run": false,
    "batch_size": 1000,
    "verify_referential_integrity": true,
    "create_backup": true
  }
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "execution_id": "exec_5m8k3p2n",
    "status": "running",
    "progress": {
      "percentage": 0,
      "current_rule": "Anonymizing users.email",
      "records_processed": 0,
      "total_records": 614047,
      "estimated_remaining": "12 minutes"
    },
    "performance_metrics": {
      "records_per_second": 0,
      "error_count": 0,
      "warning_count": 0
    },
    "logs": [
      "[2024-11-20 15:30:00] Anonymization started",
      "[2024-11-20 15:30:01] Creating backup snapshot...",
      "[2024-11-20 15:30:15] Backup created: 2.3 GB",
      "[2024-11-20 15:30:16] Applying rule: users.email (145,623 records)"
    ]
  }
}
```

**Real-time Progress Update (WebSocket):**
```json
{
  "execution_id": "exec_5m8k3p2n",
  "status": "running",
  "progress": {
    "percentage": 65.3,
    "current_rule": "Anonymizing payments.card_number",
    "records_processed": 400234,
    "total_records": 614047,
    "estimated_remaining": "4 minutes"
  },
  "performance_metrics": {
    "records_per_second": 1850,
    "error_count": 0,
    "warning_count": 2
  },
  "completed_rules": [
    {
      "rule_id": "rule_001",
      "table": "users",
      "column": "email",
      "records_anonymized": 145623,
      "duration_seconds": 78,
      "status": "completed"
    },
    {
      "rule_id": "rule_002",
      "table": "users",
      "column": "ssn",
      "records_anonymized": 89234,
      "duration_seconds": 45,
      "status": "completed"
    }
  ]
}
```

---

### 3.3.4 Data Subsetting

**Endpoint:** `POST /api/anonymization/create-subset`

**Description:** Create representative subset of production data for staging/dev

**Request:**
```json
{
  "source_connection": "postgresql://user:pass@prod:5432/prod_db",
  "target_connection": "postgresql://user:pass@staging:5432/staging_db",
  "subsetting_strategy": "random_sampling",
  "options": {
    "sample_percentage": 10,
    "preserve_referential_integrity": true,
    "include_reference_tables": "full",
    "anonymize_after_subset": true
  }
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "subset_id": "subset_3k7m2p9n",
    "subsetting_plan": {
      "estimated_duration": "25 minutes",
      "source_size_gb": 250.5,
      "target_size_gb": 25.3,
      "reduction_percentage": 90,
      "tables": [
        {
          "table": "users",
          "original_records": 145623,
          "subset_records": 14562,
          "reduction_percentage": 90,
          "subsetting_method": "Random 10% sampling",
          "foreign_key_dependencies": [],
          "includes_full_graph": true
        },
        {
          "table": "orders",
          "original_records": 456789,
          "subset_records": 45679,
          "reduction_percentage": 90,
          "subsetting_method": "All orders from sampled users",
          "foreign_key_dependencies": ["users.user_id"],
          "includes_full_graph": true
        },
        {
          "table": "order_items",
          "original_records": 1234567,
          "subset_records": 123457,
          "reduction_percentage": 90,
          "subsetting_method": "All items from sampled orders",
          "foreign_key_dependencies": ["orders.order_id", "products.product_id"],
          "includes_full_graph": true
        },
        {
          "table": "products",
          "original_records": 12345,
          "subset_records": 12345,
          "reduction_percentage": 0,
          "subsetting_method": "Full table copy (reference data)",
          "foreign_key_dependencies": [],
          "includes_full_graph": true
        }
      ],
      "total_records_to_copy": 196043,
      "estimated_copy_time": "18 minutes",
      "estimated_anonymization_time": "7 minutes"
    }
  }
}
```

**Execute Subset:** `POST /api/anonymization/subset/{subset_id}/execute`

**Response:**
```json
{
  "success": true,
  "data": {
    "execution_id": "subset_exec_2k9m5p",
    "status": "running",
    "progress": {
      "percentage": 0,
      "current_phase": "Copying reference data",
      "records_copied": 0,
      "total_records": 196043,
      "estimated_remaining": "25 minutes"
    }
  }
}
```

---

### 3.3.5 Compliance Validation

**Endpoint:** `POST /api/anonymization/validate-compliance`

**Description:** Verify anonymization meets compliance requirements

**Request:**
```json
{
  "execution_id": "exec_5m8k3p2n",
  "compliance_frameworks": ["GDPR", "CCPA", "HIPAA", "PCI-DSS"],
  "validation_options": {
    "run_pii_rescan": true,
    "check_referential_integrity": true,
    "verify_data_quality": true
  }
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "validation_id": "valid_8k3m2p9n",
    "overall_compliance_status": "compliant",
    "frameworks": [
      {
        "framework": "GDPR",
        "status": "compliant",
        "requirements_met": 12,
        "requirements_total": 12,
        "checks": [
          {
            "requirement": "Article 17 - Right to erasure",
            "status": "passed",
            "evidence": "No PII detected in anonymized database"
          },
          {
            "requirement": "Article 32 - Security of processing",
            "status": "passed",
            "evidence": "All sensitive fields encrypted or anonymized"
          },
          {
            "requirement": "Article 25 - Data protection by design",
            "status": "passed",
            "evidence": "Anonymization applied by default for non-production environments"
          }
        ]
      },
      {
        "framework": "CCPA",
        "status": "compliant",
        "requirements_met": 8,
        "requirements_total": 8,
        "checks": [
          {
            "requirement": "§ 1798.105 - Right to deletion",
            "status": "passed",
            "evidence": "Personal information anonymized, no deletion requests applicable"
          },
          {
            "requirement": "§ 1798.100 - Right to know",
            "status": "passed",
            "evidence": "Data inventory shows 0 PII fields in staging environment"
          }
        ]
      },
      {
        "framework": "HIPAA",
        "status": "compliant",
        "requirements_met": 5,
        "requirements_total": 5,
        "checks": [
          {
            "requirement": "164.514(a) - De-identification",
            "status": "passed",
            "evidence": "All 18 HIPAA identifiers anonymized or removed"
          }
        ]
      },
      {
        "framework": "PCI-DSS",
        "status": "compliant",
        "requirements_met": 4,
        "requirements_total": 4,
        "checks": [
          {
            "requirement": "3.4 - Render PAN unreadable",
            "status": "passed",
            "evidence": "Card numbers masked with last 4 digits visible only"
          }
        ]
      }
    ],
    "pii_rescan_results": {
      "pii_fields_detected": 0,
      "confidence_level": 99.8,
      "scan_coverage": "100% of columns scanned",
      "false_positive_rate": 0.2
    },
    "referential_integrity": {
      "status": "valid",
      "foreign_key_violations": 0,
      "orphaned_records": 0,
      "checks_performed": 23
    },
    "data_quality": {
      "status": "excellent",
      "null_percentage": 2.3,
      "duplicate_records": 0,
      "format_errors": 0,
      "quality_score": 98.5
    },
    "audit_log": {
      "anonymization_timestamp": "2024-11-20 15:42:35",
      "anonymized_by": "admin@company.com",
      "rules_applied": 4,
      "records_affected": 614047,
      "backup_snapshot_id": "backup_7k2m9p3n"
    }
  }
}
```

---

## Phase 3.5: Database Incident Timeline

### 3.5.1 Event Correlation

**Endpoint:** `POST /api/incidents/correlate-events`

**Description:** Correlate incidents with deployments, migrations, and system changes

**Request:**
```json
{
  "incident_id": "INC-2024-11-20-001",
  "time_window_hours": 24,
  "event_sources": [
    "deployments",
    "migrations",
    "config_changes",
    "traffic_spikes",
    "query_patterns"
  ]
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "incident": {
      "incident_id": "INC-2024-11-20-001",
      "timestamp": "2024-11-20 14:32:00",
      "title": "Database CPU Spike - 95% Utilization",
      "severity": "critical",
      "duration_minutes": 18,
      "affected_queries": 1247,
      "metrics_at_incident": {
        "cpu_usage": 95,
        "connection_count": 487,
        "slow_queries": 234,
        "disk_io": 82
      }
    },
    "correlated_events": [
      {
        "event_id": "DEPLOY-2024-11-20-045",
        "timestamp": "2024-11-20 14:15:00",
        "event_type": "deployment",
        "description": "Frontend deployment v2.3.5 - Added product search feature",
        "correlation_score": 92,
        "time_before_incident": "17 minutes before",
        "impact_likelihood": "very_high",
        "details": {
          "service": "frontend-api",
          "version": "2.3.5",
          "changes": "New ElasticSearch integration, increased DB queries by 40%",
          "deployed_by": "john.doe@company.com"
        }
      },
      {
        "event_id": "TRAFFIC-2024-11-20-112",
        "timestamp": "2024-11-20 14:20:00",
        "event_type": "traffic_spike",
        "description": "Traffic spike detected - 3x normal load",
        "correlation_score": 88,
        "time_before_incident": "12 minutes before",
        "impact_likelihood": "very_high",
        "details": {
          "normal_rpm": "5,000 req/min",
          "peak_rpm": "15,000 req/min",
          "spike_percentage": "200%",
          "source": "Marketing email campaign launched"
        }
      },
      {
        "event_id": "QUERY-2024-11-20-089",
        "timestamp": "2024-11-20 14:25:00",
        "event_type": "query_pattern",
        "description": "New query pattern: Full table scan on products table",
        "correlation_score": 85,
        "time_before_incident": "7 minutes before",
        "impact_likelihood": "high",
        "details": {
          "query": "SELECT * FROM products WHERE name LIKE '%search%'",
          "execution_count": "1,247 times",
          "avg_duration": "2.3s per query",
          "missing_index": "products.name (text search)"
        }
      },
      {
        "event_id": "CONFIG-2024-11-20-023",
        "timestamp": "2024-11-20 10:30:00",
        "event_type": "config_change",
        "description": "Database connection pool increased from 200 to 500",
        "correlation_score": 45,
        "time_before_incident": "4 hours before",
        "impact_likelihood": "medium",
        "details": {
          "parameter": "max_connections",
          "old_value": "200",
          "new_value": "500",
          "changed_by": "dba@company.com"
        }
      }
    ],
    "causality_analysis": {
      "primary_cause": {
        "event_id": "DEPLOY-2024-11-20-045",
        "confidence": 92,
        "reasoning": "Deployment introduced inefficient search query 17 minutes before incident. Query pattern correlation shows identical timing."
      },
      "contributing_factors": [
        {
          "event_id": "TRAFFIC-2024-11-20-112",
          "contribution": "Amplified impact of inefficient query",
          "explanation": "3x traffic spike increased query execution from ~400/min to 1,200/min"
        },
        {
          "event_id": "QUERY-2024-11-20-089",
          "contribution": "Missing index on products.name",
          "explanation": "Full table scan on 1.2M rows takes 2.3s per query vs <100ms with index"
        }
      ]
    }
  }
}
```

---

### 3.5.2 Root Cause Analysis

**Endpoint:** `POST /api/incidents/analyze-root-cause`

**Description:** ML-powered root cause detection with evidence and confidence

**Request:**
```json
{
  "incident_id": "INC-2024-11-20-001",
  "analysis_depth": "comprehensive",
  "include_historical_patterns": true
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "incident_id": "INC-2024-11-20-001",
    "root_causes": [
      {
        "cause_id": "cause_001",
        "category": "query_performance",
        "title": "Unindexed Full Table Scan on products.name",
        "confidence": 94,
        "description": "New search feature introduced query without supporting index, causing full table scan on 1.2M rows",
        "evidence": [
          "EXPLAIN plan shows 'Seq Scan' on products table (1,234,567 rows)",
          "Query execution time: 2.3s average (baseline: 45ms for indexed queries)",
          "Query introduced in deployment v2.3.5 at 14:15 - incident at 14:32",
          "CPU spike correlates with query execution frequency (1,247 executions)",
          "No existing index on products.name column"
        ],
        "affected_components": [
          "products table",
          "Search API endpoint /api/products/search",
          "Frontend search feature"
        ],
        "typical_symptoms": [
          "High CPU utilization (80%+)",
          "Slow API response times (2s+)",
          "Increased connection count",
          "Buffer cache churn"
        ],
        "mitigation_urgency": "immediate"
      },
      {
        "cause_id": "cause_002",
        "category": "connection_exhaustion",
        "title": "Traffic Spike Amplified Impact",
        "confidence": 88,
        "description": "Marketing campaign caused 3x normal traffic, multiplying effect of slow query",
        "evidence": [
          "Traffic increased from 5K req/min to 15K req/min at 14:20",
          "Connection count jumped from 150 to 487",
          "Query execution frequency increased proportionally",
          "Marketing email sent at 14:18 (confirmed by marketing team)"
        ],
        "affected_components": [
          "Application connection pool",
          "Database connection manager",
          "Load balancer"
        ],
        "typical_symptoms": [
          "Rapid connection count increase",
          "Connection pool saturation",
          "Queue wait times"
        ],
        "mitigation_urgency": "high"
      }
    ],
    "pattern_matches": [
      {
        "pattern_name": "Deployment-Triggered Performance Degradation",
        "similarity_score": 91,
        "historical_occurrences": 3,
        "avg_resolution_time_minutes": 22,
        "common_fix": "Add missing index + optimize query"
      },
      {
        "pattern_name": "Traffic Spike + Inefficient Query",
        "similarity_score": 86,
        "historical_occurrences": 5,
        "avg_resolution_time_minutes": 18,
        "common_fix": "Scale database + add caching layer"
      }
    ],
    "five_whys_analysis": {
      "why_1": "Why did CPU spike to 95%?",
      "answer_1": "Because search queries were running 1,247 times causing full table scans",
      "why_2": "Why were queries doing full table scans?",
      "answer_2": "Because no index exists on products.name for text search",
      "why_3": "Why was no index created before deployment?",
      "answer_3": "Because new search feature wasn't tested with production data volume",
      "why_4": "Why wasn't it tested with production data?",
      "answer_4": "Because staging database only has 10% of production data",
      "why_5": "Why doesn't staging have realistic data volume?",
      "answer_5": "Because data subsetting process excludes large tables to save costs",
      "root_cause": "Testing process doesn't validate query performance at production scale"
    }
  }
}
```

---

### 3.5.3 Similar Incidents Search

**Endpoint:** `GET /api/incidents/similar/{incident_id}`

**Description:** Find historical incidents with similar symptoms and resolutions

**Response:**
```json
{
  "success": true,
  "data": {
    "current_incident": {
      "incident_id": "INC-2024-11-20-001",
      "title": "Database CPU Spike - 95% Utilization",
      "severity": "critical"
    },
    "similar_incidents": [
      {
        "incident_id": "INC-2024-10-15-003",
        "timestamp": "2024-10-15 09:23:00",
        "title": "Database CPU Spike - 92% Utilization",
        "similarity_score": 94,
        "root_cause": "Inefficient query with full table scan on products.name after deployment v2.1.2",
        "resolution": "Added GIN index on products.name using pg_trgm extension",
        "resolution_time_minutes": 18,
        "resolved_by": "Sarah Chen (DBA)",
        "prevented_recurrence": true,
        "shared_symptoms": [
          "CPU usage spiked to 90%+ during peak hours",
          "Full table scan on products table (1.2M rows)",
          "Query execution time: 2.1s average",
          "Triggered by new deployment with search feature",
          "Connection count increased 200%+",
          "Traffic spike from marketing campaign"
        ],
        "different_factors": [
          "v2.1.2 deployment vs current v2.3.5",
          "Occurred at 9am vs current 2:32pm",
          "Peak traffic 10K req/min vs current 15K req/min"
        ],
        "lessons_learned": [
          "Always test queries in staging with production data volume",
          "Create indexes CONCURRENTLY to avoid table locks",
          "Monitor query execution plans after deployments",
          "Set up alerts for CPU >80% for 5+ minutes",
          "Implement query timeout of 5s for user-facing queries"
        ]
      },
      {
        "incident_id": "INC-2024-09-22-007",
        "timestamp": "2024-09-22 14:45:00",
        "title": "Connection Pool Exhaustion - 498/500",
        "similarity_score": 78,
        "root_cause": "Traffic spike (4x normal) exhausted database connection pool",
        "resolution": "Increased max_connections to 1000 + deployed PgBouncer",
        "resolution_time_minutes": 45,
        "resolved_by": "Mike Rodriguez (SRE)",
        "prevented_recurrence": true,
        "shared_symptoms": [
          "Connection count reached 98% of max_connections",
          "Traffic spike from external event (3x-4x normal)",
          "Connection wait time increased 100x",
          "Slow API response times (5s+)"
        ],
        "lessons_learned": [
          "Deploy PgBouncer for connection pooling",
          "Set up auto-scaling for application servers",
          "Monitor connection count and set alerts at 80% capacity",
          "Implement circuit breakers in application code"
        ]
      }
    ],
    "recurrence_patterns": [
      {
        "pattern_name": "Post-Deployment Performance Issues",
        "occurrences": 7,
        "frequency": "~1 per month",
        "avg_resolution_time_minutes": 25,
        "trend": "decreasing",
        "last_occurrence": "2024-10-15",
        "prevention_status": "partial",
        "prevention_measures": [
          "Query performance testing added to CI/CD (50% reduction in incidents)",
          "Database monitoring alerts improved",
          "Runbooks created for common scenarios"
        ]
      }
    ]
  }
}
```

---

### 3.5.4 Recommended Fix

**Endpoint:** `POST /api/incidents/generate-fix`

**Description:** Generate immediate, short-term, and long-term fixes with SQL

**Request:**
```json
{
  "incident_id": "INC-2024-11-20-001",
  "fix_preferences": {
    "risk_tolerance": "moderate",
    "downtime_acceptable": false,
    "automation_level": "supervised"
  }
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "incident_id": "INC-2024-11-20-001",
    "fixes": [
      {
        "fix_id": "FIX-001",
        "fix_type": "immediate",
        "category": "query_optimization",
        "title": "Add Index on products.name",
        "impact": "high",
        "estimated_resolution_time_minutes": 5,
        "risk_level": "safe",
        "sql_commands": [
          "-- Add index on products.name for text search (concurrent to avoid table lock)",
          "CREATE INDEX CONCURRENTLY idx_products_name ON products USING GIN (name gin_trgm_ops);",
          "",
          "-- Verify index was created",
          "SELECT indexname, indexdef FROM pg_indexes WHERE tablename = 'products' AND indexname = 'idx_products_name';",
          "",
          "-- Test query performance after index",
          "EXPLAIN ANALYZE SELECT * FROM products WHERE name ILIKE '%search%';"
        ],
        "rollback_plan": "DROP INDEX CONCURRENTLY idx_products_name;",
        "prerequisites": [
          "Install pg_trgm extension: CREATE EXTENSION IF NOT EXISTS pg_trgm;",
          "Ensure sufficient disk space for index (estimate: 150 MB)",
          "Check for existing index on products.name",
          "Verify no other CREATE INDEX operations running"
        ],
        "validation_steps": [
          "Run EXPLAIN on slow query - should show 'Index Scan' instead of 'Seq Scan'",
          "Monitor query execution time - target: <100ms (current: 2.3s)",
          "Check CPU usage - should drop from 95% to <50%",
          "Verify no lock timeouts during index creation"
        ]
      },
      {
        "fix_id": "FIX-002",
        "fix_type": "short_term",
        "category": "query_optimization",
        "title": "Add Query Result Caching",
        "impact": "medium",
        "estimated_resolution_time_minutes": 30,
        "risk_level": "moderate",
        "sql_commands": [
          "-- Enable query result caching in application layer",
          "-- Redis cache configuration (pseudo-code):",
          "CACHE_TTL = 300  -- 5 minutes",
          "CACHE_KEY = 'search:products:{search_term}'",
          "",
          "-- Example implementation:",
          "-- 1. Check Redis cache for search results",
          "-- 2. If miss, execute query and cache result",
          "-- 3. Return cached or fresh results"
        ],
        "rollback_plan": "Disable caching layer, direct database queries",
        "prerequisites": [
          "Redis cluster deployed and accessible",
          "Application code updated with caching logic",
          "Cache invalidation strategy defined"
        ],
        "validation_steps": [
          "Verify cache hit rate >70% for search queries",
          "Monitor database query count - should decrease 70%",
          "Test cache invalidation when products updated",
          "Verify stale data acceptable (5min TTL)"
        ]
      },
      {
        "fix_id": "FIX-003",
        "fix_type": "long_term",
        "category": "architecture",
        "title": "Migrate to Elasticsearch for Full-Text Search",
        "impact": "high",
        "estimated_resolution_time_minutes": 2880,
        "risk_level": "moderate",
        "sql_commands": [],
        "rollback_plan": "Maintain PostgreSQL as fallback, gradual rollback",
        "prerequisites": [
          "Elasticsearch cluster provisioned",
          "Data sync pipeline from PostgreSQL to Elasticsearch",
          "Search API refactored to use Elasticsearch",
          "Load testing completed"
        ],
        "validation_steps": [
          "Search latency <50ms (10x improvement)",
          "Handle 100K+ searches/min (10x current capacity)",
          "Zero downtime migration verified",
          "Fallback to PostgreSQL tested"
        ]
      }
    ],
    "automated_fixes": [
      {
        "fix_id": "FIX-001",
        "name": "Auto-Create Index",
        "description": "Automatically create GIN index on products.name",
        "can_automate": true,
        "automation_risk": "low",
        "estimated_duration_seconds": 300,
        "approval_required": false
      }
    ]
  }
}
```

---

### 3.5.5 Prevention Checklist

**Endpoint:** `GET /api/incidents/prevention-checklist/{incident_id}`

**Description:** Generate preventive measures to avoid recurrence

**Response:**
```json
{
  "success": true,
  "data": {
    "incident_id": "INC-2024-11-20-001",
    "prevention_checklist": [
      {
        "category": "Testing",
        "priority": "high",
        "items": [
          {
            "task": "Test all queries with production-scale data (1M+ rows)",
            "status": "not_implemented",
            "estimated_effort_hours": 8,
            "impact": "Prevent 80% of query performance incidents"
          },
          {
            "task": "Add query performance tests to CI/CD pipeline",
            "status": "not_implemented",
            "estimated_effort_hours": 16,
            "impact": "Automated detection before deployment"
          },
          {
            "task": "Run EXPLAIN ANALYZE on all new queries before merging",
            "status": "not_implemented",
            "estimated_effort_hours": 2,
            "impact": "Catch missing indexes early"
          }
        ]
      },
      {
        "category": "Monitoring",
        "priority": "high",
        "items": [
          {
            "task": "Set up alert: CPU >80% for >5 minutes",
            "status": "implemented",
            "estimated_effort_hours": 0,
            "impact": "Early warning system"
          },
          {
            "task": "Set up alert: Slow query count >10 in 1 minute",
            "status": "not_implemented",
            "estimated_effort_hours": 2,
            "impact": "Detect query performance degradation"
          },
          {
            "task": "Track query execution plans after each deployment",
            "status": "not_implemented",
            "estimated_effort_hours": 8,
            "impact": "Detect plan regressions automatically"
          }
        ]
      },
      {
        "category": "Deployment",
        "priority": "medium",
        "items": [
          {
            "task": "Implement gradual rollout (10% → 50% → 100%)",
            "status": "not_implemented",
            "estimated_effort_hours": 24,
            "impact": "Limit blast radius of performance issues"
          },
          {
            "task": "Add database schema review to deployment checklist",
            "status": "not_implemented",
            "estimated_effort_hours": 1,
            "impact": "Catch missing indexes before production"
          },
          {
            "task": "Require DBA approval for queries touching >100K rows",
            "status": "not_implemented",
            "estimated_effort_hours": 4,
            "impact": "Expert review for high-impact queries"
          }
        ]
      },
      {
        "category": "Architecture",
        "priority": "low",
        "items": [
          {
            "task": "Implement read replicas for search queries",
            "status": "not_implemented",
            "estimated_effort_hours": 40,
            "impact": "Isolate search load from transactional queries"
          },
          {
            "task": "Evaluate Elasticsearch for full-text search",
            "status": "not_implemented",
            "estimated_effort_hours": 80,
            "impact": "10x search performance improvement"
          }
        ]
      }
    ],
    "summary": {
      "total_items": 11,
      "implemented": 1,
      "not_implemented": 10,
      "high_priority": 6,
      "medium_priority": 3,
      "low_priority": 2,
      "total_estimated_effort_hours": 185
    },
    "quick_wins": [
      {
        "task": "Set up alert: Slow query count >10 in 1 minute",
        "effort_hours": 2,
        "impact": "high",
        "priority": "Implement this week"
      },
      {
        "task": "Run EXPLAIN ANALYZE on all new queries before merging",
        "effort_hours": 2,
        "impact": "high",
        "priority": "Implement this week"
      },
      {
        "task": "Add database schema review to deployment checklist",
        "effort_hours": 1,
        "impact": "medium",
        "priority": "Implement this week"
      }
    ]
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
    "code": "ANONYMIZATION_FAILED",
    "message": "PII detection scan failed",
    "details": {
      "table": "users",
      "error": "Connection timeout",
      "recoverable": true
    }
  }
}
```

### Rate Limiting
- **PII Scanning:** 10 scans/hour per user
- **Anonymization Execution:** 5 concurrent jobs per account
- **Incident Analysis:** 50 requests/hour per user
- **Event Correlation:** 100 requests/hour per user

### WebSocket Authentication
```javascript
const ws = new WebSocket('wss://api.schemasage.com/ws/anonymization/{execution_id}');
ws.addEventListener('open', () => {
  ws.send(JSON.stringify({
    type: 'auth',
    token: '<jwt_token>'
  }));
});
```

---

## Backend Implementation Priority

### Phase 3.3 - Priority 1 (Week 1-2):
1. **PII Detection Scan API** (3.3.1) - Core anonymization feature
2. **Anonymization Strategy Configuration** (3.3.2) - Rule management
3. **Data Anonymization Execution** (3.3.3) - Apply anonymization

### Phase 3.3 - Priority 2 (Week 3):
4. **Data Subsetting API** (3.3.4) - Staging environment optimization
5. **Compliance Validation API** (3.3.5) - Regulatory compliance

### Phase 3.5 - Priority 1 (Week 4-5):
1. **Event Correlation API** (3.5.1) - Incident investigation
2. **Root Cause Analysis API** (3.5.2) - ML-powered diagnosis

### Phase 3.5 - Priority 2 (Week 6):
3. **Similar Incidents Search** (3.5.3) - Historical pattern matching
4. **Recommended Fix API** (3.5.4) - Automated remediation

### Phase 3.5 - Priority 3 (Week 7):
5. **Prevention Checklist API** (3.5.5) - Recurrence prevention

---

## Testing Recommendations

### API Testing Checklist:
- [ ] PII detection achieves >95% accuracy on test dataset
- [ ] Anonymization preserves referential integrity
- [ ] Data subsetting maintains foreign key relationships
- [ ] Compliance validation covers GDPR, CCPA, HIPAA, PCI-DSS
- [ ] Event correlation scores match manual analysis (±5%)
- [ ] Root cause analysis confidence >80% for known incidents
- [ ] Similar incident matching recall >90%
- [ ] Recommended fixes generate valid SQL

### Example Integration Test:
```typescript
test('Complete anonymization workflow', async () => {
  // Scan for PII
  const scan = await api.post('/api/anonymization/scan-pii', {
    connection_string: 'postgresql://...',
    scan_options: { confidence_threshold: 75 }
  });
  
  expect(scan.success).toBe(true);
  expect(scan.data.pii_fields_detected).toBeGreaterThan(0);
  
  // Configure anonymization rules
  const rules = await api.post('/api/anonymization/create-rules', {
    scan_id: scan.data.scan_id,
    rules: [
      { table: 'users', column: 'email', strategy: 'fake_data' }
    ]
  });
  
  expect(rules.success).toBe(true);
  
  // Execute anonymization
  const execution = await api.post('/api/anonymization/apply-masking', {
    rule_set_id: rules.data.rule_set_id,
    target_connection: 'postgresql://staging...'
  });
  
  expect(execution.success).toBe(true);
  expect(execution.data.status).toBe('running');
  
  // Validate compliance
  const validation = await api.post('/api/anonymization/validate-compliance', {
    execution_id: execution.data.execution_id,
    compliance_frameworks: ['GDPR', 'CCPA']
  });
  
  expect(validation.data.overall_compliance_status).toBe('compliant');
  expect(validation.data.pii_rescan_results.pii_fields_detected).toBe(0);
});
```

---

## Summary - Phase 3 Part 2

**Total Endpoints:** 10  
- Phase 3.3 Anonymization: 5 endpoints
- Phase 3.5 Incident Timeline: 5 endpoints

**Estimated Development Timeline:**
- Anonymization APIs: 3 weeks
- Incident Management APIs: 4 weeks
- **Total:** 7 weeks for Part 2

**Key Technologies Required:**
- ML models for PII detection (AWS Comprehend / Google DLP API)
- Faker library for fake data generation
- Pattern matching algorithms for incident correlation
- Time-series analysis for event causality
- PostgreSQL pg_trgm extension for text search

**Next:** Part 3 will cover Phase 3.6 ROI Dashboard APIs and final summary.
