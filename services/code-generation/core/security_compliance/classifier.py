"""
Data classification engine for security and compliance
Automatically classifies schema data based on content and patterns
"""

import logging
import re
import asyncio
from typing import Dict, List, Optional, Any, Set, Tuple
from datetime import datetime
import uuid

from models.schemas import SchemaResponse, TableInfo, ColumnInfo, Relationship
from .models import (
    DataClassification, SecurityLevel, ComplianceFramework, 
    EncryptionType, RiskLevel
)

logger = logging.getLogger(__name__)


class DataClassificationEngine:
    """
    Automatically classifies schema data based on patterns, content, and rules
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize data classification engine
        
        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        self.classification_rules = self._load_classification_rules()
        self.sensitive_patterns = self._load_sensitive_patterns()
        self.compliance_mappings = self._load_compliance_mappings()
        
        logger.info("Data classification engine initialized")
    
    async def classify_schema(
        self,
        schema: SchemaResponse,
        custom_rules: Dict[str, Any] = None
    ) -> Dict[str, List[DataClassification]]:
        """
        Classify entire schema for security and compliance
        
        Args:
            schema: Schema response object
            custom_rules: Optional custom classification rules
            
        Returns:
            Dictionary with classifications by type
        """
        try:
            rules = custom_rules or self.classification_rules
            
            classifications = {
                'schema': [],
                'tables': [],
                'columns': [],
                'relationships': []
            }
            
            # Classify schema level
            schema_classification = await self._classify_schema_level(schema, rules)
            classifications['schema'].append(schema_classification)
            
            # Classify tables
            for table in schema.tables:
                table_classification = await self._classify_table(table, rules)
                classifications['tables'].append(table_classification)
                
                # Classify columns
                for column in table.columns:
                    column_classification = await self._classify_column(
                        column, table.table_name, schema.schema_name, rules
                    )
                    classifications['columns'].append(column_classification)
            
            # Classify relationships
            for relationship in schema.relationships or []:
                rel_classification = await self._classify_relationship(relationship, rules)
                classifications['relationships'].append(rel_classification)
            
            logger.info(f"Classified schema {schema.schema_name} - "
                       f"Tables: {len(classifications['tables'])}, "
                       f"Columns: {len(classifications['columns'])}")
            
            return classifications
            
        except Exception as e:
            logger.error(f"Error classifying schema {schema.schema_name}: {e}")
            raise
    
    async def _classify_schema_level(
        self,
        schema: SchemaResponse,
        rules: Dict[str, Any]
    ) -> DataClassification:
        """Classify at schema level"""
        try:
            # Analyze schema metadata
            schema_name = schema.schema_name.lower()
            table_names = [table.table_name.lower() for table in schema.tables]
            
            # Check for sensitive indicators in schema name
            sensitive_types = []
            security_level = SecurityLevel.INTERNAL
            compliance_requirements = []
            
            # Pattern matching for schema name
            for pattern, config in self.sensitive_patterns.items():
                if re.search(pattern, schema_name, re.IGNORECASE):
                    sensitive_types.extend(config.get('types', []))
                    if config.get('security_level'):
                        current_level = SecurityLevel(config['security_level'])
                        if self._get_security_level_priority(current_level) > self._get_security_level_priority(security_level):
                            security_level = current_level
                    compliance_requirements.extend(config.get('compliance', []))
            
            # Analyze table composition
            financial_tables = sum(1 for name in table_names if any(
                keyword in name for keyword in ['payment', 'transaction', 'invoice', 'billing']
            ))
            personal_tables = sum(1 for name in table_names if any(
                keyword in name for keyword in ['user', 'customer', 'employee', 'person']
            ))
            medical_tables = sum(1 for name in table_names if any(
                keyword in name for keyword in ['patient', 'medical', 'health', 'diagnosis']
            ))
            
            # Adjust classification based on table composition
            if medical_tables > 0:
                compliance_requirements.append(ComplianceFramework.HIPAA)
                if medical_tables / len(table_names) > 0.3:
                    security_level = SecurityLevel.CONFIDENTIAL
            
            if financial_tables > 0:
                compliance_requirements.extend([ComplianceFramework.SOX, ComplianceFramework.PCI_DSS])
                if financial_tables / len(table_names) > 0.2:
                    security_level = SecurityLevel.CONFIDENTIAL
            
            if personal_tables > 0:
                compliance_requirements.extend([ComplianceFramework.GDPR, ComplianceFramework.CCPA])
            
            # Remove duplicates
            compliance_requirements = list(set(compliance_requirements))
            sensitive_types = list(set(sensitive_types))
            
            # Determine encryption recommendation
            encryption_type = self._determine_encryption_type(security_level, sensitive_types)
            
            # Calculate risk score
            risk_score = self._calculate_risk_score(
                security_level, sensitive_types, len(compliance_requirements)
            )
            
            classification_id = str(uuid.uuid4())
            
            return DataClassification(
                classification_id=classification_id,
                target_type='schema',
                target_name=schema.schema_name,
                security_level=security_level,
                compliance_requirements=compliance_requirements,
                sensitive_data_types=sensitive_types,
                encryption_recommendation=encryption_type,
                access_restrictions=self._get_access_restrictions(security_level),
                data_lineage_tracking=security_level in [SecurityLevel.CONFIDENTIAL, SecurityLevel.RESTRICTED],
                risk_score=risk_score,
                confidence_score=0.8,
                metadata={
                    'table_count': len(schema.tables),
                    'total_columns': sum(len(table.columns) for table in schema.tables),
                    'financial_tables': financial_tables,
                    'personal_tables': personal_tables,
                    'medical_tables': medical_tables
                }
            )
            
        except Exception as e:
            logger.error(f"Error classifying schema level: {e}")
            raise
    
    async def _classify_table(
        self,
        table: TableInfo,
        rules: Dict[str, Any]
    ) -> DataClassification:
        """Classify table data"""
        try:
            table_name = table.table_name.lower()
            column_names = [col.column_name.lower() for col in table.columns]
            
            sensitive_types = []
            security_level = SecurityLevel.INTERNAL
            compliance_requirements = []
            
            # Pattern matching for table name
            for pattern, config in self.sensitive_patterns.items():
                if re.search(pattern, table_name, re.IGNORECASE):
                    sensitive_types.extend(config.get('types', []))
                    if config.get('security_level'):
                        current_level = SecurityLevel(config['security_level'])
                        if self._get_security_level_priority(current_level) > self._get_security_level_priority(security_level):
                            security_level = current_level
                    compliance_requirements.extend(config.get('compliance', []))
            
            # Analyze column composition
            pii_columns = 0
            financial_columns = 0
            medical_columns = 0
            
            for column in table.columns:
                col_name = column.column_name.lower()
                col_type = column.data_type.lower()
                
                # Check for PII indicators
                if any(indicator in col_name for indicator in [
                    'ssn', 'social_security', 'passport', 'license',
                    'email', 'phone', 'address', 'name', 'birth'
                ]):
                    pii_columns += 1
                    sensitive_types.append('PII')
                
                # Check for financial indicators
                if any(indicator in col_name for indicator in [
                    'account', 'card', 'payment', 'salary', 'amount',
                    'balance', 'transaction', 'credit', 'debit'
                ]):
                    financial_columns += 1
                    sensitive_types.append('Financial')
                
                # Check for medical indicators
                if any(indicator in col_name for indicator in [
                    'diagnosis', 'treatment', 'medication', 'symptom',
                    'allergy', 'condition', 'medical_record'
                ]):
                    medical_columns += 1
                    sensitive_types.append('Medical')
            
            # Adjust security level based on column analysis
            total_columns = len(table.columns)
            if pii_columns > 0 or medical_columns > 0:
                if (pii_columns + medical_columns) / total_columns > 0.3:
                    security_level = SecurityLevel.CONFIDENTIAL
                    compliance_requirements.extend([ComplianceFramework.GDPR, ComplianceFramework.HIPAA])
            
            if financial_columns > 0:
                if financial_columns / total_columns > 0.2:
                    security_level = SecurityLevel.CONFIDENTIAL
                    compliance_requirements.extend([ComplianceFramework.PCI_DSS, ComplianceFramework.SOX])
            
            # Remove duplicates
            compliance_requirements = list(set(compliance_requirements))
            sensitive_types = list(set(sensitive_types))
            
            # Determine encryption and access controls
            encryption_type = self._determine_encryption_type(security_level, sensitive_types)
            
            # Calculate risk score
            risk_score = self._calculate_risk_score(
                security_level, sensitive_types, len(compliance_requirements)
            )
            
            classification_id = str(uuid.uuid4())
            
            return DataClassification(
                classification_id=classification_id,
                target_type='table',
                target_name=table.table_name,
                security_level=security_level,
                compliance_requirements=compliance_requirements,
                sensitive_data_types=sensitive_types,
                encryption_recommendation=encryption_type,
                access_restrictions=self._get_access_restrictions(security_level),
                data_lineage_tracking=len(sensitive_types) > 0,
                risk_score=risk_score,
                confidence_score=0.85,
                metadata={
                    'column_count': total_columns,
                    'pii_columns': pii_columns,
                    'financial_columns': financial_columns,
                    'medical_columns': medical_columns,
                    'sensitive_ratio': (pii_columns + financial_columns + medical_columns) / total_columns
                }
            )
            
        except Exception as e:
            logger.error(f"Error classifying table {table.table_name}: {e}")
            raise
    
    async def _classify_column(
        self,
        column: ColumnInfo,
        table_name: str,
        schema_name: str,
        rules: Dict[str, Any]
    ) -> DataClassification:
        """Classify individual column"""
        try:
            column_name = column.column_name.lower()
            data_type = column.data_type.lower()
            
            sensitive_types = []
            security_level = SecurityLevel.INTERNAL
            compliance_requirements = []
            
            # Detailed column pattern matching
            column_patterns = {
                r'(ssn|social_security|social_sec)': {
                    'types': ['PII', 'SSN'],
                    'security_level': 'confidential',
                    'compliance': ['gdpr', 'ccpa']
                },
                r'(email|e_mail|email_address)': {
                    'types': ['PII', 'Contact'],
                    'security_level': 'confidential',
                    'compliance': ['gdpr', 'ccpa']
                },
                r'(phone|telephone|mobile|cell)': {
                    'types': ['PII', 'Contact'],
                    'security_level': 'confidential',
                    'compliance': ['gdpr', 'ccpa']
                },
                r'(password|pwd|pass_hash|encrypted_pass)': {
                    'types': ['Credential'],
                    'security_level': 'restricted',
                    'compliance': []
                },
                r'(credit_card|card_number|cc_num|account_number)': {
                    'types': ['Financial', 'PCI'],
                    'security_level': 'restricted',
                    'compliance': ['pci_dss', 'sox']
                },
                r'(salary|wage|income|compensation)': {
                    'types': ['Financial', 'PII'],
                    'security_level': 'confidential',
                    'compliance': ['gdpr', 'sox']
                },
                r'(medical_record|diagnosis|treatment|medication)': {
                    'types': ['Medical', 'PHI'],
                    'security_level': 'restricted',
                    'compliance': ['hipaa']
                },
                r'(birth_date|date_of_birth|dob)': {
                    'types': ['PII', 'Temporal'],
                    'security_level': 'confidential',
                    'compliance': ['gdpr', 'ccpa']
                },
                r'(address|street|city|zip|postal)': {
                    'types': ['PII', 'Location'],
                    'security_level': 'confidential',
                    'compliance': ['gdpr', 'ccpa']
                }
            }
            
            # Check column name patterns
            for pattern, config in column_patterns.items():
                if re.search(pattern, column_name, re.IGNORECASE):
                    sensitive_types.extend(config.get('types', []))
                    if config.get('security_level'):
                        current_level = SecurityLevel(config['security_level'])
                        if self._get_security_level_priority(current_level) > self._get_security_level_priority(security_level):
                            security_level = current_level
                    compliance_requirements.extend([
                        ComplianceFramework(cf) for cf in config.get('compliance', [])
                    ])
            
            # Data type analysis
            if 'varchar' in data_type or 'text' in data_type:
                # Text fields could contain sensitive information
                if any(keyword in column_name for keyword in ['comment', 'note', 'description', 'remarks']):
                    sensitive_types.append('Free Text')
                    security_level = max(security_level, SecurityLevel.INTERNAL, key=self._get_security_level_priority)
            
            if 'timestamp' in data_type or 'datetime' in data_type:
                sensitive_types.append('Temporal')
            
            # Check for foreign key relationships that might indicate sensitive data
            if column.is_foreign_key:
                sensitive_types.append('Relational')
            
            # Primary key analysis
            if column.is_primary_key and 'id' not in column_name:
                # Non-ID primary keys might be sensitive
                sensitive_types.append('Identifier')
            
            # Remove duplicates
            compliance_requirements = list(set(compliance_requirements))
            sensitive_types = list(set(sensitive_types))
            
            # Determine encryption recommendation
            encryption_type = self._determine_encryption_type(security_level, sensitive_types)
            
            # Special encryption for specific data types
            if any(stype in ['SSN', 'Credit Card', 'Medical', 'Credential'] for stype in sensitive_types):
                encryption_type = EncryptionType.FIELD_LEVEL
            
            # Calculate risk score
            risk_score = self._calculate_risk_score(
                security_level, sensitive_types, len(compliance_requirements)
            )
            
            # Increase risk for nullable sensitive columns
            if column.is_nullable and sensitive_types:
                risk_score += 0.1
            
            classification_id = str(uuid.uuid4())
            
            return DataClassification(
                classification_id=classification_id,
                target_type='column',
                target_name=f"{table_name}.{column.column_name}",
                security_level=security_level,
                compliance_requirements=compliance_requirements,
                sensitive_data_types=sensitive_types,
                encryption_recommendation=encryption_type,
                access_restrictions=self._get_access_restrictions(security_level),
                data_lineage_tracking=len(sensitive_types) > 0,
                risk_score=min(risk_score, 1.0),
                confidence_score=0.9,
                metadata={
                    'data_type': column.data_type,
                    'is_nullable': column.is_nullable,
                    'is_primary_key': column.is_primary_key,
                    'is_foreign_key': column.is_foreign_key,
                    'max_length': column.max_length,
                    'default_value': str(column.default_value) if column.default_value else None
                }
            )
            
        except Exception as e:
            logger.error(f"Error classifying column {column.column_name}: {e}")
            raise
    
    async def _classify_relationship(
        self,
        relationship: Dict[str, Any],
        rules: Dict[str, Any]
    ) -> DataClassification:
        """Classify relationship between tables"""
        try:
            from_table = relationship.get('from_table', '')
            to_table = relationship.get('to_table', '')
            from_column = relationship.get('from_column', '')
            to_column = relationship.get('to_column', '')
            
            rel_name = f"{from_table}.{from_column} -> {to_table}.{to_column}"
            
            sensitive_types = ['Relational']
            security_level = SecurityLevel.INTERNAL
            compliance_requirements = []
            
            # Check if relationship involves sensitive tables
            sensitive_table_patterns = [
                'user', 'customer', 'employee', 'patient', 'payment',
                'transaction', 'medical', 'personal', 'private'
            ]
            
            involves_sensitive = any(
                pattern in from_table.lower() or pattern in to_table.lower()
                for pattern in sensitive_table_patterns
            )
            
            if involves_sensitive:
                sensitive_types.append('Sensitive Reference')
                security_level = SecurityLevel.CONFIDENTIAL
                compliance_requirements.extend([ComplianceFramework.GDPR, ComplianceFramework.CCPA])
            
            # Check relationship type
            rel_type = relationship.get('relationship_type', 'unknown')
            if rel_type in ['one_to_many', 'many_to_many']:
                sensitive_types.append('Complex Relationship')
            
            encryption_type = self._determine_encryption_type(security_level, sensitive_types)
            risk_score = self._calculate_risk_score(
                security_level, sensitive_types, len(compliance_requirements)
            )
            
            classification_id = str(uuid.uuid4())
            
            return DataClassification(
                classification_id=classification_id,
                target_type='relationship',
                target_name=rel_name,
                security_level=security_level,
                compliance_requirements=compliance_requirements,
                sensitive_data_types=sensitive_types,
                encryption_recommendation=encryption_type,
                access_restrictions=self._get_access_restrictions(security_level),
                data_lineage_tracking=True,
                risk_score=risk_score,
                confidence_score=0.7,
                metadata={
                    'from_table': from_table,
                    'to_table': to_table,
                    'from_column': from_column,
                    'to_column': to_column,
                    'relationship_type': rel_type
                }
            )
            
        except Exception as e:
            logger.error(f"Error classifying relationship: {e}")
            raise
    
    def _load_classification_rules(self) -> Dict[str, Any]:
        """Load classification rules from configuration"""
        return self.config.get('classification_rules', {
            'default_security_level': 'internal',
            'auto_classify_pii': True,
            'require_encryption_for_confidential': True,
            'enable_data_lineage': True
        })
    
    def _load_sensitive_patterns(self) -> Dict[str, Dict[str, Any]]:
        """Load patterns for identifying sensitive data"""
        return {
            r'(user|customer|client|person|employee|staff|patient)': {
                'types': ['PII'],
                'security_level': 'confidential',
                'compliance': ['gdpr', 'ccpa']
            },
            r'(payment|transaction|billing|invoice|financial)': {
                'types': ['Financial'],
                'security_level': 'confidential',
                'compliance': ['pci_dss', 'sox']
            },
            r'(medical|health|patient|diagnosis|treatment)': {
                'types': ['Medical', 'PHI'],
                'security_level': 'restricted',
                'compliance': ['hipaa']
            },
            r'(credential|password|token|secret|key)': {
                'types': ['Credential'],
                'security_level': 'restricted',
                'compliance': []
            },
            r'(audit|log|trace|history)': {
                'types': ['Audit'],
                'security_level': 'confidential',
                'compliance': ['sox', 'iso_27001']
            }
        }
    
    def _load_compliance_mappings(self) -> Dict[str, Any]:
        """Load compliance framework mappings"""
        return {
            'gdpr': {
                'requires_encryption': True,
                'data_retention_limit': 2555,  # 7 years in days
                'requires_consent': True,
                'right_to_erasure': True
            },
            'hipaa': {
                'requires_encryption': True,
                'access_logging': True,
                'minimum_necessary': True,
                'breach_notification': True
            },
            'pci_dss': {
                'requires_encryption': True,
                'network_segmentation': True,
                'access_control': True,
                'vulnerability_scanning': True
            }
        }
    
    def _get_security_level_priority(self, level: SecurityLevel) -> int:
        """Get priority value for security level comparison"""
        priorities = {
            SecurityLevel.PUBLIC: 1,
            SecurityLevel.INTERNAL: 2,
            SecurityLevel.CONFIDENTIAL: 3,
            SecurityLevel.RESTRICTED: 4,
            SecurityLevel.TOP_SECRET: 5
        }
        return priorities.get(level, 0)
    
    def _determine_encryption_type(
        self,
        security_level: SecurityLevel,
        sensitive_types: List[str]
    ) -> EncryptionType:
        """Determine appropriate encryption type"""
        if security_level == SecurityLevel.TOP_SECRET:
            return EncryptionType.AES_256
        elif security_level == SecurityLevel.RESTRICTED:
            if any(stype in ['SSN', 'Credit Card', 'Medical'] for stype in sensitive_types):
                return EncryptionType.FIELD_LEVEL
            return EncryptionType.AES_256
        elif security_level == SecurityLevel.CONFIDENTIAL:
            return EncryptionType.AES_128
        else:
            return EncryptionType.NONE
    
    def _get_access_restrictions(self, security_level: SecurityLevel) -> List[str]:
        """Get access restrictions for security level"""
        restrictions = {
            SecurityLevel.PUBLIC: [],
            SecurityLevel.INTERNAL: ['authenticated_users'],
            SecurityLevel.CONFIDENTIAL: ['authenticated_users', 'role_based_access'],
            SecurityLevel.RESTRICTED: ['authenticated_users', 'role_based_access', 'manager_approval'],
            SecurityLevel.TOP_SECRET: ['authenticated_users', 'role_based_access', 'manager_approval', 'audit_trail']
        }
        return restrictions.get(security_level, [])
    
    def _calculate_risk_score(
        self,
        security_level: SecurityLevel,
        sensitive_types: List[str],
        compliance_count: int
    ) -> float:
        """Calculate risk score based on classification factors"""
        base_score = {
            SecurityLevel.PUBLIC: 0.1,
            SecurityLevel.INTERNAL: 0.3,
            SecurityLevel.CONFIDENTIAL: 0.6,
            SecurityLevel.RESTRICTED: 0.8,
            SecurityLevel.TOP_SECRET: 1.0
        }.get(security_level, 0.5)
        
        # Add risk for sensitive data types
        sensitive_risk = len(sensitive_types) * 0.1
        
        # Add risk for compliance requirements
        compliance_risk = compliance_count * 0.05
        
        # Calculate final score
        total_risk = base_score + sensitive_risk + compliance_risk
        return min(total_risk, 1.0)
