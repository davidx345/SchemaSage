# SchemaSage Microservices Control Script for Windows PowerShell

param(
    [Parameter(Mandatory=$true)]
    [ValidateSet("build", "start", "stop", "restart", "health", "logs", "status", "cleanup", "dev")]
    [string]$Command
)

# Colors for output
$ColorInfo = "Cyan"
$ColorSuccess = "Green"
$ColorWarning = "Yellow"
$ColorError = "Red"

function Write-Status {
    param([string]$Message)
    Write-Host "[INFO] $Message" -ForegroundColor $ColorInfo
}

function Write-Success {
    param([string]$Message)
    Write-Host "[SUCCESS] $Message" -ForegroundColor $ColorSuccess
}

function Write-Warning {
    param([string]$Message)
    Write-Host "[WARNING] $Message" -ForegroundColor $ColorWarning
}

function Write-Error {
    param([string]$Message)
    Write-Host "[ERROR] $Message" -ForegroundColor $ColorError
}

# Check if Docker is running
function Test-Docker {
    try {
        docker info 2>$null | Out-Null
        Write-Success "Docker is running"
        return $true
    }
    catch {
        Write-Error "Docker is not running. Please start Docker first."
        return $false
    }
}

# Build all services
function Build-Services {
    Write-Status "Building all microservices..."
    docker-compose build
    if ($LASTEXITCODE -eq 0) {
        Write-Success "All services built successfully"
    } else {
        Write-Error "Build failed"
        exit 1
    }
}

# Start all services
function Start-Services {
    Write-Status "Starting all microservices..."
    docker-compose up -d
    if ($LASTEXITCODE -eq 0) {
        Write-Success "All services started"
        
        # Wait for services to be ready
        Write-Status "Waiting for services to be ready..."
        Start-Sleep -Seconds 10
        
        # Check service health
        Test-Health
    } else {
        Write-Error "Failed to start services"
        exit 1
    }
}

# Stop all services
function Stop-Services {
    Write-Status "Stopping all microservices..."
    docker-compose down
    if ($LASTEXITCODE -eq 0) {
        Write-Success "All services stopped"
    } else {
        Write-Error "Failed to stop services"
    }
}

# Check health of all services
function Test-Health {
    Write-Status "Checking service health..."
    
    $services = @(
        @{Name="api-gateway"; Port=8000},
        @{Name="schema-detection"; Port=8001},
        @{Name="code-generation"; Port=8002},
        @{Name="ai-chat"; Port=8003},
        @{Name="project-management"; Port=8004}
    )
    
    foreach ($service in $services) {
        try {
            $response = Invoke-WebRequest -Uri "http://localhost:$($service.Port)/health" -Method Get -TimeoutSec 5 -UseBasicParsing
            if ($response.StatusCode -eq 200) {
                Write-Success "$($service.Name) is healthy"
            } else {
                Write-Error "$($service.Name) returned status $($response.StatusCode)"
            }
        }
        catch {
            Write-Error "$($service.Name) is not responding"
        }
    }
}

# Show logs for all services
function Show-Logs {
    Write-Status "Showing logs for all services..."
    docker-compose logs -f
}

# Show service status
function Show-Status {
    Write-Status "Service status:"
    docker-compose ps
}

# Clean up everything
function Cleanup {
    Write-Status "Cleaning up..."
    docker-compose down --volumes --remove-orphans
    docker system prune -f
    Write-Success "Cleanup completed"
}

# Development mode
function Start-DevMode {
    Write-Status "Starting development mode..."
    Write-Warning "Make sure you have your backend dependencies installed locally"
    
    # Start database first
    docker-compose up -d postgres
    
    Write-Status "You can now run individual services:"
    Write-Host "  Schema Detection: cd services/schema-detection && python main.py" -ForegroundColor White
    Write-Host "  Code Generation:  cd services/code-generation && python main.py" -ForegroundColor White
    Write-Host "  AI Chat:         cd services/ai-chat && python main.py" -ForegroundColor White
    Write-Host "  Project Mgmt:    cd services/project-management && python main.py" -ForegroundColor White
    Write-Host "  API Gateway:     cd services/api-gateway && python main.py" -ForegroundColor White
}

# Main execution
switch ($Command) {
    "build" {
        if (Test-Docker) {
            Build-Services
        }
    }
    "start" {
        if (Test-Docker) {
            Start-Services
        }
    }
    "stop" {
        Stop-Services
    }
    "restart" {
        if (Test-Docker) {
            Stop-Services
            Start-Services
        }
    }
    "health" {
        Test-Health
    }
    "logs" {
        Show-Logs
    }
    "status" {
        Show-Status
    }
    "cleanup" {
        Cleanup
    }
    "dev" {
        Start-DevMode
    }
}

Write-Host ""
Write-Host "SchemaSage Microservices Control Script" -ForegroundColor Magenta
Write-Host "Available commands: build, start, stop, restart, health, logs, status, cleanup, dev" -ForegroundColor Gray
