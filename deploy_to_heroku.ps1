# SchemaSage Heroku Deployment Script - Auto Deploy
# This script will automatically deploy all services to Heroku

Write-Host "🚀 SchemaSage Heroku Auto Deployment" -ForegroundColor Green
Write-Host "=====================================" -ForegroundColor Green

# Step 1: Create Heroku Applications and Set Environment Variables
Write-Host "`nStep 1: Creating Heroku Applications and Setting Environment Variables..." -ForegroundColor Yellow

# Authentication Service
Write-Host "Creating Authentication Service..." -ForegroundColor Cyan
heroku create schemasage-auth
heroku config:set DATABASE_URL='your-supabase-connection-string' JWT_SECRET_KEY='your-super-secret-jwt-key' OPENAI_API_KEY='your-openai-key' ANTHROPIC_API_KEY='your-anthropic-key' GOOGLE_API_KEY='your-google-key' --app=schemasage-auth

# API Gateway
Write-Host "Creating API Gateway..." -ForegroundColor Cyan
heroku create schemasage-api-gateway
heroku config:set API_GATEWAY_KEY='your-api-gateway-key' --app=schemasage-api-gateway

# Schema Detection
Write-Host "Creating Schema Detection..." -ForegroundColor Cyan
heroku create schemasage-schema-detection
heroku config:set SCHEMA_DETECTION_KEY='your-schema-detection-key' --app=schemasage-schema-detection

# Project Management
Write-Host "Creating Project Management..." -ForegroundColor Cyan
heroku create schemasage-project-mgmt
heroku config:set PROJECT_MGMT_KEY='your-project-mgmt-key' --app=schemasage-project-mgmt

# Code Generation
Write-Host "Creating Code Generation..." -ForegroundColor Cyan
heroku create schemasage-code-gen
heroku config:set CODE_GEN_KEY='your-code-gen-key' --app=schemasage-code-gen

# AI Chat
Write-Host "Creating AI Chat..." -ForegroundColor Cyan
heroku create schemasage-ai-chat
heroku config:set AI_CHAT_KEY='your-ai-chat-key' --app=schemasage-ai-chat

# Step 2: Deploy Services
Write-Host "`nStep 2: Deploying Services..." -ForegroundColor Yellow

# Deploy Authentication Service
Write-Host "`nDeploying Authentication Service..." -ForegroundColor Cyan
Set-Location "services/authentication"
git init
git add .
git commit -m "Initial deployment"
heroku git:remote -a schemasage-auth
git push heroku main
Set-Location "../.."

# Deploy API Gateway
Write-Host "`nDeploying API Gateway..." -ForegroundColor Cyan
Set-Location "services/api-gateway"
git init
git add .
git commit -m "Initial deployment"
heroku git:remote -a schemasage-api-gateway
git push heroku main
Set-Location "../.."

# Deploy Schema Detection
Write-Host "`nDeploying Schema Detection..." -ForegroundColor Cyan
Set-Location "services/schema-detection"
git init
git add .
git commit -m "Initial deployment"
heroku git:remote -a schemasage-schema-detection
git push heroku main
Set-Location "../.."

# Deploy Project Management
Write-Host "`nDeploying Project Management..." -ForegroundColor Cyan
Set-Location "services/project-management"
git init
git add .
git commit -m "Initial deployment"
heroku git:remote -a schemasage-project-mgmt
git push heroku main
Set-Location "../.."

# Deploy Code Generation
Write-Host "`nDeploying Code Generation..." -ForegroundColor Cyan
Set-Location "services/code-generation"
git init
git add .
git commit -m "Initial deployment"
heroku git:remote -a schemasage-code-gen
git push heroku main
Set-Location "../.."

# Deploy AI Chat
Write-Host "`nDeploying AI Chat..." -ForegroundColor Cyan
Set-Location "services/ai-chat"
git init
git add .
git commit -m "Initial deployment"
heroku git:remote -a schemasage-ai-chat
git push heroku main
Set-Location "../.."

Write-Host "`n✅ Deployment Complete!" -ForegroundColor Green
Write-Host "Your SchemaSage microservices are now live on Heroku!" -ForegroundColor Green

Write-Host "`nNext steps:" -ForegroundColor Yellow
Write-Host "1. Check logs: heroku logs --tail --app=APP_NAME"
Write-Host "2. Test your endpoints"
