"""
Vector intelligence data models
Defines data structures for vector embeddings and metadata
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import numpy as np

from models.schemas import SchemaResponse, TableInfo, ColumnInfo


class EmbeddingType(Enum):
    """Types of embeddings"""
    SCHEMA = "schema"
    TABLE = "table"
    COLUMN = "column"
    QUERY = "query"
    PATTERN = "pattern"


class SimilarityMetric(Enum):
    """Similarity calculation methods"""
    COSINE = "cosine"
    EUCLIDEAN = "euclidean"
    DOT_PRODUCT = "dot_product"
    MANHATTAN = "manhattan"


class ClusteringMethod(Enum):
    """Clustering algorithms"""
    KMEANS = "kmeans"
    DBSCAN = "dbscan"
    HIERARCHICAL = "hierarchical"
    GAUSSIAN_MIXTURE = "gaussian_mixture"


@dataclass
class SchemaEmbedding:
    """Schema embedding with metadata"""
    embedding_id: str
    embedding_type: EmbeddingType
    embedding: np.ndarray
    schema_data: Dict[str, Any]
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    version: int = 1
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'embedding_id': self.embedding_id,
            'embedding_type': self.embedding_type.value,
            'embedding': self.embedding.tolist(),
            'schema_data': self.schema_data,
            'metadata': self.metadata,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'version': self.version
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SchemaEmbedding':
        """Create from dictionary"""
        return cls(
            embedding_id=data['embedding_id'],
            embedding_type=EmbeddingType(data['embedding_type']),
            embedding=np.array(data['embedding']),
            schema_data=data['schema_data'],
            metadata=data.get('metadata', {}),
            created_at=datetime.fromisoformat(data['created_at']),
            updated_at=datetime.fromisoformat(data['updated_at']),
            version=data.get('version', 1)
        )


@dataclass
class SimilarityResult:
    """Result of similarity search"""
    embedding_id: str
    similarity_score: float
    metadata: Dict[str, Any]
    schema_data: Dict[str, Any] = field(default_factory=dict)
    distance: float = 0.0
    rank: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'embedding_id': self.embedding_id,
            'similarity_score': self.similarity_score,
            'metadata': self.metadata,
            'schema_data': self.schema_data,
            'distance': self.distance,
            'rank': self.rank
        }


@dataclass
class PatternMatch:
    """Pattern matching result"""
    pattern_id: str
    pattern_name: str
    pattern_type: str
    match_score: float
    matched_elements: List[str]
    confidence: float
    explanation: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'pattern_id': self.pattern_id,
            'pattern_name': self.pattern_name,
            'pattern_type': self.pattern_type,
            'match_score': self.match_score,
            'matched_elements': self.matched_elements,
            'confidence': self.confidence,
            'explanation': self.explanation,
            'metadata': self.metadata
        }


@dataclass
class SchemaCluster:
    """Schema clustering result"""
    cluster_id: str
    cluster_name: str
    centroid: np.ndarray
    members: List[str]  # embedding IDs
    cluster_score: float
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'cluster_id': self.cluster_id,
            'cluster_name': self.cluster_name,
            'centroid': self.centroid.tolist(),
            'members': self.members,
            'cluster_score': self.cluster_score,
            'metadata': self.metadata,
            'created_at': self.created_at.isoformat()
        }


@dataclass
class EmbeddingStats:
    """Statistics about embeddings"""
    total_embeddings: int
    embeddings_by_type: Dict[str, int]
    dimension: int
    average_similarity: float
    min_similarity: float
    max_similarity: float
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'total_embeddings': self.total_embeddings,
            'embeddings_by_type': self.embeddings_by_type,
            'dimension': self.dimension,
            'average_similarity': self.average_similarity,
            'min_similarity': self.min_similarity,
            'max_similarity': self.max_similarity,
            'created_at': self.created_at.isoformat()
        }


@dataclass
class QueryContext:
    """Context for semantic queries"""
    query_text: str
    query_type: EmbeddingType
    filters: Dict[str, Any] = field(default_factory=dict)
    similarity_threshold: float = 0.7
    max_results: int = 10
    include_metadata: bool = True
    boost_factors: Dict[str, float] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'query_text': self.query_text,
            'query_type': self.query_type.value,
            'filters': self.filters,
            'similarity_threshold': self.similarity_threshold,
            'max_results': self.max_results,
            'include_metadata': self.include_metadata,
            'boost_factors': self.boost_factors
        }


@dataclass
class VectorIndex:
    """Vector index configuration"""
    index_id: str
    index_name: str
    dimension: int
    metric: SimilarityMetric
    index_type: str  # "flat", "ivf", "hnsw", etc.
    parameters: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'index_id': self.index_id,
            'index_name': self.index_name,
            'dimension': self.dimension,
            'metric': self.metric.value,
            'index_type': self.index_type,
            'parameters': self.parameters,
            'created_at': self.created_at.isoformat()
        }


class VectorDatabase(ABC):
    """Abstract vector database interface"""
    
    @abstractmethod
    async def insert_embedding(
        self,
        embedding: SchemaEmbedding
    ) -> bool:
        """Insert an embedding"""
        pass
    
    @abstractmethod
    async def search_similar(
        self,
        query_embedding: np.ndarray,
        context: QueryContext
    ) -> List[SimilarityResult]:
        """Search for similar embeddings"""
        pass
    
    @abstractmethod
    async def delete_embedding(self, embedding_id: str) -> bool:
        """Delete an embedding"""
        pass
    
    @abstractmethod
    async def update_embedding(self, embedding: SchemaEmbedding) -> bool:
        """Update an embedding"""
        pass
    
    @abstractmethod
    async def get_embedding(self, embedding_id: str) -> Optional[SchemaEmbedding]:
        """Get embedding by ID"""
        pass
    
    @abstractmethod
    async def list_embeddings(
        self,
        embedding_type: EmbeddingType = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[SchemaEmbedding]:
        """List embeddings with pagination"""
        pass
    
    @abstractmethod
    async def get_statistics(self) -> EmbeddingStats:
        """Get database statistics"""
        pass
    
    @abstractmethod
    async def create_index(self, index_config: VectorIndex) -> bool:
        """Create vector index"""
        pass
    
    @abstractmethod
    async def delete_index(self, index_id: str) -> bool:
        """Delete vector index"""
        pass
    
    @abstractmethod
    async def clear_database(self) -> bool:
        """Clear all embeddings"""
        pass


@dataclass
class SemanticSearchRequest:
    """Semantic search request"""
    query: str
    search_type: EmbeddingType
    filters: Dict[str, Any] = field(default_factory=dict)
    similarity_threshold: float = 0.7
    max_results: int = 10
    include_explanations: bool = False
    boost_recent: bool = False
    boost_factors: Dict[str, float] = field(default_factory=dict)


@dataclass
class SemanticSearchResponse:
    """Semantic search response"""
    query: str
    results: List[SimilarityResult]
    total_results: int
    search_time_ms: float
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'query': self.query,
            'results': [r.to_dict() for r in self.results],
            'total_results': self.total_results,
            'search_time_ms': self.search_time_ms,
            'metadata': self.metadata
        }


@dataclass
class PatternDetectionRequest:
    """Pattern detection request"""
    schema_data: Dict[str, Any]
    pattern_types: List[str] = field(default_factory=list)
    confidence_threshold: float = 0.8
    max_patterns: int = 10
    include_explanations: bool = True


@dataclass
class PatternDetectionResponse:
    """Pattern detection response"""
    schema_id: str
    patterns: List[PatternMatch]
    detection_time_ms: float
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'schema_id': self.schema_id,
            'patterns': [p.to_dict() for p in self.patterns],
            'detection_time_ms': self.detection_time_ms,
            'metadata': self.metadata
        }


@dataclass
class ClusteringRequest:
    """Clustering request"""
    embedding_ids: List[str]
    method: ClusteringMethod
    num_clusters: Optional[int] = None
    parameters: Dict[str, Any] = field(default_factory=dict)
    min_cluster_size: int = 2
    include_outliers: bool = True


@dataclass
class ClusteringResponse:
    """Clustering response"""
    clusters: List[SchemaCluster]
    outliers: List[str]  # embedding IDs
    silhouette_score: float
    clustering_time_ms: float
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'clusters': [c.to_dict() for c in self.clusters],
            'outliers': self.outliers,
            'silhouette_score': self.silhouette_score,
            'clustering_time_ms': self.clustering_time_ms,
            'metadata': self.metadata
        }
