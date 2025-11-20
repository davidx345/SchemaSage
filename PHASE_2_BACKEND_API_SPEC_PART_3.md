# Phase 2: Backend API Specification - Part 3

**Covers:** Phase 2.4 Cost Anomaly Detector

---

## Phase 2.4: Cost Anomaly Detector

### 2.4.1 Cost Monitoring & Tracking

**Endpoint:** `POST /api/monitoring/cost-tracking`

**Request:**
```json
{
  "provider": "aws",
  "database_type": "postgresql",
  "instance_id": "db-prod-001",
  "time_range": "24h",
  "granularity": "hourly"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "time_range": {
      "start": "2024-01-17T10:00:00Z",
      "end": "2024-01-18T10:00:00Z",
      "granularity": "hourly"
    },
    "hourly_costs": [
      {
        "hour": "2024-01-18T00:00:00Z",
        "actual_cost": 23.40,
        "baseline_cost": 24.50,
        "variance_percent": -4.5,
        "status": "normal",
        "breakdown": {
          "compute": 15.20,
          "storage": 3.50,
          "iops": 2.80,
          "backup": 1.20,
          "network": 0.70
        }
      },
      {
        "hour": "2024-01-18T04:00:00Z",
        "actual_cost": 45.80,
        "baseline_cost": 12.00,
        "variance_percent": 281.7,
        "status": "critical_anomaly",
        "breakdown": {
          "compute": 38.50,
          "storage": 3.50,
          "iops": 2.30,
          "backup": 1.00,
          "network": 0.50
        },
        "anomaly_details": {
          "z_score": 4.2,
          "confidence": 0.9999,
          "primary_driver": "compute_spike",
          "contributing_services": ["RDS PostgreSQL"]
        }
      },
      {
        "hour": "2024-01-18T13:00:00Z",
        "actual_cost": 72.50,
        "baseline_cost": 24.00,
        "variance_percent": 202.1,
        "status": "critical_anomaly",
        "breakdown": {
          "compute": 58.30,
          "storage": 3.80,
          "iops": 6.40,
          "backup": 2.50,
          "network": 1.50
        },
        "anomaly_details": {
          "z_score": 4.8,
          "confidence": 0.99997,
          "primary_driver": "compute_and_iops_spike",
          "contributing_services": ["RDS PostgreSQL", "Data Transfer"]
        }
      }
    ],
    "service_breakdown": [
      {
        "service": "RDS PostgreSQL",
        "current_cost": 245.80,
        "baseline_cost": 180.00,
        "variance_percent": 36.6,
        "status": "warning",
        "top_cost_drivers": [
          {"component": "Compute", "cost": 165.40, "percent": 67.3},
          {"component": "Storage", "cost": 42.30, "percent": 17.2},
          {"component": "IOPS", "cost": 28.10, "percent": 11.4}
        ]
      },
      {
        "service": "Aurora Serverless",
        "current_cost": 156.40,
        "baseline_cost": 150.00,
        "variance_percent": 4.3,
        "status": "normal"
      },
      {
        "service": "DynamoDB",
        "current_cost": 89.20,
        "baseline_cost": 95.00,
        "variance_percent": -6.1,
        "status": "normal"
      },
      {
        "service": "ElastiCache",
        "current_cost": 67.30,
        "baseline_cost": 65.00,
        "variance_percent": 3.5,
        "status": "normal"
      },
      {
        "service": "Data Transfer",
        "current_cost": 45.60,
        "baseline_cost": 30.00,
        "variance_percent": 52.0,
        "status": "warning"
      }
    ],
    "summary": {
      "current_cost_24h": 604.30,
      "baseline_cost_24h": 424.50,
      "total_variance": 179.80,
      "variance_percent": 42.4,
      "anomalies_detected": 4,
      "critical_anomalies": 2,
      "high_anomalies": 2,
      "cost_trend": "increasing"
    },
    "optimization_insights": [
      {
        "priority": "high",
        "category": "rightsizing",
        "title": "RDS Instance Over-Provisioned During Off-Peak",
        "description": "04:00-05:00 compute spike suggests batch job - consider serverless or scheduled scaling",
        "potential_monthly_savings": 845.00,
        "implementation_effort": "medium"
      },
      {
        "priority": "high",
        "category": "query_optimization",
        "title": "Optimize Queries Causing IOPS Spike at 13:00",
        "description": "Midday traffic spike - add indexes or cache layer",
        "potential_monthly_savings": 423.00,
        "implementation_effort": "low"
      },
      {
        "priority": "medium",
        "category": "data_transfer",
        "title": "Reduce Cross-AZ Data Transfer",
        "description": "52% increase in data transfer costs - review application architecture",
        "potential_monthly_savings": 312.00,
        "implementation_effort": "high"
      },
      {
        "priority": "medium",
        "category": "reserved_capacity",
        "title": "Purchase Reserved Instances",
        "description": "Aurora Serverless baseline stable - convert to provisioned + RI for 40% savings",
        "potential_monthly_savings": 267.00,
        "implementation_effort": "low"
      }
    ],
    "projected_monthly_cost": {
      "current_trajectory": 18129.00,
      "with_optimizations": 16282.00,
      "potential_savings": 1847.00
    }
  }
}
```

---

### 2.4.2 Anomaly Alert System

**Endpoint:** `POST /api/monitoring/anomaly-alerts`

**Request:**
```json
{
  "provider": "aws",
  "database_type": "postgresql",
  "instance_id": "db-prod-001",
  "detection_config": {
    "baseline_window_days": 30,
    "detection_interval_minutes": 15,
    "min_data_points": 100,
    "seasonal_adjustment": true
  },
  "notification_channels": ["email", "slack", "pagerduty"]
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "anomalies": [
      {
        "anomaly_id": "anom_001",
        "detected_at": "2024-01-18T13:00:00Z",
        "severity": "critical",
        "status": "active",
        "metric": "Hourly Database Cost",
        "actual_value": 72.50,
        "expected_value": 24.00,
        "variance_percent": 202.1,
        "z_score": 4.8,
        "confidence_level": 0.99997,
        "confidence_percent": 99.997,
        "duration_minutes": 60,
        "cost_impact": 48.50,
        "root_cause_analysis": {
          "primary_service": "RDS PostgreSQL",
          "primary_metric": "Compute Cost",
          "contributing_factors": [
            "Unusual query pattern detected",
            "6x increase in IOPS",
            "Connection count spike to 192 (from avg 142)"
          ],
          "likely_trigger": "Marketing email campaign launched at 12:45 PM"
        },
        "recommendation": {
          "action": "Investigate new queries introduced in recent deployment",
          "priority": "immediate",
          "steps": [
            "Check slow query log for queries executed at 13:00",
            "Review application deployment logs from 12:00-13:00",
            "Add missing indexes identified in query analysis",
            "Consider enabling Aurora Auto Scaling for traffic spikes"
          ]
        },
        "related_anomalies": ["anom_002"]
      },
      {
        "anomaly_id": "anom_002",
        "detected_at": "2024-01-18T14:00:00Z",
        "severity": "high",
        "status": "active",
        "metric": "Hourly Database Cost",
        "actual_value": 56.30,
        "expected_value": 24.00,
        "variance_percent": 134.6,
        "z_score": 3.5,
        "confidence_level": 0.9995,
        "confidence_percent": 99.95,
        "duration_minutes": 60,
        "cost_impact": 32.30,
        "root_cause_analysis": {
          "primary_service": "RDS PostgreSQL",
          "likely_trigger": "Sustained elevation following 13:00 spike"
        },
        "recommendation": {
          "action": "Monitor for resolution - may be residual from previous spike",
          "priority": "high"
        }
      },
      {
        "anomaly_id": "anom_003",
        "detected_at": "2024-01-18T04:00:00Z",
        "severity": "critical",
        "status": "investigating",
        "metric": "Hourly Database Cost",
        "actual_value": 45.80,
        "expected_value": 12.00,
        "variance_percent": 281.7,
        "z_score": 4.2,
        "confidence_level": 0.9999,
        "confidence_percent": 99.99,
        "duration_minutes": 60,
        "cost_impact": 33.80,
        "root_cause_analysis": {
          "primary_service": "RDS PostgreSQL",
          "likely_trigger": "Overnight batch job or data pipeline"
        },
        "recommendation": {
          "action": "Review batch job schedule and optimize queries",
          "priority": "high",
          "steps": [
            "Move batch jobs to read replica",
            "Consider serverless Aurora for variable workloads",
            "Schedule batch jobs during off-peak hours (02:00-04:00)"
          ]
        }
      },
      {
        "anomaly_id": "anom_004",
        "detected_at": "2024-01-18T05:00:00Z",
        "severity": "high",
        "status": "resolved",
        "metric": "Hourly Database Cost",
        "actual_value": 38.20,
        "expected_value": 12.00,
        "variance_percent": 218.3,
        "z_score": 3.2,
        "confidence_level": 0.9993,
        "confidence_percent": 99.93,
        "duration_minutes": 60,
        "cost_impact": 26.20,
        "resolved_at": "2024-01-18T06:00:00Z",
        "resolution": "Batch job completed, costs returned to baseline"
      },
      {
        "anomaly_id": "anom_005",
        "detected_at": "2024-01-18T19:00:00Z",
        "severity": "medium",
        "status": "active",
        "metric": "Data Transfer Cost",
        "actual_value": 5.50,
        "expected_value": 2.00,
        "variance_percent": 175.0,
        "z_score": 2.3,
        "confidence_level": 0.9893,
        "confidence_percent": 98.93,
        "cost_impact": 3.50,
        "recommendation": {
          "action": "Review cross-region or cross-AZ data transfer patterns"
        }
      },
      {
        "anomaly_id": "anom_006",
        "detected_at": "2024-01-18T09:00:00Z",
        "severity": "low",
        "status": "ignored",
        "metric": "Aurora ACU Usage",
        "actual_value": 4.40,
        "expected_value": 2.00,
        "variance_percent": 120.0,
        "z_score": 1.8,
        "cost_impact": 2.40,
        "ignored_reason": "Expected traffic spike during business hours"
      },
      {
        "anomaly_id": "anom_007",
        "detected_at": "2024-01-18T22:00:00Z",
        "severity": "info",
        "status": "active",
        "metric": "DynamoDB Read Capacity",
        "actual_value": 1.50,
        "expected_value": 1.00,
        "variance_percent": 50.0,
        "z_score": 1.2,
        "cost_impact": 0.50,
        "recommendation": {
          "action": "Monitor - within acceptable variance"
        }
      }
    ],
    "notification_channels": [
      {
        "channel": "email",
        "enabled": true,
        "recipients": ["devops@company.com", "finops@company.com"],
        "threshold": "high",
        "last_triggered": "2024-01-18T13:05:00Z",
        "status": "healthy"
      },
      {
        "channel": "slack",
        "enabled": true,
        "webhook": "https://hooks.slack.com/services/xxx/yyy/zzz",
        "channel_name": "#database-alerts",
        "threshold": "medium",
        "last_triggered": "2024-01-18T19:05:00Z",
        "status": "healthy"
      },
      {
        "channel": "pagerduty",
        "enabled": true,
        "integration_key": "xxx",
        "threshold": "critical",
        "last_triggered": "2024-01-18T13:05:00Z",
        "status": "healthy"
      },
      {
        "channel": "sms",
        "enabled": false,
        "phone_numbers": ["+1-555-0100"],
        "threshold": "critical",
        "status": "disabled"
      }
    ],
    "detection_config": {
      "baseline_window": "30 days rolling average",
      "detection_interval": "Every 15 minutes",
      "min_data_points": 100,
      "seasonal_adjustment": true,
      "thresholds": {
        "critical": {
          "z_score": 4.0,
          "confidence": 0.9999,
          "description": "99.99% confidence - immediate action required"
        },
        "high": {
          "z_score": 3.0,
          "confidence": 0.9987,
          "description": "99.87% confidence - investigate soon"
        },
        "medium": {
          "z_score": 2.0,
          "confidence": 0.9772,
          "description": "97.72% confidence - monitor closely"
        },
        "low": {
          "z_score": 1.5,
          "confidence": 0.8664,
          "description": "86.64% confidence - informational"
        }
      }
    },
    "summary": {
      "total_anomalies": 7,
      "active_anomalies": 5,
      "critical_count": 2,
      "high_count": 2,
      "medium_count": 1,
      "low_count": 1,
      "info_count": 1,
      "total_cost_impact_24h": 88.30,
      "avg_z_score": 3.6,
      "last_detection_run": "2024-01-18T22:15:00Z"
    }
  }
}
```

---

### 2.4.3 Cost Anomaly Graph & Pattern Analysis

**Endpoint:** `POST /api/monitoring/cost-anomaly-graph`

**Request:**
```json
{
  "provider": "aws",
  "database_type": "postgresql",
  "instance_id": "db-prod-001",
  "time_range": "24h",
  "include_pattern_analysis": true
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "time_range": {
      "start": "2024-01-18T00:00:00Z",
      "end": "2024-01-18T23:00:00Z",
      "data_points": 24
    },
    "data_points": [
      {
        "timestamp": "2024-01-18T00:00:00Z",
        "hour": "00:00",
        "cost": 23.40,
        "baseline": 24.50,
        "is_anomaly": false,
        "status": "normal"
      },
      {
        "timestamp": "2024-01-18T04:00:00Z",
        "hour": "04:00",
        "cost": 45.80,
        "baseline": 12.00,
        "is_anomaly": true,
        "severity": "critical",
        "z_score": 4.2,
        "anomaly_id": "anom_003"
      },
      {
        "timestamp": "2024-01-18T13:00:00Z",
        "hour": "13:00",
        "cost": 72.50,
        "baseline": 24.00,
        "is_anomaly": true,
        "severity": "critical",
        "z_score": 4.8,
        "anomaly_id": "anom_001"
      },
      {
        "timestamp": "2024-01-18T14:00:00Z",
        "hour": "14:00",
        "cost": 56.30,
        "baseline": 24.00,
        "is_anomaly": true,
        "severity": "high",
        "z_score": 3.5,
        "anomaly_id": "anom_002"
      },
      {
        "timestamp": "2024-01-18T23:00:00Z",
        "hour": "23:00",
        "cost": 22.80,
        "baseline": 20.00,
        "is_anomaly": false,
        "status": "normal"
      }
    ],
    "thresholds": {
      "critical": 75.54,
      "high": 50.36,
      "medium": 37.77,
      "avg_cost": 25.18,
      "calculation_basis": "300%, 200%, 150% of 30-day average"
    },
    "statistics": {
      "avg_cost_per_hour": 25.18,
      "max_cost": 72.50,
      "min_cost": 12.30,
      "total_cost_24h": 604.32,
      "anomaly_count": 4,
      "critical_anomaly_count": 2,
      "high_anomaly_count": 2,
      "normal_hours": 20,
      "anomaly_hours": 4
    },
    "pattern_analysis": {
      "detected_patterns": [
        {
          "pattern_type": "early_morning_spike",
          "description": "Cost spike between 04:00-05:00 (overnight batch jobs)",
          "frequency": "daily",
          "avg_cost_impact": 30.00,
          "recommendation": "Schedule batch jobs during 02:00-04:00 window when costs are lowest",
          "affected_hours": ["04:00", "05:00"],
          "total_excess_cost": 60.00
        },
        {
          "pattern_type": "midday_critical_event",
          "description": "Critical spike at 13:00-14:00 (marketing campaigns or user traffic)",
          "frequency": "sporadic",
          "avg_cost_impact": 40.40,
          "recommendation": "Implement auto-scaling or add read replicas for traffic bursts",
          "affected_hours": ["13:00", "14:00"],
          "total_excess_cost": 80.80
        },
        {
          "pattern_type": "service_concentration",
          "description": "100% of anomalies originate from RDS PostgreSQL service",
          "recommendation": "Focus optimization efforts on RDS queries and instance sizing",
          "affected_service": "RDS PostgreSQL"
        }
      ],
      "cost_impact_summary": {
        "total_excess_cost_24h": 140.80,
        "daily_avg": 140.80,
        "projected_monthly_excess": 4224.00,
        "top_contributing_pattern": "midday_critical_event",
        "top_pattern_contribution_percent": 57.4
      },
      "time_of_day_analysis": {
        "peak_hours": ["13:00", "14:00"],
        "off_peak_hours": ["00:00", "01:00", "02:00", "03:00"],
        "highest_variance_hours": ["04:00", "13:00"],
        "most_stable_hours": ["00:00", "01:00", "23:00"]
      },
      "day_of_week_patterns": {
        "pattern": "Weekday traffic 2.5x higher than weekends",
        "recommendation": "Consider scheduled scaling: scale down Sat-Sun, scale up Mon-Fri"
      }
    },
    "cost_breakdown_by_hour": [
      {
        "hour": "13:00",
        "total_cost": 72.50,
        "services": {
          "compute": 58.30,
          "storage": 3.80,
          "iops": 6.40,
          "backup": 2.50,
          "network": 1.50
        }
      }
    ],
    "optimization_opportunities": [
      {
        "opportunity": "Move batch jobs to read replica",
        "estimated_monthly_savings": 1800.00,
        "affected_pattern": "early_morning_spike"
      },
      {
        "opportunity": "Enable Aurora Auto Scaling for traffic spikes",
        "estimated_monthly_savings": 2424.00,
        "affected_pattern": "midday_critical_event"
      },
      {
        "opportunity": "Add missing indexes on frequently queried tables",
        "estimated_monthly_savings": 423.00,
        "affected_pattern": "service_concentration"
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
    "code": "INSUFFICIENT_DATA",
    "message": "Anomaly detection requires minimum 7 days of historical data",
    "details": {
      "current_data_points": 48,
      "required_data_points": 168
    }
  }
}
```

### Rate Limiting
- **Cost Tracking:** 100 requests/hour per instance
- **Anomaly Detection:** 50 requests/hour per instance  
- **Pattern Analysis:** 20 requests/hour per instance

### Caching Strategy
- Baseline calculations: Cache for 24 hours
- Anomaly detection results: Cache for 15 minutes
- Pattern analysis: Cache for 1 hour

---

## Backend Implementation Priority

### Phase 2.4 - Priority 1 (Week 1):
1. **Cost Tracking API** (2.4.1) - Real-time cost monitoring
2. **Anomaly Detection Engine** - Z-score calculation, threshold evaluation

### Phase 2.4 - Priority 2 (Week 2):
3. **Anomaly Alert System** (2.4.2) - Multi-channel notifications
4. **Pattern Analysis** (2.4.3) - Time-series pattern detection

### Phase 2.4 - Priority 3 (Week 3):
5. **Optimization Recommendations** - ML-based cost optimization
6. **Historical Trend Analysis** - Long-term cost forecasting

---

## Testing Recommendations

### API Testing Checklist:
- [ ] Z-score calculation accuracy (±0.01 tolerance)
- [ ] Anomaly detection with 30-day rolling baseline
- [ ] Notification channel integration (Email, Slack, PagerDuty)
- [ ] Pattern recognition for daily/weekly cycles
- [ ] Cost breakdown aggregation by service
- [ ] Threshold violations trigger alerts correctly
- [ ] Historical data retention (90+ days)
- [ ] Real-time vs batch processing modes
- [ ] Multi-cloud provider support (AWS, GCP, Azure)

### Example Integration Test:
```typescript
test('Anomaly detection identifies cost spike', async () => {
  const response = await api.post('/api/monitoring/anomaly-alerts', {
    provider: 'aws',
    instance_id: 'db-test-001',
    detection_config: {
      baseline_window_days: 30,
      detection_interval_minutes: 15
    }
  });
  
  expect(response.success).toBe(true);
  expect(response.data.anomalies.length).toBeGreaterThan(0);
  
  const criticalAnomaly = response.data.anomalies.find(a => a.severity === 'critical');
  expect(criticalAnomaly.z_score).toBeGreaterThan(4.0);
  expect(criticalAnomaly.confidence_level).toBeGreaterThan(0.9999);
});
```

---

## Summary - Complete Phase 2 Backend Spec

### Total Phase 2 Endpoints:
- **Part 1:** Phase 2.1 (3 endpoints) + Phase 2.2 (2 endpoints) = 5 endpoints
- **Part 2:** Phase 2.2 (1 endpoint) + Phase 2.3 (4 endpoints) = 5 endpoints  
- **Part 3:** Phase 2.4 (3 endpoints) = 3 endpoints

**Grand Total: 13 Backend API Endpoints**

### Estimated Development Timeline:
- Phase 2.1 (Compliance): 4-5 days
- Phase 2.2 (Health Benchmark): 3-4 days
- Phase 2.3 (Schema Debt): 4-5 days
- Phase 2.4 (Cost Anomaly): 5-6 days

**Total Backend Development Time: 16-20 days**

### Key Technologies Required:
- Statistical analysis libraries (Z-score, confidence intervals)
- Time-series databases (InfluxDB, TimescaleDB)
- Real-time alerting (PagerDuty API, Slack webhooks)
- Pattern recognition (ML models for anomaly detection)
- Cost API integrations (AWS Cost Explorer, GCP Billing, Azure Cost Management)

All frontend components from Phase 2 are complete and ready for backend integration. Replace TODO comments with actual API calls once endpoints are deployed.
