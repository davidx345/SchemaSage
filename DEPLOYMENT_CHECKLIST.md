# Deployment Checklist - PgBouncer Transaction Pooler Fix

## Quick Reference

Run these commands to deploy each service:

```bash
# Project Management
git add services/project-management/core/database_service.py
git commit -m "fix: Add prepared_statement_cache_size=0 to URL for PgBouncer compatibility"
git subtree push --prefix=services/project-management heroku main

# Schema Detection
git add services/schema-detection/core/database_service.py services/schema-detection/shared/utils/database.py
git commit -m "fix: Add prepared_statement_cache_size=0 to URL for PgBouncer compatibility"
git subtree push --prefix=services/schema-detection heroku main

# Code Generation
git add services/code-generation/core/database_service.py
git commit -m "fix: Add prepared_statement_cache_size=0 to URL for PgBouncer compatibility"
git subtree push --prefix=services/code-generation heroku main

# Database Migration
git add services/database-migration/core/enterprise_store.py services/database-migration/shared/utils/database.py
git commit -m "fix: Add prepared_statement_cache_size=0 to URL for PgBouncer compatibility"
git subtree push --prefix=services/database-migration heroku main
```

## Verification

After each deployment, check logs:

```bash
# Check logs for confirmation
heroku logs --tail --app schemasage-project-management | grep "PgBouncer"
heroku logs --tail --app schemasage-schema-detection | grep "PgBouncer"
heroku logs --tail --app schemasage-code-generation | grep "PgBouncer"
heroku logs --tail --app schemasage-database-migration | grep "PgBouncer"
```

## Expected Log Output

Look for this line in startup logs:
```
🔧 PgBouncer transaction pooler: prepared_statement_cache_size=0 added to connection URL
```

And confirm no errors like:
```
❌ DuplicatePreparedStatementError: prepared statement "__asyncpg_stmt_X__" already exists
```

## Status Tracking

- [x] ai-chat - ✅ Deployed and verified
- [ ] project-management - Ready to deploy
- [ ] schema-detection - Ready to deploy
- [ ] code-generation - Ready to deploy
- [ ] database-migration - Ready to deploy

## What Changed

All services now:
1. Add `prepared_statement_cache_size=0` to DATABASE_URL programmatically
2. Include `execution_options={"compiled_cache": None}` to disable SQLAlchemy query cache
3. Log confirmation message on startup

## Rollback Plan

If any service has issues after deployment:

```bash
# Revert to previous version
heroku releases --app <app-name>
heroku rollback v<previous-version> --app <app-name>
```

## Notes

- Authentication service uses sync SQLAlchemy with NullPool - no changes needed
- API Gateway and WebSocket services don't use database - no changes needed
- All changes are backward compatible
- Services will work with both session and transaction pooler URLs
