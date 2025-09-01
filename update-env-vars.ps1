# Update Environment Variables for WebSocket Integration

Write-Host "🔧 Updating all services with WebSocket Real-time integration..." -ForegroundColor Green

$websocketServiceUrl = "https://schemasage-websocket-realtime.herokuapp.com"
$frontendUrl = "https://schemasage.vercel.app"

# Update Schema Detection Service
Write-Host "📊 Updating Schema Detection Service..." -ForegroundColor Yellow
heroku config:set WEBSOCKET_SERVICE_URL="$websocketServiceUrl" --app schemasage-schema-detection

# Update Code Generation Service  
Write-Host "⚙️ Updating Code Generation Service..." -ForegroundColor Yellow
heroku config:set WEBSOCKET_SERVICE_URL="$websocketServiceUrl" --app schemasage-code-generation

# Update Project Management Service
Write-Host "📋 Updating Project Management Service..." -ForegroundColor Yellow
heroku config:set WEBSOCKET_SERVICE_URL="$websocketServiceUrl" --app schemasage-project-management

# Update Authentication Service
Write-Host "🔐 Updating Authentication Service..." -ForegroundColor Yellow
heroku config:set WEBSOCKET_SERVICE_URL="$websocketServiceUrl" --app schemasage-auth
heroku config:set FRONTEND_URL="$frontendUrl" --app schemasage-auth

# Update API Gateway
Write-Host "🌐 Updating API Gateway..." -ForegroundColor Yellow
heroku config:set WEBSOCKET_REALTIME_SERVICE_URL="$websocketServiceUrl" --app schemasage-api-gateway-2da67d920b07

# Update WebSocket Service CORS settings
Write-Host "🔗 Updating WebSocket Service CORS settings..." -ForegroundColor Yellow
heroku config:set CORS_ORIGINS="https://schemasage.vercel.app,http://localhost:3000" --app schemasage-websocket-realtime

Write-Host "✅ All services updated with WebSocket integration!" -ForegroundColor Green
Write-Host "🔄 Services will use the WebSocket service at: $websocketServiceUrl" -ForegroundColor Cyan

# Display next steps
Write-Host "`n📋 Next Steps:" -ForegroundColor Blue
Write-Host "1. Redeploy updated services to pick up new environment variables" -ForegroundColor White
Write-Host "2. Test real-time functionality from your frontend" -ForegroundColor White
Write-Host "3. Monitor WebSocket connections in Heroku logs" -ForegroundColor White

Write-Host "`n🚀 WebSocket integration setup completed!" -ForegroundColor Green
