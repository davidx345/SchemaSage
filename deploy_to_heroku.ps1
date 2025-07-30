# SchemaSage Heroku Deployment Script
# Run this script step by step

# Prerequisites:
# 1. Install Heroku CLI: https://devcenter.heroku.com/articles/heroku-cli
# 2. Login to Heroku: heroku login
# 3. Set up your Supabase database and get the connection string

Write-Host "🚀 SchemaSage Heroku Deployment Guide" -ForegroundColor Green
Write-Host "=======================================" -ForegroundColor Green

Write-Host "`n📋 Step 1: Create Heroku Applications" -ForegroundColor Yellow
Write-Host "Run these commands one by one:" -ForegroundColor White

$services = @(
    "schemasage-auth",
    "schemasage-api-gateway", 
    "schemasage-schema-detection",
    "schemasage-project-mgmt",
    "schemasage-code-gen",
    "schemasage-ai-chat"
)

foreach ($service in $services) {
    Write-Host "heroku create $service" -ForegroundColor Cyan
}

Write-Host "`n📋 Step 2: Set Environment Variables" -ForegroundColor Yellow
Write-Host "Set these for ALL applications:" -ForegroundColor White

$envVars = @(
    "heroku config:set DATABASE_URL='your-supabase-connection-string'",
    "heroku config:set JWT_SECRET_KEY='your-super-secret-jwt-key'",
    "heroku config:set OPENAI_API_KEY='your-openai-key'",
    "heroku config:set ANTHROPIC_API_KEY='your-anthropic-key'",
    "heroku config:set GOOGLE_API_KEY='your-google-key'"
)

foreach ($var in $envVars) {
    Write-Host "$var --app=APP_NAME" -ForegroundColor Cyan
}

Write-Host "`n📋 Step 3: Deploy Services" -ForegroundColor Yellow
Write-Host "Navigate to each service directory and deploy:" -ForegroundColor White

$deployCommands = @(
    @{Service="Authentication"; Dir="services/authentication"; App="schemasage-auth"},
    @{Service="API Gateway"; Dir="services/api-gateway"; App="schemasage-api-gateway"},
    @{Service="Schema Detection"; Dir="services/schema-detection"; App="schemasage-schema-detection"},
    @{Service="Project Management"; Dir="services/project-management"; App="schemasage-project-mgmt"},
    @{Service="Code Generation"; Dir="services/code-generation"; App="schemasage-code-gen"},
    @{Service="AI Chat"; Dir="services/ai-chat"; App="schemasage-ai-chat"}
)

foreach ($deploy in $deployCommands) {
    Write-Host "`n🔧 Deploying $($deploy.Service):" -ForegroundColor Magenta
    Write-Host "cd $($deploy.Dir)" -ForegroundColor Cyan
    Write-Host "git init" -ForegroundColor Cyan
    Write-Host "git add ." -ForegroundColor Cyan
    Write-Host "git commit -m 'Initial deployment'" -ForegroundColor Cyan
    Write-Host "heroku git:remote -a $($deploy.App)" -ForegroundColor Cyan
    Write-Host "git push heroku main" -ForegroundColor Cyan
    Write-Host "cd ..\.." -ForegroundColor Cyan
}

Write-Host "`n📋 Step 4: Verify Deployments" -ForegroundColor Yellow
foreach ($service in $services) {
    Write-Host "heroku logs --tail --app=$service" -ForegroundColor Cyan
}

Write-Host "`n✅ Deployment Complete!" -ForegroundColor Green
Write-Host "Your SchemaSage microservices are now live on Heroku!" -ForegroundColor Green
