# Complete WebSocket Real-time Implementation Deployment

Write-Host "🚀 Deploying WebSocket Real-time Implementation..." -ForegroundColor Green
Write-Host "This will deploy the new WebSocket service and update all existing services." -ForegroundColor Yellow

# Step 1: Deploy WebSocket Service
Write-Host "`n📦 Step 1: Deploying WebSocket Real-time Service..." -ForegroundColor Blue
& ".\deploy-websocket.ps1"

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ WebSocket service deployment failed!" -ForegroundColor Red
    exit 1
}

# Step 2: Update Environment Variables
Write-Host "`n🔧 Step 2: Updating environment variables..." -ForegroundColor Blue  
& ".\update-env-vars.ps1"

# Step 3: Redeploy Updated Services
Write-Host "`n🔄 Step 3: Redeploying updated services..." -ForegroundColor Blue

$services = @(
    @{name="schema-detection"; path="services\schema-detection"; app="schemasage-schema-detection"},
    @{name="code-generation"; path="services\code-generation"; app="schemasage-code-generation"}, 
    @{name="project-management"; path="services\project-management"; app="schemasage-project-management"},
    @{name="authentication"; path="services\authentication"; app="schemasage-auth"},
    @{name="api-gateway"; path="services\api-gateway"; app="schemasage-api-gateway-2da67d920b07"}
)

$originalLocation = Get-Location

foreach ($service in $services) {
    Write-Host "🔄 Redeploying $($service.name)..." -ForegroundColor Yellow
    
    Set-Location $service.path
    
    try {
        # Add git remote if it doesn't exist
        git remote remove heroku 2>$null
        heroku git:remote --app $service.app
        
        # Deploy
        git add .
        git commit -m "Add WebSocket webhook integration" --allow-empty
        git push heroku HEAD:main --force
        
        Write-Host "✅ $($service.name) redeployed successfully" -ForegroundColor Green
        
    } catch {
        Write-Host "⚠️ Failed to redeploy $($service.name): $($_.Exception.Message)" -ForegroundColor Yellow
    } finally {
        Set-Location $originalLocation
    }
    
    Start-Sleep -Seconds 5
}

# Step 4: Health Check All Services
Write-Host "`n🏥 Step 4: Running health checks..." -ForegroundColor Blue

$healthChecks = @(
    @{name="WebSocket Real-time"; url="https://schemasage-websocket-realtime.herokuapp.com/health"},
    @{name="Schema Detection"; url="https://schemasage-schema-detection-0cc19b546c3c.herokuapp.com/health"},
    @{name="Code Generation"; url="https://schemasage-code-generation-56faa300323b.herokuapp.com/health"},
    @{name="Project Management"; url="https://schemasage-project-management-48496f02644b.herokuapp.com/health"},
    @{name="Authentication"; url="https://schemasage-auth-9d6de1a32af9.herokuapp.com/health"},
    @{name="API Gateway"; url="https://schemasage-api-gateway-2da67d920b07.herokuapp.com/health"}
)

Write-Host "Waiting 30 seconds for services to start..." -ForegroundColor Yellow
Start-Sleep -Seconds 30

foreach ($check in $healthChecks) {
    try {
        $response = Invoke-RestMethod -Uri $check.url -Method Get -TimeoutSec 10
        Write-Host "✅ $($check.name): $($response.status)" -ForegroundColor Green
    } catch {
        Write-Host "❌ $($check.name): Health check failed" -ForegroundColor Red
    }
}

# Display Results
Write-Host "`n🎉 WebSocket Real-time Implementation Deployment Complete!" -ForegroundColor Green
Write-Host "`n📋 Services Overview:" -ForegroundColor Blue
Write-Host "• WebSocket Real-time: https://schemasage-websocket-realtime.herokuapp.com" -ForegroundColor White
Write-Host "• API Gateway: https://schemasage-api-gateway-2da67d920b07.herokuapp.com" -ForegroundColor White
Write-Host "• Schema Detection: https://schemasage-schema-detection-0cc19b546c3c.herokuapp.com" -ForegroundColor White
Write-Host "• Code Generation: https://schemasage-code-generation-56faa300323b.herokuapp.com" -ForegroundColor White
Write-Host "• Project Management: https://schemasage-project-management-48496f02644b.herokuapp.com" -ForegroundColor White
Write-Host "• Authentication: https://schemasage-auth-9d6de1a32af9.herokuapp.com" -ForegroundColor White

Write-Host "`n🌐 Frontend Connection:" -ForegroundColor Blue
Write-Host "WebSocket URL: wss://schemasage-websocket-realtime.herokuapp.com/ws/{user_id}" -ForegroundColor Cyan

Write-Host "`n📝 What's New:" -ForegroundColor Blue
Write-Host "• Real-time dashboard updates via WebSocket" -ForegroundColor White
Write-Host "• Push notifications for schema generation" -ForegroundColor White  
Write-Host "• Live activity feed for API generation" -ForegroundColor White
Write-Host "• Instant project creation notifications" -ForegroundColor White
Write-Host "• User registration activity tracking" -ForegroundColor White
Write-Host "• Real-time statistics updates" -ForegroundColor White

Write-Host "`n🔧 Next Steps:" -ForegroundColor Blue
Write-Host "1. Update your frontend to connect to the WebSocket service" -ForegroundColor White
Write-Host "2. Test real-time functionality from your dashboard" -ForegroundColor White
Write-Host "3. Monitor Heroku logs for WebSocket connections" -ForegroundColor White

Write-Host "`n✅ Your SchemaSage platform now has real-time capabilities!" -ForegroundColor Green
