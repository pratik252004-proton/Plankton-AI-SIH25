# Build script for Plankton Detection Docker image (Windows)
# This script handles the build process with proper error checking

Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "Plankton Detection Docker Build Script" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""

# Check if Docker is running
try {
    docker info | Out-Null
    Write-Host "✓ Docker is running" -ForegroundColor Green
Write-Host ""

# Select image variant
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "Select Docker Image Variant:" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "1) Minimal (Recommended for Raspberry Pi)" -ForegroundColor Green
Write-Host "   - Size: ~2.5GB"
Write-Host "   - Features: All core detection features"
Write-Host "   - Missing: SQL chat (optional feature)"
Write-Host ""
Write-Host "2) Full (All features)" -ForegroundColor Yellow
Write-Host "   - Size: ~3.5-4GB"
Write-Host "   - Features: Everything including SQL chat"
Write-Host "   - Requires: Groq API key for chat"
Write-Host ""
$variantChoice = Read-Host "Enter choice (1 or 2) [default: 1]"
if ([string]::IsNullOrWhiteSpace($variantChoice)) { $variantChoice = "1" }

if ($variantChoice -eq "2") {
    $dockerfile = "Dockerfile"
    $imageTag = "plankton-app:full"
    Write-Host "✓ Selected: Full image with all features" -ForegroundColor Green
} else {
    $dockerfile = "Dockerfile.minimal"
    $imageTag = "plankton-app:minimal"
    Write-Host "✓ Selected: Minimal image (optimized for Raspberry Pi)" -ForegroundColor Green
}
Write-Host ""

# Create required directories if they don't exist
Write-Host "Creating required directories..." -ForegroundColor Cyan
New-Item -ItemType Directory -Force -Path "checkpoints" | Out-Null
New-Item -ItemType Directory -Force -Path "database" | Out-Null
New-Item -ItemType Directory -Force -Path "uploads" | Out-Null
Write-Host "✓ Directories created" -ForegroundColor Green
Write-Host ""

# Check disk space
$drive = (Get-Location).Drive.Name
$disk = Get-PSDrive $drive
$freeSpaceGB = [math]::Round($disk.Free / 1GB, 2)
if ($freeSpaceGB -lt 5) {
    Write-Host "⚠️  Warning: Low disk space ($freeSpaceGB GB available)" -ForegroundColor Yellow
    Write-Host "   Recommended: At least 5GB free" -ForegroundColor Yellow
    Write-Host ""
}

# Build the image
Write-Host "Building Docker image..." -ForegroundColor Cyan
Write-Host "Dockerfile: $dockerfile" -ForegroundColor Yellow
Write-Host "This may take 10-30 minutes depending on your system..." -ForegroundColor Yellow
Write-Host ""

# Build for ARM64 (Raspberry Pi) using buildx
Write-Host "Building for ARM64 (Raspberry Pi)..." -ForegroundColor Cyan
docker buildx build --platform linux/arm64 -f $dockerfile -t $imageTag --load .

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "=========================================" -ForegroundColor Green
    Write-Host "✅ Build successful!" -ForegroundColor Green
    Write-Host "=========================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "Image built: $imageTag" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Cyan
    Write-Host "1. Save image: docker save $imageTag -o plankton-app.tar"
    Write-Host "2. Transfer to Raspberry Pi: scp plankton-app.tar pi@<IP>:~/"
    Write-Host "3. On Pi, load: docker load -i plankton-app.tar"
    Write-Host "4. On Pi, run: docker-compose up -d"
    Write-Host ""
} else {
    Write-Host ""
    Write-Host "=========================================" -ForegroundColor Red
    Write-Host "❌ Build failed!" -ForegroundColor Red
    Write-Host "=========================================" -ForegroundColor Red
    Write-Host ""
    Write-Host "Troubleshooting:" -ForegroundColor Yellow
    Write-Host "1. Check the error messages above"
    Write-Host "2. Ensure all required files exist"
    Write-Host "3. Try: docker system prune -a"
    Write-Host "4. Check if buildx is enabled: docker buildx version"
    Write-Host ""
    exit 1
}
