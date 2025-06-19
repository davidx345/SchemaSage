#!/bin/bash

# SchemaSage Microservices Control Script

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Docker is running
check_docker() {
    if ! docker info > /dev/null 2>&1; then
        print_error "Docker is not running. Please start Docker first."
        exit 1
    fi
    print_success "Docker is running"
}

# Build all services
build_services() {
    print_status "Building all microservices..."
    docker-compose build
    print_success "All services built successfully"
}

# Start all services
start_services() {
    print_status "Starting all microservices..."
    docker-compose up -d
    print_success "All services started"
    
    # Wait for services to be ready
    print_status "Waiting for services to be ready..."
    sleep 10
    
    # Check service health
    check_health
}

# Stop all services
stop_services() {
    print_status "Stopping all microservices..."
    docker-compose down
    print_success "All services stopped"
}

# Check health of all services
check_health() {
    print_status "Checking service health..."
    
    services=(
        "api-gateway:8000"
        "schema-detection:8001"
        "code-generation:8002"
        "ai-chat:8003"
        "project-management:8004"
    )
    
    for service in "${services[@]}"; do
        name="${service%:*}"
        port="${service#*:}"
        
        if curl -f -s "http://localhost:${port}/health" > /dev/null; then
            print_success "${name} is healthy"
        else
            print_error "${name} is not responding"
        fi
    done
}

# Show logs for all services
show_logs() {
    print_status "Showing logs for all services..."
    docker-compose logs -f
}

# Show service status
show_status() {
    print_status "Service status:"
    docker-compose ps
}

# Clean up everything
cleanup() {
    print_status "Cleaning up..."
    docker-compose down --volumes --remove-orphans
    docker system prune -f
    print_success "Cleanup completed"
}

# Development mode - start services individually
dev_mode() {
    print_status "Starting development mode..."
    print_warning "Make sure you have your backend dependencies installed locally"
    
    # Start database first
    docker-compose up -d postgres
    
    print_status "You can now run individual services:"
    echo "  Schema Detection: cd services/schema-detection && python main.py"
    echo "  Code Generation:  cd services/code-generation && python main.py"
    echo "  AI Chat:         cd services/ai-chat && python main.py"
    echo "  Project Mgmt:    cd services/project-management && python main.py"
    echo "  API Gateway:     cd services/api-gateway && python main.py"
}

# Main menu
case "$1" in
    "build")
        check_docker
        build_services
        ;;
    "start")
        check_docker
        start_services
        ;;
    "stop")
        stop_services
        ;;
    "restart")
        check_docker
        stop_services
        start_services
        ;;
    "health")
        check_health
        ;;
    "logs")
        show_logs
        ;;
    "status")
        show_status
        ;;
    "cleanup")
        cleanup
        ;;
    "dev")
        dev_mode
        ;;
    *)
        echo "SchemaSage Microservices Control Script"
        echo ""
        echo "Usage: $0 {build|start|stop|restart|health|logs|status|cleanup|dev}"
        echo ""
        echo "Commands:"
        echo "  build    - Build all Docker images"
        echo "  start    - Start all services"
        echo "  stop     - Stop all services"
        echo "  restart  - Restart all services"
        echo "  health   - Check health of all services"
        echo "  logs     - Show logs for all services"
        echo "  status   - Show service status"
        echo "  cleanup  - Clean up all containers and volumes"
        echo "  dev      - Start development mode (database only)"
        echo ""
        echo "Examples:"
        echo "  $0 build && $0 start    # Build and start all services"
        echo "  $0 health               # Check if services are running"
        echo "  $0 logs                 # View real-time logs"
        exit 1
        ;;
esac
