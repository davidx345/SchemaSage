# Simple SchemaSage Deployment Script
param([string]$Service = "help")

function Deploy-Service {
    param($Name, $App, $Path)
    
    Write-Host "Deploying $Name..." -ForegroundColor Green
    
    # Commit and push to GitHub
    git add .
    git commit -m "Deploy $Name"
    git push origin main
    
    # Set Heroku remote and deploy
    heroku git:remote -a $App 2>$null
    git subtree push --prefix=$Path heroku main
    
    Write-Host "$Name deployed successfully!" -ForegroundColor Green
}

switch ($Service.ToLower()) {
    "auth" { 
        Deploy-Service "Authentication Service" "schemasage-auth" "services/authentication"
    }
    "gateway" { 
        Deploy-Service "API Gateway" "schemasage-api-gateway" "services/api-gateway"
    }
    "codegen" { 
        Deploy-Service "Code Generation" "schemasage-code-generation" "services/code-generation"
    }
    "schema" { 
        Deploy-Service "Schema Detection" "schemasage-schema-detection" "services/schema-detection"
    }
    "projects" { 
        Deploy-Service "Project Management" "schemasage-project-management" "services/project-management"
    }
    "chat" { 
        Deploy-Service "AI Chat" "schemasage-ai-chat" "services/ai-chat"
    }
    default { 
        Write-Host "Usage: .\simple-deploy.ps1 [auth|gateway|codegen|schema|projects|chat]" -ForegroundColor Yellow
        Write-Host "Example: .\simple-deploy.ps1 auth" -ForegroundColor Cyan
    }
}
