# Deployment Instructions - AI Chat Service
## After Critical Fixes

## 🚀 Quick Deploy to Heroku

### Step 1: Commit Changes
```bash
cd /c/Users/USER/Documents/projects/SchemaSage
git add services/ai-chat/
git commit -m "Fix: Critical missing parameters and comprehensive logging for AI chat service"
```

### Step 2: Push to Heroku
```bash
git subtree push --prefix=services/ai-chat heroku main
```

### Step 3: Monitor Deployment
```bash
heroku logs --tail --app schemasage-ai-chat
```

---

## 🔍 What to Watch For in Logs

### ✅ Successful Startup
You should see:
```
AI Chat Service starting up...
✅ Database initialized successfully
OpenAI provider configured
✅ AI Chat Service ready
```

### ✅ Successful Request
You should see:
```
📨 /chat endpoint called from IP: xxx.xxx.xxx.xxx
Getting or creating session abc-123 for user 1
✅ Session ready: abc-123
🤖 Requesting OpenAI response for question: ...
🚀 Calling OpenAI API - Model: gpt-3.5-turbo, Messages: 3, User: 1
✅ OpenAI API responded successfully - Tokens: 45
✅ Chat request completed successfully for user 1
```

### ❌ Common Errors and Solutions

**If you see: "OpenAI API key not configured"**
```bash
heroku config:set OPENAI_API_KEY="your-api-key-here" --app schemasage-ai-chat
```

**If you see: "Failed to initialize chat database"**
- Check DATABASE_URL is set correctly
- Verify Supabase connection pooler is accessible
- Check connection pool settings

**If you see: "⏱️ TIMEOUT calling OpenAI API"**
- OpenAI might be slow/down
- Check network connectivity
- Logs will show exactly how long it took

**If you see: "Authentication required"**
- Frontend needs to pass valid JWT token
- Check JWT_SECRET_KEY matches auth service

---

## 🧪 Test Endpoints After Deploy

### 1. Health Check
```bash
curl https://schemasage-ai-chat.herokuapp.com/health
```
Expected:
```json
{
  "status": "healthy",
  "service": "ai-chat",
  "version": "1.0.0",
  "ai_providers": {
    "openai": true
  }
}
```

### 2. Test OpenAI Connection (requires auth)
```bash
curl https://schemasage-ai-chat.herokuapp.com/providers/test \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### 3. Chat Request (requires auth)
```bash
curl -X POST https://schemasage-ai-chat.herokuapp.com/chat \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -d '{
    "question": "Hello, how are you?",
    "messages": []
  }'
```

---

## 📊 Verify Fixes

### Before (Issues):
- ❌ `/chat/openai` → 500 error (missing parameters)
- ❌ `/providers/test` → 500 error (missing parameters)
- ❌ No logs showing what's happening
- ❌ Can't distinguish timeout vs other errors

### After (Fixed):
- ✅ `/chat/openai` → Works with authentication
- ✅ `/providers/test` → Works (with/without auth)
- ✅ Comprehensive logs at every step
- ✅ Clear timeout vs error distinction
- ✅ Database operation visibility
- ✅ OpenAI call visibility

---

## 🔧 Environment Variables to Check

```bash
heroku config --app schemasage-ai-chat
```

Required:
- `OPENAI_API_KEY` - Your OpenAI API key
- `DATABASE_URL` - Supabase connection string (session pooler)
- `JWT_SECRET_KEY` - Shared with auth service

Optional (have defaults):
- `OPENAI_API_BASE` - Default: https://api.openai.com/v1
- `OPENAI_MODEL` - Default: gpt-3.5-turbo
- `MAX_TOKENS` - Default: 2000
- `TEMPERATURE` - Default: 0.7

---

## 📝 Post-Deploy Checklist

- [ ] Deploy successful (no errors in build)
- [ ] Service starts up (see "AI Chat Service ready" in logs)
- [ ] Database connection works (no DB errors)
- [ ] OpenAI provider configured (see "OpenAI provider configured")
- [ ] Health endpoint responds
- [ ] Test endpoint works (with auth)
- [ ] Chat endpoint works (with auth)
- [ ] Logs are visible and structured
- [ ] No 500/503 errors for valid requests

---

## 🆘 If Issues Persist

1. **Check Heroku logs first:**
   ```bash
   heroku logs --tail --app schemasage-ai-chat
   ```

2. **Look for specific error patterns:**
   - Database connection failures
   - OpenAI API timeouts
   - Authentication errors
   - Missing environment variables

3. **The logs will now show EXACTLY where the failure occurs!**

---

## 🎯 Success Criteria

You'll know it's working when:
1. Chat requests complete in < 5 seconds
2. Logs show complete request flow
3. No 500/503 errors for valid requests
4. OpenAI responses are saved to database
5. Users can have conversations

---

Good luck with deployment! The comprehensive logging will make debugging much easier. 🚀
