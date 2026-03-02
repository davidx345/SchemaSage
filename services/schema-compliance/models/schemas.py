"""Schema models for Schema Detection Service."""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


class ColumnStatistics(BaseModel):
    """Statistics for a column."""
    total_count: int = 0
    null_count: int = 0
    unique_count: int = 0
    unique_percentage: float = 0.0
    min_value: Optional[Any] = None
    max_value: Optional[Any] = None
    avg_length: Optional[float] = None
    min_length: Optional[int] = None
    max_length: Optional[int] = None
    mean: Optional[float] = None
    std_dev: Optional[float] = None
    sample_values: List[str] = []
    value_distribution: Dict[str, int] = {}


class ColumnInfo(BaseModel):
    """Information about a database column."""
    name: str
    type: str
    nullable: bool = True
    primary_key: bool = False
    foreign_key: Optional[str] = None
    unique: bool = False
    default: Optional[Any] = None
    length: Optional[int] = None
    precision: Optional[int] = None
    scale: Optional[int] = None
    format: Optional[str] = None
    validation: Optional[str] = None
    description: Optional[str] = None
    constraints: Optional[Dict[str, Any]] = None
    statistics: Optional[ColumnStatistics] = None


class TableInfo(BaseModel):
    """Information about a database table."""
    name: str
    columns: List[ColumnInfo] = []
    primary_keys: List[str] = []
    foreign_keys: List[Dict[str, str]] = []
    indexes: List[str] = []
    statistics: Dict[str, ColumnStatistics] = {}
    estimated_rows: Optional[int] = None
    row_count: int = 0
    primary_key_candidates: List[str] = []
    description: Optional[str] = None


class RelationshipType(str, Enum):
    """Types of relationships between tables."""
    ONE_TO_ONE = "one-to-one"
    ONE_TO_MANY = "one-to-many"
    MANY_TO_ONE = "many-to-one"
    MANY_TO_MANY = "many-to-many"


class Relationship(BaseModel):
    """Relationship between tables."""
    source_table: str
    source_column: str
    target_table: str
    target_column: str
    type: RelationshipType
    confidence: float = Field(ge=0.0, le=1.0, default=0.5)
    description: Optional[str] = None


class SchemaSettings(BaseModel):
    """Settings for schema detection."""
    detect_relations: bool = True
    infer_types: bool = True
    generate_nullable: bool = True
    generate_indexes: bool = True
    max_sample_size: int = 1000
    confidence_threshold: float = 0.7
    enable_ai_enhancement: bool = True


class SchemaResponse(BaseModel):
    """Complete schema detection response."""
    tables: List[TableInfo] = []
    relationships: List[Relationship] = []
    metadata: Dict[str, Any] = {}
    confidence: float = Field(ge=0.0, le=1.0, default=0.8)
    processing_time: Optional[float] = None
    warnings: List[str] = []


class DetectionRequest(BaseModel):
    """Request for schema detection."""
    data: str
    settings: Optional[SchemaSettings] = None
    format_hint: Optional[str] = None  # json, csv, etc.


class DetectionResponse(BaseModel):
    """Response from schema detection."""
    model_config = {"protected_namespaces": ()}
    
    detected_schema: SchemaResponse = Field(..., alias="schema")
    success: bool = True
    message: Optional[str] = None
    errors: List[str] = []


class RelationshipSuggestionRequest(BaseModel):
    """Request for AI-assisted relationship suggestions."""
    tables: List[TableInfo]
    settings: Optional[SchemaSettings] = None
    context: Optional[Dict[str, Any]] = None


class RelationshipSuggestionResponse(BaseModel):
    """Response with suggested relationships."""
    relationships: List[Relationship]
    confidence: float = Field(ge=0.0, le=1.0, default=0.8)
    message: Optional[str] = None
    warnings: List[str] = []


class CrossDatasetRelationshipRequest(BaseModel):
    """Request for cross-dataset relationship inference."""
    datasets: List[List[TableInfo]]
    settings: Optional[SchemaSettings] = None
    context: Optional[Dict[str, Any]] = None


class CrossDatasetRelationshipResponse(BaseModel):
    """Response with cross-dataset relationship suggestions."""
    relationships: List[Relationship]
    confidence: float = Field(ge=0.0, le=1.0, default=0.7)
    message: Optional[str] = None
    warnings: List[str] = []


class LineageNodeModel(BaseModel):
    id: str
    table: str
    column: Optional[str] = None


class LineageEdgeModel(BaseModel):
    source: str
    target: str
    relationship: Optional[Relationship] = None


class TableLineageResponse(BaseModel):
    table: str
    upstream: List[str]
    downstream: List[str]
    business_term: Optional[dict] = None
    context: Optional[Any] = None


class ColumnLineageResponse(BaseModel):
    column: str
    upstream: List[str]
    downstream: List[str]
    business_term: Optional[dict] = None
    context: Optional[Any] = None


class ImpactAnalysisResponse(BaseModel):
    changed: str
    impacted: List[str]
    business_term: Optional[dict] = None
    context: Optional[Any] = None


class SchemaSnapshotModel(BaseModel):
    model_config = {"protected_namespaces": ()}
    
    id: str
    timestamp: str
    snapshot_schema: SchemaResponse = Field(..., alias="schema")


class SchemaHistoryResponse(BaseModel):
    history: List[SchemaSnapshotModel]


class SchemaDiffResponse(BaseModel):
    tables_added: List[str]
    tables_removed: List[str]
    columns_added: List[Any]
    columns_removed: List[Any]
    relationships_added: List[Any]
    relationships_removed: List[Any]
    error: Optional[str] = None


class DocumentationRequest(BaseModel):
    model_config = {"protected_namespaces": ()}
    
    table_names: List[str] = Field(..., description="List of table names to document")
    format: str = Field(default="markdown", description="Output format (markdown, html, pdf)")
    include_examples: bool = Field(default=True, description="Include example data")
    timestamp: Optional[str] = Field(default=None, description="Generation timestamp")
    
    # Optional detailed request fields for backward compatibility
    request_schema: Optional[SchemaResponse] = Field(None, alias="schema")
    table: Optional[str] = None
    column: Optional[str] = None
    relationship: Optional[dict] = None
    glossary_term: Optional[str] = None
    regenerate: bool = False
    context: Optional[Any] = None


class DocumentationResponse(BaseModel):
    content: str = Field(..., description="Generated documentation content")
    format: str = Field(..., description="Format of the documentation")
    generated_at: Optional[str] = Field(None, description="Generation timestamp")
    tables_included: List[str] = Field(default_factory=list, description="Tables included in documentation")
    
    # Optional detailed response fields for backward compatibility
    object_type: Optional[str] = Field(None, description="table, column, relationship, glossary")
    object_id: Optional[str] = Field(None, description="ID of the documented object")
    documentation: Optional[str] = Field(None, description="Documentation content (alias for content)")
    generated: bool = Field(default=True, description="Whether documentation was generated")
    last_updated: Optional[str] = None
    warnings: Optional[List[str]] = None


class DataCleaningRequest(BaseModel):
    table: str
    data: List[dict]
    columns: Optional[List[str]] = None
    context: Optional[Any] = None


class CleaningSuggestion(BaseModel):
    column: str
    issue: str
    suggestion: str
    fix_code: Optional[str] = None  # SQL or Python code
    confidence: float = 1.0


class DataCleaningResponse(BaseModel):
    table: str
    suggestions: List[CleaningSuggestion]
    warnings: Optional[List[str]] = None


class ApplyCleaningRequest(BaseModel):
    table: str
    data: List[dict]
    actions: List[dict]  # e.g., [{column, action, params}]


class ApplyCleaningResponse(BaseModel):
    table: str
    cleaned_data: List[dict]
    applied_actions: List[dict]
    warnings: Optional[List[str]] = None


# ============================================================================
# Cloud Provisioning Schemas
# ============================================================================

class CloudProvider(str, Enum):
    """Supported cloud providers"""
    AWS = "aws"
    GCP = "gcp"
    AZURE = "azure"


class DeploymentStatus(str, Enum):
    """Deployment status options"""
    PENDING = "pending"
    ANALYZING = "analyzing"
    PROVISIONING = "provisioning"
    CONFIGURING = "configuring"
    GENERATING = "generating"
    READY = "ready"
    FAILED = "failed"


class AnalyzeRequest(BaseModel):
    """Request schema for analyzing deployment requirements"""
    description: str = Field(..., description="Natural language description of database needs")
    preferences: Optional[Dict[str, Any]] = Field(default=None, description="User preferences for provider, region, budget")


class TableDefinition(BaseModel):
    """Table definition in schema"""
    name: str
    columns: List[Dict[str, Any]]
    purpose: Optional[str] = None
    indexes: Optional[List[str]] = None
    constraints: Optional[List[Dict[str, Any]]] = None


class RelationshipDefinition(BaseModel):
    """Relationship between tables"""
    from_table: str = Field(..., alias="from")
    to_table: str = Field(..., alias="to")
    type: str  # one-to-one, one-to-many, many-to-many
    foreign_key: str


class SchemaAnalysis(BaseModel):
    """Analyzed schema from description"""
    database_type: str
    version: str
    tables: List[TableDefinition]
    relationships: List[RelationshipDefinition]
    features: List[str]
    estimated_size: str


class ProviderRecommendation(BaseModel):
    """Cloud provider recommendation"""
    provider: str
    instance_type: str
    cost_per_month: float
    reasoning: Optional[str] = None


class CloudRecommendations(BaseModel):
    """Cloud recommendations for deployment"""
    provider: str
    instance_type: str
    storage: int
    cost_per_month: float
    reasoning: str
    alternatives: List[ProviderRecommendation] = []


class AnalyzeResponse(BaseModel):
    """Response schema for analyze endpoint"""
    analysis: SchemaAnalysis
    recommendations: CloudRecommendations
    schema: Dict[str, Any]


class AWSCredentials(BaseModel):
    """AWS credentials"""
    access_key: str = Field(..., alias="accessKey")
    secret_key: str = Field(..., alias="secretKey")
    region: str


class GCPCredentials(BaseModel):
    """GCP credentials"""
    project_id: str = Field(..., alias="projectId")
    credentials_json: str = Field(..., alias="credentialsJson")
    region: str


class AzureCredentials(BaseModel):
    """Azure credentials"""
    subscription_id: str = Field(..., alias="subscriptionId")
    tenant_id: str = Field(..., alias="tenantId")
    client_id: str = Field(..., alias="clientId")
    client_secret: str = Field(..., alias="clientSecret")
    region: str


class ValidateCredentialsRequest(BaseModel):
    """Request to validate cloud credentials"""
    provider: CloudProvider
    credentials: Dict[str, Any]


class ValidateCredentialsResponse(BaseModel):
    """Response from credential validation"""
    valid: bool
    permissions: Optional[List[str]] = None
    account_id: Optional[str] = None
    message: str
    error: Optional[str] = None


class DeploymentOptions(BaseModel):
    """Options for code and asset generation"""
    generate_code: bool = Field(default=True, alias="generateCode")
    create_migrations: bool = Field(default=True, alias="createMigrations")
    setup_api: bool = Field(default=False, alias="setupAPI")
    language: Optional[str] = "typescript"
    framework: Optional[str] = "fastapi"


class InstanceConfig(BaseModel):
    """Cloud instance configuration"""
    instance_type: str = Field(..., alias="instanceType")
    storage: int
    region: str
    auto_scaling: bool = Field(default=False, alias="autoScaling")
    backup_enabled: bool = Field(default=True, alias="backupEnabled")
    multi_az: bool = Field(default=False, alias="multiAz")
    public_access: bool = Field(default=True, alias="publicAccess")


class DeployRequest(BaseModel):
    """Request to deploy cloud infrastructure"""
    provider: CloudProvider
    credentials: Dict[str, Any]
    schema: Dict[str, Any]
    options: DeploymentOptions
    instance_config: InstanceConfig = Field(..., alias="instanceConfig")


class DeployResponse(BaseModel):
    """Response from deploy endpoint"""
    deployment_id: str = Field(..., alias="deploymentId")
    status: str
    websocket_url: str = Field(..., alias="websocketUrl")


class ProgressUpdate(BaseModel):
    """Progress update message"""
    type: str = "progress"
    data: Dict[str, Any]


class DeploymentResult(BaseModel):
    """Final deployment result"""
    connection_string: str = Field(..., alias="connectionString")
    cloud_resource_id: str = Field(..., alias="cloudResourceId")
    generated_assets: Optional[Dict[str, Any]] = Field(default=None, alias="generatedAssets")


class CompleteMessage(BaseModel):
    """Completion message"""
    type: str = "complete"
    data: DeploymentResult


class CostEstimateRequest(BaseModel):
    """Request to estimate costs"""
    provider: CloudProvider
    instance_type: str = Field(..., alias="instanceType")
    storage: int
    region: str
    backup_enabled: bool = Field(default=True, alias="backupEnabled")
    auto_scaling: bool = Field(default=False, alias="autoScaling")


class CostBreakdown(BaseModel):
    """Cost breakdown by component"""
    compute: float
    storage: float
    backup: float
    network: float = 0.0


class CostEstimateResponse(BaseModel):
    """Response with cost estimates"""
    monthly_total: float = Field(..., alias="monthlyTotal")
    hourly_total: float = Field(..., alias="hourlyTotal")
    breakdown: CostBreakdown
    comparison: Optional[Dict[str, float]] = None


class DeploymentSummary(BaseModel):
    """Summary of a deployment"""
    deployment_id: str = Field(..., alias="deploymentId")
    description: str
    provider: str
    status: str
    database_type: str = Field(..., alias="databaseType")
    created_at: str = Field(..., alias="createdAt")
    cost_per_month: Optional[float] = Field(None, alias="costPerMonth")


class ListDeploymentsResponse(BaseModel):
    """Response listing deployments"""
    deployments: List[DeploymentSummary]
    total: int


class DeploymentProgress(BaseModel):
    """Deployment progress information"""
    percentage: int
    current_step: str = Field(..., alias="currentStep")


class GetDeploymentResponse(BaseModel):
    """Response for get deployment details"""
    deployment_id: str = Field(..., alias="deploymentId")
    status: str
    progress: DeploymentProgress
    result: Optional[DeploymentResult] = None
    created_at: str = Field(..., alias="createdAt")
    completed_at: Optional[str] = Field(None, alias="completedAt")


class DeleteDeploymentRequest(BaseModel):
    """Request to delete deployment"""
    delete_resources: bool = Field(default=True, alias="deleteResources")


class DeleteDeploymentResponse(BaseModel):
    """Response from delete deployment"""
    success: bool
    message: str

