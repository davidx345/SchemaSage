"""
Data Quality Service Module
Data quality validation and monitoring with comprehensive rule engine.
"""
from typing import List, Dict, Any
from datetime import datetime
import uuid

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from ...models.data_migration import DataQualityRule, DataQualityStatus
from ...core.database import DatabaseManager
from ...utils.logging import get_logger

logger = get_logger(__name__)

class DataQualityService:
    """Data quality validation and monitoring service."""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
    
    async def validate_data_quality(
        self, 
        rules: List[DataQualityRule],
        connection_id: str,
        session: AsyncSession
    ) -> Dict[str, Any]:
        """Execute comprehensive data quality validation."""
        
        connection = await self.db_manager.get_connection(connection_id)
        
        results = {
            "validation_id": str(uuid.uuid4()),
            "executed_at": datetime.utcnow(),
            "total_rules": len(rules),
            "passed_rules": 0,
            "failed_rules": 0,
            "error_rules": 0,
            "overall_score": 0.0,
            "rule_results": []
        }
        
        for rule in rules:
            rule_result = await self._execute_quality_rule(connection, rule)
            results["rule_results"].append(rule_result)
            
            if rule_result["status"] == DataQualityStatus.PASSED:
                results["passed_rules"] += 1
            elif rule_result["status"] == DataQualityStatus.FAILED:
                results["failed_rules"] += 1
            else:
                results["error_rules"] += 1
        
        # Calculate overall quality score
        if results["total_rules"] > 0:
            results["overall_score"] = (results["passed_rules"] / results["total_rules"]) * 100
        
        return results
    
    async def _execute_quality_rule(
        self, 
        connection: Any, 
        rule: DataQualityRule
    ) -> Dict[str, Any]:
        """Execute a single data quality rule."""
        
        try:
            async with connection.execute(text(rule.validation_query)) as result:
                query_result = await result.fetchone()
            
            actual_value = query_result[0] if query_result else None
            
            # Compare with expected result
            if rule.expected_result is not None:
                if rule.operator == "equals":
                    passed = actual_value == rule.expected_result
                elif rule.operator == "greater_than":
                    passed = actual_value > rule.expected_result
                elif rule.operator == "less_than":
                    passed = actual_value < rule.expected_result
                elif rule.operator == "between":
                    min_val, max_val = rule.expected_result
                    passed = min_val <= actual_value <= max_val
                else:
                    passed = bool(actual_value)
            else:
                passed = bool(actual_value)
            
            return {
                "rule_id": rule.rule_id,
                "rule_name": rule.rule_name,
                "rule_type": rule.rule_type,
                "status": DataQualityStatus.PASSED if passed else DataQualityStatus.FAILED,
                "actual_value": actual_value,
                "expected_value": rule.expected_result,
                "severity": rule.severity,
                "executed_at": datetime.utcnow()
            }
            
        except Exception as e:
            return {
                "rule_id": rule.rule_id,
                "rule_name": rule.rule_name,
                "rule_type": rule.rule_type,
                "status": DataQualityStatus.ERROR,
                "error_message": str(e),
                "executed_at": datetime.utcnow()
            }
    
    async def generate_quality_report(
        self, 
        validation_results: Dict[str, Any],
        connection_id: str,
        session: AsyncSession
    ) -> Dict[str, Any]:
        """Generate a comprehensive data quality report."""
        
        report = {
            "report_id": str(uuid.uuid4()),
            "generated_at": datetime.utcnow(),
            "connection_id": connection_id,
            "validation_summary": {
                "total_rules": validation_results["total_rules"],
                "passed_rules": validation_results["passed_rules"],
                "failed_rules": validation_results["failed_rules"],
                "error_rules": validation_results["error_rules"],
                "overall_score": validation_results["overall_score"]
            },
            "critical_issues": [],
            "warnings": [],
            "recommendations": []
        }
        
        # Analyze rule results
        for rule_result in validation_results["rule_results"]:
            if rule_result["status"] == DataQualityStatus.FAILED:
                if rule_result.get("severity", "medium") == "critical":
                    report["critical_issues"].append(rule_result)
                else:
                    report["warnings"].append(rule_result)
        
        # Generate recommendations
        report["recommendations"] = self._generate_quality_recommendations(validation_results)
        
        return report
    
    def _generate_quality_recommendations(
        self, 
        validation_results: Dict[str, Any]
    ) -> List[str]:
        """Generate data quality improvement recommendations."""
        
        recommendations = []
        
        # Analyze overall score
        overall_score = validation_results["overall_score"]
        if overall_score < 70:
            recommendations.append("Overall data quality score is below acceptable threshold. Immediate action required.")
        elif overall_score < 85:
            recommendations.append("Data quality score indicates room for improvement. Review failed rules.")
        
        # Analyze specific rule failures
        failed_rules = [r for r in validation_results["rule_results"] 
                       if r["status"] == DataQualityStatus.FAILED]
        
        if failed_rules:
            rule_types = [r.get("rule_type", "unknown") for r in failed_rules]
            
            if "completeness" in rule_types:
                recommendations.append("Data completeness issues detected. Consider implementing NOT NULL constraints or default values.")
            
            if "uniqueness" in rule_types:
                recommendations.append("Data uniqueness violations found. Review primary key and unique constraint definitions.")
            
            if "consistency" in rule_types:
                recommendations.append("Data consistency issues identified. Implement referential integrity constraints.")
            
            if "validity" in rule_types:
                recommendations.append("Data validity problems detected. Add check constraints or validation rules.")
        
        return recommendations
