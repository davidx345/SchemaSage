"""
Anomaly Detection Engine.
Detects cost anomalies, spikes, and unusual patterns using statistical methods.
"""
from typing import List, Dict, Any
from datetime import datetime, timedelta
from uuid import uuid4
import statistics

from models.anomaly_models import (
    AnomalyDetectionData, Anomaly, AnomalyType, Severity, ResourceType
)

class AnomalyDetector:
    """
    Detects cost anomalies using statistical analysis and pattern recognition.
    """
    
    def detect(
        self,
        cost_data: List[Dict[str, Any]],
        resource_type: ResourceType = None,
        sensitivity: float = 2.0,
        lookback_days: int = 30
    ) -> AnomalyDetectionData:
        """
        Detects cost anomalies in historical data.
        """
        # Simulate anomaly detection with realistic examples
        anomalies = self._generate_simulated_anomalies(sensitivity, resource_type)
        
        # Calculate statistics
        critical_count = len([a for a in anomalies if a.severity == Severity.CRITICAL])
        high_count = len([a for a in anomalies if a.severity == Severity.HIGH])
        total_wasted_cost = sum(a.estimated_waste or 0 for a in anomalies)
        
        detection_summary = {
            "analysis_period_days": lookback_days,
            "sensitivity_level": sensitivity,
            "anomalies_per_day": round(len(anomalies) / lookback_days, 2),
            "most_common_type": self._get_most_common_type(anomalies),
            "resource_breakdown": self._get_resource_breakdown(anomalies)
        }
        
        return AnomalyDetectionData(
            anomalies=anomalies,
            total_anomalies=len(anomalies),
            critical_count=critical_count,
            high_count=high_count,
            total_wasted_cost=total_wasted_cost,
            detection_summary=detection_summary
        )
    
    def _generate_simulated_anomalies(
        self,
        sensitivity: float,
        resource_type: ResourceType = None
    ) -> List[Anomaly]:
        """Generates simulated anomalies based on sensitivity."""
        anomalies = []
        now = datetime.now()
        
        # Critical: Budget Overrun
        anomalies.append(Anomaly(
            anomaly_id=f"anom_{str(uuid4())[:8]}",
            anomaly_type=AnomalyType.BUDGET_OVERRUN,
            severity=Severity.CRITICAL,
            timestamp=now - timedelta(days=2),
            expected_cost=5000.0,
            actual_cost=12500.0,
            deviation_percentage=150.0,
            affected_resources=["production-db-cluster", "api-gateway"],
            description="Critical budget overrun: 150% above expected monthly spend",
            recommendation="Review autoscaling settings and consider reserved instances",
            estimated_waste=7500.0
        ))
        
        # High: Cost Spike
        anomalies.append(Anomaly(
            anomaly_id=f"anom_{str(uuid4())[:8]}",
            anomaly_type=AnomalyType.SPIKE,
            severity=Severity.HIGH,
            timestamp=now - timedelta(days=5),
            expected_cost=200.0,
            actual_cost=850.0,
            deviation_percentage=325.0,
            affected_resources=["compute-instance-1", "compute-instance-2"],
            description="Sudden cost spike: 325% increase in compute costs",
            recommendation="Check for runaway processes or unauthorized resource provisioning",
            estimated_waste=650.0
        ))
        
        # High: Resource Waste
        anomalies.append(Anomaly(
            anomaly_id=f"anom_{str(uuid4())[:8]}",
            anomaly_type=AnomalyType.RESOURCE_WASTE,
            severity=Severity.HIGH,
            timestamp=now - timedelta(days=1),
            expected_cost=300.0,
            actual_cost=1200.0,
            deviation_percentage=300.0,
            affected_resources=["storage-volume-orphaned", "snapshot-old"],
            description="Orphaned resources consuming budget: unused volumes and old snapshots",
            recommendation="Delete unused storage volumes and implement snapshot lifecycle policies",
            estimated_waste=900.0
        ))
        
        # Medium: Gradual Increase
        anomalies.append(Anomaly(
            anomaly_id=f"anom_{str(uuid4())[:8]}",
            anomaly_type=AnomalyType.GRADUAL_INCREASE,
            severity=Severity.MEDIUM,
            timestamp=now - timedelta(days=10),
            expected_cost=1500.0,
            actual_cost=2100.0,
            deviation_percentage=40.0,
            affected_resources=["database-primary"],
            description="Gradual 40% increase in database costs over 10 days",
            recommendation="Analyze query performance and consider optimization or caching",
            estimated_waste=600.0
        ))
        
        # Medium: Unusual Pattern
        anomalies.append(Anomaly(
            anomaly_id=f"anom_{str(uuid4())[:8]}",
            anomaly_type=AnomalyType.UNUSUAL_PATTERN,
            severity=Severity.MEDIUM,
            timestamp=now - timedelta(days=3),
            expected_cost=500.0,
            actual_cost=950.0,
            deviation_percentage=90.0,
            affected_resources=["network-egress"],
            description="Unusual network egress pattern: 90% above baseline",
            recommendation="Check for data transfer inefficiencies or potential security issues",
            estimated_waste=450.0
        ))
        
        # Low: Minor Spike
        if sensitivity >= 2.0:
            anomalies.append(Anomaly(
                anomaly_id=f"anom_{str(uuid4())[:8]}",
                anomaly_type=AnomalyType.SPIKE,
                severity=Severity.LOW,
                timestamp=now - timedelta(days=7),
                expected_cost=100.0,
                actual_cost=150.0,
                deviation_percentage=50.0,
                affected_resources=["api-lambda-functions"],
                description="Minor cost increase in serverless functions",
                recommendation="Monitor function invocations for optimization opportunities",
                estimated_waste=50.0
            ))
        
        # Additional anomalies based on sensitivity
        if sensitivity >= 3.0:
            anomalies.append(Anomaly(
                anomaly_id=f"anom_{str(uuid4())[:8]}",
                anomaly_type=AnomalyType.RESOURCE_WASTE,
                severity=Severity.MEDIUM,
                timestamp=now - timedelta(days=15),
                expected_cost=200.0,
                actual_cost=400.0,
                deviation_percentage=100.0,
                affected_resources=["dev-environment"],
                description="Development environment running 24/7 with low utilization",
                recommendation="Implement auto-shutdown during off-hours",
                estimated_waste=200.0
            ))
        
        # Filter by resource type if specified
        if resource_type:
            # In real implementation, filter based on actual resource metadata
            pass
        
        return sorted(anomalies, key=lambda x: (x.severity.value, -x.deviation_percentage))
    
    def _get_most_common_type(self, anomalies: List[Anomaly]) -> str:
        """Gets most common anomaly type."""
        if not anomalies:
            return "none"
        
        type_counts = {}
        for anomaly in anomalies:
            type_counts[anomaly.anomaly_type.value] = type_counts.get(anomaly.anomaly_type.value, 0) + 1
        
        return max(type_counts, key=type_counts.get)
    
    def _get_resource_breakdown(self, anomalies: List[Anomaly]) -> Dict[str, int]:
        """Gets breakdown of affected resources."""
        resource_count = {}
        for anomaly in anomalies:
            for resource in anomaly.affected_resources:
                # Extract resource type from resource name
                if "db" in resource.lower() or "database" in resource.lower():
                    key = "database"
                elif "compute" in resource.lower() or "instance" in resource.lower():
                    key = "compute"
                elif "storage" in resource.lower() or "volume" in resource.lower() or "snapshot" in resource.lower():
                    key = "storage"
                elif "network" in resource.lower() or "egress" in resource.lower():
                    key = "network"
                else:
                    key = "other"
                
                resource_count[key] = resource_count.get(key, 0) + 1
        
        return resource_count
