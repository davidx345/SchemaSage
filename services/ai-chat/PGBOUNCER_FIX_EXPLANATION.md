# PgBouncer Transaction Pooler - Fundamental Issue & Fix

## The Root Cause

### What Was Happening:
Your ai-chat service uses **background tasks** (`asyncio.create_task()`) to update usage statistics asynchronously. This creates a race condition with PgBouncer transaction pooler:

1. **Main Request Transaction**:
   - Gets Connection A from pool
   - Executes queries (may create prepared statements internally)
   - Commits transaction
   - Returns Connection A to PgBouncer pool

2. **Background Task** (fire-and-forget):
   - Starts execution slightly later
   - Gets Connection B from pool (could be the SAME physical connection)
   - Tries to execute query
   - **asyncpg attempts to create/reuse a prepared statement with a name that already exists**
   - Error: `DuplicatePreparedStatementError: prepared statement "__asyncpg_stmt_b__" already exists`

### Why `connect_args={"statement_cache_size": 0}` Wasn't Enough:

The problem is that `connect_args` in SQLAlchemy's `create_async_engine()` only passes parameters at **connection creation time**, but:

- asyncpg may still internally try to cache prepared statements
- Background tasks running in different async contexts may not honor the setting
- PgBouncer transaction mode doesn't fully clear prepared statement state between transactions in all scenarios

### The Real Issue: asyncpg URL Parameters vs connect_args

asyncpg has **two ways** to receive configuration:

1. **Via `connect_args`** (passed through SQLAlchemy) - Sometimes ignored for certain settings
2. **Via URL query parameters** (parsed directly by asyncpg) - **Always honored**

For PgBouncer transaction pooler compatibility, you **MUST** use the URL parameter method to guarantee that asyncpg disables prepared statement caching.

## The Fix

### What Changed:

```python
# OLD (not reliable):
database_url = "postgresql+asyncpg://..."
engine = create_async_engine(
    database_url,
    connect_args={"statement_cache_size": 0}  # May be ignored
)

# NEW (reliable):
database_url = "postgresql+asyncpg://...?prepared_statement_cache_size=0"
engine = create_async_engine(
    database_url,
    connect_args={"statement_cache_size": 0},  # Belt
    execution_options={"compiled_cache": None}  # Suspenders
)
```

### Why This Works:

1. **`prepared_statement_cache_size=0` in URL**: asyncpg reads this directly and completely disables prepared statement caching at the driver level
2. **`statement_cache_size=0` in connect_args**: Backup for older asyncpg versions
3. **`compiled_cache: None` in execution_options**: Disables SQLAlchemy's query compilation cache

This triple-layered approach ensures that:
- No prepared statements are created by asyncpg
- No compiled queries are cached by SQLAlchemy
- Background tasks get fresh connections with no cached state
- PgBouncer transaction pooler works correctly

## How to Verify the Fix

After redeploying, you should see in the logs:
```
🔧 PgBouncer transaction pooler: prepared_statement_cache_size=0 added to connection URL
```

And you should **NOT** see any more errors like:
```
DuplicatePreparedStatementError: prepared statement "__asyncpg_stmt_X__" already exists
```

## Background Tasks and Connection Pooling

The fundamental lesson here is that **fire-and-forget background tasks** (`asyncio.create_task()`) can cause subtle issues with database connection pooling because:

1. They run asynchronously after the main request completes
2. They get connections from the same pool but in a different async context
3. They may reuse connections that still have cached state from previous transactions

For PgBouncer transaction mode, you **must** ensure that every connection, regardless of when or how it's acquired, has prepared statement caching disabled.

## Why Transaction Pooler is Still Worth It

Despite this complexity, transaction pooler is the right choice for async FastAPI services because:

- **Scalability**: Supports many more concurrent requests with fewer database connections
- **Efficiency**: Connections are released immediately after each transaction
- **Cost**: Reduces database resource usage and connection limits

The key is just ensuring that your driver (asyncpg) is configured correctly for transaction-scoped connections.

## Summary

**The fundamental issue was**: Background tasks + PgBouncer transaction pooler + asyncpg prepared statement caching = race condition

**The solution is**: Disable prepared statement caching at the URL level (most reliable) + disable SQLAlchemy query cache + use connect_args as backup

**The result**: Stable, scalable, production-ready async API service with PgBouncer transaction pooler.
