# Build and Push Docker Images to Docker Hub for Raspberry Pi
# This script builds ARM64 images and pushes them to Docker Hub

Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "Docker Hub Build & Push Script" -ForegroundColor Cyan
Write-Host "Raspberry Pi ARM64 Images" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""

# Check if Docker is running
try {
    docker info | Out-Null
    Write-Host "✓ Docker is running" -ForegroundColor Green
} catch {
    Write-Host "❌ Error: Docker is not running!" -ForegroundColor Red
    Write-Host "Please start Docker Desktop and try again." -ForegroundColor Yellow
    exit 1
}

Write-Host ""

# Get Docker Hub username
Write-Host "Docker Hub Configuration" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan
$dockerUsername = Read-Host "Enter your Docker Hub username"

if ([string]::IsNullOrWhiteSpace($dockerUsername)) {
    Write-Host "❌ Docker Hub username is required!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Don't have a Docker Hub account?" -ForegroundColor Yellow
    Write-Host "1. Go to https://hub.docker.com/" -ForegroundColor White
    Write-Host "2. Sign up for free" -ForegroundColor White
    Write-Host "3. Run this script again" -ForegroundColor White
    exit 1
}

Write-Host ""
Write-Host "Docker Hub username: $dockerUsername" -ForegroundColor Green
Write-Host ""

# Login to Docker Hub
Write-Host "Logging in to Docker Hub..." -ForegroundColor Cyan
docker login

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Docker Hub login failed!" -ForegroundColor Red
    exit 1
}

Write-Host "✓ Logged in successfully" -ForegroundColor Green
Write-Host ""

# Check if buildx is available
Write-Host "Checking Docker Buildx..." -ForegroundColor Cyan
try {
    docker buildx version | Out-Null
    Write-Host "✓ Docker Buildx is available" -ForegroundColor Green
} catch {
    Write-Host "❌ Error: Docker Buildx is not available!" -ForegroundColor Red
    Write-Host "Please update Docker Desktop to the latest version." -ForegroundColor Yellow
    exit 1
}

Write-Host ""

# Select build mode
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "Select Build Mode:" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "1) Both containers (Recommended)" -ForegroundColor White
Write-Host "   - Main App (Streamlit + ML)" -ForegroundColor Gray
Write-Host "   - SQL Agent Service (FastAPI)" -ForegroundColor Gray
Write-Host ""
Write-Host "2) Main App only" -ForegroundColor White
Write-Host ""
Write-Host "3) SQL Agent only" -ForegroundColor White
Write-Host ""

$buildMode = Read-Host "Enter choice (1, 2, or 3) [default: 1]"
if ([string]::IsNullOrWhiteSpace($buildMode)) {
    $buildMode = "1"
}

# Select main app variant
$mainAppVariant = "minimal"
if ($buildMode -eq "1" -or $buildMode -eq "2") {
    Write-Host ""
    Write-Host "=========================================" -ForegroundColor Cyan
    Write-Host "Select Main App Variant:" -ForegroundColor Cyan
    Write-Host "=========================================" -ForegroundColor Cyan
    Write-Host "1) Minimal (Recommended for Raspberry Pi)" -ForegroundColor White
    Write-Host "   - Size: ~2.5GB" -ForegroundColor Gray
    Write-Host ""
    Write-Host "2) Full" -ForegroundColor White
    Write-Host "   - Size: ~3.5GB" -ForegroundColor Gray
    Write-Host ""
    
    $variantChoice = Read-Host "Enter choice (1 or 2) [default: 1]"
    if ($variantChoice -eq "2") {
        $mainAppVariant = "full"
        $dockerfile = "Dockerfile"
        Write-Host "✓ Selected: Full variant" -ForegroundColor Green
    } else {
        $mainAppVariant = "minimal"
        $dockerfile = "Dockerfile.minimal"
        Write-Host "✓ Selected: Minimal variant" -ForegroundColor Green
    }
}

Write-Host ""

# Create or use existing buildx builder
Write-Host "Setting up Docker Buildx builder..." -ForegroundColor Cyan
$builderName = "plankton-multiplatform"

# Check if builder exists
$existingBuilder = docker buildx ls | Select-String $builderName
if ($existingBuilder) {
    Write-Host "✓ Using existing builder: $builderName" -ForegroundColor Green
} else {
    Write-Host "Creating new builder: $builderName" -ForegroundColor Yellow
    docker buildx create --name $builderName --use --platform linux/arm64,linux/amd64
    Write-Host "✓ Builder created" -ForegroundColor Green
}

# Use the builder
docker buildx use $builderName
Write-Host ""

# Build and push images
$buildSuccess = $true

# Build Main App
if ($buildMode -eq "1" -or $buildMode -eq "2") {
    Write-Host "=========================================" -ForegroundColor Cyan
    Write-Host "Building & Pushing Main App" -ForegroundColor Cyan
    Write-Host "=========================================" -ForegroundColor Cyan
    Write-Host "Dockerfile: $dockerfile" -ForegroundColor White
    Write-Host "Target Platform: linux/arm64" -ForegroundColor White
    Write-Host "Docker Hub: $dockerUsername/plankton-app:$mainAppVariant-arm64" -ForegroundColor White
    Write-Host ""
    Write-Host "This may take 20-40 minutes..." -ForegroundColor Yellow
    Write-Host ""
    
    try {
        docker buildx build `
            --platform linux/arm64 `
            -f $dockerfile `
            -t "${dockerUsername}/plankton-app:$mainAppVariant-arm64" `
            -t "${dockerUsername}/plankton-app:latest" `
            --push `
            .
        
        if ($LASTEXITCODE -ne 0) {
            $buildSuccess = $false
            Write-Host "❌ Main App build/push failed!" -ForegroundColor Red
        } else {
            Write-Host "✓ Main App built and pushed successfully!" -ForegroundColor Green
        }
    } catch {
        $buildSuccess = $false
        Write-Host "❌ Main App build/push failed!" -ForegroundColor Red
    }
    Write-Host ""
}

# Build SQL Agent
if ($buildMode -eq "1" -or $buildMode -eq "3") {
    Write-Host "=========================================" -ForegroundColor Cyan
    Write-Host "Building & Pushing SQL Agent" -ForegroundColor Cyan
    Write-Host "=========================================" -ForegroundColor Cyan
    Write-Host "Dockerfile: services/sql-agent/Dockerfile" -ForegroundColor White
    Write-Host "Target Platform: linux/arm64" -ForegroundColor White
    Write-Host "Docker Hub: $dockerUsername/plankton-sql-agent:arm64" -ForegroundColor White
    Write-Host ""
    Write-Host "This may take 10-15 minutes..." -ForegroundColor Yellow
    Write-Host ""
    
    try {
        docker buildx build `
            --platform linux/arm64 `
            -f services/sql-agent/Dockerfile `
            -t "${dockerUsername}/plankton-sql-agent:arm64" `
            -t "${dockerUsername}/plankton-sql-agent:latest" `
            --push `
            services/sql-agent
        
        if ($LASTEXITCODE -ne 0) {
            $buildSuccess = $false
            Write-Host "❌ SQL Agent build/push failed!" -ForegroundColor Red
        } else {
            Write-Host "✓ SQL Agent built and pushed successfully!" -ForegroundColor Green
        }
    } catch {
        $buildSuccess = $false
        Write-Host "❌ SQL Agent build/push failed!" -ForegroundColor Red
    }
    Write-Host ""
}

# Summary
Write-Host ""
if ($buildSuccess) {
    Write-Host "=========================================" -ForegroundColor Green
    Write-Host "✅ Build & Push Successful!" -ForegroundColor Green
    Write-Host "=========================================" -ForegroundColor Green
    Write-Host ""
    
    Write-Host "Images on Docker Hub:" -ForegroundColor Cyan
    if ($buildMode -eq "1" -or $buildMode -eq "2") {
        Write-Host "  ✓ $dockerUsername/plankton-app:$mainAppVariant-arm64" -ForegroundColor White
        Write-Host "  ✓ $dockerUsername/plankton-app:latest" -ForegroundColor White
    }
    if ($buildMode -eq "1" -or $buildMode -eq "3") {
        Write-Host "  ✓ $dockerUsername/plankton-sql-agent:arm64" -ForegroundColor White
        Write-Host "  ✓ $dockerUsername/plankton-sql-agent:latest" -ForegroundColor White
    }
    Write-Host ""
    
    Write-Host "View on Docker Hub:" -ForegroundColor Cyan
    Write-Host "  https://hub.docker.com/u/$dockerUsername" -ForegroundColor Yellow
    Write-Host ""
    
    Write-Host "=========================================" -ForegroundColor Cyan
    Write-Host "Raspberry Pi Deployment Commands" -ForegroundColor Cyan
    Write-Host "=========================================" -ForegroundColor Cyan
    Write-Host ""
    
    if ($buildMode -eq "1") {
        Write-Host "# On Raspberry Pi, run:" -ForegroundColor Green
        Write-Host ""
        Write-Host "# 1. Pull images" -ForegroundColor White
        Write-Host "docker pull $dockerUsername/plankton-app:$mainAppVariant-arm64" -ForegroundColor Yellow
        Write-Host "docker pull $dockerUsername/plankton-sql-agent:arm64" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "# 2. Setup directories" -ForegroundColor White
        Write-Host "mkdir -p ~/plankton/{checkpoints,database,uploads}" -ForegroundColor Yellow
        Write-Host "cd ~/plankton" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "# 3. Create .env file" -ForegroundColor White
        Write-Host "echo 'GROQ_API_KEY=your_key_here' > .env" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "# 4. Create docker-compose.yml" -ForegroundColor White
        Write-Host "# (Use the provided docker-compose-dockerhub.yml template)" -ForegroundColor Gray
        Write-Host ""
        Write-Host "# 5. Run" -ForegroundColor White
        Write-Host "docker-compose up -d" -ForegroundColor Yellow
    } elseif ($buildMode -eq "2") {
        Write-Host "# On Raspberry Pi, run:" -ForegroundColor Green
        Write-Host ""
        Write-Host "docker pull $dockerUsername/plankton-app:$mainAppVariant-arm64" -ForegroundColor Yellow
        Write-Host "docker run -d --name plankton-detection -p 8501:8501 \\" -ForegroundColor Yellow
        Write-Host "  -v ~/plankton/checkpoints:/app/checkpoints \\" -ForegroundColor Yellow
        Write-Host "  -v ~/plankton/database:/app/database \\" -ForegroundColor Yellow
        Write-Host "  -v ~/plankton/uploads:/app/uploads \\" -ForegroundColor Yellow
        Write-Host "  --restart unless-stopped \\" -ForegroundColor Yellow
        Write-Host "  $dockerUsername/plankton-app:$mainAppVariant-arm64" -ForegroundColor Yellow
    }
    
    Write-Host ""
    Write-Host "📖 See DOCKERHUB_DEPLOYMENT.md for detailed instructions" -ForegroundColor Cyan
    
} else {
    Write-Host "=========================================" -ForegroundColor Red
    Write-Host "❌ Build/Push Failed!" -ForegroundColor Red
    Write-Host "=========================================" -ForegroundColor Red
    Write-Host ""
    Write-Host "Troubleshooting:" -ForegroundColor Yellow
    Write-Host "1. Check error messages above" -ForegroundColor White
    Write-Host "2. Verify Docker Hub login: docker login" -ForegroundColor White
    Write-Host "3. Check internet connection" -ForegroundColor White
    Write-Host "4. Try: docker system prune -a" -ForegroundColor White
    Write-Host ""
    exit 1
}
