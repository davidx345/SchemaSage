# Quick deployment script for individual services
param(
    [Parameter(Mandatory=$true)]
    [string]$Service,
    [string]$Message = "Quick update"
)

$apps = @{
    "gateway" = @{app="schemasage-api-gateway"; path="services/api-gateway"}
    "auth" = @{app="schemasage-auth"; path="services/authentication"}
    "codegen" = @{app="schemasage-code-generation"; path="services/code-generation"}
    "schema" = @{app="schemasage-schema-detection"; path="services/schema-detection"}
    "projects" = @{app="schemasage-project-management"; path="services/project-management"}
    "chat" = @{app="schemasage-ai-chat"; path="services/ai-chat"}
}

if ($apps.ContainsKey($Service)) {
    $config = $apps[$Service]
    
    Write-Host "🚀 Deploying $Service..." -ForegroundColor Green
    
    # Commit and push to GitHub
    git add .
    git commit -m $Message
    git push origin main
    
    # Add heroku remote if needed
    heroku git:remote -a $config.app -r "heroku-$Service" 2>$null
    
    # Deploy
    git subtree push --prefix=$($config.path) "heroku-$Service" main
    
    Write-Host "✅ $Service deployed!" -ForegroundColor Green
} else {
    Write-Host "❌ Unknown service. Use: gateway, auth, codegen, schema, projects, chat" -ForegroundColor Red
}
