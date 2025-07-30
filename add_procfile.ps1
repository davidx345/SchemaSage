# PowerShell Script to Add Procfile, requirements.txt, and .python-version to Services

Write-Host "Processing services..." -ForegroundColor Green

# Define the services directory
$servicesDir = "c:\Users\USER\Documents\projects\SchemaSage\services"

# List of services
$services = @("ai-chat", "api-gateway", "authentication", "code-generation", "project-management", "schema-detection")

# Loop through each service
foreach ($service in $services) {
    $servicePath = Join-Path $servicesDir $service
    $procfilePath = Join-Path $servicePath "Procfile"
    $requirementsPath = Join-Path $servicePath "requirements.txt"
    $pythonVersionPath = Join-Path $servicePath ".python-version"

    # Check if Procfile exists
    if (Test-Path $procfilePath) {
        Write-Host "Procfile already exists for $service" -ForegroundColor Yellow
    } else {
        Write-Host "Creating Procfile for $service..." -ForegroundColor Cyan
        Set-Content -Path $procfilePath -Value "web: python main.py"
        Write-Host "Procfile created for $service" -ForegroundColor Green
    }

    # Check if requirements.txt exists
    if (Test-Path $requirementsPath) {
        Write-Host "requirements.txt already exists for $service" -ForegroundColor Yellow
    } else {
        Write-Host "Creating requirements.txt for $service..." -ForegroundColor Cyan
        Set-Content -Path $requirementsPath -Value "fastapi==0.104.1`nuvicorn[standard]==0.24.0`npydantic==2.5.0`ngoogle-generativeai==0.3.2`npython-dotenv==1.0.0`naiohttp==3.9.1"
        Write-Host "requirements.txt created for $service" -ForegroundColor Green
    }

    # Check if .python-version exists
    if (Test-Path $pythonVersionPath) {
        Write-Host ".python-version already exists for $service" -ForegroundColor Yellow
    } else {
        Write-Host "Creating .python-version for $service..." -ForegroundColor Cyan
        Set-Content -Path $pythonVersionPath -Value "3.11"
        Write-Host ".python-version created for $service" -ForegroundColor Green
    }

    # Set the buildpack for the Heroku app
    Write-Host "Setting buildpack for $service..." -ForegroundColor Cyan
    heroku buildpacks:set heroku/python --app schemasage-$service

    # Commit and push changes to Heroku
    Write-Host "Committing and pushing changes for $service to Heroku..." -ForegroundColor Cyan
    Set-Location $servicePath
    git add Procfile requirements.txt .python-version
    git commit -m "Add Procfile, requirements.txt, and .python-version for $service"

    # Ensure the correct branch is pushed
    Write-Host "Pushing to Heroku main branch for $service..." -ForegroundColor Cyan
    heroku git:remote -a schemasage-$service
    git push heroku HEAD:main
    Set-Location "..\.."
}

Write-Host "✅ All services processed and pushed to Heroku!" -ForegroundColor Green
