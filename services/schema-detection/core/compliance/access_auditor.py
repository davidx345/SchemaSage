"""
Access Control Auditor Core Logic.
Audits database users and roles against compliance frameworks.
"""
from typing import List, Dict, Any
from datetime import datetime, timedelta
from models.compliance_models import AccessControlData, UserAudit, RoleAudit, AccessRecommendation, AccessSummary, Severity, ComplianceFramework, DatabaseType


class AccessAuditor:
    """
    Audits database access controls.
    """

    def audit(self, db_type: DatabaseType, connection_string: str, framework: ComplianceFramework) -> AccessControlData:
        """
        Performs the access control audit.
        """
        # In a real implementation, this would connect to the DB and query system catalogs.
        # For this implementation, we will simulate the audit based on common patterns.
        
        users = self._audit_users()
        roles = self._audit_roles()
        recommendations = self._generate_recommendations(users, roles, framework)
        summary = self._generate_summary(users, recommendations)
        auto_fix = self._generate_auto_fix(recommendations)

        return AccessControlData(
            users=users,
            role_matrix=roles,
            recommendations=recommendations,
            summary=summary,
            auto_fix_sql=auto_fix
        )

    def _audit_users(self) -> List[UserAudit]:
        """Simulates user auditing."""
        return [
            UserAudit(
                username="admin",
                roles=["superuser"],
                last_login=datetime.now(),
                password_last_changed=datetime.now() - timedelta(days=45),
                is_superuser=True,
                failed_login_attempts=0
            ),
            UserAudit(
                username="app_user",
                roles=["read_write"],
                last_login=datetime.now(),
                password_last_changed=datetime.now() - timedelta(days=10),
                is_superuser=False,
                failed_login_attempts=0
            ),
            UserAudit(
                username="analytics",
                roles=["read_only"],
                last_login=datetime.now() - timedelta(hours=2),
                password_last_changed=datetime.now() - timedelta(days=120),
                is_superuser=False,
                failed_login_attempts=2
            )
        ]

    def _audit_roles(self) -> List[RoleAudit]:
        """Simulates role auditing."""
        return [
            RoleAudit(
                role="superuser",
                permissions=["ALL"],
                assigned_users=1,
                risk_level=Severity.CRITICAL,
                recommendation="Limit to 0 users in production - use break-glass procedure instead"
            ),
            RoleAudit(
                role="read_write",
                permissions=["SELECT", "INSERT", "UPDATE", "DELETE"],
                assigned_users=5,
                risk_level=Severity.MEDIUM,
                recommendation="Review DELETE permissions"
            ),
            RoleAudit(
                role="read_only",
                permissions=["SELECT"],
                assigned_users=10,
                risk_level=Severity.LOW,
                recommendation="Well configured"
            )
        ]

    def _generate_recommendations(self, users: List[UserAudit], roles: List[RoleAudit], framework: ComplianceFramework) -> List[AccessRecommendation]:
        """Generates recommendations based on findings."""
        recs = []
        
        # Check superusers
        superusers = [u for u in users if u.is_superuser]
        if superusers:
            recs.append(AccessRecommendation(
                priority=Severity.CRITICAL,
                issue=f"{len(superusers)} users have superuser privileges",
                remediation="Revoke superuser and create limited admin roles",
                compliance_impact=f"{framework.value} Access Control Violation"
            ))

        # Check old passwords
        old_pw_users = [u for u in users if u.password_last_changed and (datetime.now() - u.password_last_changed).days > 90]
        if old_pw_users:
            recs.append(AccessRecommendation(
                priority=Severity.HIGH,
                issue=f"{len(old_pw_users)} users have not changed password in 90 days",
                remediation="Enforce password rotation policy",
                compliance_impact=f"{framework.value} Password Policy"
            ))

        return recs

    def _generate_summary(self, users: List[UserAudit], recs: List[AccessRecommendation]) -> AccessSummary:
        """Generates summary."""
        critical = sum(1 for r in recs if r.priority == Severity.CRITICAL)
        high = sum(1 for r in recs if r.priority == Severity.HIGH)
        
        return AccessSummary(
            total_users=len(users),
            critical_risk_users=sum(1 for u in users if u.is_superuser),
            high_risk_users=sum(1 for u in users if u.failed_login_attempts > 0),
            medium_risk_users=0,
            low_risk_users=len(users) - 2,
            total_issues=len(recs),
            compliance_score=max(0, 100 - (critical * 20) - (high * 10)),
            auto_fix_available=True
        )

    def _generate_auto_fix(self, recs: List[AccessRecommendation]) -> List[str]:
        """Generates SQL fixes."""
        sql = []
        for rec in recs:
            if "superuser" in rec.issue:
                sql.append("-- Fix: Remove superuser access")
                sql.append("ALTER ROLE admin NOSUPERUSER;")
                sql.append("CREATE ROLE limited_admin;")
                sql.append("GRANT CONNECT ON DATABASE production TO limited_admin;")
        return sql
