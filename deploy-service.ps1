# SchemaSage Service Deployment Script
param(
    [Parameter(Mandatory=$true)]
    [ValidateSet("api-gateway", "authentication", "code-generation", "schema-detection", "project-management", "ai-chat", "all")]
    [string]$Service,
    
    [string]$CommitMessage = "Update service configuration"
)

# Service to Heroku app mapping
$ServiceApps = @{
    "api-gateway" = "schemasage-api-gateway"
    "authentication" = "schemasage-auth"
    "code-generation" = "schemasage-code-generation"
    "schema-detection" = "schemasage-schema-detection"
    "project-management" = "schemasage-project-management"
    "ai-chat" = "schemasage-ai-chat"
}

function Deploy-Service {
    param($ServiceName)
    
    $AppName = $ServiceApps[$ServiceName]
    $ServicePath = "services/$ServiceName"
    
    Write-Host "🚀 Deploying $ServiceName to $AppName..." -ForegroundColor Green
    
    try {
        # Add remote if it doesn't exist
        $remoteExists = git remote | Select-String "heroku-$ServiceName"
        if (-not $remoteExists) {
            Write-Host "📡 Adding Heroku remote for $ServiceName..."
            heroku git:remote -a $AppName -r "heroku-$ServiceName"
        }
        
        # Deploy using subtree
        Write-Host "📦 Pushing $ServicePath to Heroku..."
        git subtree push --prefix=$ServicePath "heroku-$ServiceName" main
        
        # Wait a moment for deployment
        Start-Sleep -Seconds 3
        
        # Check deployment status
        Write-Host "🔍 Checking deployment status..."
        $appInfo = heroku ps --app $AppName --json | ConvertFrom-Json
        
        if ($appInfo.Count -gt 0 -and $appInfo[0].state -eq "up") {
            Write-Host "✅ $ServiceName deployed successfully!" -ForegroundColor Green
            
            # Show app URL
            $appUrl = heroku info --app $AppName | Select-String "Web URL" | ForEach-Object { $_.ToString().Split(":")[1].Trim() }
            Write-Host "🌐 Service URL: $appUrl" -ForegroundColor Blue
        } else {
            Write-Host "⚠️  Deployment completed but service may not be running" -ForegroundColor Yellow
        }
        
    } catch {
        Write-Host "❌ Failed to deploy $ServiceName`: $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
    
    return $true
}

# Main execution
Write-Host "🔄 SchemaSage Deployment Starting..." -ForegroundColor Cyan

# First, commit and push to GitHub
Write-Host "📝 Committing changes to GitHub..."
git add .
git commit -m $CommitMessage
git push origin main

if ($Service -eq "all") {
    # Deploy all services
    $services = @("api-gateway", "authentication", "code-generation", "schema-detection", "project-management", "ai-chat")
    $successCount = 0
    
    foreach ($svc in $services) {
        if (Deploy-Service $svc) {
            $successCount++
        }
        Write-Host ""
    }
    
    Write-Host "🎉 Deployment Summary: $successCount/$($services.Count) services deployed successfully" -ForegroundColor Green
} else {
    # Deploy single service
    Deploy-Service $Service
}

Write-Host "✨ Deployment process completed!" -ForegroundColor Cyan
