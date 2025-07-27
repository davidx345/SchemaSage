"""
Message queue integration implementations
"""
import asyncio
import logging
import json
import time
from typing import Dict, List, Optional, Any, Callable
import pika
import aio_pika
import aiokafka
from redis import Redis
import aioredis

from .base import BaseIntegration, IntegrationConfig, IntegrationType, AuthenticationType

logger = logging.getLogger(__name__)

class MessageQueueIntegration(BaseIntegration):
    """Base class for message queue integrations"""
    
    def __init__(self, config: IntegrationConfig):
        super().__init__(config)
        self.connection = None
        self.channel = None
    
    async def publish_message(self, queue_name: str, message: Dict[str, Any], **kwargs) -> bool:
        """Publish message to queue"""
        raise NotImplementedError
    
    async def consume_messages(self, queue_name: str, callback: Callable, **kwargs):
        """Consume messages from queue"""
        raise NotImplementedError
    
    async def create_queue(self, queue_name: str, **kwargs) -> bool:
        """Create a queue"""
        raise NotImplementedError
    
    async def delete_queue(self, queue_name: str) -> bool:
        """Delete a queue"""
        raise NotImplementedError
    
    async def get_queue_info(self, queue_name: str) -> Optional[Dict[str, Any]]:
        """Get queue information"""
        raise NotImplementedError

class RabbitMQIntegration(MessageQueueIntegration):
    """Integration for RabbitMQ"""
    
    def __init__(self, config: IntegrationConfig):
        super().__init__(config)
        self.connection: Optional[aio_pika.Connection] = None
        self.channel: Optional[aio_pika.Channel] = None
    
    async def connect(self) -> bool:
        """Establish RabbitMQ connection"""
        try:
            connection_url = self._build_connection_url()
            
            self.connection = await aio_pika.connect_robust(connection_url)
            self.channel = await self.connection.channel()
            
            self.is_connected = True
            logger.info(f"Connected to RabbitMQ: {self.config.name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to RabbitMQ {self.config.name}: {str(e)}")
            self.config.last_error = str(e)
            return False
    
    async def disconnect(self):
        """Close RabbitMQ connection"""
        if self.channel:
            await self.channel.close()
            self.channel = None
        
        if self.connection:
            await self.connection.close()
            self.connection = None
        
        self.is_connected = False
    
    async def test_connection(self) -> Dict[str, Any]:
        """Test RabbitMQ connection"""
        start_time = time.time()
        
        try:
            if not self.connection or self.connection.is_closed:
                await self.connect()
            
            # Test by creating a temporary queue
            test_queue_name = f"test_queue_{int(time.time())}"
            queue = await self.channel.declare_queue(test_queue_name, auto_delete=True)
            await queue.delete()
            
            response_time = time.time() - start_time
            self.update_metrics(True, response_time)
            
            return {
                "success": True,
                "message": "RabbitMQ connection successful",
                "response_time": response_time,
                "server_properties": self.connection.server_properties if self.connection else {}
            }
            
        except Exception as e:
            response_time = time.time() - start_time
            self.update_metrics(False, response_time)
            
            return {
                "success": False,
                "message": f"RabbitMQ connection failed: {str(e)}",
                "response_time": response_time,
                "error": str(e)
            }
    
    async def publish_message(self, queue_name: str, message: Dict[str, Any], **kwargs) -> bool:
        """Publish message to RabbitMQ queue"""
        try:
            if not self.channel:
                await self.connect()
            
            # Declare queue if it doesn't exist
            queue = await self.channel.declare_queue(queue_name, durable=True)
            
            # Prepare message
            message_body = json.dumps(message).encode()
            
            # Get message properties
            priority = kwargs.get("priority", 0)
            expiration = kwargs.get("expiration")
            
            message_properties = {}
            if priority:
                message_properties["priority"] = priority
            if expiration:
                message_properties["expiration"] = str(expiration)
            
            # Publish message
            await self.channel.default_exchange.publish(
                aio_pika.Message(
                    message_body,
                    delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
                    **message_properties
                ),
                routing_key=queue_name
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to publish message to RabbitMQ: {str(e)}")
            return False
    
    async def consume_messages(self, queue_name: str, callback: Callable, **kwargs):
        """Consume messages from RabbitMQ queue"""
        try:
            if not self.channel:
                await self.connect()
            
            # Declare queue
            queue = await self.channel.declare_queue(queue_name, durable=True)
            
            # Set QoS
            prefetch_count = kwargs.get("prefetch_count", 1)
            await self.channel.set_qos(prefetch_count=prefetch_count)
            
            async def message_handler(message: aio_pika.IncomingMessage):
                async with message.process():
                    try:
                        # Parse message
                        message_data = json.loads(message.body.decode())
                        
                        # Call callback
                        await callback(message_data, message)
                        
                    except Exception as e:
                        logger.error(f"Error processing message: {str(e)}")
                        # Message will be nacked automatically due to exception
            
            # Start consuming
            await queue.consume(message_handler)
            
        except Exception as e:
            logger.error(f"Failed to consume messages from RabbitMQ: {str(e)}")
    
    async def create_queue(self, queue_name: str, **kwargs) -> bool:
        """Create RabbitMQ queue"""
        try:
            if not self.channel:
                await self.connect()
            
            durable = kwargs.get("durable", True)
            auto_delete = kwargs.get("auto_delete", False)
            exclusive = kwargs.get("exclusive", False)
            
            await self.channel.declare_queue(
                queue_name,
                durable=durable,
                auto_delete=auto_delete,
                exclusive=exclusive
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to create RabbitMQ queue: {str(e)}")
            return False
    
    async def delete_queue(self, queue_name: str) -> bool:
        """Delete RabbitMQ queue"""
        try:
            if not self.channel:
                await self.connect()
            
            queue = await self.channel.declare_queue(queue_name, passive=True)
            await queue.delete()
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete RabbitMQ queue: {str(e)}")
            return False
    
    async def get_queue_info(self, queue_name: str) -> Optional[Dict[str, Any]]:
        """Get RabbitMQ queue information"""
        try:
            if not self.channel:
                await self.connect()
            
            queue = await self.channel.declare_queue(queue_name, passive=True)
            
            # Get queue info via management API if available
            # For now, return basic info
            return {
                "name": queue_name,
                "durable": True,  # Assumed from declaration
                "message_count": "unknown",  # Would need management API
                "consumer_count": "unknown"
            }
            
        except Exception as e:
            logger.error(f"Failed to get RabbitMQ queue info: {str(e)}")
            return None
    
    def _build_connection_url(self) -> str:
        """Build RabbitMQ connection URL"""
        creds = self.config.credentials.credentials
        settings = self.config.settings
        
        host = settings.get("host", "localhost")
        port = settings.get("port", 5672)
        virtual_host = settings.get("virtual_host", "/")
        
        if self.config.credentials.auth_type == AuthenticationType.BASIC_AUTH:
            username = creds.get("username", "guest")
            password = creds.get("password", "guest")
            return f"amqp://{username}:{password}@{host}:{port}/{virtual_host}"
        
        return f"amqp://{host}:{port}/{virtual_host}"

class KafkaIntegration(MessageQueueIntegration):
    """Integration for Apache Kafka"""
    
    def __init__(self, config: IntegrationConfig):
        super().__init__(config)
        self.producer: Optional[aiokafka.AIOKafkaProducer] = None
        self.consumer: Optional[aiokafka.AIOKafkaConsumer] = None
        self.bootstrap_servers = self._get_bootstrap_servers()
    
    async def connect(self) -> bool:
        """Establish Kafka connection"""
        try:
            # Create producer for testing
            self.producer = aiokafka.AIOKafkaProducer(
                bootstrap_servers=self.bootstrap_servers,
                **self._get_kafka_config()
            )
            
            await self.producer.start()
            
            self.is_connected = True
            logger.info(f"Connected to Kafka: {self.config.name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to Kafka {self.config.name}: {str(e)}")
            self.config.last_error = str(e)
            return False
    
    async def disconnect(self):
        """Close Kafka connection"""
        if self.producer:
            await self.producer.stop()
            self.producer = None
        
        if self.consumer:
            await self.consumer.stop()
            self.consumer = None
        
        self.is_connected = False
    
    async def test_connection(self) -> Dict[str, Any]:
        """Test Kafka connection"""
        start_time = time.time()
        
        try:
            if not self.producer:
                await self.connect()
            
            # Test by getting cluster metadata
            metadata = await self.producer.client.check_version()
            
            response_time = time.time() - start_time
            self.update_metrics(True, response_time)
            
            return {
                "success": True,
                "message": "Kafka connection successful",
                "response_time": response_time,
                "cluster_metadata": str(metadata)
            }
            
        except Exception as e:
            response_time = time.time() - start_time
            self.update_metrics(False, response_time)
            
            return {
                "success": False,
                "message": f"Kafka connection failed: {str(e)}",
                "response_time": response_time,
                "error": str(e)
            }
    
    async def publish_message(self, topic_name: str, message: Dict[str, Any], **kwargs) -> bool:
        """Publish message to Kafka topic"""
        try:
            if not self.producer:
                await self.connect()
            
            # Prepare message
            message_value = json.dumps(message).encode()
            message_key = kwargs.get("key", "").encode() if kwargs.get("key") else None
            
            # Send message
            await self.producer.send_and_wait(
                topic_name,
                value=message_value,
                key=message_key,
                partition=kwargs.get("partition")
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to publish message to Kafka: {str(e)}")
            return False
    
    async def consume_messages(self, topic_name: str, callback: Callable, **kwargs):
        """Consume messages from Kafka topic"""
        try:
            consumer = aiokafka.AIOKafkaConsumer(
                topic_name,
                bootstrap_servers=self.bootstrap_servers,
                group_id=kwargs.get("group_id", "schemasage"),
                auto_offset_reset=kwargs.get("auto_offset_reset", "earliest"),
                **self._get_kafka_config()
            )
            
            await consumer.start()
            
            try:
                async for message in consumer:
                    try:
                        # Parse message
                        message_data = json.loads(message.value.decode())
                        
                        # Call callback
                        await callback(message_data, message)
                        
                    except Exception as e:
                        logger.error(f"Error processing Kafka message: {str(e)}")
                        
            finally:
                await consumer.stop()
                
        except Exception as e:
            logger.error(f"Failed to consume messages from Kafka: {str(e)}")
    
    async def create_queue(self, topic_name: str, **kwargs) -> bool:
        """Create Kafka topic (requires admin privileges)"""
        try:
            from aiokafka.admin import AIOKafkaAdminClient, NewTopic
            
            admin_client = AIOKafkaAdminClient(
                bootstrap_servers=self.bootstrap_servers,
                **self._get_kafka_config()
            )
            
            await admin_client.start()
            
            try:
                num_partitions = kwargs.get("num_partitions", 1)
                replication_factor = kwargs.get("replication_factor", 1)
                
                topic = NewTopic(
                    name=topic_name,
                    num_partitions=num_partitions,
                    replication_factor=replication_factor
                )
                
                await admin_client.create_topics([topic])
                return True
                
            finally:
                await admin_client.close()
                
        except Exception as e:
            logger.error(f"Failed to create Kafka topic: {str(e)}")
            return False
    
    async def delete_queue(self, topic_name: str) -> bool:
        """Delete Kafka topic"""
        try:
            from aiokafka.admin import AIOKafkaAdminClient
            
            admin_client = AIOKafkaAdminClient(
                bootstrap_servers=self.bootstrap_servers,
                **self._get_kafka_config()
            )
            
            await admin_client.start()
            
            try:
                await admin_client.delete_topics([topic_name])
                return True
                
            finally:
                await admin_client.close()
                
        except Exception as e:
            logger.error(f"Failed to delete Kafka topic: {str(e)}")
            return False
    
    async def get_queue_info(self, topic_name: str) -> Optional[Dict[str, Any]]:
        """Get Kafka topic information"""
        try:
            from aiokafka.admin import AIOKafkaAdminClient
            
            admin_client = AIOKafkaAdminClient(
                bootstrap_servers=self.bootstrap_servers,
                **self._get_kafka_config()
            )
            
            await admin_client.start()
            
            try:
                metadata = await admin_client.describe_topics([topic_name])
                topic_metadata = metadata.get(topic_name)
                
                if topic_metadata:
                    return {
                        "name": topic_name,
                        "partitions": len(topic_metadata.partitions),
                        "replication_factor": len(topic_metadata.partitions[0].replicas) if topic_metadata.partitions else 0
                    }
                
                return None
                
            finally:
                await admin_client.close()
                
        except Exception as e:
            logger.error(f"Failed to get Kafka topic info: {str(e)}")
            return None
    
    def _get_bootstrap_servers(self) -> List[str]:
        """Get Kafka bootstrap servers"""
        servers = self.config.settings.get("bootstrap_servers", ["localhost:9092"])
        if isinstance(servers, str):
            return [servers]
        return servers
    
    def _get_kafka_config(self) -> Dict[str, Any]:
        """Get Kafka client configuration"""
        config = {}
        
        # Security configuration
        if self.config.credentials.auth_type == AuthenticationType.SASL_PLAIN:
            creds = self.config.credentials.credentials
            config.update({
                "security_protocol": "SASL_PLAINTEXT",
                "sasl_mechanism": "PLAIN",
                "sasl_plain_username": creds.get("username"),
                "sasl_plain_password": creds.get("password")
            })
        
        # SSL configuration
        ssl_settings = self.config.settings.get("ssl", {})
        if ssl_settings:
            config.update({
                "security_protocol": "SSL",
                "ssl_context": ssl_settings
            })
        
        return config

class RedisQueueIntegration(MessageQueueIntegration):
    """Integration for Redis as message queue"""
    
    def __init__(self, config: IntegrationConfig):
        super().__init__(config)
        self.redis_client: Optional[aioredis.Redis] = None
    
    async def connect(self) -> bool:
        """Establish Redis connection"""
        try:
            connection_url = self._build_connection_url()
            
            self.redis_client = aioredis.from_url(connection_url)
            
            # Test connection
            await self.redis_client.ping()
            
            self.is_connected = True
            logger.info(f"Connected to Redis Queue: {self.config.name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to Redis Queue {self.config.name}: {str(e)}")
            self.config.last_error = str(e)
            return False
    
    async def disconnect(self):
        """Close Redis connection"""
        if self.redis_client:
            await self.redis_client.close()
            self.redis_client = None
        
        self.is_connected = False
    
    async def test_connection(self) -> Dict[str, Any]:
        """Test Redis connection"""
        start_time = time.time()
        
        try:
            if not self.redis_client:
                await self.connect()
            
            await self.redis_client.ping()
            
            response_time = time.time() - start_time
            self.update_metrics(True, response_time)
            
            return {
                "success": True,
                "message": "Redis Queue connection successful",
                "response_time": response_time,
                "server_info": await self.redis_client.info()
            }
            
        except Exception as e:
            response_time = time.time() - start_time
            self.update_metrics(False, response_time)
            
            return {
                "success": False,
                "message": f"Redis Queue connection failed: {str(e)}",
                "response_time": response_time,
                "error": str(e)
            }
    
    async def publish_message(self, queue_name: str, message: Dict[str, Any], **kwargs) -> bool:
        """Publish message to Redis list"""
        try:
            if not self.redis_client:
                await self.connect()
            
            message_str = json.dumps(message)
            
            # Use LPUSH to add to the left of the list
            await self.redis_client.lpush(queue_name, message_str)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to publish message to Redis: {str(e)}")
            return False
    
    async def consume_messages(self, queue_name: str, callback: Callable, **kwargs):
        """Consume messages from Redis list"""
        try:
            if not self.redis_client:
                await self.connect()
            
            timeout = kwargs.get("timeout", 1)  # Blocking timeout in seconds
            
            while True:
                try:
                    # Use BRPOP for blocking right pop
                    result = await self.redis_client.brpop(queue_name, timeout=timeout)
                    
                    if result:
                        _, message_str = result
                        message_data = json.loads(message_str)
                        
                        # Call callback
                        await callback(message_data, {"queue": queue_name})
                        
                except asyncio.TimeoutError:
                    # Continue polling
                    continue
                except Exception as e:
                    logger.error(f"Error processing Redis message: {str(e)}")
                    
        except Exception as e:
            logger.error(f"Failed to consume messages from Redis: {str(e)}")
    
    async def create_queue(self, queue_name: str, **kwargs) -> bool:
        """Create Redis list (implicit creation)"""
        try:
            # Redis lists are created implicitly, just ensure connection
            if not self.redis_client:
                await self.connect()
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to create Redis queue: {str(e)}")
            return False
    
    async def delete_queue(self, queue_name: str) -> bool:
        """Delete Redis list"""
        try:
            if not self.redis_client:
                await self.connect()
            
            await self.redis_client.delete(queue_name)
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete Redis queue: {str(e)}")
            return False
    
    async def get_queue_info(self, queue_name: str) -> Optional[Dict[str, Any]]:
        """Get Redis list information"""
        try:
            if not self.redis_client:
                await self.connect()
            
            length = await self.redis_client.llen(queue_name)
            
            return {
                "name": queue_name,
                "length": length,
                "type": "list"
            }
            
        except Exception as e:
            logger.error(f"Failed to get Redis queue info: {str(e)}")
            return None
    
    def _build_connection_url(self) -> str:
        """Build Redis connection URL"""
        creds = self.config.credentials.credentials
        settings = self.config.settings
        
        host = settings.get("host", "localhost")
        port = settings.get("port", 6379)
        db = settings.get("database", 0)
        
        if self.config.credentials.auth_type == AuthenticationType.BASIC_AUTH:
            password = creds.get("password")
            return f"redis://:{password}@{host}:{port}/{db}"
        
        return f"redis://{host}:{port}/{db}"
