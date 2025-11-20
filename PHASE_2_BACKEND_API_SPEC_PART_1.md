# Phase 2: Backend API Specification - Part 1

**Purpose:** Complete API endpoints documentation for Phase 2.1 and 2.2 features to ensure seamless frontend-backend integration.

---

## API Base Configuration

```typescript
// Frontend: src/lib/config.ts
const API_GATEWAY = "https://schemasage-api-gateway-2da67d920b07.herokuapp.com";

// Service-specific endpoints (fallback)
const COMPLIANCE_SERVICE = "https://schemasage-compliance.herokuapp.com";
const MONITORING_SERVICE = "https://schemasage-monitoring.herokuapp.com";
const ANALYTICS_SERVICE = "https://schemasage-analytics.herokuapp.com";
```

---

## Phase 2.1: Compliance Auto-Fixer

### 2.1.1 Encryption Detector & Fixer

**Endpoint:** `POST /api/compliance/detect-encryption`

**Request:**
```json
{
  "schema": {
    "database_type": "postgresql",
    "tables": [
      {
        "name": "users",
        "columns": [
          {
            "name": "email",
            "type": "varchar",
            "is_encrypted": false,
            "contains_pii": true
          },
          {
            "name": "ssn",
            "type": "varchar",
            "is_encrypted": false,
            "contains_pii": true
          },
          {
            "name": "password_hash",
            "type": "varchar",
            "is_encrypted": false,
            "contains_pii": false
          }
        ]
      },
      {
        "name": "payment_methods",
        "columns": [
          {
            "name": "card_number",
            "type": "varchar",
            "is_encrypted": false,
            "contains_pii": true
          }
        ]
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
    "issues": [
      {
        "table": "users",
        "column": "email",
        "severity": "high",
        "issue_type": "unencrypted_pii",
        "pii_type": "email_address",
        "compliance_frameworks": ["GDPR", "CCPA"],
        "affected_records": 125847,
        "recommendation": "Enable column-level encryption with AES-256",
        "encryption_options": {
          "transparent_data_encryption": {
            "supported": true,
            "sql": "ALTER TABLE users ALTER COLUMN email TYPE bytea USING pgp_sym_encrypt(email::text, 'encryption_key');",
            "pros": ["No application changes", "Database-level encryption"],
            "cons": ["Key management complexity", "Performance impact 15-20%"],
            "estimated_cost_increase": 12.50
          },
          "application_level": {
            "supported": true,
            "implementation": "Use crypto library (bcrypt, argon2) in application layer",
            "pros": ["Fine-grained control", "Better performance"],
            "cons": ["Requires code changes", "Migration effort"],
            "estimated_cost_increase": 0
          },
          "kms_integration": {
            "supported": true,
            "sql": "CREATE EXTENSION IF NOT EXISTS aws_kms;\nALTER TABLE users ALTER COLUMN email TYPE bytea USING aws_kms_encrypt(email::text, 'alias/database-key');",
            "pros": ["Enterprise-grade key management", "Compliance-ready"],
            "cons": ["Additional AWS KMS costs", "Latency overhead"],
            "estimated_cost_increase": 45.00
          }
        }
      },
      {
        "table": "users",
        "column": "ssn",
        "severity": "critical",
        "issue_type": "unencrypted_pii",
        "pii_type": "social_security_number",
        "compliance_frameworks": ["GDPR", "HIPAA", "PCI-DSS"],
        "affected_records": 125847,
        "recommendation": "URGENT: Encrypt SSN immediately with field-level encryption",
        "encryption_options": {
          "transparent_data_encryption": {
            "supported": true,
            "sql": "ALTER TABLE users ALTER COLUMN ssn TYPE bytea USING pgp_sym_encrypt(ssn::text, 'encryption_key');",
            "pros": ["Immediate deployment", "No app changes"],
            "cons": ["Performance impact", "Key rotation complexity"],
            "estimated_cost_increase": 18.75
          },
          "kms_integration": {
            "supported": true,
            "sql": "ALTER TABLE users ALTER COLUMN ssn TYPE bytea USING aws_kms_encrypt(ssn::text, 'alias/pii-key');",
            "pros": ["HSM-backed keys", "Audit trail", "Compliance-ready"],
            "cons": ["Higher cost", "AWS dependency"],
            "estimated_cost_increase": 67.50
          }
        }
      },
      {
        "table": "payment_methods",
        "column": "card_number",
        "severity": "critical",
        "issue_type": "unencrypted_pii",
        "pii_type": "credit_card",
        "compliance_frameworks": ["PCI-DSS"],
        "affected_records": 34521,
        "recommendation": "PCI-DSS violation: Encrypt card data with tokenization",
        "encryption_options": {
          "tokenization": {
            "supported": true,
            "implementation": "Replace card numbers with tokens from payment processor (Stripe, Braintree)",
            "pros": ["PCI-DSS compliant", "No encryption key management", "Reduced liability"],
            "cons": ["Vendor lock-in", "Migration complexity"],
            "estimated_cost_increase": 0,
            "integration_guide": "https://stripe.com/docs/security/tokenization"
          },
          "vault_encryption": {
            "supported": true,
            "sql": "-- Use HashiCorp Vault for encryption\nCREATE EXTENSION vault_encrypt;\nALTER TABLE payment_methods ALTER COLUMN card_number TYPE bytea USING vault_encrypt(card_number::text);",
            "pros": ["Centralized key management", "Audit logs", "Dynamic secrets"],
            "cons": ["Infrastructure complexity", "Additional service costs"],
            "estimated_cost_increase": 95.00
          }
        }
      }
    ],
    "summary": {
      "total_issues": 3,
      "critical_issues": 2,
      "high_issues": 1,
      "total_affected_records": 286215,
      "compliance_frameworks_at_risk": ["GDPR", "CCPA", "HIPAA", "PCI-DSS"],
      "estimated_fix_time_hours": 16,
      "estimated_monthly_cost_increase": {
        "min": 12.50,
        "max": 226.25,
        "recommended": 131.25
      }
    },
    "auto_fix_available": true,
    "auto_fix_sql": [
      "-- Enable pgcrypto extension",
      "CREATE EXTENSION IF NOT EXISTS pgcrypto;",
      "",
      "-- Encrypt email column",
      "ALTER TABLE users ADD COLUMN email_encrypted bytea;",
      "UPDATE users SET email_encrypted = pgp_sym_encrypt(email::text, current_setting('app.encryption_key'));",
      "ALTER TABLE users DROP COLUMN email;",
      "ALTER TABLE users RENAME COLUMN email_encrypted TO email;",
      "",
      "-- Encrypt SSN column",
      "ALTER TABLE users ADD COLUMN ssn_encrypted bytea;",
      "UPDATE users SET ssn_encrypted = pgp_sym_encrypt(ssn::text, current_setting('app.encryption_key'));",
      "ALTER TABLE users DROP COLUMN ssn;",
      "ALTER TABLE users RENAME COLUMN ssn_encrypted TO ssn;",
      "",
      "-- Encrypt card_number column",
      "ALTER TABLE payment_methods ADD COLUMN card_number_encrypted bytea;",
      "UPDATE payment_methods SET card_number_encrypted = pgp_sym_encrypt(card_number::text, current_setting('app.encryption_key'));",
      "ALTER TABLE payment_methods DROP COLUMN card_number;",
      "ALTER TABLE payment_methods RENAME COLUMN card_number_encrypted TO card_number;"
    ]
  }
}
```

---

### 2.1.2 Access Control Auditor

**Endpoint:** `POST /api/compliance/audit-access-control`

**Request:**
```json
{
  "database_type": "postgresql",
  "connection_string": "postgresql://user:pass@host:5432/dbname",
  "compliance_framework": "SOC2"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "users": [
      {
        "username": "admin",
        "roles": ["superuser"],
        "permissions": ["ALL"],
        "risk_level": "critical",
        "issues": [
          {
            "type": "excessive_permissions",
            "description": "Superuser role grants unrestricted access to all databases",
            "severity": "critical",
            "recommendation": "Create role-based access with principle of least privilege",
            "affected_databases": ["production", "staging", "analytics"],
            "compliance_violation": "SOC2 CC6.3 - Logical access controls"
          }
        ],
        "last_login": "2024-01-15T14:32:00Z",
        "failed_login_attempts": 0
      },
      {
        "username": "app_readonly",
        "roles": ["read_only"],
        "permissions": ["SELECT"],
        "risk_level": "low",
        "issues": [],
        "last_login": "2024-01-18T09:15:00Z",
        "failed_login_attempts": 0
      },
      {
        "username": "analytics_user",
        "roles": ["analyst"],
        "permissions": ["SELECT", "INSERT", "UPDATE", "DELETE"],
        "risk_level": "high",
        "issues": [
          {
            "type": "unnecessary_write_access",
            "description": "Analytics user has DELETE permission on production tables",
            "severity": "high",
            "recommendation": "Remove DELETE permission - analytics should be read-only",
            "affected_tables": ["users", "orders", "payments"],
            "compliance_violation": "SOC2 CC6.1 - Separation of duties"
          }
        ],
        "last_login": "2024-01-17T11:20:00Z",
        "failed_login_attempts": 2
      },
      {
        "username": "old_developer",
        "roles": ["developer"],
        "permissions": ["SELECT", "INSERT", "UPDATE"],
        "risk_level": "high",
        "issues": [
          {
            "type": "inactive_account",
            "description": "User has not logged in for 120 days",
            "severity": "high",
            "recommendation": "Disable or remove inactive user accounts",
            "last_activity": "2023-09-20T10:00:00Z",
            "compliance_violation": "SOC2 CC6.2 - Account lifecycle management"
          }
        ],
        "last_login": "2023-09-20T10:00:00Z",
        "failed_login_attempts": 0
      },
      {
        "username": "backup_service",
        "roles": ["backup"],
        "permissions": ["SELECT", "REPLICATION"],
        "risk_level": "medium",
        "issues": [
          {
            "type": "missing_mfa",
            "description": "Service account lacks multi-factor authentication",
            "severity": "medium",
            "recommendation": "Enable certificate-based authentication for service accounts",
            "compliance_violation": "SOC2 CC6.1 - Multi-factor authentication"
          }
        ],
        "last_login": "2024-01-18T02:00:00Z",
        "failed_login_attempts": 0
      }
    ],
    "role_matrix": [
      {
        "role": "superuser",
        "users_count": 1,
        "permissions": ["ALL"],
        "tables_accessible": ["ALL"],
        "risk_score": 100,
        "recommendation": "Limit to 0 users in production - use break-glass procedure instead"
      },
      {
        "role": "developer",
        "users_count": 3,
        "permissions": ["SELECT", "INSERT", "UPDATE", "DELETE"],
        "tables_accessible": ["users", "orders", "products", "categories"],
        "risk_score": 75,
        "recommendation": "Remove DELETE permission - use separate admin role for destructive operations"
      },
      {
        "role": "analyst",
        "users_count": 2,
        "permissions": ["SELECT", "INSERT", "UPDATE", "DELETE"],
        "tables_accessible": ["ALL"],
        "risk_score": 70,
        "recommendation": "Restrict to SELECT only on analytics views, not raw tables"
      },
      {
        "role": "read_only",
        "users_count": 5,
        "permissions": ["SELECT"],
        "tables_accessible": ["users", "orders", "products"],
        "risk_score": 20,
        "recommendation": "Well-configured - no changes needed"
      }
    ],
    "recommendations": [
      {
        "priority": "critical",
        "category": "principle_of_least_privilege",
        "title": "Remove Superuser Access from Production",
        "description": "Superuser 'admin' has unrestricted access - violates SOC2 CC6.3",
        "fix_sql": [
          "-- Revoke superuser role",
          "ALTER ROLE admin NOSUPERUSER;",
          "",
          "-- Create limited admin role",
          "CREATE ROLE limited_admin;",
          "GRANT CONNECT ON DATABASE production TO limited_admin;",
          "GRANT USAGE ON SCHEMA public TO limited_admin;",
          "GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA public TO limited_admin;",
          "",
          "-- Assign to admin user",
          "GRANT limited_admin TO admin;"
        ],
        "affected_users": ["admin"],
        "compliance_impact": "SOC2 CC6.3"
      },
      {
        "priority": "high",
        "category": "separation_of_duties",
        "title": "Restrict Analytics User to Read-Only",
        "description": "Analytics user should not have write access to production data",
        "fix_sql": [
          "-- Revoke write permissions",
          "REVOKE INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public FROM analytics_user;",
          "",
          "-- Grant read-only access to analytics views",
          "GRANT SELECT ON ALL TABLES IN SCHEMA analytics TO analytics_user;"
        ],
        "affected_users": ["analytics_user"],
        "compliance_impact": "SOC2 CC6.1"
      },
      {
        "priority": "high",
        "category": "account_lifecycle",
        "title": "Disable Inactive User Accounts",
        "description": "User 'old_developer' has not logged in for 120 days",
        "fix_sql": [
          "-- Disable inactive user",
          "ALTER ROLE old_developer NOLOGIN;",
          "",
          "-- Or remove entirely",
          "DROP ROLE old_developer;"
        ],
        "affected_users": ["old_developer"],
        "compliance_impact": "SOC2 CC6.2"
      },
      {
        "priority": "medium",
        "category": "authentication",
        "title": "Enable Certificate-Based Auth for Service Accounts",
        "description": "Service accounts should use certificate authentication instead of passwords",
        "fix_sql": [
          "-- Create certificate authentication",
          "ALTER ROLE backup_service WITH PASSWORD NULL;",
          "",
          "-- Configure pg_hba.conf:",
          "-- hostssl all backup_service 0.0.0.0/0 cert clientcert=verify-full"
        ],
        "affected_users": ["backup_service"],
        "compliance_impact": "SOC2 CC6.1"
      }
    ],
    "summary": {
      "total_users": 5,
      "critical_risk_users": 1,
      "high_risk_users": 2,
      "medium_risk_users": 1,
      "low_risk_users": 1,
      "total_issues": 5,
      "compliance_score": 42,
      "auto_fix_available": true
    },
    "auto_fix_sql": [
      "-- Fix 1: Remove superuser access",
      "ALTER ROLE admin NOSUPERUSER;",
      "CREATE ROLE limited_admin;",
      "GRANT CONNECT ON DATABASE production TO limited_admin;",
      "GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA public TO limited_admin;",
      "GRANT limited_admin TO admin;",
      "",
      "-- Fix 2: Restrict analytics to read-only",
      "REVOKE INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public FROM analytics_user;",
      "",
      "-- Fix 3: Disable inactive account",
      "ALTER ROLE old_developer NOLOGIN;",
      "",
      "-- Fix 4: Document certificate auth requirement for backup_service",
      "-- Manual step: Update pg_hba.conf and restart PostgreSQL"
    ]
  }
}
```

---

### 2.1.3 Automated Compliance Reports

**Endpoint:** `POST /api/compliance/generate-report`

**Request:**
```json
{
  "database_type": "postgresql",
  "connection_string": "postgresql://user:pass@host:5432/dbname",
  "frameworks": ["GDPR", "SOC2", "HIPAA"],
  "report_type": "executive_summary",
  "include_recommendations": true
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "report_id": "rpt_2024_01_18_abc123",
    "generated_at": "2024-01-18T10:30:00Z",
    "database_name": "production_db",
    "frameworks_assessed": ["GDPR", "SOC2", "HIPAA"],
    "overall_compliance_score": 68,
    "executive_summary": {
      "status": "non_compliant",
      "critical_findings": 3,
      "high_findings": 5,
      "medium_findings": 8,
      "low_findings": 12,
      "compliant_controls": 42,
      "total_controls_assessed": 70,
      "estimated_remediation_time_hours": 48,
      "estimated_cost": 12500
    },
    "framework_scores": {
      "GDPR": {
        "score": 72,
        "status": "partial_compliance",
        "compliant_requirements": 18,
        "total_requirements": 25,
        "critical_gaps": [
          {
            "requirement": "Article 32 - Security of Processing",
            "description": "3 PII fields lack encryption at rest",
            "affected_tables": ["users", "payment_methods"],
            "remediation": "Implement column-level encryption with AES-256"
          },
          {
            "requirement": "Article 17 - Right to Erasure",
            "description": "No automated data deletion mechanism for GDPR requests",
            "affected_tables": ["users", "orders", "audit_logs"],
            "remediation": "Implement GDPR deletion workflow with cascade rules"
          }
        ]
      },
      "SOC2": {
        "score": 65,
        "status": "non_compliant",
        "compliant_requirements": 13,
        "total_requirements": 20,
        "critical_gaps": [
          {
            "requirement": "CC6.1 - Logical Access Controls",
            "description": "1 superuser account with unrestricted access",
            "affected_users": ["admin"],
            "remediation": "Implement role-based access control (RBAC)"
          },
          {
            "requirement": "CC7.2 - System Monitoring",
            "description": "No audit logging for failed login attempts",
            "remediation": "Enable PostgreSQL audit extension (pgaudit)"
          },
          {
            "requirement": "CC6.2 - Prior to Issuing System Credentials",
            "description": "1 inactive account not disabled (120+ days)",
            "affected_users": ["old_developer"],
            "remediation": "Implement 90-day account review policy"
          }
        ]
      },
      "HIPAA": {
        "score": 58,
        "status": "non_compliant",
        "compliant_requirements": 7,
        "total_requirements": 12,
        "critical_gaps": [
          {
            "requirement": "164.312(a)(2)(i) - Unique User Identification",
            "description": "Shared service accounts without individual attribution",
            "affected_users": ["backup_service", "monitoring_service"],
            "remediation": "Create individual service principals with audit trails"
          },
          {
            "requirement": "164.312(e)(2)(i) - Encryption and Decryption",
            "description": "SSN field unencrypted - PHI exposure risk",
            "affected_tables": ["users"],
            "remediation": "Enable transparent data encryption (TDE)"
          },
          {
            "requirement": "164.308(a)(1)(ii)(D) - Information System Activity Review",
            "description": "No automated alerting for unauthorized PHI access",
            "remediation": "Implement real-time audit log analysis with alerts"
          }
        ]
      }
    },
    "findings_by_severity": [
      {
        "severity": "critical",
        "count": 3,
        "findings": [
          {
            "id": "CRIT-001",
            "title": "Unencrypted PII Fields",
            "description": "3 columns containing PII lack encryption at rest",
            "affected_resources": ["users.email", "users.ssn", "payment_methods.card_number"],
            "frameworks": ["GDPR", "HIPAA", "PCI-DSS"],
            "cvss_score": 8.5,
            "remediation_steps": [
              "Enable pgcrypto extension",
              "Migrate columns to bytea type with pgp_sym_encrypt",
              "Update application code to decrypt on read",
              "Implement key rotation policy"
            ],
            "estimated_fix_time_hours": 16,
            "auto_fix_available": true
          },
          {
            "id": "CRIT-002",
            "title": "Superuser Access in Production",
            "description": "Admin user has unrestricted superuser privileges",
            "affected_resources": ["admin"],
            "frameworks": ["SOC2", "HIPAA"],
            "cvss_score": 7.8,
            "remediation_steps": [
              "Revoke superuser role",
              "Create limited admin role with granular permissions",
              "Implement break-glass procedure for emergency access",
              "Enable audit logging for admin actions"
            ],
            "estimated_fix_time_hours": 4,
            "auto_fix_available": true
          },
          {
            "id": "CRIT-003",
            "title": "No Audit Logging Enabled",
            "description": "Database lacks comprehensive audit trail for compliance",
            "affected_resources": ["entire_database"],
            "frameworks": ["SOC2", "HIPAA", "GDPR"],
            "cvss_score": 7.2,
            "remediation_steps": [
              "Install pgaudit extension",
              "Configure audit policy for DDL, DML, and DCL statements",
              "Set up log aggregation to SIEM (Splunk, ELK)",
              "Implement 7-year log retention per GDPR"
            ],
            "estimated_fix_time_hours": 8,
            "auto_fix_available": false
          }
        ]
      },
      {
        "severity": "high",
        "count": 5,
        "findings": [
          {
            "id": "HIGH-001",
            "title": "Excessive Permissions for Analytics User",
            "description": "Analytics user has DELETE permission on production tables",
            "affected_resources": ["analytics_user"],
            "frameworks": ["SOC2"],
            "remediation_steps": [
              "Revoke INSERT, UPDATE, DELETE permissions",
              "Grant SELECT only on analytics views",
              "Create read-replica for analytics workloads"
            ],
            "estimated_fix_time_hours": 2,
            "auto_fix_available": true
          },
          {
            "id": "HIGH-002",
            "title": "No Data Retention Policy",
            "description": "3 tables lack automated data retention and deletion",
            "affected_resources": ["users", "audit_logs", "sessions"],
            "frameworks": ["GDPR"],
            "remediation_steps": [
              "Define retention periods per data classification",
              "Implement scheduled deletion jobs",
              "Add deleted_at timestamp columns",
              "Create archive process for compliance"
            ],
            "estimated_fix_time_hours": 12,
            "auto_fix_available": false
          }
        ]
      }
    ],
    "compliance_controls": [
      {
        "control_id": "GDPR-Art32-Encryption",
        "status": "non_compliant",
        "description": "Encryption of personal data at rest",
        "evidence": "3/8 PII columns encrypted (37.5%)",
        "gap": "email, ssn, card_number lack encryption",
        "remediation": "Enable transparent data encryption"
      },
      {
        "control_id": "SOC2-CC6.1-RBAC",
        "status": "non_compliant",
        "description": "Role-based access control implementation",
        "evidence": "1/5 users have excessive permissions (20%)",
        "gap": "Admin user has superuser role",
        "remediation": "Implement least privilege access model"
      },
      {
        "control_id": "HIPAA-164.312-AuditControls",
        "status": "non_compliant",
        "description": "Audit controls for PHI access tracking",
        "evidence": "pgaudit extension not installed",
        "gap": "No audit logging for SELECT, INSERT, UPDATE, DELETE",
        "remediation": "Enable pgaudit with comprehensive policy"
      }
    ],
    "remediation_roadmap": {
      "phase_1_critical": {
        "duration_days": 3,
        "tasks": [
          {
            "task": "Enable encryption for PII fields",
            "priority": 1,
            "estimated_hours": 16,
            "auto_fix_available": true
          },
          {
            "task": "Remove superuser access",
            "priority": 2,
            "estimated_hours": 4,
            "auto_fix_available": true
          },
          {
            "task": "Enable audit logging (pgaudit)",
            "priority": 3,
            "estimated_hours": 8,
            "auto_fix_available": false
          }
        ]
      },
      "phase_2_high": {
        "duration_days": 5,
        "tasks": [
          {
            "task": "Implement RBAC for all users",
            "priority": 4,
            "estimated_hours": 12,
            "auto_fix_available": true
          },
          {
            "task": "Create data retention policies",
            "priority": 5,
            "estimated_hours": 12,
            "auto_fix_available": false
          }
        ]
      }
    },
    "auto_fix_sql": [
      "-- Phase 1: Critical Fixes",
      "",
      "-- 1. Enable encryption extension",
      "CREATE EXTENSION IF NOT EXISTS pgcrypto;",
      "",
      "-- 2. Encrypt PII columns",
      "ALTER TABLE users ADD COLUMN email_encrypted bytea;",
      "UPDATE users SET email_encrypted = pgp_sym_encrypt(email::text, current_setting('app.encryption_key'));",
      "ALTER TABLE users DROP COLUMN email;",
      "ALTER TABLE users RENAME COLUMN email_encrypted TO email;",
      "",
      "-- 3. Remove superuser access",
      "ALTER ROLE admin NOSUPERUSER;",
      "CREATE ROLE limited_admin;",
      "GRANT CONNECT ON DATABASE production TO limited_admin;",
      "GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA public TO limited_admin;",
      "GRANT limited_admin TO admin;",
      "",
      "-- 4. Restrict analytics user",
      "REVOKE INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public FROM analytics_user;",
      "",
      "-- Phase 2: Manual configuration required",
      "-- Install pgaudit: https://github.com/pgaudit/pgaudit",
      "-- Configure postgresql.conf:",
      "-- shared_preload_libraries = 'pgaudit'",
      "-- pgaudit.log = 'all'",
      "-- Restart PostgreSQL service"
    ],
    "report_download_url": "https://schemasage.com/reports/rpt_2024_01_18_abc123.pdf",
    "report_expires_at": "2024-02-18T10:30:00Z"
  }
}
```

---

## Phase 2.2: Database Health Benchmark

### 2.2.1 Performance Score Calculator

**Endpoint:** `POST /api/monitoring/performance-score`

**Request:**
```json
{
  "database_type": "postgresql",
  "connection_string": "postgresql://user:pass@host:5432/dbname",
  "benchmark_duration_minutes": 60
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "overall_score": 68,
    "health_status": "warning",
    "benchmark_period": {
      "start_time": "2024-01-18T09:00:00Z",
      "end_time": "2024-01-18T10:00:00Z",
      "duration_minutes": 60
    },
    "metrics": {
      "query_performance": {
        "score": 72,
        "status": "good",
        "avg_query_time_ms": 145,
        "p95_query_time_ms": 890,
        "p99_query_time_ms": 2340,
        "slow_queries_count": 47,
        "slow_query_threshold_ms": 1000,
        "queries_per_second": 234,
        "recommendation": "47 slow queries detected - optimize top 10 queries for 35% performance gain"
      },
      "connection_health": {
        "score": 85,
        "status": "excellent",
        "active_connections": 142,
        "max_connections": 200,
        "connection_utilization_percent": 71,
        "idle_connections": 23,
        "idle_in_transaction": 5,
        "waiting_connections": 0,
        "connection_churn_per_minute": 12,
        "recommendation": "Healthy connection pool - consider increasing max_connections to 300 for growth headroom"
      },
      "cpu_usage": {
        "score": 58,
        "status": "warning",
        "avg_cpu_percent": 78,
        "peak_cpu_percent": 94,
        "cpu_threshold_warning": 70,
        "cpu_threshold_critical": 90,
        "cpu_spikes_count": 8,
        "top_cpu_queries": [
          {
            "query": "SELECT * FROM orders WHERE created_at > NOW() - INTERVAL '30 days'",
            "cpu_percent": 23,
            "execution_count": 847,
            "avg_time_ms": 2340
          },
          {
            "query": "SELECT COUNT(*) FROM users",
            "cpu_percent": 15,
            "execution_count": 1250,
            "avg_time_ms": 450
          }
        ],
        "recommendation": "CPU usage high - add indexes on orders.created_at and optimize COUNT queries"
      },
      "memory_usage": {
        "score": 75,
        "status": "good",
        "allocated_memory_gb": 16,
        "used_memory_gb": 11.2,
        "memory_utilization_percent": 70,
        "cache_hit_ratio": 0.94,
        "shared_buffers_hit_ratio": 0.96,
        "buffer_cache_size_gb": 4,
        "recommendation": "Cache hit ratio excellent (94%) - current memory allocation optimal"
      },
      "disk_io": {
        "score": 62,
        "status": "warning",
        "read_iops": 2847,
        "write_iops": 1234,
        "total_iops": 4081,
        "provisioned_iops": 5000,
        "iops_utilization_percent": 82,
        "avg_read_latency_ms": 8.5,
        "avg_write_latency_ms": 12.3,
        "disk_queue_depth": 24,
        "recommendation": "IOPS utilization high (82%) - consider upgrading to 7500 provisioned IOPS"
      },
      "table_bloat": {
        "score": 45,
        "status": "critical",
        "total_database_size_gb": 245,
        "actual_data_size_gb": 187,
        "bloat_size_gb": 58,
        "bloat_percent": 23.7,
        "tables_needing_vacuum": 12,
        "last_vacuum_age_days": 15,
        "recommendation": "CRITICAL: 23.7% bloat detected - run VACUUM FULL on 12 tables to reclaim 58 GB"
      },
      "index_efficiency": {
        "score": 80,
        "status": "good",
        "total_indexes": 87,
        "used_indexes": 72,
        "unused_indexes": 15,
        "missing_indexes": 4,
        "duplicate_indexes": 2,
        "index_scan_ratio": 0.85,
        "index_size_gb": 34,
        "recommendation": "Drop 15 unused indexes to save 8.2 GB - create 4 missing indexes for query optimization"
      },
      "replication_lag": {
        "score": 92,
        "status": "excellent",
        "replicas_count": 2,
        "avg_lag_seconds": 0.8,
        "max_lag_seconds": 2.3,
        "lag_threshold_warning": 5,
        "lag_threshold_critical": 30,
        "replica_status": [
          {
            "replica_id": "replica-1",
            "lag_seconds": 0.5,
            "status": "healthy"
          },
          {
            "replica_id": "replica-2",
            "lag_seconds": 1.1,
            "status": "healthy"
          }
        ],
        "recommendation": "Replication healthy - sub-second lag across all replicas"
      }
    },
    "industry_comparison": {
      "database_type": "postgresql",
      "company_size": "medium",
      "industry_avg_score": 72,
      "percentile": 58,
      "similar_companies": {
        "top_performer_score": 94,
        "median_score": 72,
        "bottom_quartile_score": 48
      },
      "insight": "Your database scores in the 58th percentile - addressing table bloat and CPU issues would move you to top quartile"
    },
    "recommendations_summary": [
      {
        "priority": "critical",
        "category": "table_bloat",
        "title": "Run VACUUM FULL to reclaim 58 GB",
        "impact": "Reclaim 23.7% wasted space, improve query performance by 15-20%",
        "estimated_time_hours": 4,
        "sql": "VACUUM FULL ANALYZE users, orders, products;"
      },
      {
        "priority": "high",
        "category": "cpu_optimization",
        "title": "Add index on orders.created_at",
        "impact": "Reduce CPU usage by 23%, speed up 847 queries/hour",
        "estimated_time_hours": 0.5,
        "sql": "CREATE INDEX idx_orders_created_at ON orders(created_at DESC);"
      },
      {
        "priority": "high",
        "category": "disk_io",
        "title": "Upgrade provisioned IOPS from 5000 to 7500",
        "impact": "Reduce I/O bottleneck, improve write latency by 40%",
        "estimated_cost_increase": 45.00,
        "estimated_time_hours": 0
      },
      {
        "priority": "medium",
        "category": "index_cleanup",
        "title": "Drop 15 unused indexes",
        "impact": "Save 8.2 GB storage, reduce write overhead",
        "estimated_time_hours": 1,
        "sql": "-- Drop unused indexes\nDROP INDEX idx_users_old_column;\nDROP INDEX idx_orders_unused;\n-- ... (13 more)"
      }
    ],
    "score_history": [
      {
        "date": "2024-01-11",
        "score": 72
      },
      {
        "date": "2024-01-14",
        "score": 70
      },
      {
        "date": "2024-01-18",
        "score": 68
      }
    ],
    "trend": "declining",
    "forecast_30_days": {
      "predicted_score": 62,
      "confidence": 0.85,
      "risks": [
        "Table bloat will reach 30% without vacuum",
        "CPU usage will hit 95% average during peak hours",
        "IOPS will max out, causing query timeouts"
      ]
    }
  }
}
```

---

### 2.2.2 Health Timeline Visualization

**Endpoint:** `POST /api/monitoring/health-timeline`

**Request:**
```json
{
  "database_type": "postgresql",
  "connection_string": "postgresql://user:pass@host:5432/dbname",
  "time_range": "7d",
  "metrics": ["cpu", "memory", "connections", "query_performance"]
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "time_range": {
      "start": "2024-01-11T00:00:00Z",
      "end": "2024-01-18T00:00:00Z",
      "granularity": "1h",
      "total_data_points": 168
    },
    "metrics": {
      "cpu_usage": {
        "unit": "percent",
        "threshold_warning": 70,
        "threshold_critical": 90,
        "data_points": [
          {
            "timestamp": "2024-01-11T00:00:00Z",
            "value": 45,
            "status": "normal"
          },
          {
            "timestamp": "2024-01-11T01:00:00Z",
            "value": 52,
            "status": "normal"
          },
          {
            "timestamp": "2024-01-11T09:00:00Z",
            "value": 78,
            "status": "warning"
          },
          {
            "timestamp": "2024-01-11T13:00:00Z",
            "value": 94,
            "status": "critical"
          }
        ],
        "summary": {
          "avg": 68,
          "min": 32,
          "max": 94,
          "p95": 88,
          "threshold_violations": 45
        }
      },
      "memory_usage": {
        "unit": "percent",
        "threshold_warning": 80,
        "threshold_critical": 95,
        "data_points": [
          {
            "timestamp": "2024-01-11T00:00:00Z",
            "value": 62,
            "status": "normal"
          },
          {
            "timestamp": "2024-01-11T01:00:00Z",
            "value": 64,
            "status": "normal"
          },
          {
            "timestamp": "2024-01-11T09:00:00Z",
            "value": 70,
            "status": "normal"
          }
        ],
        "summary": {
          "avg": 68,
          "min": 58,
          "max": 75,
          "p95": 73,
          "threshold_violations": 0
        }
      },
      "active_connections": {
        "unit": "count",
        "max_allowed": 200,
        "threshold_warning": 160,
        "threshold_critical": 190,
        "data_points": [
          {
            "timestamp": "2024-01-11T00:00:00Z",
            "value": 89,
            "status": "normal"
          },
          {
            "timestamp": "2024-01-11T09:00:00Z",
            "value": 165,
            "status": "warning"
          },
          {
            "timestamp": "2024-01-11T13:00:00Z",
            "value": 192,
            "status": "critical"
          }
        ],
        "summary": {
          "avg": 142,
          "min": 78,
          "max": 192,
          "p95": 178,
          "threshold_violations": 12
        }
      },
      "avg_query_time": {
        "unit": "milliseconds",
        "threshold_warning": 500,
        "threshold_critical": 2000,
        "data_points": [
          {
            "timestamp": "2024-01-11T00:00:00Z",
            "value": 123,
            "status": "normal"
          },
          {
            "timestamp": "2024-01-11T09:00:00Z",
            "value": 678,
            "status": "warning"
          },
          {
            "timestamp": "2024-01-11T13:00:00Z",
            "value": 2340,
            "status": "critical"
          }
        ],
        "summary": {
          "avg": 456,
          "min": 98,
          "max": 2340,
          "p95": 1245,
          "threshold_violations": 23
        }
      }
    },
    "incidents": [
      {
        "incident_id": "inc_001",
        "timestamp": "2024-01-11T13:00:00Z",
        "severity": "critical",
        "title": "CPU and Connection Spike During Marketing Campaign",
        "affected_metrics": ["cpu_usage", "active_connections", "avg_query_time"],
        "values": {
          "cpu_usage": 94,
          "active_connections": 192,
          "avg_query_time": 2340
        },
        "duration_minutes": 45,
        "root_cause": "Unindexed query in new email campaign feature",
        "resolution": "Added index on users.subscription_status - performance restored in 5 minutes"
      },
      {
        "incident_id": "inc_002",
        "timestamp": "2024-01-14T18:00:00Z",
        "severity": "warning",
        "title": "Evening CPU Spike - Long-Running Report Query",
        "affected_metrics": ["cpu_usage"],
        "values": {
          "cpu_usage": 85
        },
        "duration_minutes": 120,
        "root_cause": "Weekly analytics report running on production database",
        "resolution": "Moved report to read-replica"
      }
    ],
    "anomalies": [
      {
        "timestamp": "2024-01-16T04:00:00Z",
        "metric": "active_connections",
        "expected_value": 85,
        "actual_value": 145,
        "deviation_percent": 70,
        "severity": "medium",
        "possible_cause": "Overnight batch job connection leak"
      }
    ],
    "patterns": {
      "daily_peak_hours": ["09:00-10:00", "13:00-14:00", "18:00-19:00"],
      "weekly_peak_day": "Wednesday",
      "monthly_trend": "CPU usage increasing 5% month-over-month",
      "seasonal_observations": [
        "CPU spikes correlate with marketing email sends (Tuesdays 13:00)",
        "Connection count drops 40% on weekends",
        "Query performance degrades 15% between vacuum cycles (every 14 days)"
      ]
    }
  }
}
```

---

*Continued in PHASE_2_BACKEND_API_SPEC_PART_2.md...*
