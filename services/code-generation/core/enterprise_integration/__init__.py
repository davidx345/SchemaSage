"""
Enterprise integration module initialization
"""

from .base import (
    IntegrationType,
    AuthenticationType,
    IntegrationStatus,
    Credentials,
    IntegrationConfig,
    DataTransferJob,
    IntegrationEvent,
    IntegrationHealth,
    BaseIntegration
)

from .database_integration import (
    DatabaseIntegration,
    MongoDBIntegration,
    RedisIntegration
)

from .cloud_storage import (
    CloudStorageIntegration,
    AWSStorageIntegration,
    AzureStorageIntegration,
    GCPStorageIntegration
)

from .api_integration import (
    APIIntegration,
    WebhookIntegration,
    GraphQLIntegration
)

from .messaging import (
    MessageQueueIntegration,
    RabbitMQIntegration,
    KafkaIntegration,
    RedisQueueIntegration
)

__all__ = [
    # Base types and classes
    "IntegrationType",
    "AuthenticationType", 
    "IntegrationStatus",
    "Credentials",
    "IntegrationConfig",
    "DataTransferJob",
    "IntegrationEvent",
    "IntegrationHealth",
    "BaseIntegration",
    
    # Database integrations
    "DatabaseIntegration",
    "MongoDBIntegration", 
    "RedisIntegration",
    
    # Cloud storage integrations
    "CloudStorageIntegration",
    "AWSStorageIntegration",
    "AzureStorageIntegration",
    "GCPStorageIntegration",
    
    # API integrations
    "APIIntegration",
    "WebhookIntegration",
    "GraphQLIntegration",
    
    # Message queue integrations
    "MessageQueueIntegration",
    "RabbitMQIntegration",
    "KafkaIntegration",
    "RedisQueueIntegration"
]

# Integration factory function
def create_integration(config: IntegrationConfig) -> BaseIntegration:
    """
    Factory function to create integration instances based on type
    """
    integration_map = {
        IntegrationType.DATABASE: DatabaseIntegration,
        IntegrationType.MONGODB: MongoDBIntegration,
        IntegrationType.REDIS: RedisIntegration,
        IntegrationType.AWS_S3: AWSStorageIntegration,
        IntegrationType.AZURE_BLOB: AzureStorageIntegration,
        IntegrationType.GCP_STORAGE: GCPStorageIntegration,
        IntegrationType.REST_API: APIIntegration,
        IntegrationType.GRAPHQL: GraphQLIntegration,
        IntegrationType.WEBHOOK: WebhookIntegration,
        IntegrationType.RABBITMQ: RabbitMQIntegration,
        IntegrationType.KAFKA: KafkaIntegration,
        IntegrationType.REDIS_QUEUE: RedisQueueIntegration
    }
    
    integration_class = integration_map.get(config.integration_type)
    if not integration_class:
        raise ValueError(f"Unsupported integration type: {config.integration_type}")
    
    return integration_class(config)
