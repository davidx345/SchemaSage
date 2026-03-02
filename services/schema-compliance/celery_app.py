"""
Celery Application Configuration for Schema Detection Service
⚡ SHARED WORKER: Uses the same Celery worker from database-migration service

This configuration connects to the same Redis broker and Celery app
as the database-migration service, allowing both services to share
a single Celery worker (cost-efficient).

The database-migration worker will process tasks from both:
- database-migration service (schema extraction, data migration)
- schema-detection service (cloud provisioning, code generation)
"""
import os
from celery import Celery
from kombu import Exchange, Queue

# 🔗 Connect to the SAME Redis broker used by database-migration service
# This will be set via Heroku config in database-migration service
# No need to set REDIS_URL separately in schema-detection service
redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Handle Heroku Redis TLS
if redis_url and redis_url.startswith('redis://'):
    # Check if we need SSL
    if 'rediscloud' in redis_url or os.getenv('REDIS_TLS', 'false').lower() == 'true':
        redis_url = redis_url.replace('redis://', 'rediss://', 1)

# Initialize Celery app with SAME name as database-migration service
# This ensures both services share the same Celery instance
celery_app = Celery(
    "database_migration_worker",  # ⚠️ MUST match database-migration/celery_app.py
    broker=redis_url,
    backend=redis_url,
    include=['deployment_tasks']  # Import tasks from schema-detection service
)

# Celery configuration (matches database-migration settings)
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
    worker_prefetch_multiplier=1,  # One task at a time
    worker_max_tasks_per_child=50,
    
    # Task time limits (cloud provisioning can take 10-30 minutes)
    task_time_limit=1800,  # Hard limit: 30 minutes
    task_soft_time_limit=1680,  # Soft limit: 28 minutes
    
    # Retry settings
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    
    # Queue configuration
    task_default_queue='default',
    task_default_exchange='default',
    task_default_exchange_type='direct',
    task_default_routing_key='default',
    
    # 🔥 SHARED QUEUES: These will be processed by database-migration worker
    task_queues=(
        Queue('default', Exchange('default'), routing_key='default'),
        Queue('schema_extraction', Exchange('schema_extraction'), routing_key='schema_extraction'),
        Queue('data_migration', Exchange('data_migration'), routing_key='data_migration'),
        Queue('cloud_provisioning', Exchange('cloud_provisioning'), routing_key='cloud_provisioning'),
        Queue('code_generation', Exchange('code_generation'), routing_key='code_generation'),
    ),
    
    # Task routes (for schema-detection tasks)
    task_routes={
        'deployment_tasks.run_deployment_task': {'queue': 'cloud_provisioning'},
        'deployment_tasks.generate_code_task': {'queue': 'code_generation'},
        # database-migration tasks are routed in their service
        'tasks.extract_schema_task': {'queue': 'schema_extraction'},
        'tasks.migrate_data_task': {'queue': 'data_migration'},
    },
    
    # Broker connection settings
    broker_connection_retry_on_startup=True,
    broker_connection_retry=True,
    broker_connection_max_retries=10,
    
    # Redis SSL/TLS support (same as database-migration)
    broker_use_ssl={
        'ssl_cert_reqs': None
    } if redis_url and redis_url.startswith('rediss://') else None,
    
    redis_backend_use_ssl={
        'ssl_cert_reqs': None
    } if redis_url and redis_url.startswith('rediss://') else None,
)

# Configure logging
celery_app.conf.update(
    worker_hijack_root_logger=False,
    worker_log_format='[%(asctime)s: %(levelname)s/%(processName)s] %(message)s',
    worker_task_log_format='[%(asctime)s: %(levelname)s/%(processName)s] [%(task_name)s(%(task_id)s)] %(message)s',
)

if __name__ == '__main__':
    celery_app.start()
