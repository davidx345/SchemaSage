"""
Vector database implementations
Provides storage and retrieval for vector embeddings
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
import numpy as np
import json
import os
from datetime import datetime
import asyncio
from concurrent.futures import ThreadPoolExecutor
import sqlite3
import pickle

from .models import (
    VectorDatabase, SchemaEmbedding, SimilarityResult, QueryContext,
    EmbeddingStats, VectorIndex, SimilarityMetric, EmbeddingType
)

logger = logging.getLogger(__name__)


class InMemoryVectorDB(VectorDatabase):
    """
    In-memory vector database implementation
    Suitable for development and small datasets
    """
    
    def __init__(self):
        """Initialize in-memory vector database"""
        self.embeddings: Dict[str, SchemaEmbedding] = {}
        self.indexes: Dict[str, VectorIndex] = {}
        self._lock = asyncio.Lock()
        
        logger.info("Initialized in-memory vector database")
    
    async def insert_embedding(self, embedding: SchemaEmbedding) -> bool:
        """Insert an embedding"""
        try:
            async with self._lock:
                self.embeddings[embedding.embedding_id] = embedding
                logger.debug(f"Inserted embedding {embedding.embedding_id}")
                return True
        except Exception as e:
            logger.error(f"Error inserting embedding {embedding.embedding_id}: {e}")
            return False
    
    async def search_similar(
        self,
        query_embedding: np.ndarray,
        context: QueryContext
    ) -> List[SimilarityResult]:
        """Search for similar embeddings"""
        try:
            async with self._lock:
                candidates = []
                
                # Filter embeddings based on context
                for embedding in self.embeddings.values():
                    # Type filter
                    if context.query_type and embedding.embedding_type != context.query_type:
                        continue
                    
                    # Apply additional filters
                    if not self._matches_filters(embedding, context.filters):
                        continue
                    
                    # Calculate similarity
                    similarity = self._calculate_similarity(
                        query_embedding, 
                        embedding.embedding,
                        SimilarityMetric.COSINE
                    )
                    
                    # Apply similarity threshold
                    if similarity < context.similarity_threshold:
                        continue
                    
                    # Apply boost factors
                    boosted_similarity = self._apply_boost_factors(
                        similarity, embedding, context.boost_factors
                    )
                    
                    candidates.append((embedding, boosted_similarity, similarity))
                
                # Sort by boosted similarity and limit results
                candidates.sort(key=lambda x: x[1], reverse=True)
                candidates = candidates[:context.max_results]
                
                # Create results
                results = []
                for rank, (embedding, boosted_score, original_score) in enumerate(candidates):
                    metadata = embedding.metadata.copy() if context.include_metadata else {}
                    
                    result = SimilarityResult(
                        embedding_id=embedding.embedding_id,
                        similarity_score=boosted_score,
                        metadata=metadata,
                        schema_data=embedding.schema_data,
                        distance=1.0 - original_score,
                        rank=rank + 1
                    )
                    results.append(result)
                
                logger.debug(f"Found {len(results)} similar embeddings")
                return results
                
        except Exception as e:
            logger.error(f"Error searching similar embeddings: {e}")
            return []
    
    async def delete_embedding(self, embedding_id: str) -> bool:
        """Delete an embedding"""
        try:
            async with self._lock:
                if embedding_id in self.embeddings:
                    del self.embeddings[embedding_id]
                    logger.debug(f"Deleted embedding {embedding_id}")
                    return True
                return False
        except Exception as e:
            logger.error(f"Error deleting embedding {embedding_id}: {e}")
            return False
    
    async def update_embedding(self, embedding: SchemaEmbedding) -> bool:
        """Update an embedding"""
        try:
            async with self._lock:
                if embedding.embedding_id in self.embeddings:
                    self.embeddings[embedding.embedding_id] = embedding
                    logger.debug(f"Updated embedding {embedding.embedding_id}")
                    return True
                return False
        except Exception as e:
            logger.error(f"Error updating embedding {embedding.embedding_id}: {e}")
            return False
    
    async def get_embedding(self, embedding_id: str) -> Optional[SchemaEmbedding]:
        """Get embedding by ID"""
        try:
            async with self._lock:
                return self.embeddings.get(embedding_id)
        except Exception as e:
            logger.error(f"Error getting embedding {embedding_id}: {e}")
            return None
    
    async def list_embeddings(
        self,
        embedding_type: EmbeddingType = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[SchemaEmbedding]:
        """List embeddings with pagination"""
        try:
            async with self._lock:
                embeddings = list(self.embeddings.values())
                
                # Filter by type
                if embedding_type:
                    embeddings = [e for e in embeddings if e.embedding_type == embedding_type]
                
                # Sort by creation time (most recent first)
                embeddings.sort(key=lambda x: x.created_at, reverse=True)
                
                # Apply pagination
                start_idx = offset
                end_idx = offset + limit
                return embeddings[start_idx:end_idx]
                
        except Exception as e:
            logger.error(f"Error listing embeddings: {e}")
            return []
    
    async def get_statistics(self) -> EmbeddingStats:
        """Get database statistics"""
        try:
            async with self._lock:
                total_embeddings = len(self.embeddings)
                
                if total_embeddings == 0:
                    return EmbeddingStats(
                        total_embeddings=0,
                        embeddings_by_type={},
                        dimension=0,
                        average_similarity=0.0,
                        min_similarity=0.0,
                        max_similarity=0.0
                    )
                
                # Count by type
                embeddings_by_type = {}
                dimensions = set()
                
                for embedding in self.embeddings.values():
                    type_name = embedding.embedding_type.value
                    embeddings_by_type[type_name] = embeddings_by_type.get(type_name, 0) + 1
                    dimensions.add(len(embedding.embedding))
                
                # Calculate similarity statistics (sample-based for large datasets)
                sample_embeddings = list(self.embeddings.values())
                if len(sample_embeddings) > 100:
                    sample_embeddings = sample_embeddings[:100]
                
                similarities = []
                for i, emb1 in enumerate(sample_embeddings):
                    for emb2 in sample_embeddings[i+1:]:
                        sim = self._calculate_similarity(
                            emb1.embedding, emb2.embedding, SimilarityMetric.COSINE
                        )
                        similarities.append(sim)
                
                avg_similarity = np.mean(similarities) if similarities else 0.0
                min_similarity = np.min(similarities) if similarities else 0.0
                max_similarity = np.max(similarities) if similarities else 0.0
                
                return EmbeddingStats(
                    total_embeddings=total_embeddings,
                    embeddings_by_type=embeddings_by_type,
                    dimension=list(dimensions)[0] if dimensions else 0,
                    average_similarity=float(avg_similarity),
                    min_similarity=float(min_similarity),
                    max_similarity=float(max_similarity)
                )
                
        except Exception as e:
            logger.error(f"Error getting statistics: {e}")
            return EmbeddingStats(
                total_embeddings=0,
                embeddings_by_type={},
                dimension=0,
                average_similarity=0.0,
                min_similarity=0.0,
                max_similarity=0.0
            )
    
    async def create_index(self, index_config: VectorIndex) -> bool:
        """Create vector index (no-op for in-memory)"""
        try:
            async with self._lock:
                self.indexes[index_config.index_id] = index_config
                logger.info(f"Created index {index_config.index_name}")
                return True
        except Exception as e:
            logger.error(f"Error creating index: {e}")
            return False
    
    async def delete_index(self, index_id: str) -> bool:
        """Delete vector index"""
        try:
            async with self._lock:
                if index_id in self.indexes:
                    del self.indexes[index_id]
                    logger.info(f"Deleted index {index_id}")
                    return True
                return False
        except Exception as e:
            logger.error(f"Error deleting index: {e}")
            return False
    
    async def clear_database(self) -> bool:
        """Clear all embeddings"""
        try:
            async with self._lock:
                self.embeddings.clear()
                self.indexes.clear()
                logger.info("Cleared all embeddings and indexes")
                return True
        except Exception as e:
            logger.error(f"Error clearing database: {e}")
            return False
    
    def _matches_filters(self, embedding: SchemaEmbedding, filters: Dict[str, Any]) -> bool:
        """Check if embedding matches filters"""
        if not filters:
            return True
        
        for key, value in filters.items():
            # Check in metadata
            if key in embedding.metadata:
                if embedding.metadata[key] != value:
                    return False
            # Check in schema data
            elif key in embedding.schema_data:
                if embedding.schema_data[key] != value:
                    return False
            else:
                # Filter key not found, consider as not matching
                return False
        
        return True
    
    def _calculate_similarity(
        self,
        vec1: np.ndarray,
        vec2: np.ndarray,
        metric: SimilarityMetric
    ) -> float:
        """Calculate similarity between two vectors"""
        try:
            if metric == SimilarityMetric.COSINE:
                # Cosine similarity
                dot_product = np.dot(vec1, vec2)
                norm1 = np.linalg.norm(vec1)
                norm2 = np.linalg.norm(vec2)
                
                if norm1 == 0 or norm2 == 0:
                    return 0.0
                
                return dot_product / (norm1 * norm2)
                
            elif metric == SimilarityMetric.EUCLIDEAN:
                # Euclidean distance (converted to similarity)
                distance = np.linalg.norm(vec1 - vec2)
                return 1.0 / (1.0 + distance)
                
            elif metric == SimilarityMetric.DOT_PRODUCT:
                # Dot product
                return np.dot(vec1, vec2)
                
            elif metric == SimilarityMetric.MANHATTAN:
                # Manhattan distance (converted to similarity)
                distance = np.sum(np.abs(vec1 - vec2))
                return 1.0 / (1.0 + distance)
                
            else:
                logger.warning(f"Unknown similarity metric: {metric}")
                return 0.0
                
        except Exception as e:
            logger.error(f"Error calculating similarity: {e}")
            return 0.0
    
    def _apply_boost_factors(
        self,
        similarity: float,
        embedding: SchemaEmbedding,
        boost_factors: Dict[str, float]
    ) -> float:
        """Apply boost factors to similarity score"""
        if not boost_factors:
            return similarity
        
        boosted_score = similarity
        
        try:
            # Time-based boost (recent embeddings)
            if 'recent' in boost_factors:
                age_hours = (datetime.utcnow() - embedding.created_at).total_seconds() / 3600
                if age_hours < 24:  # Boost embeddings less than 24 hours old
                    boosted_score *= boost_factors['recent']
            
            # Type-based boost
            type_key = f"type_{embedding.embedding_type.value}"
            if type_key in boost_factors:
                boosted_score *= boost_factors[type_key]
            
            # Metadata-based boost
            for key, boost_value in boost_factors.items():
                if key.startswith('meta_'):
                    meta_key = key[5:]  # Remove 'meta_' prefix
                    if meta_key in embedding.metadata:
                        boosted_score *= boost_value
            
            # Ensure score doesn't exceed 1.0
            return min(boosted_score, 1.0)
            
        except Exception as e:
            logger.error(f"Error applying boost factors: {e}")
            return similarity


class SQLiteVectorDB(VectorDatabase):
    """
    SQLite-based vector database implementation
    Suitable for persistent storage and medium datasets
    """
    
    def __init__(self, db_path: str = "vector_db.sqlite"):
        """
        Initialize SQLite vector database
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self._executor = ThreadPoolExecutor(max_workers=4)
        self._init_database()
        
        logger.info(f"Initialized SQLite vector database at {db_path}")
    
    def _init_database(self):
        """Initialize database tables"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Create embeddings table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS embeddings (
                        embedding_id TEXT PRIMARY KEY,
                        embedding_type TEXT NOT NULL,
                        embedding_data BLOB NOT NULL,
                        schema_data TEXT NOT NULL,
                        metadata TEXT NOT NULL,
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL,
                        version INTEGER NOT NULL
                    )
                """)
                
                # Create indexes table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS indexes (
                        index_id TEXT PRIMARY KEY,
                        index_name TEXT NOT NULL,
                        dimension INTEGER NOT NULL,
                        metric TEXT NOT NULL,
                        index_type TEXT NOT NULL,
                        parameters TEXT NOT NULL,
                        created_at TEXT NOT NULL
                    )
                """)
                
                # Create indexes for better performance
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_embedding_type ON embeddings(embedding_type)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_created_at ON embeddings(created_at)")
                
                conn.commit()
                
        except Exception as e:
            logger.error(f"Error initializing database: {e}")
            raise
    
    async def insert_embedding(self, embedding: SchemaEmbedding) -> bool:
        """Insert an embedding"""
        try:
            def _insert():
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute("""
                        INSERT OR REPLACE INTO embeddings 
                        (embedding_id, embedding_type, embedding_data, schema_data, 
                         metadata, created_at, updated_at, version)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        embedding.embedding_id,
                        embedding.embedding_type.value,
                        pickle.dumps(embedding.embedding),
                        json.dumps(embedding.schema_data),
                        json.dumps(embedding.metadata),
                        embedding.created_at.isoformat(),
                        embedding.updated_at.isoformat(),
                        embedding.version
                    ))
                    conn.commit()
                    return True
            
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(self._executor, _insert)
            
            logger.debug(f"Inserted embedding {embedding.embedding_id}")
            return result
            
        except Exception as e:
            logger.error(f"Error inserting embedding {embedding.embedding_id}: {e}")
            return False
    
    async def search_similar(
        self,
        query_embedding: np.ndarray,
        context: QueryContext
    ) -> List[SimilarityResult]:
        """Search for similar embeddings"""
        try:
            def _search():
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    
                    # Build query with filters
                    query = "SELECT * FROM embeddings"
                    params = []
                    
                    where_clauses = []
                    if context.query_type:
                        where_clauses.append("embedding_type = ?")
                        params.append(context.query_type.value)
                    
                    if where_clauses:
                        query += " WHERE " + " AND ".join(where_clauses)
                    
                    cursor.execute(query, params)
                    rows = cursor.fetchall()
                    
                    candidates = []
                    for row in rows:
                        embedding_id, embedding_type, embedding_data, schema_data, metadata, created_at, updated_at, version = row
                        
                        # Deserialize data
                        embedding_vector = pickle.loads(embedding_data)
                        schema_data_dict = json.loads(schema_data)
                        metadata_dict = json.loads(metadata)
                        
                        # Create embedding object
                        embedding = SchemaEmbedding(
                            embedding_id=embedding_id,
                            embedding_type=EmbeddingType(embedding_type),
                            embedding=embedding_vector,
                            schema_data=schema_data_dict,
                            metadata=metadata_dict,
                            created_at=datetime.fromisoformat(created_at),
                            updated_at=datetime.fromisoformat(updated_at),
                            version=version
                        )
                        
                        # Apply additional filters
                        if not self._matches_filters(embedding, context.filters):
                            continue
                        
                        # Calculate similarity
                        similarity = self._calculate_similarity(
                            query_embedding, 
                            embedding.embedding,
                            SimilarityMetric.COSINE
                        )
                        
                        # Apply similarity threshold
                        if similarity < context.similarity_threshold:
                            continue
                        
                        candidates.append((embedding, similarity))
                    
                    # Sort by similarity and limit results
                    candidates.sort(key=lambda x: x[1], reverse=True)
                    candidates = candidates[:context.max_results]
                    
                    # Create results
                    results = []
                    for rank, (embedding, similarity) in enumerate(candidates):
                        metadata = embedding.metadata.copy() if context.include_metadata else {}
                        
                        result = SimilarityResult(
                            embedding_id=embedding.embedding_id,
                            similarity_score=similarity,
                            metadata=metadata,
                            schema_data=embedding.schema_data,
                            distance=1.0 - similarity,
                            rank=rank + 1
                        )
                        results.append(result)
                    
                    return results
            
            loop = asyncio.get_event_loop()
            results = await loop.run_in_executor(self._executor, _search)
            
            logger.debug(f"Found {len(results)} similar embeddings")
            return results
            
        except Exception as e:
            logger.error(f"Error searching similar embeddings: {e}")
            return []
    
    async def delete_embedding(self, embedding_id: str) -> bool:
        """Delete an embedding"""
        try:
            def _delete():
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute("DELETE FROM embeddings WHERE embedding_id = ?", (embedding_id,))
                    conn.commit()
                    return cursor.rowcount > 0
            
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(self._executor, _delete)
            
            logger.debug(f"Deleted embedding {embedding_id}")
            return result
            
        except Exception as e:
            logger.error(f"Error deleting embedding {embedding_id}: {e}")
            return False
    
    async def update_embedding(self, embedding: SchemaEmbedding) -> bool:
        """Update an embedding"""
        return await self.insert_embedding(embedding)  # SQLite uses INSERT OR REPLACE
    
    async def get_embedding(self, embedding_id: str) -> Optional[SchemaEmbedding]:
        """Get embedding by ID"""
        try:
            def _get():
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT * FROM embeddings WHERE embedding_id = ?", (embedding_id,))
                    row = cursor.fetchone()
                    
                    if not row:
                        return None
                    
                    embedding_id, embedding_type, embedding_data, schema_data, metadata, created_at, updated_at, version = row
                    
                    return SchemaEmbedding(
                        embedding_id=embedding_id,
                        embedding_type=EmbeddingType(embedding_type),
                        embedding=pickle.loads(embedding_data),
                        schema_data=json.loads(schema_data),
                        metadata=json.loads(metadata),
                        created_at=datetime.fromisoformat(created_at),
                        updated_at=datetime.fromisoformat(updated_at),
                        version=version
                    )
            
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(self._executor, _get)
            return result
            
        except Exception as e:
            logger.error(f"Error getting embedding {embedding_id}: {e}")
            return None
    
    async def list_embeddings(
        self,
        embedding_type: EmbeddingType = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[SchemaEmbedding]:
        """List embeddings with pagination"""
        try:
            def _list():
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    
                    query = "SELECT * FROM embeddings"
                    params = []
                    
                    if embedding_type:
                        query += " WHERE embedding_type = ?"
                        params.append(embedding_type.value)
                    
                    query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
                    params.extend([limit, offset])
                    
                    cursor.execute(query, params)
                    rows = cursor.fetchall()
                    
                    embeddings = []
                    for row in rows:
                        embedding_id, embedding_type, embedding_data, schema_data, metadata, created_at, updated_at, version = row
                        
                        embedding = SchemaEmbedding(
                            embedding_id=embedding_id,
                            embedding_type=EmbeddingType(embedding_type),
                            embedding=pickle.loads(embedding_data),
                            schema_data=json.loads(schema_data),
                            metadata=json.loads(metadata),
                            created_at=datetime.fromisoformat(created_at),
                            updated_at=datetime.fromisoformat(updated_at),
                            version=version
                        )
                        embeddings.append(embedding)
                    
                    return embeddings
            
            loop = asyncio.get_event_loop()
            embeddings = await loop.run_in_executor(self._executor, _list)
            return embeddings
            
        except Exception as e:
            logger.error(f"Error listing embeddings: {e}")
            return []
    
    async def get_statistics(self) -> EmbeddingStats:
        """Get database statistics"""
        try:
            def _get_stats():
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    
                    # Total count
                    cursor.execute("SELECT COUNT(*) FROM embeddings")
                    total_embeddings = cursor.fetchone()[0]
                    
                    if total_embeddings == 0:
                        return EmbeddingStats(
                            total_embeddings=0,
                            embeddings_by_type={},
                            dimension=0,
                            average_similarity=0.0,
                            min_similarity=0.0,
                            max_similarity=0.0
                        )
                    
                    # Count by type
                    cursor.execute("SELECT embedding_type, COUNT(*) FROM embeddings GROUP BY embedding_type")
                    embeddings_by_type = dict(cursor.fetchall())
                    
                    # Get sample for similarity calculations
                    cursor.execute("SELECT embedding_data FROM embeddings LIMIT 10")
                    sample_embeddings = [pickle.loads(row[0]) for row in cursor.fetchall()]
                    
                    if sample_embeddings:
                        dimension = len(sample_embeddings[0])
                        
                        # Calculate similarities
                        similarities = []
                        for i, emb1 in enumerate(sample_embeddings):
                            for emb2 in sample_embeddings[i+1:]:
                                sim = self._calculate_similarity(emb1, emb2, SimilarityMetric.COSINE)
                                similarities.append(sim)
                        
                        avg_similarity = np.mean(similarities) if similarities else 0.0
                        min_similarity = np.min(similarities) if similarities else 0.0
                        max_similarity = np.max(similarities) if similarities else 0.0
                    else:
                        dimension = 0
                        avg_similarity = 0.0
                        min_similarity = 0.0
                        max_similarity = 0.0
                    
                    return EmbeddingStats(
                        total_embeddings=total_embeddings,
                        embeddings_by_type=embeddings_by_type,
                        dimension=dimension,
                        average_similarity=float(avg_similarity),
                        min_similarity=float(min_similarity),
                        max_similarity=float(max_similarity)
                    )
            
            loop = asyncio.get_event_loop()
            stats = await loop.run_in_executor(self._executor, _get_stats)
            return stats
            
        except Exception as e:
            logger.error(f"Error getting statistics: {e}")
            return EmbeddingStats(
                total_embeddings=0,
                embeddings_by_type={},
                dimension=0,
                average_similarity=0.0,
                min_similarity=0.0,
                max_similarity=0.0
            )
    
    async def create_index(self, index_config: VectorIndex) -> bool:
        """Create vector index"""
        try:
            def _create_index():
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute("""
                        INSERT OR REPLACE INTO indexes 
                        (index_id, index_name, dimension, metric, index_type, parameters, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (
                        index_config.index_id,
                        index_config.index_name,
                        index_config.dimension,
                        index_config.metric.value,
                        index_config.index_type,
                        json.dumps(index_config.parameters),
                        index_config.created_at.isoformat()
                    ))
                    conn.commit()
                    return True
            
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(self._executor, _create_index)
            
            logger.info(f"Created index {index_config.index_name}")
            return result
            
        except Exception as e:
            logger.error(f"Error creating index: {e}")
            return False
    
    async def delete_index(self, index_id: str) -> bool:
        """Delete vector index"""
        try:
            def _delete_index():
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute("DELETE FROM indexes WHERE index_id = ?", (index_id,))
                    conn.commit()
                    return cursor.rowcount > 0
            
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(self._executor, _delete_index)
            
            logger.info(f"Deleted index {index_id}")
            return result
            
        except Exception as e:
            logger.error(f"Error deleting index: {e}")
            return False
    
    async def clear_database(self) -> bool:
        """Clear all embeddings"""
        try:
            def _clear():
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute("DELETE FROM embeddings")
                    cursor.execute("DELETE FROM indexes")
                    conn.commit()
                    return True
            
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(self._executor, _clear)
            
            logger.info("Cleared all embeddings and indexes")
            return result
            
        except Exception as e:
            logger.error(f"Error clearing database: {e}")
            return False
    
    def _matches_filters(self, embedding: SchemaEmbedding, filters: Dict[str, Any]) -> bool:
        """Check if embedding matches filters"""
        if not filters:
            return True
        
        for key, value in filters.items():
            # Check in metadata
            if key in embedding.metadata:
                if embedding.metadata[key] != value:
                    return False
            # Check in schema data
            elif key in embedding.schema_data:
                if embedding.schema_data[key] != value:
                    return False
            else:
                # Filter key not found, consider as not matching
                return False
        
        return True
    
    def _calculate_similarity(
        self,
        vec1: np.ndarray,
        vec2: np.ndarray,
        metric: SimilarityMetric
    ) -> float:
        """Calculate similarity between two vectors"""
        try:
            if metric == SimilarityMetric.COSINE:
                # Cosine similarity
                dot_product = np.dot(vec1, vec2)
                norm1 = np.linalg.norm(vec1)
                norm2 = np.linalg.norm(vec2)
                
                if norm1 == 0 or norm2 == 0:
                    return 0.0
                
                return dot_product / (norm1 * norm2)
                
            elif metric == SimilarityMetric.EUCLIDEAN:
                # Euclidean distance (converted to similarity)
                distance = np.linalg.norm(vec1 - vec2)
                return 1.0 / (1.0 + distance)
                
            elif metric == SimilarityMetric.DOT_PRODUCT:
                # Dot product
                return np.dot(vec1, vec2)
                
            elif metric == SimilarityMetric.MANHATTAN:
                # Manhattan distance (converted to similarity)
                distance = np.sum(np.abs(vec1 - vec2))
                return 1.0 / (1.0 + distance)
                
            else:
                logger.warning(f"Unknown similarity metric: {metric}")
                return 0.0
                
        except Exception as e:
            logger.error(f"Error calculating similarity: {e}")
            return 0.0
