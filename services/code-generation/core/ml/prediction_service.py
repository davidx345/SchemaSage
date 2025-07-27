"""
Prediction and analysis services for ML pipeline
"""
import asyncio
import logging
import uuid
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.cluster import KMeans
import networkx as nx

from models.schemas import SchemaResponse
from .base import MLPrediction, SchemaFeatures, MLTaskType
from .feature_extractor import FeatureExtractor
from .model_trainer import ModelTrainer

logger = logging.getLogger(__name__)

class PredictionService:
    """Handle ML predictions and analysis"""
    
    def __init__(self):
        self.feature_extractor = FeatureExtractor()
        self.model_trainer = ModelTrainer()
        self.prediction_cache: Dict[str, MLPrediction] = {}
    
    async def predict_schema_quality(self, schema: SchemaResponse, schema_id: str) -> Dict[str, Any]:
        """Predict overall schema quality score"""
        try:
            # Extract features
            features = await self.feature_extractor.extract_schema_features(schema, schema_id)
            feature_vector = self.feature_extractor.prepare_features_for_ml(features)
            
            # Calculate quality score based on features
            quality_score = self._calculate_quality_score(features)
            
            # Generate recommendations
            recommendations = self._generate_quality_recommendations(features)
            
            return {
                'schema_id': schema_id,
                'quality_score': quality_score,
                'quality_grade': self._get_quality_grade(quality_score),
                'recommendations': recommendations,
                'feature_scores': {
                    'complexity': features.complexity_score,
                    'normalization': features.normalization_score,
                    'naming_consistency': features.naming_consistency_score
                },
                'analysis_timestamp': datetime.now().isoformat()
            }
        
        except Exception as e:
            logger.error(f"Error predicting schema quality: {e}")
            raise
    
    async def predict_performance_impact(
        self,
        schema: SchemaResponse,
        schema_id: str,
        workload_info: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Predict performance impact of schema"""
        try:
            features = await self.feature_extractor.extract_schema_features(schema, schema_id)
            
            # Performance factors
            performance_factors = {
                'table_count_impact': self._assess_table_count_impact(features.table_count),
                'relationship_impact': self._assess_relationship_impact(features),
                'indexing_recommendations': self._generate_indexing_recommendations(schema),
                'query_complexity_prediction': self._predict_query_complexity(features)
            }
            
            # Overall performance score
            performance_score = self._calculate_performance_score(features, workload_info)
            
            return {
                'schema_id': schema_id,
                'performance_score': performance_score,
                'performance_grade': self._get_performance_grade(performance_score),
                'factors': performance_factors,
                'recommendations': self._generate_performance_recommendations(features),
                'analysis_timestamp': datetime.now().isoformat()
            }
        
        except Exception as e:
            logger.error(f"Error predicting performance impact: {e}")
            raise
    
    async def detect_schema_anomalies(
        self,
        schema: SchemaResponse,
        schema_id: str,
        historical_schemas: List[SchemaResponse] = None
    ) -> Dict[str, Any]:
        """Detect anomalies in schema structure"""
        try:
            features = await self.feature_extractor.extract_schema_features(schema, schema_id)
            
            anomalies = []
            
            # Check for structural anomalies
            structural_anomalies = self._detect_structural_anomalies(features)
            anomalies.extend(structural_anomalies)
            
            # Check for naming anomalies
            naming_anomalies = self._detect_naming_anomalies(schema)
            anomalies.extend(naming_anomalies)
            
            # Check for relationship anomalies
            relationship_anomalies = self._detect_relationship_anomalies(schema)
            anomalies.extend(relationship_anomalies)
            
            # Compare with historical schemas if available
            if historical_schemas:
                evolution_anomalies = await self._detect_evolution_anomalies(
                    schema, historical_schemas
                )
                anomalies.extend(evolution_anomalies)
            
            return {
                'schema_id': schema_id,
                'anomaly_count': len(anomalies),
                'anomalies': anomalies,
                'severity_summary': self._summarize_anomaly_severity(anomalies),
                'analysis_timestamp': datetime.now().isoformat()
            }
        
        except Exception as e:
            logger.error(f"Error detecting schema anomalies: {e}")
            raise
    
    async def analyze_schema_similarity(
        self,
        schema1: SchemaResponse,
        schema2: SchemaResponse,
        schema1_id: str,
        schema2_id: str
    ) -> Dict[str, Any]:
        """Analyze similarity between two schemas"""
        try:
            # Extract features for both schemas
            features1 = await self.feature_extractor.extract_schema_features(schema1, schema1_id)
            features2 = await self.feature_extractor.extract_schema_features(schema2, schema2_id)
            
            # Calculate different types of similarity
            structural_similarity = self._calculate_structural_similarity(features1, features2)
            semantic_similarity = self._calculate_semantic_similarity(schema1, schema2)
            relationship_similarity = self._calculate_relationship_similarity(features1, features2)
            
            # Overall similarity score
            overall_similarity = (
                structural_similarity * 0.4 +
                semantic_similarity * 0.3 +
                relationship_similarity * 0.3
            )
            
            return {
                'schema1_id': schema1_id,
                'schema2_id': schema2_id,
                'overall_similarity': overall_similarity,
                'similarity_breakdown': {
                    'structural': structural_similarity,
                    'semantic': semantic_similarity,
                    'relationship': relationship_similarity
                },
                'common_patterns': self._identify_common_patterns(schema1, schema2),
                'differences': self._identify_key_differences(features1, features2),
                'analysis_timestamp': datetime.now().isoformat()
            }
        
        except Exception as e:
            logger.error(f"Error analyzing schema similarity: {e}")
            raise
    
    async def recommend_optimizations(
        self,
        schema: SchemaResponse,
        schema_id: str,
        usage_patterns: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Recommend schema optimizations"""
        try:
            features = await self.feature_extractor.extract_schema_features(schema, schema_id)
            
            recommendations = []
            
            # Normalization recommendations
            norm_recommendations = self._generate_normalization_recommendations(schema)
            recommendations.extend(norm_recommendations)
            
            # Indexing recommendations
            index_recommendations = self._generate_indexing_recommendations(schema)
            recommendations.extend(index_recommendations)
            
            # Partitioning recommendations
            partition_recommendations = self._generate_partitioning_recommendations(
                schema, usage_patterns
            )
            recommendations.extend(partition_recommendations)
            
            # Data type optimization
            datatype_recommendations = self._generate_datatype_recommendations(schema)
            recommendations.extend(datatype_recommendations)
            
            # Prioritize recommendations
            prioritized_recommendations = self._prioritize_recommendations(recommendations)
            
            return {
                'schema_id': schema_id,
                'recommendation_count': len(prioritized_recommendations),
                'recommendations': prioritized_recommendations,
                'estimated_benefits': self._estimate_optimization_benefits(recommendations),
                'analysis_timestamp': datetime.now().isoformat()
            }
        
        except Exception as e:
            logger.error(f"Error generating optimization recommendations: {e}")
            raise
    
    def _calculate_quality_score(self, features: SchemaFeatures) -> float:
        """Calculate overall schema quality score"""
        # Weighted combination of quality factors
        quality_score = (
            features.normalization_score * 0.35 +
            features.naming_consistency_score * 0.25 +
            (1 - features.complexity_score) * 0.20 +  # Lower complexity is better
            self._calculate_relationship_quality(features) * 0.20
        )
        
        return min(max(quality_score, 0.0), 1.0)  # Clamp to [0, 1]
    
    def _calculate_performance_score(
        self,
        features: SchemaFeatures,
        workload_info: Dict[str, Any] = None
    ) -> float:
        """Calculate performance score"""
        # Base performance factors
        table_factor = 1.0 - min(features.table_count / 50, 1.0)  # Penalty for too many tables
        column_factor = 1.0 - min(features.avg_columns_per_table / 20, 1.0)  # Penalty for wide tables
        relationship_factor = min(features.relationship_count / max(features.table_count, 1) / 3, 1.0)  # Optimal relationship density
        
        performance_score = (table_factor + column_factor + relationship_factor) / 3
        
        return min(max(performance_score, 0.0), 1.0)
    
    def _get_quality_grade(self, score: float) -> str:
        """Convert quality score to grade"""
        if score >= 0.9:
            return "A+"
        elif score >= 0.8:
            return "A"
        elif score >= 0.7:
            return "B"
        elif score >= 0.6:
            return "C"
        elif score >= 0.5:
            return "D"
        else:
            return "F"
    
    def _get_performance_grade(self, score: float) -> str:
        """Convert performance score to grade"""
        return self._get_quality_grade(score)  # Same grading scale
    
    def _generate_quality_recommendations(self, features: SchemaFeatures) -> List[Dict[str, Any]]:
        """Generate quality improvement recommendations"""
        recommendations = []
        
        # Naming consistency
        if features.naming_consistency_score < 0.7:
            recommendations.append({
                'type': 'naming_consistency',
                'priority': 'medium',
                'title': 'Improve Naming Consistency',
                'description': 'Consider adopting a consistent naming convention across tables and columns',
                'impact': 'maintainability'
            })
        
        # Normalization
        if features.normalization_score < 0.6:
            recommendations.append({
                'type': 'normalization',
                'priority': 'high',
                'title': 'Improve Schema Normalization',
                'description': 'Consider normalizing tables to reduce redundancy and improve data integrity',
                'impact': 'data_quality'
            })
        
        # Complexity
        if features.complexity_score > 0.8:
            recommendations.append({
                'type': 'complexity_reduction',
                'priority': 'medium',
                'title': 'Reduce Schema Complexity',
                'description': 'Consider breaking down complex tables or reducing the number of relationships',
                'impact': 'maintainability'
            })
        
        return recommendations
    
    def _generate_performance_recommendations(self, features: SchemaFeatures) -> List[Dict[str, Any]]:
        """Generate performance improvement recommendations"""
        recommendations = []
        
        if features.table_count > 30:
            recommendations.append({
                'type': 'table_optimization',
                'priority': 'medium',
                'title': 'Consider Table Consolidation',
                'description': 'Large number of tables may impact query performance',
                'impact': 'query_performance'
            })
        
        if features.avg_columns_per_table > 15:
            recommendations.append({
                'type': 'column_optimization',
                'priority': 'medium',
                'title': 'Consider Vertical Partitioning',
                'description': 'Wide tables may benefit from vertical partitioning',
                'impact': 'query_performance'
            })
        
        return recommendations
    
    # Additional helper methods for anomaly detection, similarity analysis, etc.
    def _detect_structural_anomalies(self, features: SchemaFeatures) -> List[Dict[str, Any]]:
        """Detect structural anomalies"""
        anomalies = []
        
        # Check for extreme table counts
        if features.table_count > 100:
            anomalies.append({
                'type': 'structural',
                'severity': 'high',
                'title': 'Excessive Table Count',
                'description': f'Schema has {features.table_count} tables, which may indicate over-normalization'
            })
        
        # Check for extreme column variations
        if features.max_columns_per_table > 50:
            anomalies.append({
                'type': 'structural',
                'severity': 'medium',
                'title': 'Very Wide Table',
                'description': f'Table with {features.max_columns_per_table} columns detected'
            })
        
        return anomalies
    
    def _detect_naming_anomalies(self, schema: SchemaResponse) -> List[Dict[str, Any]]:
        """Detect naming anomalies"""
        anomalies = []
        
        # Check for reserved keywords
        reserved_keywords = {'user', 'order', 'group', 'table', 'index', 'key', 'where', 'select'}
        
        for table in schema.tables:
            if table.name.lower() in reserved_keywords:
                anomalies.append({
                    'type': 'naming',
                    'severity': 'medium',
                    'title': 'Reserved Keyword Used',
                    'description': f'Table name "{table.name}" is a reserved keyword'
                })
        
        return anomalies
    
    def _detect_relationship_anomalies(self, schema: SchemaResponse) -> List[Dict[str, Any]]:
        """Detect relationship anomalies"""
        anomalies = []
        
        # Check for tables with no relationships
        table_names = {table.name for table in schema.tables}
        tables_with_relationships = set()
        
        for rel in schema.relationships:
            tables_with_relationships.add(rel.from_table)
            tables_with_relationships.add(rel.to_table)
        
        isolated_tables = table_names - tables_with_relationships
        
        if len(isolated_tables) > len(table_names) * 0.3:  # More than 30% isolated
            anomalies.append({
                'type': 'relationship',
                'severity': 'medium',
                'title': 'Many Isolated Tables',
                'description': f'{len(isolated_tables)} tables have no relationships'
            })
        
        return anomalies
