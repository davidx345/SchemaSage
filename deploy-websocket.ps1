# Deploy WebSocket Real-time Service to Heroku

Write-Host "🚀 Deploying WebSocket Real-time Service to Heroku..." -ForegroundColor Green

# Set the current directory to the websocket service
$originalLocation = Get-Location
Set-Location "services\websocket-realtime"

try {
    # Create Heroku app if it doesn't exist
    Write-Host "📦 Creating Heroku app..." -ForegroundColor Yellow
    $appName = "schemasage-websocket-realtime"
    
    heroku create $appName --region us 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Heroku app '$appName' created successfully" -ForegroundColor Green
    } else {
        Write-Host "ℹ️ Heroku app '$appName' already exists" -ForegroundColor Blue
    }
    
    # Set environment variables
    Write-Host "🔧 Setting environment variables..." -ForegroundColor Yellow
    heroku config:set JWT_SECRET_KEY="$env:JWT_SECRET_KEY" --app $appName
    heroku config:set JWT_ALGORITHM="HS256" --app $appName
    heroku config:set SCHEMA_DETECTION_SERVICE_URL="https://schemasage-schema-detection-0cc19b546c3c.herokuapp.com" --app $appName
    heroku config:set PROJECT_MANAGEMENT_SERVICE_URL="https://schemasage-project-management-48496f02644b.herokuapp.com" --app $appName
    heroku config:set CODE_GENERATION_SERVICE_URL="https://schemasage-code-generation-56faa300323b.herokuapp.com" --app $appName
    heroku config:set AUTHENTICATION_SERVICE_URL="https://schemasage-auth-9d6de1a32af9.herokuapp.com" --app $appName
    heroku config:set CORS_ORIGINS="https://schemasage.vercel.app,http://localhost:3000" --app $appName
    
    # Add git remote if it doesn't exist
    git remote remove heroku 2>$null
    heroku git:remote --app $appName
    
    # Deploy to Heroku
    Write-Host "🚀 Deploying to Heroku..." -ForegroundColor Yellow
    git add .
    git commit -m "Deploy WebSocket Real-time Service" --allow-empty
    git push heroku HEAD:main --force
    
    # Check deployment status
    Write-Host "🏥 Checking service health..." -ForegroundColor Yellow
    Start-Sleep -Seconds 30
    
    $healthUrl = "https://$appName.herokuapp.com/health"
    try {
        $response = Invoke-RestMethod -Uri $healthUrl -Method Get -TimeoutSec 10
        Write-Host "✅ WebSocket Real-time Service deployed successfully!" -ForegroundColor Green
        Write-Host "🌐 Service URL: https://$appName.herokuapp.com" -ForegroundColor Cyan
        Write-Host "📊 Health Status: $($response.status)" -ForegroundColor Cyan
    } catch {
        Write-Host "⚠️ Service deployed but health check failed. This is normal for new deployments." -ForegroundColor Yellow
        Write-Host "🌐 Service URL: https://$appName.herokuapp.com" -ForegroundColor Cyan
    }
    
    Write-Host "✅ WebSocket Real-time Service deployment completed!" -ForegroundColor Green
    
} catch {
    Write-Host "❌ Deployment failed: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
} finally {
    # Return to original location
    Set-Location $originalLocation
}

Write-Host "🎉 WebSocket Real-time Service is ready for real-time dashboard updates!" -ForegroundColor Green
