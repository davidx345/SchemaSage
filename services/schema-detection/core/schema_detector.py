"""
Schema Detection Core Logic - Modular Version

Main orchestrator for schema detection using specialized modules.
"""
from typing import Dict, List, Optional, Any, Union, Tuple
import logging
from datetime import datetime

from .data_parser import DataParser
from .schema_analyzer import SchemaAnalyzer
from .ai_enhancer import AISchemaEnhancer
from ..models.schemas import (
    SchemaResponse, TableInfo, ColumnInfo, ColumnStatistics, 
    Relationship, SchemaSettings, RelationshipType,
    RelationshipSuggestionResponse, CrossDatasetRelationshipResponse
)

logger = logging.getLogger(__name__)


class SchemaValidationError(Exception):
    """Schema validation error."""
    pass


class SchemaDetector:
    """Advanced schema detection with AI-powered inference."""
    
    def __init__(self):
        self.data_parser = DataParser()
        self.schema_analyzer = SchemaAnalyzer()
        self.ai_enhancer = AISchemaEnhancer()
        self.settings = SchemaSettings()
    
    def configure_settings(self, settings: SchemaSettings):
        """Configure detection settings."""
        self.settings = settings
    
    async def detect_schema(
        self, 
        data: str, 
        file_format: str = None, 
        table_name: str = "detected_table",
        enable_ai: bool = True
    ) -> SchemaResponse:
        """Main entry point for schema detection."""
        try:
            # Step 1: Parse the data
            parsed_data = self.data_parser.parse_data(data, file_format)
            
            if not parsed_data:
                raise SchemaValidationError("No valid data found to analyze")
            
            # Step 2: Normalize and sample data if needed
            normalized_data = self.data_parser.normalize_data(parsed_data)
            
            if self.settings.sample_size and len(normalized_data) > self.settings.sample_size:
                sampled_data = self.data_parser.sample_data(normalized_data, self.settings.sample_size)
            else:
                sampled_data = normalized_data
            
            # Step 3: Analyze schema
            table_info = self.schema_analyzer.analyze_table(sampled_data, table_name)
            
            # Step 4: Get schema improvement suggestions
            suggestions = self.schema_analyzer.suggest_improvements(table_info)
            
            # Step 5: AI enhancement (if enabled)
            ai_insights = {}
            if enable_ai and self.settings.enable_ai_enhancement:
                ai_insights = await self.ai_enhancer.enhance_schema_with_ai(
                    table_info, 
                    sampled_data[:5]  # Send small sample for AI analysis
                )
            
            # Step 6: Build response
            response = SchemaResponse(
                table_name=table_name,
                tables=[table_info],
                relationships=[],  # Single table, no relationships
                confidence_score=self._calculate_confidence_score(table_info),
                suggestions=suggestions,
                metadata={
                    "total_rows": len(normalized_data),
                    "sampled_rows": len(sampled_data),
                    "detected_format": self.data_parser.detect_format(data),
                    "analysis_timestamp": datetime.now().isoformat(),
                    "ai_insights": ai_insights
                }
            )
            
            return response
        
        except Exception as e:
            logger.error(f"Schema detection failed: {e}")
            raise SchemaValidationError(f"Schema detection failed: {str(e)}")
    
    async def suggest_relationships(
        self, 
        tables: List[TableInfo], 
        enable_ai: bool = True
    ) -> RelationshipSuggestionResponse:
        """Suggest relationships between multiple tables."""
        relationships = []
        
        try:
            # Rule-based relationship detection
            rule_based_relationships = self._detect_relationships_by_rules(tables)
            relationships.extend(rule_based_relationships)
            
            # AI-powered relationship suggestions
            if enable_ai and self.settings.enable_ai_enhancement:
                ai_relationships = await self.ai_enhancer.suggest_relationships(tables)
                relationships.extend(ai_relationships)
            
            # Remove duplicates and sort by confidence
            unique_relationships = self._deduplicate_relationships(relationships)
            unique_relationships.sort(key=lambda r: r.confidence_score, reverse=True)
            
            return RelationshipSuggestionResponse(
                relationships=unique_relationships,
                confidence_score=self._calculate_relationship_confidence(unique_relationships),
                metadata={
                    "analysis_timestamp": datetime.now().isoformat(),
                    "total_tables": len(tables),
                    "rule_based_count": len(rule_based_relationships),
                    "ai_suggested_count": len(ai_relationships) if enable_ai else 0
                }
            )
        
        except Exception as e:
            logger.error(f"Relationship suggestion failed: {e}")
            return RelationshipSuggestionResponse(
                relationships=[],
                confidence_score=0.0,
                metadata={"error": str(e)}
            )
    
    async def analyze_cross_dataset_relationships(
        self, 
        datasets: Dict[str, List[Dict[str, Any]]]
    ) -> CrossDatasetRelationshipResponse:
        """Analyze relationships across multiple datasets."""
        try:
            # Analyze each dataset
            table_infos = []
            for dataset_name, dataset_data in datasets.items():
                normalized_data = self.data_parser.normalize_data(dataset_data)
                table_info = self.schema_analyzer.analyze_table(normalized_data, dataset_name)
                table_infos.append(table_info)
            
            # Suggest relationships
            relationship_response = await self.suggest_relationships(table_infos, enable_ai=True)
            
            return CrossDatasetRelationshipResponse(
                datasets=list(datasets.keys()),
                relationships=relationship_response.relationships,
                schema_overlap=self._calculate_schema_overlap(table_infos),
                confidence_score=relationship_response.confidence_score,
                metadata={
                    "analysis_timestamp": datetime.now().isoformat(),
                    "dataset_count": len(datasets),
                    "total_tables": len(table_infos)
                }
            )
        
        except Exception as e:
            logger.error(f"Cross-dataset analysis failed: {e}")
            return CrossDatasetRelationshipResponse(
                datasets=list(datasets.keys()),
                relationships=[],
                schema_overlap={},
                confidence_score=0.0,
                metadata={"error": str(e)}
            )
    
    def _detect_relationships_by_rules(self, tables: List[TableInfo]) -> List[Relationship]:
        """Detect relationships using rule-based approaches."""
        relationships = []
        
        for i, source_table in enumerate(tables):
            for j, target_table in enumerate(tables):
                if i >= j:  # Avoid duplicates and self-references
                    continue
                
                # Look for potential foreign key relationships
                for source_col in source_table.columns:
                    for target_col in target_table.columns:
                        # Check if column names suggest a relationship
                        relationship = self._check_column_relationship(
                            source_table.name, source_col,
                            target_table.name, target_col
                        )
                        if relationship:
                            relationships.append(relationship)
        
        return relationships
    
    def _check_column_relationship(
        self, 
        source_table: str, source_col: ColumnInfo,
        target_table: str, target_col: ColumnInfo
    ) -> Optional[Relationship]:
        """Check if two columns might be related."""
        
        # Check for exact name matches
        if source_col.name == target_col.name and source_col.data_type == target_col.data_type:
            return Relationship(
                source_table=source_table,
                source_column=source_col.name,
                target_table=target_table,
                target_column=target_col.name,
                relationship_type=RelationshipType.ONE_TO_MANY,
                confidence_score=0.8
            )
        
        # Check for foreign key naming patterns
        fk_patterns = [
            f"{target_table}_id",
            f"{target_table}Id", 
            f"{target_table}_key",
            f"fk_{target_table}"
        ]
        
        if (source_col.name.lower() in [p.lower() for p in fk_patterns] and 
            target_col.name.lower() in ['id', 'key', 'pk'] and
            source_col.data_type == target_col.data_type):
            return Relationship(
                source_table=source_table,
                source_column=source_col.name,
                target_table=target_table,
                target_column=target_col.name,
                relationship_type=RelationshipType.ONE_TO_MANY,
                confidence_score=0.7
            )
        
        return None
    
    def _deduplicate_relationships(self, relationships: List[Relationship]) -> List[Relationship]:
        """Remove duplicate relationships."""
        seen = set()
        unique = []
        
        for rel in relationships:
            key = (rel.source_table, rel.source_column, rel.target_table, rel.target_column)
            if key not in seen:
                seen.add(key)
                unique.append(rel)
        
        return unique
    
    def _calculate_confidence_score(self, table_info: TableInfo) -> float:
        """Calculate overall confidence score for schema detection."""
        if not table_info.columns:
            return 0.0
        
        # Base score on data type detection confidence
        type_confidence = 0.0
        for column in table_info.columns:
            if column.data_type != 'string':  # Non-string types have higher confidence
                type_confidence += 0.8
            else:
                type_confidence += 0.6
        
        avg_confidence = type_confidence / len(table_info.columns)
        
        # Boost confidence if we have good statistics
        stats_boost = 0.0
        columns_with_stats = sum(1 for col in table_info.columns if col.statistics)
        if columns_with_stats > 0:
            stats_boost = 0.1 * (columns_with_stats / len(table_info.columns))
        
        return min(1.0, avg_confidence + stats_boost)
    
    def _calculate_relationship_confidence(self, relationships: List[Relationship]) -> float:
        """Calculate confidence for relationship suggestions."""
        if not relationships:
            return 0.0
        
        total_confidence = sum(rel.confidence_score for rel in relationships)
        return total_confidence / len(relationships)
    
    def _calculate_schema_overlap(self, tables: List[TableInfo]) -> Dict[str, Any]:
        """Calculate schema overlap between tables."""
        if len(tables) < 2:
            return {}
        
        # Collect all column names and types
        all_columns = {}
        for table in tables:
            for column in table.columns:
                key = f"{column.name}:{column.data_type}"
                if key not in all_columns:
                    all_columns[key] = []
                all_columns[key].append(table.name)
        
        # Find overlapping columns
        overlapping_columns = {
            key: table_list for key, table_list in all_columns.items() 
            if len(table_list) > 1
        }
        
        return {
            "total_unique_columns": len(all_columns),
            "overlapping_columns": len(overlapping_columns),
            "overlap_percentage": len(overlapping_columns) / len(all_columns) * 100 if all_columns else 0,
            "common_columns": overlapping_columns
        }
