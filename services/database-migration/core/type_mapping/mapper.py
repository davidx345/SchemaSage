"""
Data Type Mapper

Maps data types between different database systems.
"""

import logging
from typing import List, Tuple, Dict
from models.type_mapping_models import (
    TypeMappingRequest, DataTypeMapping, TargetTypeMapping,
    TypeMappingWarning, MappingSummary, MappingConfidence,
    DataLossRisk, WarningLevel, SourceDataType
)

logger = logging.getLogger(__name__)


class TypeMapper:
    """Map data types between database systems"""
    
    # Comprehensive type mapping database
    TYPE_MAPPINGS_DB = {
        "postgresql_mysql": {
            # Numeric types
            "smallint": ("smallint", MappingConfidence.EXACT, DataLossRisk.NONE),
            "integer": ("int", MappingConfidence.EXACT, DataLossRisk.NONE),
            "bigint": ("bigint", MappingConfidence.EXACT, DataLossRisk.NONE),
            "decimal": ("decimal", MappingConfidence.EXACT, DataLossRisk.NONE),
            "numeric": ("decimal", MappingConfidence.EXACT, DataLossRisk.NONE),
            "real": ("float", MappingConfidence.HIGH, DataLossRisk.LOW),
            "double precision": ("double", MappingConfidence.EXACT, DataLossRisk.NONE),
            "serial": ("int auto_increment", MappingConfidence.HIGH, DataLossRisk.NONE),
            "bigserial": ("bigint auto_increment", MappingConfidence.HIGH, DataLossRisk.NONE),
            
            # String types
            "varchar": ("varchar", MappingConfidence.EXACT, DataLossRisk.NONE),
            "char": ("char", MappingConfidence.EXACT, DataLossRisk.NONE),
            "text": ("longtext", MappingConfidence.HIGH, DataLossRisk.NONE),
            
            # Binary types
            "bytea": ("blob", MappingConfidence.HIGH, DataLossRisk.LOW),
            
            # Date/Time types
            "timestamp": ("datetime", MappingConfidence.HIGH, DataLossRisk.LOW),
            "timestamptz": ("datetime", MappingConfidence.MEDIUM, DataLossRisk.MEDIUM),
            "date": ("date", MappingConfidence.EXACT, DataLossRisk.NONE),
            "time": ("time", MappingConfidence.EXACT, DataLossRisk.NONE),
            "interval": (None, MappingConfidence.NONE, DataLossRisk.CRITICAL),
            
            # Boolean
            "boolean": ("tinyint(1)", MappingConfidence.HIGH, DataLossRisk.NONE),
            
            # JSON
            "json": ("json", MappingConfidence.EXACT, DataLossRisk.NONE),
            "jsonb": ("json", MappingConfidence.MEDIUM, DataLossRisk.LOW),
            
            # Special types
            "uuid": ("char(36)", MappingConfidence.MEDIUM, DataLossRisk.LOW),
            "array": (None, MappingConfidence.NONE, DataLossRisk.CRITICAL),
            "hstore": (None, MappingConfidence.NONE, DataLossRisk.CRITICAL),
        },
        "mysql_postgresql": {
            # Numeric types
            "tinyint": ("smallint", MappingConfidence.HIGH, DataLossRisk.LOW),
            "smallint": ("smallint", MappingConfidence.EXACT, DataLossRisk.NONE),
            "int": ("integer", MappingConfidence.EXACT, DataLossRisk.NONE),
            "bigint": ("bigint", MappingConfidence.EXACT, DataLossRisk.NONE),
            "decimal": ("decimal", MappingConfidence.EXACT, DataLossRisk.NONE),
            "float": ("real", MappingConfidence.HIGH, DataLossRisk.LOW),
            "double": ("double precision", MappingConfidence.EXACT, DataLossRisk.NONE),
            
            # String types
            "varchar": ("varchar", MappingConfidence.EXACT, DataLossRisk.NONE),
            "char": ("char", MappingConfidence.EXACT, DataLossRisk.NONE),
            "text": ("text", MappingConfidence.EXACT, DataLossRisk.NONE),
            "longtext": ("text", MappingConfidence.EXACT, DataLossRisk.NONE),
            "mediumtext": ("text", MappingConfidence.EXACT, DataLossRisk.NONE),
            
            # Binary types
            "blob": ("bytea", MappingConfidence.HIGH, DataLossRisk.LOW),
            "longblob": ("bytea", MappingConfidence.HIGH, DataLossRisk.LOW),
            
            # Date/Time types
            "datetime": ("timestamp", MappingConfidence.HIGH, DataLossRisk.LOW),
            "date": ("date", MappingConfidence.EXACT, DataLossRisk.NONE),
            "time": ("time", MappingConfidence.EXACT, DataLossRisk.NONE),
            "timestamp": ("timestamp", MappingConfidence.HIGH, DataLossRisk.LOW),
            
            # JSON
            "json": ("jsonb", MappingConfidence.HIGH, DataLossRisk.NONE),
            
            # Special types
            "enum": ("varchar with check constraint", MappingConfidence.MEDIUM, DataLossRisk.MEDIUM),
        },
        "postgresql_sqlserver": {
            # Numeric types
            "smallint": ("smallint", MappingConfidence.EXACT, DataLossRisk.NONE),
            "integer": ("int", MappingConfidence.EXACT, DataLossRisk.NONE),
            "bigint": ("bigint", MappingConfidence.EXACT, DataLossRisk.NONE),
            "decimal": ("decimal", MappingConfidence.EXACT, DataLossRisk.NONE),
            "numeric": ("numeric", MappingConfidence.EXACT, DataLossRisk.NONE),
            "real": ("real", MappingConfidence.EXACT, DataLossRisk.NONE),
            "double precision": ("float", MappingConfidence.HIGH, DataLossRisk.LOW),
            "serial": ("int identity(1,1)", MappingConfidence.HIGH, DataLossRisk.NONE),
            "bigserial": ("bigint identity(1,1)", MappingConfidence.HIGH, DataLossRisk.NONE),
            
            # String types
            "varchar": ("varchar", MappingConfidence.EXACT, DataLossRisk.NONE),
            "char": ("char", MappingConfidence.EXACT, DataLossRisk.NONE),
            "text": ("varchar(max)", MappingConfidence.HIGH, DataLossRisk.NONE),
            
            # Binary types
            "bytea": ("varbinary(max)", MappingConfidence.HIGH, DataLossRisk.LOW),
            
            # Date/Time types
            "timestamp": ("datetime2", MappingConfidence.HIGH, DataLossRisk.LOW),
            "timestamptz": ("datetimeoffset", MappingConfidence.HIGH, DataLossRisk.LOW),
            "date": ("date", MappingConfidence.EXACT, DataLossRisk.NONE),
            "time": ("time", MappingConfidence.EXACT, DataLossRisk.NONE),
            
            # Boolean
            "boolean": ("bit", MappingConfidence.HIGH, DataLossRisk.NONE),
            
            # JSON
            "json": ("nvarchar(max)", MappingConfidence.MEDIUM, DataLossRisk.MEDIUM),
            "jsonb": ("nvarchar(max)", MappingConfidence.MEDIUM, DataLossRisk.MEDIUM),
            
            # Special types
            "uuid": ("uniqueidentifier", MappingConfidence.EXACT, DataLossRisk.NONE),
            "array": (None, MappingConfidence.NONE, DataLossRisk.CRITICAL),
        }
    }
    
    def __init__(self):
        self.mappings: List[DataTypeMapping] = []
        
    def map_types(self, request: TypeMappingRequest) -> Tuple[MappingSummary, List[DataTypeMapping], List[str], List[str]]:
        """
        Map data types between databases
        
        Args:
            request: Type mapping request
            
        Returns:
            Tuple of (summary, mappings, recommendations, unsupported_types)
        """
        self.mappings = []
        
        source_db = request.source_db_type.value
        target_db = request.target_db_type.value
        mapping_key = f"{source_db}_{target_db}"
        
        # Get mapping database
        type_db = self.TYPE_MAPPINGS_DB.get(mapping_key, {})
        
        # Map each source type
        for source_type in request.source_types:
            mapping = self._map_single_type(
                source_type, type_db, source_db, target_db,
                request.preserve_precision, request.allow_lossy_conversion
            )
            self.mappings.append(mapping)
        
        # Generate summary
        summary = self._generate_summary()
        
        # Generate recommendations
        recommendations = self._generate_recommendations(summary, request)
        
        # Collect unsupported types
        unsupported_types = [
            m.source_type.type_name
            for m in self.mappings
            if m.mapping_confidence == MappingConfidence.NONE
        ]
        
        return summary, self.mappings, recommendations, unsupported_types
    
    def _map_single_type(
        self,
        source_type: SourceDataType,
        type_db: Dict,
        source_db: str,
        target_db: str,
        preserve_precision: bool,
        allow_lossy: bool
    ) -> DataTypeMapping:
        """Map a single data type"""
        type_name = source_type.type_name.lower()
        
        # Get mapping from database
        if type_name in type_db:
            target_type_name, confidence, risk = type_db[type_name]
            
            if target_type_name is None:
                # Unsupported type
                return self._create_unsupported_mapping(source_type, type_name)
            
            # Create target type
            target_type = TargetTypeMapping(
                type_name=target_type_name,
                max_length=source_type.max_length,
                precision=source_type.precision,
                scale=source_type.scale,
                sql_definition=self._build_sql_definition(
                    target_type_name,
                    source_type.max_length,
                    source_type.precision,
                    source_type.scale
                )
            )
            
            # Generate warnings
            warnings = self._generate_type_warnings(
                source_type, target_type, confidence, risk, preserve_precision, allow_lossy
            )
            
            # Determine if conversion is needed
            requires_conversion = confidence in [MappingConfidence.MEDIUM, MappingConfidence.LOW]
            
            return DataTypeMapping(
                source_type=source_type,
                target_type=target_type,
                mapping_confidence=confidence,
                data_loss_risk=risk,
                is_direct_mapping=(confidence == MappingConfidence.EXACT),
                requires_conversion=requires_conversion,
                warnings=warnings,
                notes=[]
            )
        else:
            # Unknown type - try to provide a reasonable default
            return self._create_unknown_type_mapping(source_type, type_name, target_db)
    
    def _create_unsupported_mapping(self, source_type: SourceDataType, type_name: str) -> DataTypeMapping:
        """Create mapping for unsupported type"""
        target_type = TargetTypeMapping(
            type_name="TEXT",
            sql_definition="TEXT"
        )
        
        warning = TypeMappingWarning(
            level=WarningLevel.CRITICAL,
            category="unsupported_type",
            message=f"Type '{type_name}' is not supported in target database",
            recommendation="Consider redesigning schema or using alternative approach"
        )
        
        return DataTypeMapping(
            source_type=source_type,
            target_type=target_type,
            mapping_confidence=MappingConfidence.NONE,
            data_loss_risk=DataLossRisk.CRITICAL,
            is_direct_mapping=False,
            requires_conversion=True,
            warnings=[warning],
            notes=["This type requires manual intervention"]
        )
    
    def _create_unknown_type_mapping(self, source_type: SourceDataType, type_name: str, target_db: str) -> DataTypeMapping:
        """Create mapping for unknown type"""
        # Provide reasonable defaults
        if "int" in type_name:
            target_name = "INTEGER"
        elif "char" in type_name or "text" in type_name:
            target_name = "VARCHAR(255)"
        elif "date" in type_name or "time" in type_name:
            target_name = "TIMESTAMP"
        else:
            target_name = "TEXT"
        
        target_type = TargetTypeMapping(
            type_name=target_name,
            sql_definition=target_name
        )
        
        warning = TypeMappingWarning(
            level=WarningLevel.WARNING,
            category="unknown_type",
            message=f"Unknown type '{type_name}' - using best guess: {target_name}",
            recommendation="Manually verify this type mapping"
        )
        
        return DataTypeMapping(
            source_type=source_type,
            target_type=target_type,
            mapping_confidence=MappingConfidence.LOW,
            data_loss_risk=DataLossRisk.MEDIUM,
            is_direct_mapping=False,
            requires_conversion=True,
            warnings=[warning],
            notes=["Type mapping based on heuristic - requires verification"]
        )
    
    def _build_sql_definition(self, type_name: str, max_length: int = None, precision: int = None, scale: int = None) -> str:
        """Build complete SQL type definition"""
        if precision is not None and scale is not None:
            return f"{type_name}({precision},{scale})"
        elif precision is not None:
            return f"{type_name}({precision})"
        elif max_length is not None:
            return f"{type_name}({max_length})"
        else:
            return type_name
    
    def _generate_type_warnings(
        self,
        source_type: SourceDataType,
        target_type: TargetTypeMapping,
        confidence: MappingConfidence,
        risk: DataLossRisk,
        preserve_precision: bool,
        allow_lossy: bool
    ) -> List[TypeMappingWarning]:
        """Generate warnings for type mapping"""
        warnings = []
        
        if risk == DataLossRisk.CRITICAL and not allow_lossy:
            warnings.append(TypeMappingWarning(
                level=WarningLevel.CRITICAL,
                category="data_loss",
                message="High risk of data loss during conversion",
                recommendation="Review data carefully and consider alternative approaches"
            ))
        elif risk in [DataLossRisk.HIGH, DataLossRisk.MEDIUM]:
            warnings.append(TypeMappingWarning(
                level=WarningLevel.WARNING,
                category="data_loss",
                message=f"{risk.value.title()} risk of data loss",
                recommendation="Test conversion with representative data"
            ))
        
        if preserve_precision and source_type.precision:
            if not target_type.precision or target_type.precision < source_type.precision:
                warnings.append(TypeMappingWarning(
                    level=WarningLevel.WARNING,
                    category="precision_loss",
                    message="Target type may not preserve source precision",
                    recommendation="Verify precision requirements"
                ))
        
        if confidence == MappingConfidence.LOW:
            warnings.append(TypeMappingWarning(
                level=WarningLevel.ERROR,
                category="low_confidence",
                message="Low confidence in type mapping",
                recommendation="Manual review and testing required"
            ))
        
        return warnings
    
    def _generate_summary(self) -> MappingSummary:
        """Generate mapping summary"""
        exact = sum(1 for m in self.mappings if m.mapping_confidence == MappingConfidence.EXACT)
        approximate = sum(1 for m in self.mappings if m.mapping_confidence in [MappingConfidence.HIGH, MappingConfidence.MEDIUM])
        lossy = sum(1 for m in self.mappings if m.data_loss_risk in [DataLossRisk.HIGH, DataLossRisk.CRITICAL])
        
        # Count warnings by level
        all_warnings = [w for m in self.mappings for w in m.warnings]
        critical_warnings = sum(1 for w in all_warnings if w.level == WarningLevel.CRITICAL)
        error_warnings = sum(1 for w in all_warnings if w.level == WarningLevel.ERROR)
        
        # Determine overall confidence
        if exact == len(self.mappings):
            overall_confidence = MappingConfidence.EXACT
        elif exact + approximate == len(self.mappings):
            overall_confidence = MappingConfidence.HIGH
        elif approximate > len(self.mappings) / 2:
            overall_confidence = MappingConfidence.MEDIUM
        else:
            overall_confidence = MappingConfidence.LOW
        
        # Determine overall risk
        if lossy > len(self.mappings) / 2:
            overall_risk = DataLossRisk.HIGH
        elif lossy > 0:
            overall_risk = DataLossRisk.MEDIUM
        else:
            overall_risk = DataLossRisk.LOW
        
        return MappingSummary(
            total_types=len(self.mappings),
            exact_mappings=exact,
            approximate_mappings=approximate,
            lossy_mappings=lossy,
            critical_warnings=critical_warnings,
            error_warnings=error_warnings,
            overall_confidence=overall_confidence,
            overall_data_loss_risk=overall_risk
        )
    
    def _generate_recommendations(self, summary: MappingSummary, request: TypeMappingRequest) -> List[str]:
        """Generate general recommendations"""
        recommendations = []
        
        if summary.lossy_mappings > 0:
            recommendations.append(
                f"Test data conversion thoroughly - {summary.lossy_mappings} types have potential data loss"
            )
        
        if summary.critical_warnings > 0:
            recommendations.append(
                f"Address {summary.critical_warnings} critical warnings before proceeding"
            )
        
        if summary.overall_confidence in [MappingConfidence.LOW, MappingConfidence.MEDIUM]:
            recommendations.append(
                "Manual review of all type mappings recommended due to lower confidence"
            )
        
        recommendations.append("Always validate migrated data against source")
        recommendations.append("Consider creating comprehensive test dataset")
        
        return recommendations


def map_data_types(request: TypeMappingRequest) -> Tuple[MappingSummary, List[DataTypeMapping], List[str], List[str]]:
    """
    Convenience function to map data types
    
    Args:
        request: Type mapping request
        
    Returns:
        Tuple of (summary, mappings, recommendations, unsupported_types)
    """
    mapper = TypeMapper()
    return mapper.map_types(request)
