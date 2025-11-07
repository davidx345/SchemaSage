# 🔥 Shared Celery Worker Setup (Cost-Efficient)

## Overview

Both `database-migration` and `schema-detection` services now share a **single Celery worker**, saving you the cost of running multiple worker dynos on Heroku.

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Redis Broker                          │
│              (Heroku Redis - Single Instance)                │
└─────────────────────────────────────────────────────────────┘
                            ▲
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
        ▼                   ▼                   ▼
┌──────────────┐   ┌──────────────┐   ┌──────────────┐
│ database-    │   │ schema-      │   │ SHARED       │
│ migration    │   │ detection    │   │ Celery Worker│
│ Service      │   │ Service      │   │ (1 dyno)     │
│              │   │              │   │              │
│ Sends tasks  │   │ Sends tasks  │   │ Processes    │
│ to Redis     │   │ to Redis     │   │ ALL tasks    │
└──────────────┘   └──────────────┘   └──────────────┘
```

### Queues Processed by Shared Worker

| Queue Name           | Service              | Task Type                    |
|---------------------|----------------------|------------------------------|
| `default`           | Both                 | General tasks                |
| `schema_extraction` | database-migration   | Schema extraction            |
| `data_migration`    | database-migration   | Data migration               |
| `cloud_provisioning`| schema-detection     | AWS/GCP/Azure provisioning   |
| `code_generation`   | schema-detection     | Code generation              |

---

## 🚀 Deployment Steps

### 1. Update Database-Migration Service

The `database-migration` service is where the **shared Celery worker runs**.

**Files modified:**
- ✅ `services/database-migration/celery_app.py` - Updated to include schema-detection queues

**No changes needed to:**
- `services/database-migration/tasks.py` - Existing tasks remain unchanged
- `services/database-migration/Procfile` - Worker already configured

### 2. Update Schema-Detection Service

The `schema-detection` service now **connects to the shared worker** instead of running its own.

**Files modified:**
- ✅ `services/schema-detection/celery_app.py` - Now uses same Celery app name and Redis

**Key changes:**
```python
# Changed from:
celery_app = Celery("schema_detection_worker", ...)

# To:
celery_app = Celery("database_migration_worker", ...)  # Same name as database-migration
```

**No need to:**
- ❌ Start a separate Celery worker in schema-detection
- ❌ Set REDIS_URL in schema-detection (uses database-migration's Redis)

### 3. Deploy to Heroku

#### A. Deploy Database-Migration Service (with Worker)

```bash
cd services/database-migration

# Commit changes
git add .
git commit -m "Add shared Celery worker support for schema-detection tasks"

# Deploy
git push heroku main

# Ensure Redis addon is installed
heroku addons:create heroku-redis:mini -a your-database-migration-app

# Ensure worker dyno is running
heroku ps:scale worker=1 -a your-database-migration-app

# Verify worker is processing all queues
heroku logs --tail --dyno=worker -a your-database-migration-app
```

You should see the worker listening to all queues:
```
[INFO/MainProcess] Connected to redis://...
[INFO/MainProcess] Consuming from:
- default
- schema_extraction
- data_migration
- cloud_provisioning
- code_generation
```

#### B. Deploy Schema-Detection Service (NO Worker Needed)

```bash
cd services/schema-detection

# Commit changes
git add .
git commit -m "Use shared Celery worker from database-migration service"

# Deploy
git push heroku main

# ⚠️ IMPORTANT: Set REDIS_URL to use database-migration's Redis
heroku config:set REDIS_URL=$(heroku config:get REDIS_URL -a your-database-migration-app) -a your-schema-detection-app

# ✅ NO worker dyno needed!
# If you had one running, scale it down:
heroku ps:scale worker=0 -a your-schema-detection-app
```

---

## 🧪 Testing the Shared Worker

### Test 1: Database Migration Task

```bash
# From database-migration service
curl -X POST https://your-database-migration-app.herokuapp.com/api/migrations/extract-schema \
  -H "Content-Type: application/json" \
  -d '{
    "connection_string": "postgresql://user:pass@host:5432/db",
    "migration_id": "test-123"
  }'
```

**Expected:** Task processed by shared worker in `schema_extraction` queue.

### Test 2: Cloud Provisioning Task (Schema Detection)

```bash
# From schema-detection service
curl -X POST https://your-schema-detection-app.herokuapp.com/api/cloud-provision/deploy \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_JWT" \
  -d '{
    "provider": "aws",
    "credentials": {...},
    "schema": {...}
  }'
```

**Expected:** Task processed by shared worker in `cloud_provisioning` queue.

### Test 3: Monitor Worker

```bash
# Check worker status
heroku ps -a your-database-migration-app

# View worker logs
heroku logs --tail --dyno=worker -a your-database-migration-app

# Check active tasks
heroku run celery -A celery_app inspect active -a your-database-migration-app

# Check registered tasks (should show tasks from BOTH services)
heroku run celery -A celery_app inspect registered -a your-database-migration-app
```

Expected output:
```json
{
  "tasks": [
    "tasks.extract_schema_task",
    "tasks.migrate_data_task",
    "deployment_tasks.run_deployment_task",
    "deployment_tasks.generate_code_task"
  ]
}
```

---

## 💰 Cost Savings

### Before (Separate Workers)

| Service              | Dyno Type | Cost/Month |
|---------------------|-----------|------------|
| database-migration  | worker x1 | $7         |
| schema-detection    | worker x1 | $7         |
| Redis (shared)      | mini      | $3         |
| **Total**           |           | **$17/mo** |

### After (Shared Worker)

| Service              | Dyno Type | Cost/Month |
|---------------------|-----------|------------|
| database-migration  | worker x1 | $7         |
| schema-detection    | -         | $0         |
| Redis (shared)      | mini      | $3         |
| **Total**           |           | **$10/mo** |

**💰 Savings: $7/month (41% reduction)**

---

## 🔧 Troubleshooting

### Issue: Tasks not being processed

**Solution:**
1. Check worker is running:
   ```bash
   heroku ps -a your-database-migration-app
   ```

2. Verify REDIS_URL is set correctly in schema-detection:
   ```bash
   heroku config:get REDIS_URL -a your-schema-detection-app
   heroku config:get REDIS_URL -a your-database-migration-app
   ```
   These should be **identical**.

3. Check worker logs for errors:
   ```bash
   heroku logs --tail --dyno=worker -a your-database-migration-app
   ```

### Issue: Schema-detection tasks not found

**Cause:** Worker hasn't discovered deployment_tasks module.

**Solution:** Tasks are registered when first sent. Send a test task from schema-detection, then check:
```bash
heroku run celery -A celery_app inspect registered -a your-database-migration-app
```

### Issue: Worker crashes or restarts frequently

**Cause:** Too many tasks or memory issues.

**Solution:** Increase `worker_max_tasks_per_child` in `celery_app.py`:
```python
worker_max_tasks_per_child=100,  # Increase from 50
```

---

## 📊 Monitoring

### View Queue Lengths

```bash
# Connect to Redis
heroku redis:cli -a your-database-migration-app

# Check queue lengths
> LLEN schema_extraction
> LLEN data_migration
> LLEN cloud_provisioning
> LLEN code_generation
```

### View Task Results

```bash
# Get task result by ID
> GET celery-task-meta-<task_id>
```

### Worker Health Check

```bash
# Ping workers
heroku run celery -A celery_app inspect ping -a your-database-migration-app

# Check worker stats
heroku run celery -A celery_app inspect stats -a your-database-migration-app
```

---

## 🎉 Summary

✅ **Single Celery worker** processes tasks from both services  
✅ **Shared Redis broker** reduces infrastructure costs  
✅ **No code duplication** - each service defines its own tasks  
✅ **Easy to monitor** - all tasks visible in one worker  
✅ **Scalable** - can add more workers if needed  

You're now saving **$7/month** with no functionality loss! 🚀
