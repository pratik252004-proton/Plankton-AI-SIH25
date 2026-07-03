# Build Docker Images for Raspberry Pi (ARM64) - 2-Container Architecture
# This script builds both images: Main App + SQL Agent Service

Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "Plankton Detection - Raspberry Pi Build" -ForegroundColor Cyan
Write-Host "2-Container Architecture (App + SQL Agent)" -ForegroundColor Cyan
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
Write-Host "2) Main App only (without SQL chat)" -ForegroundColor White
Write-Host "   - Lighter, no Groq API needed" -ForegroundColor Gray
Write-Host ""
Write-Host "3) SQL Agent only" -ForegroundColor White
Write-Host "   - For updating just the SQL service" -ForegroundColor Gray
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
    Write-Host "   - All core features" -ForegroundColor Gray
    Write-Host ""
    Write-Host "2) Full" -ForegroundColor White
    Write-Host "   - Size: ~3.5GB" -ForegroundColor Gray
    Write-Host "   - Includes extra dependencies" -ForegroundColor Gray
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

# Create required directories
Write-Host "Creating required directories..." -ForegroundColor Cyan
New-Item -ItemType Directory -Force -Path "checkpoints" | Out-Null
New-Item -ItemType Directory -Force -Path "database" | Out-Null
New-Item -ItemType Directory -Force -Path "uploads" | Out-Null
Write-Host "✓ Directories created" -ForegroundColor Green
Write-Host ""

# Create or use existing buildx builder
Write-Host "Setting up Docker Buildx builder..." -ForegroundColor Cyan
$builderName = "plankton-builder"

# Check if builder exists
$existingBuilder = docker buildx ls | Select-String $builderName
if ($existingBuilder) {
    Write-Host "✓ Using existing builder: $builderName" -ForegroundColor Green
} else {
    Write-Host "Creating new builder: $builderName" -ForegroundColor Yellow
    docker buildx create --name $builderName --use
    Write-Host "✓ Builder created" -ForegroundColor Green
}

# Use the builder
docker buildx use $builderName
Write-Host ""

# Build images based on selection
$buildSuccess = $true

# Build Main App
if ($buildMode -eq "1" -or $buildMode -eq "2") {
    Write-Host "=========================================" -ForegroundColor Cyan
    Write-Host "Building Main App (Streamlit + ML)" -ForegroundColor Cyan
    Write-Host "=========================================" -ForegroundColor Cyan
    Write-Host "Dockerfile: $dockerfile" -ForegroundColor White
    Write-Host "Target Platform: linux/arm64" -ForegroundColor White
    Write-Host "Image Tag: plankton-app:$mainAppVariant-arm64" -ForegroundColor White
    Write-Host ""
    Write-Host "This may take 20-40 minutes..." -ForegroundColor Yellow
    Write-Host ""
    
    try {
        docker buildx build `
            --platform linux/arm64 `
            -f $dockerfile `
            -t "plankton-app:$mainAppVariant-arm64" `
            --load `
            .
        
        if ($LASTEXITCODE -ne 0) {
            $buildSuccess = $false
            Write-Host "❌ Main App build failed!" -ForegroundColor Red
        } else {
            Write-Host "✓ Main App built successfully!" -ForegroundColor Green
        }
    } catch {
        $buildSuccess = $false
        Write-Host "❌ Main App build failed!" -ForegroundColor Red
    }
    Write-Host ""
}

# Build SQL Agent
if ($buildMode -eq "1" -or $buildMode -eq "3") {
    Write-Host "=========================================" -ForegroundColor Cyan
    Write-Host "Building SQL Agent Service (FastAPI)" -ForegroundColor Cyan
    Write-Host "=========================================" -ForegroundColor Cyan
    Write-Host "Dockerfile: services/sql-agent/Dockerfile" -ForegroundColor White
    Write-Host "Target Platform: linux/arm64" -ForegroundColor White
    Write-Host "Image Tag: plankton-sql-agent:arm64" -ForegroundColor White
    Write-Host ""
    Write-Host "This may take 10-15 minutes..." -ForegroundColor Yellow
    Write-Host ""
    
    try {
        docker buildx build `
            --platform linux/arm64 `
            -f services/sql-agent/Dockerfile `
            -t "plankton-sql-agent:arm64" `
            --load `
            services/sql-agent
        
        if ($LASTEXITCODE -ne 0) {
            $buildSuccess = $false
            Write-Host "❌ SQL Agent build failed!" -ForegroundColor Red
        } else {
            Write-Host "✓ SQL Agent built successfully!" -ForegroundColor Green
        }
    } catch {
        $buildSuccess = $false
        Write-Host "❌ SQL Agent build failed!" -ForegroundColor Red
    }
    Write-Host ""
}

# Summary
Write-Host ""
if ($buildSuccess) {
    Write-Host "=========================================" -ForegroundColor Green
    Write-Host "✅ Build Successful!" -ForegroundColor Green
    Write-Host "=========================================" -ForegroundColor Green
    Write-Host ""
    
    Write-Host "Built Images:" -ForegroundColor Cyan
    if ($buildMode -eq "1" -or $buildMode -eq "2") {
        Write-Host "  ✓ plankton-app:$mainAppVariant-arm64" -ForegroundColor White
    }
    if ($buildMode -eq "1" -or $buildMode -eq "3") {
        Write-Host "  ✓ plankton-sql-agent:arm64" -ForegroundColor White
    }
    Write-Host ""
    
    # Ask if user wants to save images
    $saveImages = Read-Host "Do you want to save images to .tar files? (y/n) [default: y]"
    if ([string]::IsNullOrWhiteSpace($saveImages) -or $saveImages -eq "y") {
        Write-Host ""
        Write-Host "Saving images..." -ForegroundColor Cyan
        
        if ($buildMode -eq "1" -or $buildMode -eq "2") {
            Write-Host "  Saving main app..." -ForegroundColor Gray
            docker save "plankton-app:$mainAppVariant-arm64" -o "plankton-app-$mainAppVariant-raspi.tar"
            if ($LASTEXITCODE -eq 0) {
                $fileSize = (Get-Item "plankton-app-$mainAppVariant-raspi.tar").Length / 1GB
                Write-Host "  ✓ plankton-app-$mainAppVariant-raspi.tar ($([math]::Round($fileSize, 2)) GB)" -ForegroundColor Green
            }
        }
        
        if ($buildMode -eq "1" -or $buildMode -eq "3") {
            Write-Host "  Saving SQL agent..." -ForegroundColor Gray
            docker save "plankton-sql-agent:arm64" -o "plankton-sql-agent-raspi.tar"
            if ($LASTEXITCODE -eq 0) {
                $fileSize = (Get-Item "plankton-sql-agent-raspi.tar").Length / 1MB
                Write-Host "  ✓ plankton-sql-agent-raspi.tar ($([math]::Round($fileSize, 2)) MB)" -ForegroundColor Green
            }
        }
        
        Write-Host ""
        Write-Host "Transfer to Raspberry Pi:" -ForegroundColor Cyan
        if ($buildMode -eq "1") {
            Write-Host "  scp plankton-app-$mainAppVariant-raspi.tar plankton-sql-agent-raspi.tar pi@<ip>:~/" -ForegroundColor Yellow
        } elseif ($buildMode -eq "2") {
            Write-Host "  scp plankton-app-$mainAppVariant-raspi.tar pi@<ip>:~/" -ForegroundColor Yellow
        } else {
            Write-Host "  scp plankton-sql-agent-raspi.tar pi@<ip>:~/" -ForegroundColor Yellow
        }
    }
    
    Write-Host ""
    Write-Host "Next Steps:" -ForegroundColor Cyan
    Write-Host "1. Transfer .tar files to Raspberry Pi" -ForegroundColor White
    Write-Host "2. Load images: docker load -i <filename>.tar" -ForegroundColor White
    Write-Host "3. Copy docker-compose-2container.yml to Raspberry Pi" -ForegroundColor White
    Write-Host "4. Create .env file with GROQ_API_KEY (if using SQL agent)" -ForegroundColor White
    Write-Host "5. Run: docker-compose -f docker-compose-2container.yml up -d" -ForegroundColor White
    Write-Host ""
    Write-Host "📖 See RASPBERRY_PI_DEPLOYMENT.md for detailed instructions" -ForegroundColor Cyan
    
} else {
    Write-Host "=========================================" -ForegroundColor Red
    Write-Host "❌ Build Failed!" -ForegroundColor Red
    Write-Host "=========================================" -ForegroundColor Red
    Write-Host ""
    Write-Host "Troubleshooting:" -ForegroundColor Yellow
    Write-Host "1. Check error messages above" -ForegroundColor White
    Write-Host "2. Ensure all required files exist" -ForegroundColor White
    Write-Host "3. Try: docker system prune -a" -ForegroundColor White
    Write-Host "4. Check disk space: Get-PSDrive C" -ForegroundColor White
    Write-Host "5. Ensure Docker Desktop has enough resources" -ForegroundColor White
    Write-Host ""
    exit 1
}

