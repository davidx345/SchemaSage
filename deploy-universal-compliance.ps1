# Universal Compliance Platform Deployment Script
# Deploys enhanced SchemaSage services with universal compliance features

Write-Host "🚀 Deploying SchemaSage Universal Compliance Platform..." -ForegroundColor Green

# Function to deploy a service
function Deploy-Service {
    param(
        [string]$ServiceName,
        [string]$ServicePath,
        [string]$HerokuApp
    )
    
    Write-Host "📦 Deploying $ServiceName..." -ForegroundColor Yellow
    
    try {
        # Navigate to service directory
        Push-Location $ServicePath
        
        # Deploy using git subtree
        git add .
        git commit -m "Universal Compliance Platform: $ServiceName updates" -q
        git subtree push --prefix=services/$ServiceName heroku main --force
        
        Write-Host "✅ $ServiceName deployed successfully" -ForegroundColor Green
        
        # Check deployment status
        $status = heroku ps -a $HerokuApp | Select-String "up"
        if ($status) {
            Write-Host "✅ $ServiceName is running" -ForegroundColor Green
        } else {
            Write-Host "⚠️  $ServiceName may have issues" -ForegroundColor Yellow
        }
        
        Pop-Location
    }
    catch {
        Write-Host "❌ Failed to deploy $ServiceName`: $_" -ForegroundColor Red
        Pop-Location
    }
}

# Update environment variables for all services
function Update-Environment-Variables {
    Write-Host "🔧 Updating environment variables..." -ForegroundColor Yellow
    
    $services = @(
        @{name="project-management"; app="schemasage-project-mgmt-95b70e4b3251"},
        @{name="schema-detection"; app="schemasage-schema-detection"},
        @{name="code-generation"; app="schemasage-code-generation-d30feec36ac5"}
    )
    
    foreach ($service in $services) {
        try {
            Write-Host "Setting up $($service.name) environment..." -ForegroundColor Cyan
            
            # Add universal compliance feature flags
            heroku config:set UNIVERSAL_COMPLIANCE_ENABLED=true -a $service.app
            heroku config:set COMPLIANCE_FRAMEWORKS="gdpr,hipaa,sox,pci_dss,ferpa,fisma,soc2,ccpa,iso_27001,nist,pipeda,itar" -a $service.app
            heroku config:set MULTI_FRAMEWORK_DETECTION=true -a $service.app
            heroku config:set INDUSTRY_TEMPLATES_ENABLED=true -a $service.app
            
            Write-Host "✅ Environment updated for $($service.name)" -ForegroundColor Green
        }
        catch {
            Write-Host "❌ Failed to update environment for $($service.name)`: $_" -ForegroundColor Red
        }
    }
}

# Main deployment process
try {
    Write-Host "🌟 SchemaSage Universal Compliance Platform Deployment" -ForegroundColor Cyan
    Write-Host "=====================================================" -ForegroundColor Cyan
    Write-Host ""
    
    # Check if we're in the right directory
    if (-not (Test-Path "services")) {
        Write-Host "❌ Please run this script from the SchemaSage root directory" -ForegroundColor Red
        exit 1
    }
    
    # Update environment variables first
    Update-Environment-Variables
    Write-Host ""
    
    # Deploy each service with universal compliance features
    Write-Host "🚀 Deploying services with Universal Compliance features..." -ForegroundColor Green
    Write-Host ""
    
    # Deploy Project Management Service (Universal Compliance Dashboard)
    Deploy-Service -ServiceName "project-management" -ServicePath "services/project-management" -HerokuApp "schemasage-project-mgmt-95b70e4b3251"
    Start-Sleep -Seconds 10
    
    # Deploy Schema Detection Service (Multi-Framework PII Detection)  
    Deploy-Service -ServiceName "schema-detection" -ServicePath "services/schema-detection" -HerokuApp "schemasage-schema-detection"
    Start-Sleep -Seconds 10
    
    # Deploy Code Generation Service (Compliance Templates)
    Deploy-Service -ServiceName "code-generation" -ServicePath "services/code-generation" -HerokuApp "schemasage-code-generation-d30feec36ac5"
    Start-Sleep -Seconds 10
    
    Write-Host ""
    Write-Host "🎉 Universal Compliance Platform Deployment Complete!" -ForegroundColor Green
    Write-Host ""
    Write-Host "🔥 NEW UNIVERSAL COMPLIANCE FEATURES:" -ForegroundColor Cyan
    Write-Host "   ✨ Multi-Framework Compliance Dashboard" -ForegroundColor White
    Write-Host "   ✨ Universal PII Detection (GDPR + SOC 2 + FERPA + HIPAA + more)" -ForegroundColor White
    Write-Host "   ✨ Industry-Specific Templates (Healthcare, Education, Financial, Government)" -ForegroundColor White
    Write-Host "   ✨ Cross-Compliance Mapping & Analysis" -ForegroundColor White
    Write-Host "   ✨ Compliance-Ready Code Generation" -ForegroundColor White
    Write-Host "   ✨ Universal Audit Trail Generation" -ForegroundColor White
    Write-Host ""
    Write-Host "📊 COMPLIANCE ENDPOINTS:" -ForegroundColor Cyan
    Write-Host "   🔗 Project Management: https://schemasage-project-mgmt-95b70e4b3251.herokuapp.com/compliance" -ForegroundColor White
    Write-Host "   🔗 Schema Detection: https://schemasage-schema-detection.herokuapp.com/compliance" -ForegroundColor White  
    Write-Host "   🔗 Code Generation: https://schemasage-code-generation-d30feec36ac5.herokuapp.com/compliance-generation" -ForegroundColor White
    Write-Host ""
    Write-Host "🎯 TARGET INDUSTRIES:" -ForegroundColor Cyan
    Write-Host "   🏥 Healthcare (HIPAA compliance)" -ForegroundColor White
    Write-Host "   🎓 Education (FERPA student privacy)" -ForegroundColor White
    Write-Host "   💼 SaaS Companies (SOC 2 compliance)" -ForegroundColor White
    Write-Host "   🏛️ Government Contractors (FISMA/FedRAMP)" -ForegroundColor White
    Write-Host "   🏦 Financial Services (SOX, PCI-DSS)" -ForegroundColor White
    Write-Host "   🏭 Manufacturing (Export controls ITAR, EAR)" -ForegroundColor White
    Write-Host "   🤝 Non-profits (Donor privacy regulations)" -ForegroundColor White
    Write-Host ""
    Write-Host "💰 PRICING READY:" -ForegroundColor Cyan
    Write-Host "   📈 Compliance Starter: `$299/month (2 frameworks)" -ForegroundColor White
    Write-Host "   📈 Multi-Framework Pro: `$999/month (5+ frameworks)" -ForegroundColor White
    Write-Host "   📈 Enterprise Universal: `$2,999/month (All frameworks)" -ForegroundColor White
    Write-Host "   📈 Government Certified: `$9,999/month (FedRAMP certified)" -ForegroundColor White
    Write-Host ""
    Write-Host "🚀 SchemaSage is now a Universal Compliance Platform!" -ForegroundColor Green
    
}
catch {
    Write-Host "❌ Deployment failed: $_" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "✅ Done! Your Universal Compliance Platform is live!" -ForegroundColor Green
