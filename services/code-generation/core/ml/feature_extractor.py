"""
Feature extraction utilities for ML pipeline
"""
import logging
import asyncio
from typing import Dict, List, Any, Set
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import StandardScaler, LabelEncoder

from models.schemas import SchemaResponse, TableInfo, ColumnInfo
from .base import SchemaFeatures

logger = logging.getLogger(__name__)

class FeatureExtractor:
    """Extract ML features from schemas"""
    
    def __init__(self):
        self.text_vectorizer = TfidfVectorizer(max_features=1000, stop_words='english')
        self.label_encoders: Dict[str, LabelEncoder] = {}
        self.scalers: Dict[str, StandardScaler] = {}
        self.feature_cache: Dict[str, SchemaFeatures] = {}
    
    async def extract_schema_features(self, schema: SchemaResponse, schema_id: str) -> SchemaFeatures:
        """Extract ML features from schema"""
        
        if schema_id in self.feature_cache:
            return self.feature_cache[schema_id]
        
        # Basic structural features
        table_count = len(schema.tables)
        column_count = sum(len(table.columns) for table in schema.tables)
        relationship_count = len(schema.relationships)
        
        # Column statistics
        columns_per_table = [len(table.columns) for table in schema.tables]
        avg_columns_per_table = np.mean(columns_per_table) if columns_per_table else 0
        max_columns_per_table = max(columns_per_table) if columns_per_table else 0
        min_columns_per_table = min(columns_per_table) if columns_per_table else 0
        
        # Data type distribution
        data_type_distribution = {}
        for table in schema.tables:
            for column in table.columns:
                data_type = column.type.lower()
                data_type_distribution[data_type] = data_type_distribution.get(data_type, 0) + 1
        
        # Relationship type distribution
        relationship_types = {}
        for rel in schema.relationships:
            rel_type = rel.type if hasattr(rel, 'type') else 'unknown'
            relationship_types[rel_type] = relationship_types.get(rel_type, 0) + 1
        
        # Calculate complexity score
        complexity_score = self._calculate_complexity_score(schema)
        
        # Calculate normalization score
        normalization_score = self._calculate_normalization_score(schema)
        
        # Calculate naming consistency score
        naming_consistency_score = self._calculate_naming_consistency(schema)
        
        # Extract names
        table_names = [table.name for table in schema.tables]
        column_names = []
        for table in schema.tables:
            column_names.extend([f"{table.name}.{col.name}" for col in table.columns])
        
        features = SchemaFeatures(
            schema_id=schema_id,
            table_count=table_count,
            column_count=column_count,
            relationship_count=relationship_count,
            avg_columns_per_table=avg_columns_per_table,
            max_columns_per_table=max_columns_per_table,
            min_columns_per_table=min_columns_per_table,
            complexity_score=complexity_score,
            normalization_score=normalization_score,
            data_type_distribution=data_type_distribution,
            naming_consistency_score=naming_consistency_score,
            table_names=table_names,
            column_names=column_names,
            relationship_types=relationship_types
        )
        
        self.feature_cache[schema_id] = features
        return features
    
    def _calculate_complexity_score(self, schema: SchemaResponse) -> float:
        """Calculate schema complexity score"""
        try:
            # Factors contributing to complexity
            table_count = len(schema.tables)
            total_columns = sum(len(table.columns) for table in schema.tables)
            relationship_count = len(schema.relationships)
            
            # Calculate average relationships per table
            avg_relationships = relationship_count / table_count if table_count > 0 else 0
            
            # Calculate average columns per table
            avg_columns = total_columns / table_count if table_count > 0 else 0
            
            # Normalize and weight the factors
            table_score = min(table_count / 20, 1.0) * 0.3  # Max 20 tables
            column_score = min(avg_columns / 15, 1.0) * 0.4  # Max 15 avg columns
            relationship_score = min(avg_relationships / 5, 1.0) * 0.3  # Max 5 avg relationships
            
            return table_score + column_score + relationship_score
        
        except Exception as e:
            logger.error(f"Error calculating complexity score: {e}")
            return 0.5  # Default moderate complexity
    
    def _calculate_normalization_score(self, schema: SchemaResponse) -> float:
        """Calculate schema normalization score"""
        try:
            if not schema.tables:
                return 0.0
            
            total_score = 0.0
            table_count = len(schema.tables)
            
            for table in schema.tables:
                table_score = 0.0
                
                # Check for primary keys
                has_primary_key = any(col.primary_key for col in table.columns if hasattr(col, 'primary_key'))
                if has_primary_key:
                    table_score += 0.3
                
                # Check for foreign keys (relationships)
                foreign_key_count = sum(1 for rel in schema.relationships 
                                      if rel.from_table == table.name or rel.to_table == table.name)
                if foreign_key_count > 0:
                    table_score += 0.2
                
                # Check for reasonable column count (not too many)
                column_count = len(table.columns)
                if 3 <= column_count <= 12:
                    table_score += 0.3
                elif 13 <= column_count <= 20:
                    table_score += 0.2
                
                # Check for data type diversity
                data_types = set(col.type.lower() for col in table.columns)
                if len(data_types) > 1:
                    table_score += 0.2
                
                total_score += table_score
            
            return total_score / table_count
        
        except Exception as e:
            logger.error(f"Error calculating normalization score: {e}")
            return 0.5  # Default moderate normalization
    
    def _calculate_naming_consistency(self, schema: SchemaResponse) -> float:
        """Calculate naming consistency score"""
        try:
            if not schema.tables:
                return 1.0
            
            # Analyze table naming patterns
            table_names = [table.name for table in schema.tables]
            table_consistency = self._analyze_naming_pattern(table_names)
            
            # Analyze column naming patterns
            all_column_names = []
            for table in schema.tables:
                all_column_names.extend([col.name for col in table.columns])
            
            column_consistency = self._analyze_naming_pattern(all_column_names)
            
            # Weighted average
            return (table_consistency * 0.4) + (column_consistency * 0.6)
        
        except Exception as e:
            logger.error(f"Error calculating naming consistency: {e}")
            return 0.5  # Default moderate consistency
    
    def _analyze_naming_pattern(self, names: List[str]) -> float:
        """Analyze naming pattern consistency"""
        if not names:
            return 1.0
        
        # Check for consistent case
        case_patterns = {
            'snake_case': sum(1 for name in names if '_' in name and name.islower()),
            'camelCase': sum(1 for name in names if name[0].islower() and any(c.isupper() for c in name[1:])),
            'PascalCase': sum(1 for name in names if name[0].isupper() and any(c.isupper() for c in name[1:])),
            'lowercase': sum(1 for name in names if name.islower() and '_' not in name),
            'UPPERCASE': sum(1 for name in names if name.isupper())
        }
        
        # Find dominant pattern
        total_names = len(names)
        max_pattern_count = max(case_patterns.values())
        consistency_score = max_pattern_count / total_names
        
        return consistency_score
    
    def extract_textual_features(self, schema: SchemaResponse) -> Dict[str, Any]:
        """Extract textual features using NLP"""
        try:
            # Combine all text from schema
            text_data = []
            
            # Table names and descriptions
            for table in schema.tables:
                text_data.append(table.name)
                if hasattr(table, 'description') and table.description:
                    text_data.append(table.description)
            
            # Column names and descriptions
            for table in schema.tables:
                for column in table.columns:
                    text_data.append(column.name)
                    if hasattr(column, 'description') and column.description:
                        text_data.append(column.description)
            
            # Vectorize text
            combined_text = ' '.join(text_data)
            if combined_text.strip():
                tfidf_features = self.text_vectorizer.fit_transform([combined_text])
                feature_names = self.text_vectorizer.get_feature_names_out()
                
                return {
                    'tfidf_features': tfidf_features.toarray()[0],
                    'feature_names': feature_names.tolist(),
                    'vocabulary_size': len(feature_names)
                }
            
            return {'tfidf_features': [], 'feature_names': [], 'vocabulary_size': 0}
        
        except Exception as e:
            logger.error(f"Error extracting textual features: {e}")
            return {'tfidf_features': [], 'feature_names': [], 'vocabulary_size': 0}
    
    def prepare_features_for_ml(self, features: SchemaFeatures) -> Dict[str, Any]:
        """Prepare features for ML algorithms"""
        try:
            feature_vector = {
                # Structural features
                'table_count': features.table_count,
                'column_count': features.column_count,
                'relationship_count': features.relationship_count,
                'avg_columns_per_table': features.avg_columns_per_table,
                'max_columns_per_table': features.max_columns_per_table,
                'min_columns_per_table': features.min_columns_per_table,
                
                # Quality scores
                'complexity_score': features.complexity_score,
                'normalization_score': features.normalization_score,
                'naming_consistency_score': features.naming_consistency_score,
                
                # Data type ratios
                'total_data_types': len(features.data_type_distribution),
                'numeric_ratio': self._calculate_type_ratio(features.data_type_distribution, ['int', 'integer', 'float', 'decimal', 'number']),
                'text_ratio': self._calculate_type_ratio(features.data_type_distribution, ['varchar', 'text', 'string', 'char']),
                'date_ratio': self._calculate_type_ratio(features.data_type_distribution, ['date', 'datetime', 'timestamp']),
                'boolean_ratio': self._calculate_type_ratio(features.data_type_distribution, ['boolean', 'bool']),
                
                # Relationship features
                'total_relationship_types': len(features.relationship_types),
                'relationship_density': features.relationship_count / max(features.table_count, 1)
            }
            
            return feature_vector
        
        except Exception as e:
            logger.error(f"Error preparing features for ML: {e}")
            return {}
    
    def _calculate_type_ratio(self, data_type_dist: Dict[str, int], type_keywords: List[str]) -> float:
        """Calculate ratio of specific data types"""
        total_columns = sum(data_type_dist.values())
        if total_columns == 0:
            return 0.0
        
        matching_count = 0
        for data_type, count in data_type_dist.items():
            if any(keyword in data_type.lower() for keyword in type_keywords):
                matching_count += count
        
        return matching_count / total_columns
