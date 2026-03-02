"""
Universal Database Migration Engine
Handles cross-database migrations with intelligent type conversion
"""
import asyncio
import logging
import uuid
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from enum import Enum
import json

from shared.utils.connection_parser import ConnectionURLParser
from shared.utils.database_manager import connection_manager

logger = logging.getLogger(__name__)

class MigrationType(str, Enum):
    SCHEMA_ONLY = "schema_only"
    DATA_ONLY = "data_only"
    SCHEMA_AND_DATA = "schema_and_data"

class MigrationStatus(str, Enum):
    PLANNING = "planning"
    PLANNED = "planned"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"

class TypeConversionMode(str, Enum):
    CONVERT = "convert"
    SKIP = "skip"
    ERROR = "error"

class MigrationEngine:
    """Universal database migration engine"""
    
    def __init__(self):
        self.migration_plans = {}
        self.migration_executions = {}
        self.type_conversion_matrix = self._build_type_conversion_matrix()
    
    async def create_migration_plan(self, 
                                  source_url: str,
                                  target_url: str,
                                  migration_type: MigrationType = MigrationType.SCHEMA_AND_DATA,
                                  options: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Create a migration plan between two databases
        
        Args:
            source_url: Source database connection URL
            target_url: Target database connection URL
            migration_type: Type of migration to perform
            options: Migration options
            
        Returns:
            Migration plan with analysis and steps
        """
        migration_id = f"mig_{uuid.uuid4().hex[:8]}"
        start_time = datetime.now()
        
        try:
            logger.info(f"Creating migration plan {migration_id}")
            
            # Parse connection URLs
            source_params = ConnectionURLParser.parse_connection_url(source_url)
            target_params = ConnectionURLParser.parse_connection_url(target_url)
            
            # Test connections
            source_test = await connection_manager.test_connection(source_url)
            target_test = await connection_manager.test_connection(target_url)
            
            if source_test['status'] != 'success':
                raise ValueError(f"Source database connection failed: {source_test.get('error')}")
            
            if target_test['status'] != 'success':
                raise ValueError(f"Target database connection failed: {target_test.get('error')}")
            
            # Analyze source database
            source_analysis = await self._analyze_source_database(source_params, source_test)
            
            # Analyze target database compatibility
            target_analysis = await self._analyze_target_compatibility(
                source_params, target_params, source_analysis, options or {}
            )
            
            # Create migration steps
            migration_steps = await self._create_migration_steps(
                source_analysis, target_analysis, migration_type, options or {}
            )
            
            # Calculate estimates
            estimates = self._calculate_migration_estimates(source_analysis, target_analysis, migration_steps)
            
            # Create migration plan
            migration_plan = {
                'migration_id': migration_id,
                'status': MigrationStatus.PLANNED,
                'created_at': start_time.isoformat(),
                'source_info': {
                    'database_type': source_params['database_type'],
                    'connection_id': source_test['connection_id'],
                    'masked_url': ConnectionURLParser.mask_sensitive_data(source_url)
                },
                'target_info': {
                    'database_type': target_params['database_type'],
                    'connection_id': target_test['connection_id'],
                    'masked_url': ConnectionURLParser.mask_sensitive_data(target_url)
                },
                'migration_type': migration_type,
                'source_analysis': source_analysis,
                'target_analysis': target_analysis,
                'migration_plan': {
                    'steps': migration_steps,
                    'total_steps': len(migration_steps),
                    'estimated_duration_minutes': estimates['duration_minutes'],
                    'estimated_size_mb': estimates['size_mb'],
                    'complexity_score': estimates['complexity_score']
                },
                'compatibility_issues': target_analysis.get('compatibility_issues', []),
                'warnings': target_analysis.get('warnings', []),
                'rollback_available': self._check_rollback_capability(source_params, target_params),
                'options': options or {}
            }
            
            # Store migration plan
            self.migration_plans[migration_id] = migration_plan
            
            return migration_plan
            
        except Exception as e:
            logger.error(f"Failed to create migration plan: {str(e)}")
            raise Exception(f"Migration planning failed: {str(e)}")
    
    async def _analyze_source_database(self, source_params: Dict[str, Any], connection_test: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze source database structure and data"""
        db_type = source_params['database_type']
        
        # Get mock schema information (in real implementation, this would introspect the actual database)
        schema_info = await self._get_database_schema(source_params)
        
        # Calculate data statistics
        total_records = sum(table.get('row_count', 0) for table in schema_info.get('tables', []))
        total_size_mb = sum(table.get('size_mb', 0) for table in schema_info.get('tables', []))
        
        return {
            'database_type': db_type,
            'server_info': connection_test.get('server_info', {}),
            'schema_info': schema_info,
            'statistics': {
                'total_tables': len(schema_info.get('tables', [])),
                'total_records': total_records,
                'total_size_mb': total_size_mb,
                'has_foreign_keys': any(table.get('foreign_keys', []) for table in schema_info.get('tables', [])),
                'has_indexes': any(table.get('indexes', []) for table in schema_info.get('tables', [])),
                'has_views': len(schema_info.get('views', [])) > 0,
                'has_functions': len(schema_info.get('functions', [])) > 0
            }
        }
    
    async def _analyze_target_compatibility(self, 
                                          source_params: Dict[str, Any],
                                          target_params: Dict[str, Any],
                                          source_analysis: Dict[str, Any],
                                          options: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze target database compatibility"""
        source_type = source_params['database_type']
        target_type = target_params['database_type']
        
        compatibility_issues = []
        warnings = []
        transformation_plan = []
        
        # Check basic compatibility
        if source_type == target_type:
            compatibility_score = 95
        else:
            compatibility_score = self._calculate_compatibility_score(source_type, target_type)
        
        # Analyze table transformations
        source_tables = source_analysis['schema_info'].get('tables', [])
        for table in source_tables:
            table_transformation = self._analyze_table_transformation(
                table, source_type, target_type, options
            )
            transformation_plan.append(table_transformation)
            
            # Collect issues and warnings
            compatibility_issues.extend(table_transformation.get('issues', []))
            warnings.extend(table_transformation.get('warnings', []))
        
        # Database-specific compatibility checks
        if source_type == 'postgresql' and target_type == 'mongodb':
            warnings.extend([
                "PostgreSQL foreign keys will be converted to references",
                "Complex queries may need rewriting for MongoDB",
                "Triggers and functions cannot be directly migrated"
            ])
        elif source_type == 'mysql' and target_type == 'postgresql':
            warnings.extend([
                "MySQL AUTO_INCREMENT will be converted to SERIAL",
                "Case sensitivity differences may affect queries",
                "Some MySQL-specific data types need conversion"
            ])
        elif source_type in ['postgresql', 'mysql'] and target_type == 'sqlite':
            warnings.extend([
                "SQLite has limited data type support",
                "Foreign key constraints may need adjustment",
                "Some advanced features will be simplified"
            ])
        
        return {
            'database_type': target_type,
            'compatibility_score': compatibility_score,
            'compatibility_issues': compatibility_issues,
            'warnings': warnings,
            'transformation_plan': transformation_plan,
            'estimated_target_size_mb': source_analysis['statistics']['total_size_mb'] * 1.1,  # 10% overhead
            'estimated_collections_or_tables': len(transformation_plan)
        }
    
    def _analyze_table_transformation(self, 
                                    table: Dict[str, Any],
                                    source_type: str,
                                    target_type: str,
                                    options: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze how a table should be transformed"""
        table_name = table['name']
        columns = table.get('columns', [])
        
        transformation = {
            'source_table': table_name,
            'target_name': table_name,  # Default to same name
            'transformation_type': 'direct',
            'column_mappings': [],
            'issues': [],
            'warnings': []
        }
        
        # Handle different database paradigms
        if source_type in ['postgresql', 'mysql', 'sqlite'] and target_type == 'mongodb':
            # SQL to NoSQL transformation
            transformation['transformation_type'] = 'sql_to_nosql'
            transformation['target_name'] = table_name  # Collection name
            
            # Convert columns to document fields
            for column in columns:
                field_mapping = self._convert_sql_column_to_mongo_field(column, options)
                transformation['column_mappings'].append(field_mapping)
                
                if field_mapping.get('conversion_warning'):
                    transformation['warnings'].append(
                        f"Column {column['name']}: {field_mapping['conversion_warning']}"
                    )
        
        elif source_type == 'mongodb' and target_type in ['postgresql', 'mysql', 'sqlite']:
            # NoSQL to SQL transformation
            transformation['transformation_type'] = 'nosql_to_sql'
            
            # This would need document analysis in real implementation
            transformation['warnings'].append(
                f"Collection {table_name} structure needs analysis for SQL conversion"
            )
        
        else:
            # SQL to SQL transformation
            transformation['transformation_type'] = 'sql_to_sql'
            
            for column in columns:
                field_mapping = self._convert_sql_column_between_dbs(
                    column, source_type, target_type, options
                )
                transformation['column_mappings'].append(field_mapping)
                
                if field_mapping.get('conversion_warning'):
                    transformation['warnings'].append(
                        f"Column {column['name']}: {field_mapping['conversion_warning']}"
                    )
        
        return transformation
    
    def _convert_sql_column_to_mongo_field(self, column: Dict[str, Any], options: Dict[str, Any]) -> Dict[str, Any]:
        """Convert SQL column to MongoDB field"""
        column_name = column['name']
        column_type = column.get('type', '').lower()
        
        mapping = {
            'source_column': column_name,
            'target_field': column_name,
            'source_type': column_type,
            'target_type': 'string',  # Default
            'conversion_method': 'direct'
        }
        
        # Type conversion mapping
        if 'int' in column_type or 'serial' in column_type:
            mapping['target_type'] = 'int'
        elif 'float' in column_type or 'decimal' in column_type or 'numeric' in column_type:
            mapping['target_type'] = 'double'
        elif 'bool' in column_type:
            mapping['target_type'] = 'bool'
        elif 'timestamp' in column_type or 'datetime' in column_type:
            mapping['target_type'] = 'date'
        elif 'json' in column_type:
            mapping['target_type'] = 'object'
        elif 'text' in column_type or 'varchar' in column_type or 'char' in column_type:
            mapping['target_type'] = 'string'
        else:
            mapping['conversion_warning'] = f"Unknown type {column_type}, defaulting to string"
        
        # Handle primary keys
        if column.get('primary_key'):
            if column_name.lower() == 'id':
                mapping['target_field'] = '_id'
                mapping['target_type'] = 'objectId'
                mapping['conversion_method'] = 'primary_key_conversion'
        
        return mapping
    
    def _convert_sql_column_between_dbs(self, 
                                      column: Dict[str, Any],
                                      source_type: str,
                                      target_type: str,
                                      options: Dict[str, Any]) -> Dict[str, Any]:
        """Convert SQL column between different SQL databases"""
        column_name = column['name']
        source_column_type = column.get('type', '').lower()
        
        # Get type conversion from matrix
        target_column_type = self._get_converted_type(source_column_type, source_type, target_type)
        
        mapping = {
            'source_column': column_name,
            'target_column': column_name,
            'source_type': source_column_type,
            'target_type': target_column_type,
            'conversion_method': 'type_mapping'
        }
        
        # Add conversion warnings for problematic conversions
        if source_column_type != target_column_type:
            if 'auto_increment' in source_column_type and target_type == 'postgresql':
                mapping['conversion_warning'] = "AUTO_INCREMENT converted to SERIAL"
            elif 'jsonb' in source_column_type and target_type == 'mysql':
                mapping['conversion_warning'] = "JSONB converted to JSON (less efficient)"
            elif 'array' in source_column_type and target_type in ['mysql', 'sqlite']:
                mapping['conversion_warning'] = "Array type not supported, converting to TEXT"
        
        return mapping
    
    def _get_converted_type(self, source_type: str, source_db: str, target_db: str) -> str:
        """Get converted type using conversion matrix"""
        conversion_key = f"{source_db}_{target_db}"
        
        if conversion_key in self.type_conversion_matrix:
            conversions = self.type_conversion_matrix[conversion_key]
            for pattern, target_type in conversions.items():
                if pattern in source_type:
                    return target_type
        
        # Default conversions if no specific mapping found
        return self._get_default_type_conversion(source_type, target_db)
    
    def _get_default_type_conversion(self, source_type: str, target_db: str) -> str:
        """Get default type conversion"""
        if 'int' in source_type:
            return 'INTEGER' if target_db == 'sqlite' else 'INT'
        elif 'varchar' in source_type or 'text' in source_type:
            return 'TEXT'
        elif 'timestamp' in source_type or 'datetime' in source_type:
            return 'TIMESTAMP' if target_db == 'postgresql' else 'DATETIME'
        elif 'bool' in source_type:
            return 'BOOLEAN' if target_db == 'postgresql' else 'TINYINT(1)'
        else:
            return 'TEXT'  # Safe default
    
    async def _create_migration_steps(self,
                                    source_analysis: Dict[str, Any],
                                    target_analysis: Dict[str, Any],
                                    migration_type: MigrationType,
                                    options: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create detailed migration steps"""
        steps = []
        step_number = 1
        
        # Step 1: Prepare target database
        steps.append({
            'step_number': step_number,
            'name': 'prepare_target_database',
            'description': 'Prepare target database for migration',
            'estimated_time_minutes': 2,
            'actions': [
                'Verify target database connection',
                'Check available space and permissions',
                'Create backup point if supported'
            ]
        })
        step_number += 1
        
        # Step 2: Schema migration (if required)
        if migration_type in [MigrationType.SCHEMA_ONLY, MigrationType.SCHEMA_AND_DATA]:
            steps.append({
                'step_number': step_number,
                'name': 'create_schema',
                'description': 'Create target database schema',
                'estimated_time_minutes': 5,
                'actions': [
                    f"Create {len(target_analysis['transformation_plan'])} tables/collections",
                    'Create indexes and constraints',
                    'Verify schema creation'
                ]
            })
            step_number += 1
        
        # Step 3: Data migration (if required)
        if migration_type in [MigrationType.DATA_ONLY, MigrationType.SCHEMA_AND_DATA]:
            total_records = source_analysis['statistics']['total_records']
            batch_size = options.get('batch_size', 1000)
            estimated_batches = max(1, total_records // batch_size)
            
            steps.append({
                'step_number': step_number,
                'name': 'migrate_data',
                'description': f'Migrate {total_records:,} records in batches',
                'estimated_time_minutes': max(5, estimated_batches // 100),  # Rough estimate
                'actions': [
                    f'Process {estimated_batches:,} batches of {batch_size:,} records',
                    'Apply data transformations',
                    'Verify data integrity'
                ]
            })
            step_number += 1
        
        # Step 4: Create relationships (if applicable)
        if (migration_type in [MigrationType.SCHEMA_ONLY, MigrationType.SCHEMA_AND_DATA] and
            source_analysis['statistics']['has_foreign_keys']):
            steps.append({
                'step_number': step_number,
                'name': 'create_relationships',
                'description': 'Create foreign key relationships and references',
                'estimated_time_minutes': 3,
                'actions': [
                    'Create foreign key constraints',
                    'Verify referential integrity',
                    'Update relationship mappings'
                ]
            })
            step_number += 1
        
        # Step 5: Final verification
        steps.append({
            'step_number': step_number,
            'name': 'verify_migration',
            'description': 'Verify migration completion and data integrity',
            'estimated_time_minutes': 3,
            'actions': [
                'Compare record counts',
                'Verify data sample accuracy',
                'Generate migration report'
            ]
        })
        
        return steps
    
    def _calculate_migration_estimates(self,
                                     source_analysis: Dict[str, Any],
                                     target_analysis: Dict[str, Any],
                                     steps: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate migration time and complexity estimates"""
        total_records = source_analysis['statistics']['total_records']
        total_size_mb = source_analysis['statistics']['total_size_mb']
        
        # Base time calculation
        base_time = sum(step['estimated_time_minutes'] for step in steps)
        
        # Complexity factors
        complexity_factors = []
        complexity_score = 1.0
        
        # Record count factor
        if total_records > 1000000:
            complexity_score *= 1.5
            complexity_factors.append("Large dataset (>1M records)")
        elif total_records > 100000:
            complexity_score *= 1.2
            complexity_factors.append("Medium dataset (>100K records)")
        
        # Cross-database migration factor
        source_type = source_analysis['database_type']
        target_type = target_analysis['database_type']
        if source_type != target_type:
            complexity_score *= 1.3
            complexity_factors.append("Cross-database migration")
        
        # Compatibility issues factor
        issues_count = len(target_analysis.get('compatibility_issues', []))
        if issues_count > 0:
            complexity_score *= (1.0 + issues_count * 0.1)
            complexity_factors.append(f"{issues_count} compatibility issues")
        
        # Foreign keys factor
        if source_analysis['statistics']['has_foreign_keys']:
            complexity_score *= 1.1
            complexity_factors.append("Foreign key relationships")
        
        estimated_duration = int(base_time * complexity_score)
        
        return {
            'duration_minutes': estimated_duration,
            'size_mb': total_size_mb,
            'complexity_score': round(complexity_score, 2),
            'complexity_factors': complexity_factors
        }
    
    def _check_rollback_capability(self, source_params: Dict[str, Any], target_params: Dict[str, Any]) -> bool:
        """Check if rollback is possible for this migration"""
        source_type = source_params['database_type']
        target_type = target_params['database_type']
        
        # Same database type migrations usually support rollback
        if source_type == target_type:
            return True
        
        # Cross-database migrations have limited rollback
        # This would be more sophisticated in real implementation
        return False
    
    def _calculate_compatibility_score(self, source_type: str, target_type: str) -> int:
        """Calculate compatibility score between database types"""
        if source_type == target_type:
            return 95
        
        compatibility_matrix = {
            ('postgresql', 'mysql'): 85,
            ('mysql', 'postgresql'): 80,
            ('postgresql', 'sqlite'): 75,
            ('mysql', 'sqlite'): 75,
            ('sqlite', 'postgresql'): 70,
            ('sqlite', 'mysql'): 70,
            ('postgresql', 'mongodb'): 60,
            ('mysql', 'mongodb'): 60,
            ('sqlite', 'mongodb'): 55,
            ('mongodb', 'postgresql'): 65,
            ('mongodb', 'mysql'): 60,
            ('mongodb', 'sqlite'): 55
        }
        
        return compatibility_matrix.get((source_type, target_type), 50)
    
    def _build_type_conversion_matrix(self) -> Dict[str, Dict[str, str]]:
        """Build comprehensive type conversion matrix"""
        return {
            'postgresql_mysql': {
                'serial': 'AUTO_INCREMENT',
                'bigserial': 'BIGINT AUTO_INCREMENT',
                'boolean': 'TINYINT(1)',
                'jsonb': 'JSON',
                'text[]': 'TEXT',
                'uuid': 'CHAR(36)',
                'timestamp': 'DATETIME'
            },
            'mysql_postgresql': {
                'auto_increment': 'SERIAL',
                'tinyint(1)': 'BOOLEAN',
                'datetime': 'TIMESTAMP',
                'mediumtext': 'TEXT',
                'longtext': 'TEXT',
                'json': 'JSONB'
            },
            'postgresql_sqlite': {
                'serial': 'INTEGER',
                'bigserial': 'INTEGER',
                'boolean': 'INTEGER',
                'jsonb': 'TEXT',
                'text[]': 'TEXT',
                'uuid': 'TEXT'
            },
            'mysql_sqlite': {
                'auto_increment': 'INTEGER',
                'tinyint(1)': 'INTEGER',
                'mediumtext': 'TEXT',
                'longtext': 'TEXT',
                'json': 'TEXT'
            },
            'sqlite_postgresql': {
                'integer': 'INTEGER',
                'real': 'FLOAT',
                'text': 'TEXT',
                'blob': 'BYTEA'
            },
            'sqlite_mysql': {
                'integer': 'INT',
                'real': 'FLOAT',
                'text': 'TEXT',
                'blob': 'LONGBLOB'
            }
        }
    
    async def _get_database_schema(self, db_params: Dict[str, Any]) -> Dict[str, Any]:
        """Get database schema information (mock implementation)"""
        # This is a mock implementation
        # In real implementation, this would introspect the actual database
        return {
            'tables': [
                {
                    'name': 'users',
                    'columns': [
                        {'name': 'id', 'type': 'serial', 'primary_key': True, 'nullable': False},
                        {'name': 'email', 'type': 'varchar(255)', 'primary_key': False, 'nullable': False},
                        {'name': 'name', 'type': 'varchar(100)', 'primary_key': False, 'nullable': True},
                        {'name': 'created_at', 'type': 'timestamp', 'primary_key': False, 'nullable': False}
                    ],
                    'indexes': [{'name': 'idx_users_email', 'columns': ['email'], 'unique': True}],
                    'foreign_keys': [],
                    'row_count': 10000,
                    'size_mb': 5.2
                },
                {
                    'name': 'orders',
                    'columns': [
                        {'name': 'id', 'type': 'serial', 'primary_key': True, 'nullable': False},
                        {'name': 'user_id', 'type': 'integer', 'primary_key': False, 'nullable': False},
                        {'name': 'total', 'type': 'decimal(10,2)', 'primary_key': False, 'nullable': False},
                        {'name': 'status', 'type': 'varchar(50)', 'primary_key': False, 'nullable': False}
                    ],
                    'indexes': [{'name': 'idx_orders_user_id', 'columns': ['user_id'], 'unique': False}],
                    'foreign_keys': [{'column': 'user_id', 'references_table': 'users', 'references_column': 'id'}],
                    'row_count': 25000,
                    'size_mb': 12.8
                }
            ],
            'views': [],
            'functions': []
        }

# Global migration engine instance
migration_engine = MigrationEngine()
