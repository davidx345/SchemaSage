# SchemaSage Heroku Environment Variables Setup Script
# Run this script to set all required environment variables for your microservices

Write-Host "🚀 Setting up SchemaSage Environment Variables..." -ForegroundColor Green
Write-Host ""

# IMPORTANT: Replace these placeholder values with your actual credentials
$JWT_SECRET_KEY = "your-super-secret-jwt-key-change-this-in-production"
$DATABASE_URL = "your-supabase-database-url-here"
$GEMINI_API_KEY = "your-gemini-api-key-here"
$OPENAI_API_KEY = "your-openai-api-key-here"
$AWS_ACCESS_KEY_ID = "your-aws-access-key-here"
$AWS_SECRET_ACCESS_KEY = "your-aws-secret-key-here"
$AWS_S3_BUCKET = "your-s3-bucket-name-here"
$FRONTEND_URL = "https://schemasage.vercel.app"

# Common environment variables
$CORS_ORIGINS = "$FRONTEND_URL,http://localhost:3000"
$AWS_REGION = "us-east-1"

Write-Host "📋 BEFORE RUNNING: Update the variables above with your actual values!" -ForegroundColor Yellow
Write-Host ""
Read-Host "Press Enter to continue after updating the variables..."

# Function to set environment variables for a Heroku app
function Set-HerokuEnvVars {
    param(
        [string]$AppName,
        [hashtable]$EnvVars
    )
    
    Write-Host "🔧 Setting environment variables for $AppName..." -ForegroundColor Cyan
    
    $configString = ""
    foreach ($key in $EnvVars.Keys) {
        $configString += "$key=`"$($EnvVars[$key])`" "
    }
    
    $command = "heroku config:set $configString --app $AppName"
    Write-Host "Running: $command"
    Invoke-Expression $command
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Successfully set environment variables for $AppName" -ForegroundColor Green
    } else {
        Write-Host "❌ Failed to set environment variables for $AppName" -ForegroundColor Red
    }
    Write-Host ""
}

# 1. API Gateway Service
Write-Host "1️⃣ API Gateway Service" -ForegroundColor Magenta
$apiGatewayVars = @{
    "JWT_SECRET_KEY" = $JWT_SECRET_KEY
    "CORS_ORIGINS" = $CORS_ORIGINS
    "AUTH_SERVICE_URL" = "https://schemasage-auth.herokuapp.com"
    "SCHEMA_SERVICE_URL" = "https://schemasage-schema-detection.herokuapp.com"
    "CODE_GEN_SERVICE_URL" = "https://schemasage-code-generation.herokuapp.com"
    "PROJECT_SERVICE_URL" = "https://schemasage-project-management.herokuapp.com"
    "AI_CHAT_SERVICE_URL" = "https://schemasage-ai-chat.herokuapp.com"
}
Set-HerokuEnvVars -AppName "schemasage-api-gateway" -EnvVars $apiGatewayVars

# 2. Authentication Service
Write-Host "2️⃣ Authentication Service" -ForegroundColor Magenta
$authVars = @{
    "DATABASE_URL" = $DATABASE_URL
    "JWT_SECRET_KEY" = $JWT_SECRET_KEY
    "JWT_ALGORITHM" = "HS256"
    "JWT_EXPIRATION_HOURS" = "24"
    "CORS_ORIGINS" = $CORS_ORIGINS
}
Set-HerokuEnvVars -AppName "schemasage-auth" -EnvVars $authVars

# 3. Schema Detection Service
Write-Host "3️⃣ Schema Detection Service" -ForegroundColor Magenta
$schemaVars = @{
    "JWT_SECRET_KEY" = $JWT_SECRET_KEY
    "CORS_ORIGINS" = $CORS_ORIGINS
    "GEMINI_API_KEY" = $GEMINI_API_KEY
    "OPENAI_API_KEY" = $OPENAI_API_KEY
    "MAX_FILE_SIZE" = "10485760"
    "MAX_SAMPLE_ROWS" = "10000"
    "PROCESSING_TIMEOUT" = "30"
    "LOG_LEVEL" = "INFO"
}
Set-HerokuEnvVars -AppName "schemasage-schema-detection" -EnvVars $schemaVars

# 4. AI Chat Service
Write-Host "4️⃣ AI Chat Service" -ForegroundColor Magenta
$aiChatVars = @{
    "JWT_SECRET_KEY" = $JWT_SECRET_KEY
    "CORS_ORIGINS" = $CORS_ORIGINS
    "GEMINI_API_KEY" = $GEMINI_API_KEY
    "OPENAI_API_KEY" = $OPENAI_API_KEY
    "LOG_LEVEL" = "INFO"
}
Set-HerokuEnvVars -AppName "schemasage-ai-chat" -EnvVars $aiChatVars

# 5. Code Generation Service
Write-Host "5️⃣ Code Generation Service" -ForegroundColor Magenta
$codeGenVars = @{
    "JWT_SECRET_KEY" = $JWT_SECRET_KEY
    "CORS_ORIGINS" = $CORS_ORIGINS
    "OPENAI_API_KEY" = $OPENAI_API_KEY
    "LOG_LEVEL" = "INFO"
}
Set-HerokuEnvVars -AppName "schemasage-code-generation" -EnvVars $codeGenVars

# 6. Project Management Service
Write-Host "6️⃣ Project Management Service" -ForegroundColor Magenta
$projectVars = @{
    "JWT_SECRET_KEY" = $JWT_SECRET_KEY
    "CORS_ORIGINS" = $CORS_ORIGINS
    "DATABASE_URL" = $DATABASE_URL
    "AWS_ACCESS_KEY_ID" = $AWS_ACCESS_KEY_ID
    "AWS_SECRET_ACCESS_KEY" = $AWS_SECRET_ACCESS_KEY
    "AWS_REGION" = $AWS_REGION
    "S3_BUCKET_NAME" = $AWS_S3_BUCKET
    "MAX_FILE_SIZE" = "10485760"
    "ALLOWED_EXTENSIONS" = "csv,json,sql,xlsx"
    "LOG_LEVEL" = "INFO"
}
Set-HerokuEnvVars -AppName "schemasage-project-management" -EnvVars $projectVars

Write-Host ""
Write-Host "🎉 Environment variables setup complete!" -ForegroundColor Green
Write-Host ""
Write-Host "📝 Next steps:" -ForegroundColor Yellow
Write-Host "   1. Verify all your actual credentials are correct"
Write-Host "   2. Check each Heroku app logs: heroku logs --tail --app [app-name]"
Write-Host "   3. Test your endpoints to ensure services are working"
Write-Host "   4. Deploy your frontend to Vercel if not already done"
Write-Host ""
Write-Host "🔍 To verify environment variables were set:"
Write-Host "   heroku config --app schemasage-auth"
Write-Host "   heroku config --app schemasage-schema-detection"
Write-Host "   (repeat for other services)"
Write-Host ""

# Optional: Check if Heroku CLI is installed
if (!(Get-Command "heroku" -ErrorAction SilentlyContinue)) {
    Write-Host "⚠️  WARNING: Heroku CLI not found!" -ForegroundColor Red
    Write-Host "   Please install it from: https://devcenter.heroku.com/articles/heroku-cli"
    Write-Host "   Then run: heroku login"
}

Write-Host "Script completed! 🚀" -ForegroundColor Green
