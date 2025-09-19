# 🧪 SchemaSage Testing Guide

## **Testing Strategy**

### **Phase 1: Backend API Testing (Heroku)**
Test your backend APIs directly to ensure they work independently.

**Backend URL**: `https://schemasage-database-migration-dfc50cf95a69.herokuapp.com`

#### **Quick Manual Tests:**

1. **Health Check**: 
   ```
   GET https://schemasage-database-migration-dfc50cf95a69.herokuapp.com/health
   ```

2. **API Documentation**: 
   ```
   https://schemasage-database-migration-dfc50cf95a69.herokuapp.com/docs
   ```

3. **Cloud Providers List**:
   ```
   GET https://schemasage-database-migration-dfc50cf95a69.herokuapp.com/api/v1/cloud/providers
   ```

#### **Automated Testing:**
Run the test script I created:
```bash
python test_backend_endpoints.py
```

---

### **Phase 2: Frontend Integration Testing (Vercel)**
Once backend tests pass, test the full user experience.

**Frontend URL**: `https://schemasage.vercel.app`

#### **Features to Test:**

**🎯 Core Migration Features:**
- [ ] Database connection testing
- [ ] Schema detection and analysis
- [ ] Basic migration creation
- [ ] Migration progress monitoring

**☁️ Cloud Migration Features:**
- [ ] Cloud readiness assessment
- [ ] Cloud provider comparison
- [ ] Migration planning wizard
- [ ] Cost estimation
- [ ] Terraform code generation

**💰 Cost Optimization:**
- [ ] Cost analysis dashboard
- [ ] Optimization recommendations
- [ ] Savings calculations

**🛡️ Disaster Recovery:**
- [ ] Backup configuration
- [ ] DR testing
- [ ] Recovery procedures

**📊 Analytics & Monitoring:**
- [ ] Migration analytics
- [ ] Real-time monitoring
- [ ] Performance metrics

---

### **Phase 3: End-to-End Integration**
Test complete workflows from frontend to backend.

#### **Test Scenarios:**

**Scenario 1: Simple Database Migration**
1. Go to `schemasage.vercel.app/migration`
2. Enter test database connection
3. Run connection test
4. Create migration plan
5. Monitor progress

**Scenario 2: Cloud Migration Workflow**
1. Start cloud migration wizard
2. Run readiness assessment
3. Compare cloud providers
4. Generate migration plan
5. Review Terraform code

**Scenario 3: Cost Optimization**
1. Connect cloud account (test mode)
2. Analyze current costs
3. Review recommendations
4. Apply optimizations

---

## **Recommended Testing Order:**

### **Start Here** ⭐
1. **Run Backend Tests First**:
   ```bash
   python test_backend_endpoints.py
   ```

2. **If Backend Tests Pass** ✅:
   - Test frontend at `schemasage.vercel.app`
   - Verify frontend-backend integration

3. **If Backend Tests Fail** ❌:
   - Check Heroku logs: `heroku logs --tail -a schemasage-database-migration`
   - Fix backend issues first
   - Re-deploy and test again

---

## **Expected Results:**

### **Backend Should Return:**
- ✅ Health check: `{"status": "healthy"}`
- ✅ API docs: Interactive Swagger UI
- ✅ Cloud providers: List of AWS, Azure, GCP
- ✅ Assessment: Readiness scores and recommendations
- ✅ Migration plans: Terraform code and cost estimates

### **Frontend Should Show:**
- ✅ Migration dashboard with cloud options
- ✅ Cloud provider selection cards
- ✅ Cost optimization widgets
- ✅ Real-time progress indicators
- ✅ Generated infrastructure code

---

## **Troubleshooting:**

### **Common Issues:**
1. **CORS Errors**: Frontend can't reach backend
2. **Authentication**: Missing API keys or tokens
3. **Rate Limits**: Too many test requests
4. **Timeouts**: Long-running operations

### **Debug Commands:**
```bash
# Check backend logs
heroku logs --tail -a schemasage-database-migration

# Test specific endpoint
curl https://schemasage-database-migration-dfc50cf95a69.herokuapp.com/health

# Check frontend console for errors
# Open browser dev tools on schemasage.vercel.app
```

---

## **Next Steps After Testing:**
1. Document any bugs found
2. Test with real database connections
3. Verify cloud provider integrations
4. Load test with multiple users
5. Security audit for production readiness
