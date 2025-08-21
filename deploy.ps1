# SchemaSage Deployment Commands
# Usage: .\deploy.ps1 <command>
# Commands: auth, gateway, codegen, schema, projects, chat, all

param([string]$Command = "help")

function Show-Help {
    Write-Host @"
🚀 SchemaSage Deployment Tool
    
Usage: .\deploy.ps1 <command>

Commands:
  auth      - Deploy Authentication Service
  gateway   - Deploy API Gateway  
  codegen   - Deploy Code Generation Service
  schema    - Deploy Schema Detection Service
  projects  - Deploy Project Management Service
  chat      - Deploy AI Chat Service
  all       - Deploy All Services
  help      - Show this help

Examples:
  .\deploy.ps1 auth
  .\deploy.ps1 all
"@ -ForegroundColor Cyan
}

function Deploy-ToHeroku {
    param($ServiceName, $AppName, $Path)
    
    Write-Host "🚀 Deploying $ServiceName..." -ForegroundColor Green
    
    # Commit and push to GitHub
    git add .
    git commit -m "Deploy $ServiceName"
    git push origin main
    
    # Set Heroku remote
    heroku git:remote -a $AppName 2>$null
    
    # Deploy using subtree
    git subtree push --prefix=$Path heroku main
    
    Write-Host "✅ $ServiceName deployed to $AppName" -ForegroundColor Green
}

switch ($Command.ToLower()) {
    "auth" { 
        Deploy-ToHeroku "Authentication Service" "schemasage-auth" "services/authentication"
    }
    "gateway" { 
        Deploy-ToHeroku "API Gateway" "schemasage-api-gateway" "services/api-gateway"
    }
    "codegen" { 
        Deploy-ToHeroku "Code Generation Service" "schemasage-code-generation" "services/code-generation"
    }
    "schema" { 
        Deploy-ToHeroku "Schema Detection Service" "schemasage-schema-detection" "services/schema-detection"
    }
    "projects" { 
        Deploy-ToHeroku "Project Management Service" "schemasage-project-management" "services/project-management"
    }
    "chat" { 
        Deploy-ToHeroku "AI Chat Service" "schemasage-ai-chat" "services/ai-chat"
    }
    "all" {
        Write-Host "🚀 Deploying ALL services..." -ForegroundColor Cyan
        
        # Commit once
        git add .
        git commit -m "Deploy all services"
        git push origin main
        
        $services = @(
            @("Authentication", "schemasage-auth", "services/authentication"),
            @("API Gateway", "schemasage-api-gateway", "services/api-gateway"),
            @("Code Generation", "schemasage-code-generation", "services/code-generation"),
            @("Schema Detection", "schemasage-schema-detection", "services/schema-detection"),
            @("Project Management", "schemasage-project-management", "services/project-management"),
            @("AI Chat", "schemasage-ai-chat", "services/ai-chat")
        )
        
        foreach ($service in $services) {
            Write-Host "📦 Deploying $($service[0])..." -ForegroundColor Yellow
            heroku git:remote -a $service[1] 2>$null
            git subtree push --prefix=$service[2] heroku main
            Write-Host "✅ $($service[0]) deployed!" -ForegroundColor Green
        }
        
        Write-Host "🎉 All services deployed!" -ForegroundColor Cyan
    }
    default { 
        Show-Help 
    }
}
