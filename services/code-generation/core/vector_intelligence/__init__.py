"""
Vector intelligence orchestrator module
Main interface for schema intelligence and vector operations
"""

import logging
from typing import Dict, List, Any, Optional, Union
import asyncio
import time
import numpy as np
from datetime import datetime

from models.schemas import SchemaResponse, TableInfo, ColumnInfo
from .models import (
    SchemaEmbedding, SimilarityResult, QueryContext, PatternMatch,
    SemanticSearchRequest, SemanticSearchResponse, PatternDetectionRequest,
    PatternDetectionResponse, ClusteringRequest, ClusteringResponse,
    EmbeddingType, SimilarityMetric, ClusteringMethod, SchemaCluster
)
from .embedding_generator import SchemaEmbeddingGenerator
from .vector_database import InMemoryVectorDB, SQLiteVectorDB
from .pattern_detector import SchemaPatternDetector
from .clustering import SchemaClustering

logger = logging.getLogger(__name__)


class VectorIntelligenceOrchestrator:
    """
    Main orchestrator for vector intelligence operations
    Provides semantic search, pattern detection, and clustering for schemas
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize vector intelligence orchestrator
        
        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        
        # Initialize components
        model_name = self.config.get('embedding_model', 'all-MiniLM-L6-v2')
        self.embedding_generator = SchemaEmbeddingGenerator(model_name)
        
        # Initialize vector database
        db_type = self.config.get('database_type', 'memory')
        if db_type == 'sqlite':
            db_path = self.config.get('database_path', 'vector_db.sqlite')
            self.vector_db = SQLiteVectorDB(db_path)
        else:
            self.vector_db = InMemoryVectorDB()
        
        # Initialize pattern detector and clustering
        self.pattern_detector = SchemaPatternDetector()
        self.clustering = SchemaClustering()
        
        # Cache for frequent operations
        self._query_cache: Dict[str, Any] = {}
        self._cache_ttl = self.config.get('cache_ttl', 300)  # 5 minutes
        
        logger.info("Vector intelligence orchestrator initialized")
    
    # Schema Processing
    
    async def process_schema(self, schema: SchemaResponse) -> Dict[str, Any]:
        """
        Process complete schema and generate embeddings
        
        Args:
            schema: Schema response object
            
        Returns:
            Processing results with embedding IDs
        """
        try:
            results = {
                'schema_embedding_id': None,
                'table_embedding_ids': [],
                'column_embedding_ids': [],
                'processing_time_ms': 0
            }
            
            start_time = time.time()
            
            # Generate schema embedding
            schema_embedding = self.embedding_generator.generate_schema_embedding(schema)
            await self.vector_db.insert_embedding(schema_embedding)
            results['schema_embedding_id'] = schema_embedding.embedding_id
            
            # Generate table embeddings
            for table in schema.tables:
                table_embedding = self.embedding_generator.generate_table_embedding(
                    table, schema.schema_name
                )
                await self.vector_db.insert_embedding(table_embedding)
                results['table_embedding_ids'].append(table_embedding.embedding_id)
                
                # Generate column embeddings
                for column in table.columns:
                    column_embedding = self.embedding_generator.generate_column_embedding(
                        column, table.table_name, schema.schema_name
                    )
                    await self.vector_db.insert_embedding(column_embedding)
                    results['column_embedding_ids'].append(column_embedding.embedding_id)
            
            results['processing_time_ms'] = (time.time() - start_time) * 1000
            
            logger.info(f"Processed schema {schema.schema_name} - "
                       f"Generated {1 + len(results['table_embedding_ids']) + len(results['column_embedding_ids'])} embeddings")
            
            return results
            
        except Exception as e:
            logger.error(f"Error processing schema {schema.schema_name}: {e}")
            raise
    
    async def process_table(self, table: TableInfo, schema_name: str = None) -> Dict[str, Any]:
        """
        Process individual table and generate embeddings
        
        Args:
            table: Table info object
            schema_name: Optional schema name
            
        Returns:
            Processing results
        """
        try:
            results = {
                'table_embedding_id': None,
                'column_embedding_ids': [],
                'processing_time_ms': 0
            }
            
            start_time = time.time()
            
            # Generate table embedding
            table_embedding = self.embedding_generator.generate_table_embedding(table, schema_name)
            await self.vector_db.insert_embedding(table_embedding)
            results['table_embedding_id'] = table_embedding.embedding_id
            
            # Generate column embeddings
            for column in table.columns:
                column_embedding = self.embedding_generator.generate_column_embedding(
                    column, table.table_name, schema_name
                )
                await self.vector_db.insert_embedding(column_embedding)
                results['column_embedding_ids'].append(column_embedding.embedding_id)
            
            results['processing_time_ms'] = (time.time() - start_time) * 1000
            
            logger.info(f"Processed table {table.table_name} - "
                       f"Generated {1 + len(results['column_embedding_ids'])} embeddings")
            
            return results
            
        except Exception as e:
            logger.error(f"Error processing table {table.table_name}: {e}")
            raise
    
    # Semantic Search
    
    async def semantic_search(self, request: SemanticSearchRequest) -> SemanticSearchResponse:
        """
        Perform semantic search for schemas
        
        Args:
            request: Search request
            
        Returns:
            Search response with results
        """
        try:
            start_time = time.time()
            
            # Check cache
            cache_key = self._generate_cache_key('search', request.query, request.search_type.value)
            cached_result = self._get_from_cache(cache_key)
            if cached_result:
                logger.debug(f"Returning cached search results for query: {request.query}")
                return cached_result
            
            # Generate query embedding
            query_embedding = self.embedding_generator.generate_query_embedding(request.query)
            
            # Create query context
            context = QueryContext(
                query_text=request.query,
                query_type=request.search_type,
                filters=request.filters,
                similarity_threshold=request.similarity_threshold,
                max_results=request.max_results,
                boost_factors=request.boost_factors
            )
            
            # Perform search
            results = await self.vector_db.search_similar(query_embedding, context)
            
            # Apply post-processing
            if request.boost_recent:
                results = self._boost_recent_results(results)
            
            search_time = (time.time() - start_time) * 1000
            
            response = SemanticSearchResponse(
                query=request.query,
                results=results,
                total_results=len(results),
                search_time_ms=search_time,
                metadata={
                    'embedding_model': self.embedding_generator.model_name,
                    'similarity_threshold': request.similarity_threshold,
                    'filters_applied': bool(request.filters)
                }
            )
            
            # Cache result
            self._cache_result(cache_key, response)
            
            logger.info(f"Semantic search completed - Query: '{request.query}', Results: {len(results)}")
            return response
            
        except Exception as e:
            logger.error(f"Error in semantic search: {e}")
            raise
    
    async def find_similar_schemas(
        self,
        schema_id: str,
        limit: int = 10,
        similarity_threshold: float = 0.7
    ) -> List[SimilarityResult]:
        """
        Find schemas similar to given schema
        
        Args:
            schema_id: ID of reference schema
            limit: Maximum results
            similarity_threshold: Minimum similarity score
            
        Returns:
            List of similar schemas
        """
        try:
            # Get reference schema embedding
            reference_embedding = await self.vector_db.get_embedding(schema_id)
            if not reference_embedding:
                raise ValueError(f"Schema embedding {schema_id} not found")
            
            # Search for similar schemas
            context = QueryContext(
                query_text="",
                query_type=EmbeddingType.SCHEMA,
                similarity_threshold=similarity_threshold,
                max_results=limit
            )
            
            results = await self.vector_db.search_similar(reference_embedding.embedding, context)
            
            # Filter out the reference schema itself
            results = [r for r in results if r.embedding_id != schema_id]
            
            logger.info(f"Found {len(results)} similar schemas for {schema_id}")
            return results
            
        except Exception as e:
            logger.error(f"Error finding similar schemas for {schema_id}: {e}")
            raise
    
    # Pattern Detection
    
    async def detect_patterns(self, request: PatternDetectionRequest) -> PatternDetectionResponse:
        """
        Detect patterns in schema data
        
        Args:
            request: Pattern detection request
            
        Returns:
            Pattern detection response
        """
        try:
            start_time = time.time()
            
            # Detect patterns using pattern detector
            patterns = await self.pattern_detector.detect_patterns(
                request.schema_data,
                pattern_types=request.pattern_types,
                confidence_threshold=request.confidence_threshold,
                max_patterns=request.max_patterns
            )
            
            detection_time = (time.time() - start_time) * 1000
            
            response = PatternDetectionResponse(
                schema_id=request.schema_data.get('schema_id', 'unknown'),
                patterns=patterns,
                detection_time_ms=detection_time,
                metadata={
                    'pattern_types_requested': request.pattern_types,
                    'confidence_threshold': request.confidence_threshold,
                    'total_patterns_found': len(patterns)
                }
            )
            
            logger.info(f"Pattern detection completed - Found {len(patterns)} patterns")
            return response
            
        except Exception as e:
            logger.error(f"Error in pattern detection: {e}")
            raise
    
    # Clustering
    
    async def cluster_schemas(self, request: ClusteringRequest) -> ClusteringResponse:
        """
        Cluster schemas based on similarity
        
        Args:
            request: Clustering request
            
        Returns:
            Clustering response
        """
        try:
            start_time = time.time()
            
            # Get embeddings for clustering
            embeddings = []
            embedding_ids = []
            
            for embedding_id in request.embedding_ids:
                embedding = await self.vector_db.get_embedding(embedding_id)
                if embedding:
                    embeddings.append(embedding.embedding)
                    embedding_ids.append(embedding_id)
            
            if len(embeddings) < request.min_cluster_size:
                raise ValueError(f"Not enough embeddings for clustering: {len(embeddings)} < {request.min_cluster_size}")
            
            # Perform clustering
            clustering_result = await self.clustering.cluster_embeddings(
                embeddings,
                embedding_ids,
                method=request.method,
                num_clusters=request.num_clusters,
                parameters=request.parameters
            )
            
            clustering_time = (time.time() - start_time) * 1000
            
            response = ClusteringResponse(
                clusters=clustering_result['clusters'],
                outliers=clustering_result.get('outliers', []),
                silhouette_score=clustering_result.get('silhouette_score', 0.0),
                clustering_time_ms=clustering_time,
                metadata={
                    'method': request.method.value,
                    'num_embeddings': len(embeddings),
                    'num_clusters': len(clustering_result['clusters'])
                }
            )
            
            logger.info(f"Clustering completed - {len(clustering_result['clusters'])} clusters found")
            return response
            
        except Exception as e:
            logger.error(f"Error in clustering: {e}")
            raise
    
    # Database Management
    
    async def get_embedding_statistics(self):
        """Get embedding database statistics"""
        try:
            stats = await self.vector_db.get_statistics()
            return stats.to_dict()
        except Exception as e:
            logger.error(f"Error getting statistics: {e}")
            raise
    
    async def delete_embedding(self, embedding_id: str) -> bool:
        """Delete an embedding"""
        try:
            result = await self.vector_db.delete_embedding(embedding_id)
            if result:
                logger.info(f"Deleted embedding {embedding_id}")
            return result
        except Exception as e:
            logger.error(f"Error deleting embedding {embedding_id}: {e}")
            return False
    
    async def clear_all_embeddings(self) -> bool:
        """Clear all embeddings from database"""
        try:
            result = await self.vector_db.clear_database()
            if result:
                self._query_cache.clear()
                logger.info("Cleared all embeddings and cache")
            return result
        except Exception as e:
            logger.error(f"Error clearing embeddings: {e}")
            return False
    
    async def update_schema_embedding(
        self,
        embedding_id: str,
        new_schema_data: Dict[str, Any]
    ) -> bool:
        """
        Update schema embedding with new data
        
        Args:
            embedding_id: ID of embedding to update
            new_schema_data: New schema data
            
        Returns:
            Success status
        """
        try:
            # Get existing embedding
            embedding = await self.vector_db.get_embedding(embedding_id)
            if not embedding:
                raise ValueError(f"Embedding {embedding_id} not found")
            
            # Update embedding
            updated_embedding = self.embedding_generator.update_embedding(embedding, new_schema_data)
            
            # Save updated embedding
            result = await self.vector_db.update_embedding(updated_embedding)
            
            if result:
                # Clear related cache entries
                self._clear_cache_for_embedding(embedding_id)
                logger.info(f"Updated embedding {embedding_id}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error updating embedding {embedding_id}: {e}")
            return False
    
    # Cache Management
    
    def _generate_cache_key(self, operation: str, *args) -> str:
        """Generate cache key for operation"""
        key_parts = [operation] + [str(arg) for arg in args]
        return ":".join(key_parts)
    
    def _get_from_cache(self, key: str) -> Any:
        """Get result from cache"""
        if key in self._query_cache:
            result, timestamp = self._query_cache[key]
            if time.time() - timestamp < self._cache_ttl:
                return result
            else:
                # Expired entry
                del self._query_cache[key]
        return None
    
    def _cache_result(self, key: str, result: Any):
        """Cache operation result"""
        self._query_cache[key] = (result, time.time())
        
        # Simple cache cleanup - remove old entries if cache gets too large
        if len(self._query_cache) > 1000:
            # Remove oldest 25% of entries
            sorted_items = sorted(self._query_cache.items(), key=lambda x: x[1][1])
            for k, _ in sorted_items[:250]:
                del self._query_cache[k]
    
    def _clear_cache_for_embedding(self, embedding_id: str):
        """Clear cache entries related to specific embedding"""
        keys_to_remove = []
        for key in self._query_cache:
            if embedding_id in key:
                keys_to_remove.append(key)
        
        for key in keys_to_remove:
            del self._query_cache[key]
    
    def _boost_recent_results(self, results: List[SimilarityResult]) -> List[SimilarityResult]:
        """Apply boost to recent results"""
        current_time = datetime.utcnow()
        
        for result in results:
            # Check if embedding has creation time in metadata
            created_at_str = result.metadata.get('created_at')
            if created_at_str:
                try:
                    created_at = datetime.fromisoformat(created_at_str.replace('Z', '+00:00'))
                    age_hours = (current_time - created_at).total_seconds() / 3600
                    
                    # Boost results less than 24 hours old
                    if age_hours < 24:
                        boost_factor = 1.1 - (age_hours / 24) * 0.1  # 1.1 to 1.0
                        result.similarity_score = min(result.similarity_score * boost_factor, 1.0)
                        
                except ValueError:
                    # Invalid datetime format, skip boost
                    pass
        
        # Re-sort by boosted scores
        results.sort(key=lambda x: x.similarity_score, reverse=True)
        
        # Update ranks
        for i, result in enumerate(results):
            result.rank = i + 1
        
        return results
    
    # Batch Operations
    
    async def batch_process_schemas(
        self,
        schemas: List[SchemaResponse],
        batch_size: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Process multiple schemas in batches
        
        Args:
            schemas: List of schemas to process
            batch_size: Batch size for processing
            
        Returns:
            List of processing results
        """
        results = []
        
        try:
            for i in range(0, len(schemas), batch_size):
                batch = schemas[i:i + batch_size]
                batch_tasks = [self.process_schema(schema) for schema in batch]
                batch_results = await asyncio.gather(*batch_tasks)
                results.extend(batch_results)
                
                logger.info(f"Processed batch {i//batch_size + 1}/{(len(schemas) + batch_size - 1)//batch_size}")
            
            logger.info(f"Batch processing completed - Processed {len(schemas)} schemas")
            return results
            
        except Exception as e:
            logger.error(f"Error in batch processing: {e}")
            raise
    
    async def batch_semantic_search(
        self,
        queries: List[str],
        search_type: EmbeddingType = EmbeddingType.SCHEMA,
        **kwargs
    ) -> List[SemanticSearchResponse]:
        """
        Perform multiple semantic searches
        
        Args:
            queries: List of search queries
            search_type: Type of embeddings to search
            **kwargs: Additional search parameters
            
        Returns:
            List of search responses
        """
        results = []
        
        try:
            for query in queries:
                request = SemanticSearchRequest(
                    query=query,
                    search_type=search_type,
                    **kwargs
                )
                response = await self.semantic_search(request)
                results.append(response)
            
            logger.info(f"Batch search completed - Processed {len(queries)} queries")
            return results
            
        except Exception as e:
            logger.error(f"Error in batch search: {e}")
            raise
