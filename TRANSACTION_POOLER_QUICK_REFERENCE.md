# Transaction Pooler Quick Reference

## 🎯 **TL;DR - What Changed**

All services now use **PgBouncer transaction pooler** compatible configuration:
- ✅ `statement_cache_size=0` (MOST CRITICAL)
- ✅ Small pool sizes (3-5)
- ✅ Fast recycling (5 minutes)
- ✅ Connection verification enabled
- ✅ Query timeouts configured

---

## 📋 **Services Modified**

| Service | Files Changed | Status |
|---------|--------------|--------|
| Authentication | `main.py`, `models/user.py` | ✅ Complete |
| Project Management | `core/database_service.py` | ✅ Complete |
| Schema Detection | `core/database_service.py`, `shared/utils/database.py` | ✅ Complete |
| Code Generation | `core/database_service.py`, `enterprise_integration/database_integration.py` | ✅ Complete |
| AI Chat | `core/database_service.py` | ✅ Complete |
| Database Migration | `core/enterprise_store.py`, `shared/utils/database.py` | ✅ Complete |

---

## ⚙️ **Critical Configuration**

### **The One Setting You Must Have:**
```python
connect_args={
    "statement_cache_size": 0  # 👈 THIS IS CRITICAL
}
```

Without this, you'll get: `"prepared statement does not exist"` errors.

---

## 🚀 **Deployment Command**

```bash
# 1. Update DATABASE_URL to transaction pooler
heroku config:set DATABASE_URL="<transaction_pooler_url>" --app <app-name>

# 2. For database-migration service ONLY, also add session pooler
heroku config:set DATABASE_URL_SESSION="<session_pooler_url>" --app schemasage-database-migration

# 3. Deploy
git push heroku main

# 4. Monitor
heroku logs --tail --app <app-name>
```

---

## 🔍 **What to Watch For**

### **Good Signs ✅:**
- Fast response times (<2s)
- No connection errors
- Connections released quickly

### **Bad Signs ❌:**
- "prepared statement does not exist"
- "MaxClientsInSessionMode"
- "server closed connection unexpectedly"
- Request timeouts

---

## 🛠️ **Troubleshooting**

### **Problem:** Still getting "prepared statement" errors
**Solution:** Double-check `statement_cache_size=0` in ALL engine configs

### **Problem:** Connection timeouts
**Solution:** Verify you're using the **transaction pooler** URL, not session pooler

### **Problem:** Slow performance
**Solution:** Check query performance, ensure indexes exist

---

## 📞 **Database Migration Service - Special Case**

This service needs **BOTH** poolers:

- **API endpoints** → Use `DATABASE_URL` (transaction pooler) ✅
- **ETL/migration scripts** → Use `DATABASE_URL_SESSION` (session pooler) ✅

**Why?** Scripts need long-lived connections, APIs need short-lived ones.

---

## ✅ **Verification Steps**

1. **Deploy code**
2. **Test each service** (health endpoints)
3. **Run basic operations** (create, read, update, delete)
4. **Monitor logs** for 1 hour
5. **Check Supabase dashboard** (connection count should be low)

---

## 📖 **Full Documentation**

See `TRANSACTION_POOLER_IMPLEMENTATION.md` for complete details.

---

**Last Updated:** October 27, 2025  
**Status:** ✅ Ready for deployment
