"""
Base classes and types for ML pipeline
"""
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any
from datetime import datetime

class MLTaskType(Enum):
    """Types of ML tasks supported"""
    SCHEMA_CLASSIFICATION = "schema_classification"
    PERFORMANCE_PREDICTION = "performance_prediction"
    ANOMALY_DETECTION = "anomaly_detection"
    SIMILARITY_ANALYSIS = "similarity_analysis"
    OPTIMIZATION_RECOMMENDATION = "optimization_recommendation"
    USAGE_PREDICTION = "usage_prediction"
    DATA_QUALITY_ASSESSMENT = "data_quality_assessment"
    RELATIONSHIP_DISCOVERY = "relationship_discovery"

class ModelStatus(Enum):
    """ML model status"""
    TRAINING = "training"
    TRAINED = "trained"
    DEPLOYING = "deploying"
    DEPLOYED = "deployed"
    ERROR = "error"
    RETRAINING = "retraining"

@dataclass
class MLFeature:
    """Represents a machine learning feature"""
    name: str
    feature_type: str  # numerical, categorical, text, boolean
    value: Any
    importance: Optional[float] = None
    description: str = ""

@dataclass
class MLModelConfig:
    """Configuration for ML model"""
    model_id: str
    task_type: MLTaskType
    algorithm: str
    hyperparameters: Dict[str, Any]
    features: List[str]
    target_variable: str
    preprocessing_steps: List[str] = field(default_factory=list)
    evaluation_metrics: List[str] = field(default_factory=list)

@dataclass
class MLModel:
    """Represents a trained ML model"""
    model_id: str
    config: MLModelConfig
    model_object: Any
    preprocessor: Any
    feature_importance: Dict[str, float] = field(default_factory=dict)
    performance_metrics: Dict[str, float] = field(default_factory=dict)
    training_data_size: int = 0
    created_at: datetime = field(default_factory=datetime.now)
    last_updated: datetime = field(default_factory=datetime.now)
    status: ModelStatus = ModelStatus.TRAINING
    version: str = "1.0"

@dataclass
class MLPrediction:
    """Represents an ML prediction"""
    prediction_id: str
    model_id: str
    input_features: Dict[str, Any]
    prediction: Any
    confidence: float
    explanation: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)

@dataclass
class SchemaFeatures:
    """Features extracted from schema for ML"""
    schema_id: str
    table_count: int
    column_count: int
    relationship_count: int
    avg_columns_per_table: float
    max_columns_per_table: int
    min_columns_per_table: int
    complexity_score: float
    normalization_score: float
    data_type_distribution: Dict[str, int]
    naming_consistency_score: float
    table_names: List[str]
    column_names: List[str]
    relationship_types: Dict[str, int]
    extracted_at: datetime = field(default_factory=datetime.now)
