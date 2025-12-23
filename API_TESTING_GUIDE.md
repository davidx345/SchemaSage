# API Testing Guide - New Features

## Quick Test Commands

### 1. Deployment Analysis Endpoints

#### Test Performance Prediction
```bash
curl -X POST "https://schemasage-api-gateway-2da67d920b07.herokuapp.com/api/deployment/predict-performance" \
  -H "Content-Type: application/json" \
  -d '{
    "database_engine": "postgresql",
    "expected_operations_per_second": 5000,
    "average_query_complexity": "medium",
    "concurrent_connections": 100,
    "data_size_gb": 250,
    "cloud_provider": "aws"
  }'
```

#### Test Reserved Instance Advice
```bash
curl -X POST "https://schemasage-api-gateway-2da67d920b07.herokuapp.com/api/deployment/reserved-instance-advice" \
  -H "Content-Type: application/json" \
  -d '{
    "cloud_provider": "aws",
    "database_engine": "postgresql",
    "vcpu_count": 4,
    "memory_gb": 32,
    "storage_gb": 500,
    "usage_pattern": "steady",
    "commitment_period": 24
  }'
```

#### Test Multi-Region Cost Analysis
```bash
curl -X POST "https://schemasage-api-gateway-2da67d920b07.herokuapp.com/api/deployment/multi-region-cost" \
  -H "Content-Type: application/json" \
  -d '{
    "database_engine": "postgresql",
    "primary_region": "us-east-1",
    "replica_regions": ["us-west-2", "eu-west-1"],
    "data_size_gb": 500,
    "cross_region_queries_per_day": 50000,
    "replication_lag_tolerance_seconds": 5
  }'
```

#### Test Disaster Recovery Planning
```bash
curl -X POST "https://schemasage-api-gateway-2da67d920b07.herokuapp.com/api/deployment/disaster-recovery-plan" \
  -H "Content-Type: application/json" \
  -d '{
    "database_engine": "postgresql",
    "data_size_gb": 500,
    "recovery_time_objective_minutes": 60,
    "recovery_point_objective_minutes": 15,
    "cloud_provider": "aws",
    "current_region": "us-east-1"
  }'
```

#### Test Cost Comparison
```bash
curl -X POST "https://schemasage-api-gateway-2da67d920b07.herokuapp.com/api/deployment/compare-costs" \
  -H "Content-Type: application/json" \
  -d '{
    "database_engine": "postgresql",
    "vcpu_count": 8,
    "memory_gb": 64,
    "storage_gb": 1000,
    "iops_required": 10000,
    "backup_retention_days": 7,
    "high_availability": true,
    "target_providers": ["aws", "gcp", "azure"]
  }'
```

---

### 2. Data Lineage Endpoints

#### Test Column Lineage
```bash
curl "https://schemasage-api-gateway-2da67d920b07.herokuapp.com/api/lineage/column/users/user_id?schema=public&direction=both&depth=3"
```

#### Test Table Lineage
```bash
curl "https://schemasage-api-gateway-2da67d920b07.herokuapp.com/api/lineage/table/orders?schema=public&include_columns=true&depth=2"
```

#### Test Lineage Graph (for visualization)
```bash
curl "https://schemasage-api-gateway-2da67d920b07.herokuapp.com/api/lineage/graph?schema=public&max_depth=3&include_external=true"
```

---

### 3. Incident Management Endpoints

#### Create Incident
```bash
curl -X POST "https://schemasage-api-gateway-2da67d920b07.herokuapp.com/api/incidents/create" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Database Connection Pool Exhaustion",
    "description": "Production database experiencing connection timeouts",
    "severity": "high",
    "affected_systems": ["production-db-1", "api-server"],
    "affected_queries": ["user_search", "checkout_process"],
    "tags": ["performance", "connections"]
  }'
```

#### List Incidents
```bash
curl "https://schemasage-api-gateway-2da67d920b07.herokuapp.com/api/incidents/list?status_filter=open&page=1&limit=10"
```

#### Correlate Events
```bash
curl -X POST "https://schemasage-api-gateway-2da67d920b07.herokuapp.com/api/incidents/correlate-events" \
  -H "Content-Type: application/json" \
  -d '{
    "incident_id": "incident-123",
    "time_window_hours": 24,
    "event_sources": ["deployments", "migrations", "config_changes"]
  }'
```

#### Analyze Root Cause
```bash
curl -X POST "https://schemasage-api-gateway-2da67d920b07.herokuapp.com/api/incidents/analyze-root-cause" \
  -H "Content-Type: application/json" \
  -d '{
    "incident_id": "incident-123",
    "analysis_depth": "comprehensive",
    "include_historical_patterns": true
  }'
```

#### Find Similar Incidents
```bash
curl "https://schemasage-api-gateway-2da67d920b07.herokuapp.com/api/incidents/similar/incident-123"
```

#### Generate Fix
```bash
curl -X POST "https://schemasage-api-gateway-2da67d920b07.herokuapp.com/api/incidents/generate-fix" \
  -H "Content-Type: application/json" \
  -d '{
    "incident_id": "incident-123",
    "fix_preferences": {
      "prefer_automated": true,
      "risk_tolerance": "moderate"
    }
  }'
```

#### Get Prevention Checklist
```bash
curl "https://schemasage-api-gateway-2da67d920b07.herokuapp.com/api/incidents/prevention-checklist/incident-123"
```

---

### 4. Anonymization Endpoints

#### Scan for PII
```bash
curl -X POST "https://schemasage-api-gateway-2da67d920b07.herokuapp.com/api/anonymization/scan-pii" \
  -H "Content-Type: application/json" \
  -d '{
    "connection_string": "postgresql://user:pass@host:5432/dbname",
    "scan_options": {
      "confidence_threshold": 0.8,
      "include_sample_data": true
    }
  }'
```

#### Create Anonymization Rules
```bash
curl -X POST "https://schemasage-api-gateway-2da67d920b07.herokuapp.com/api/anonymization/create-rules" \
  -H "Content-Type: application/json" \
  -d '{
    "scan_id": "scan-123",
    "rules": [
      {
        "table": "users",
        "column": "email",
        "strategy": "fake_data",
        "options": {}
      },
      {
        "table": "users",
        "column": "ssn",
        "strategy": "masking",
        "options": {"pattern": "***-**-{last4}"}
      }
    ]
  }'
```

#### Apply Masking
```bash
curl -X POST "https://schemasage-api-gateway-2da67d920b07.herokuapp.com/api/anonymization/apply-masking" \
  -H "Content-Type: application/json" \
  -d '{
    "rule_set_id": "ruleset-123",
    "target_connection": "postgresql://user:pass@host:5432/target_db",
    "execution_options": {
      "dry_run": false,
      "batch_size": 1000,
      "create_backup": true
    }
  }'
```

#### Create Data Subset
```bash
curl -X POST "https://schemasage-api-gateway-2da67d920b07.herokuapp.com/api/anonymization/create-subset" \
  -H "Content-Type: application/json" \
  -d '{
    "source_connection": "postgresql://user:pass@host:5432/prod",
    "target_connection": "postgresql://user:pass@host:5432/staging",
    "subsetting_strategy": "stratified_sampling",
    "options": {
      "sample_percentage": 10,
      "preserve_referential_integrity": true
    }
  }'
```

#### Validate Compliance
```bash
curl -X POST "https://schemasage-api-gateway-2da67d920b07.herokuapp.com/api/anonymization/validate-compliance" \
  -H "Content-Type: application/json" \
  -d '{
    "connection_string": "postgresql://user:pass@host:5432/dbname",
    "compliance_frameworks": ["GDPR", "CCPA", "HIPAA"]
  }'
```

---

## Health Check Endpoints

```bash
# Database Migration Service (includes deployment analysis)
curl https://schemasage-database-migration-dfc50cf95a69.herokuapp.com/health

# Deployment Analysis specific health
curl https://schemasage-database-migration-dfc50cf95a69.herokuapp.com/deployment/health

# Schema Detection Service (includes lineage, incidents, anonymization)
curl https://schemasage-schema-detection-0cc19b546c3c.herokuapp.com/health

# Lineage specific health
curl https://schemasage-schema-detection-0cc19b546c3c.herokuapp.com/lineage/health

# API Gateway
curl https://schemasage-api-gateway-2da67d920b07.herokuapp.com/health
```

---

## Frontend Integration Testing

### From Frontend `api.ts`

#### Deployment API
```typescript
// In your frontend code
import { deploymentApi } from '@/lib/api';

// Test performance prediction
const result = await deploymentApi.predictPerformance({
  database_engine: 'postgresql',
  expected_operations_per_second: 5000,
  average_query_complexity: 'medium',
  concurrent_connections: 100,
  data_size_gb: 250,
  cloud_provider: 'aws'
});
console.log('Performance prediction:', result);
```

#### Lineage API
```typescript
import { lineageApi } from '@/lib/api';

// Test column lineage
const columnLineage = await lineageApi.getColumnLineage('users', 'user_id', {
  schema: 'public',
  direction: 'both',
  depth: 3
});
console.log('Column lineage:', columnLineage);

// Test table lineage
const tableLineage = await lineageApi.getTableLineage('orders', {
  schema: 'public',
  include_columns: true,
  depth: 2
});
console.log('Table lineage:', tableLineage);

// Test lineage graph
const graph = await lineageApi.getLineageGraph({
  schema: 'public',
  max_depth: 3,
  include_external: true
});
console.log('Lineage graph:', graph);
```

#### Incidents API
```typescript
import { incidentsApi } from '@/lib/api';

// Create incident
const incident = await incidentsApi.create({
  title: 'Database Timeout',
  description: 'Users experiencing connection timeouts',
  severity: 'high',
  affected_systems: ['db-prod-1'],
  affected_queries: ['user_search'],
  tags: ['performance']
});

// Correlate events
const correlation = await incidentsApi.correlateEvents({
  incident_id: incident.incident_id,
  time_window_hours: 24,
  event_sources: ['deployments', 'migrations']
});
```

#### Anonymization API
```typescript
import { anonymizationApi } from '@/lib/api';

// Scan for PII
const scanResult = await anonymizationApi.scanPII({
  connection_string: 'postgresql://...',
  scan_options: {
    confidence_threshold: 0.8,
    include_sample_data: true
  }
});

// Create anonymization rules
const ruleset = await anonymizationApi.createRules({
  scan_id: scanResult.scan_id,
  rules: [
    {
      table: 'users',
      column: 'email',
      strategy: 'fake_data',
      options: {}
    }
  ]
});
```

---

## Expected Response Structures

### Deployment Analysis Response Example
```json
{
  "predicted_metrics": {
    "average_latency_ms": 12.5,
    "p95_latency_ms": 18.75,
    "p99_latency_ms": 25.0,
    "max_throughput_ops": 8000,
    "expected_cpu_utilization_percent": 62.5
  },
  "recommendations": {
    "vcpu_count": 4,
    "memory_gb": 32,
    "storage_type": "SSD",
    "needs_scaling": false
  },
  "cost_estimates": {
    "monthly_cost_usd": 456.00,
    "annual_cost_usd": 5472.00
  }
}
```

### Lineage Response Example
```json
{
  "source_column": {
    "table": "users",
    "column": "user_id",
    "schema": "public"
  },
  "upstream_lineage": [...],
  "downstream_lineage": [
    {
      "node": {
        "column_name": "customer_id",
        "table_name": "orders",
        "data_type": "integer"
      },
      "path_length": 1,
      "transformation_chain": ["JOIN orders ON users.id = orders.customer_id"]
    }
  ],
  "impact_analysis": {
    "affected_tables": 5,
    "affected_columns": 12
  }
}
```

---

## Troubleshooting

### If endpoints return 404
1. Check service is running: `curl [SERVICE_URL]/health`
2. Verify API Gateway routing: `curl https://schemasage-api-gateway-2da67d920b07.herokuapp.com/`
3. Check service logs on Heroku

### If endpoints return 500
1. Check service logs for errors
2. Verify request payload matches expected schema
3. Check database connectivity if applicable

### If endpoints timeout
1. Increase client timeout (default 30s may be insufficient)
2. Check service health and resource usage
3. Consider caching for expensive operations
