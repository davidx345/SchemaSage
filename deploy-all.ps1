# Deploy all services at once
param([string]$Message = "Update all services")

Write-Host "🚀 Deploying all SchemaSage services..." -ForegroundColor Cyan

# Commit to GitHub first
git add .
git commit -m $Message
git push origin main

$services = @(
    @{name="API Gateway"; app="schemasage-api-gateway"; path="services/api-gateway"}
    @{name="Authentication"; app="schemasage-auth"; path="services/authentication"}
    @{name="Code Generation"; app="schemasage-code-generation"; path="services/code-generation"}
    @{name="Schema Detection"; app="schemasage-schema-detection"; path="services/schema-detection"}
    @{name="Project Management"; app="schemasage-project-management"; path="services/project-management"}
    @{name="AI Chat"; app="schemasage-ai-chat"; path="services/ai-chat"}
)

foreach ($service in $services) {
    Write-Host "📦 Deploying $($service.name)..." -ForegroundColor Yellow
    
    # Add remote if needed
    heroku git:remote -a $service.app -r "heroku-$($service.name.Replace(' ', '').ToLower())" 2>$null
    
    # Deploy
    try {
        git subtree push --prefix=$service.path "heroku-$($service.name.Replace(' ', '').ToLower())" main
        Write-Host "✅ $($service.name) deployed successfully!" -ForegroundColor Green
    } catch {
        Write-Host "❌ Failed to deploy $($service.name)" -ForegroundColor Red
    }
    
    Start-Sleep -Seconds 2
}

Write-Host "🎉 All services deployment completed!" -ForegroundColor Cyan
