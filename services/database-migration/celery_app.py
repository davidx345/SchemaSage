"""
Celery Application Configuration for Database Migration Service
Handles long-running tasks like schema extraction and data migration
"""
import os
from celery import Celery
from kombu import Exchange, Queue

# Get Redis URL from environment (set by Heroku config)
redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Initialize Celery app
celery_app = Celery(
    "database_migration_worker",
    broker=redis_url,
    backend=redis_url,
    include=['tasks']  # Import tasks module
)

# Celery configuration
celery_app.conf.update(
    # Task execution settings
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    
    # Task result settings
    result_expires=3600,  # Results expire after 1 hour
    result_backend_transport_options={
        'master_name': 'mymaster',
        'visibility_timeout': 3600,
    },
    
    # Task tracking
    task_track_started=True,
    task_send_sent_event=True,
    
    # Worker settings
    worker_prefetch_multiplier=1,  # One task at a time for long-running tasks
    worker_max_tasks_per_child=50,  # Restart worker after 50 tasks to prevent memory leaks
    
    # Task time limits (in seconds)
    task_time_limit=600,  # Hard limit: 10 minutes (must complete before this)
    task_soft_time_limit=540,  # Soft limit: 9 minutes (raises exception, can be caught)
    
    # Retry settings
    task_acks_late=True,  # Acknowledge task after completion (ensures retry on failure)
    task_reject_on_worker_lost=True,
    
    # Queue configuration
    task_default_queue='default',
    task_default_exchange='default',
    task_default_exchange_type='direct',
    task_default_routing_key='default',
    
    # Custom queues
    task_queues=(
        Queue('default', Exchange('default'), routing_key='default'),
        Queue('schema_extraction', Exchange('schema_extraction'), routing_key='schema_extraction'),
        Queue('data_migration', Exchange('data_migration'), routing_key='data_migration'),
    ),
    
    # Task routes (assign tasks to specific queues)
    task_routes={
        'tasks.extract_schema_task': {'queue': 'schema_extraction'},
        'tasks.migrate_data_task': {'queue': 'data_migration'},
    },
    
    # Broker connection settings
    broker_connection_retry_on_startup=True,
    broker_connection_retry=True,
    broker_connection_max_retries=10,
    
    # Redis SSL/TLS support (for Redis Cloud)
    broker_use_ssl={
        'ssl_cert_reqs': None  # Don't verify SSL certificates (for development)
    } if redis_url.startswith('rediss://') else None,
    
    redis_backend_use_ssl={
        'ssl_cert_reqs': None
    } if redis_url.startswith('rediss://') else None,
)

# Configure logging
celery_app.conf.update(
    worker_hijack_root_logger=False,
    worker_log_format='[%(asctime)s: %(levelname)s/%(processName)s] %(message)s',
    worker_task_log_format='[%(asctime)s: %(levelname)s/%(processName)s] [%(task_name)s(%(task_id)s)] %(message)s',
)

if __name__ == '__main__':
    celery_app.start()
