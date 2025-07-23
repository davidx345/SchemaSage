# SchemaSage Microservices Deployment Guide

## Ready for Heroku Deployment ✅

Each service is now properly configured as an independent Heroku app.

### Services Ready for Deployment:

1. **Authentication Service** - `/services/authentication/`
2. **Schema Detection Service** - `/services/schema-detection/`  
3. **AI Chat Service** - `/services/ai-chat/`
4. **Code Generation Service** - `/services/code-generation/`
5. **Project Management Service** - `/services/project-management/`

### Deployment Steps:

For each service directory:

1. Create a new Heroku app:
   ```bash
   heroku create your-app-name-auth
   heroku create your-app-name-schema
   heroku create your-app-name-chat
   heroku create your-app-name-code
   heroku create your-app-name-projects
   ```

2. Add PostgreSQL addon:
   ```bash
   heroku addons:create heroku-postgresql:mini
   ```

3. Set environment variables:
   ```bash
   heroku config:set JWT_SECRET_KEY=your_secret_key
   heroku config:set OPENAI_API_KEY=your_openai_key
   heroku config:set GEMINI_API_KEY=your_gemini_key
   ```

4. Deploy from service directory:
   ```bash
   cd services/authentication
   git subtree push --prefix services/authentication heroku main
   
   ```

### Cost: FREE TIER
- Each service uses 1 free dyno
- Shared PostgreSQL databases
- Total: $0/month

All services are now deployment-ready! 🚀
