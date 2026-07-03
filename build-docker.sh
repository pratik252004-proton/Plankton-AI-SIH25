#!/bin/bash
# Build script for Plankton Detection Docker image
# This script handles the build process with proper error checking

set -e  # Exit on error

echo "========================================="
echo "Plankton Detection Docker Build Script"
echo "========================================="
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Error: Docker is not running!"
    echo "Please start Docker and try again."
    exit 1
fi

echo "✓ Docker is running"
echo ""

# Select image variant
echo "========================================="
echo "Select Docker Image Variant:"
echo "========================================="
echo "1) Minimal (Recommended for Raspberry Pi)"
echo "   - Size: ~2.5GB"
echo "   - Features: All core detection features"
echo "   - Missing: SQL chat (optional feature)"
echo ""
echo "2) Full (All features)"
echo "   - Size: ~3.5-4GB"
echo "   - Features: Everything including SQL chat"
echo "   - Requires: Groq API key for chat"
echo ""
read -p "Enter choice (1 or 2) [default: 1]: " VARIANT_CHOICE
VARIANT_CHOICE=${VARIANT_CHOICE:-1}

if [ "$VARIANT_CHOICE" = "2" ]; then
    DOCKERFILE="Dockerfile"
    IMAGE_TAG="plankton-app:full"
    echo "✓ Selected: Full image with all features"
else
    DOCKERFILE="Dockerfile.minimal"
    IMAGE_TAG="plankton-app:minimal"
    echo "✓ Selected: Minimal image (optimized for Raspberry Pi)"
fi
echo ""

# Create required directories if they don't exist
echo "Creating required directories..."
mkdir -p checkpoints database uploads
echo "✓ Directories created"
echo ""

# Check disk space
AVAILABLE_SPACE=$(df -BG . | tail -1 | awk '{print $4}' | sed 's/G//')
if [ "$AVAILABLE_SPACE" -lt 5 ]; then
    echo "⚠️  Warning: Low disk space (${AVAILABLE_SPACE}GB available)"
    echo "   Recommended: At least 5GB free"
    echo ""
fi

# Build the image
echo "Building Docker image..."
echo "Dockerfile: $DOCKERFILE"
echo "This may take 10-30 minutes depending on your system..."
echo ""

# Detect if running on ARM (Raspberry Pi)
ARCH=$(uname -m)
if [[ "$ARCH" == "aarch64" || "$ARCH" == "arm64" ]]; then
    echo "✓ Detected ARM64 architecture (Raspberry Pi)"
    # Build with memory limits for Raspberry Pi
    docker build -f "$DOCKERFILE" --memory=2g --memory-swap=4g -t "$IMAGE_TAG" .
else
    echo "✓ Detected x86_64 architecture"
    # Build normally
    docker build -f "$DOCKERFILE" -t "$IMAGE_TAG" .
fi

BUILD_STATUS=$?

echo ""
if [ $BUILD_STATUS -eq 0 ]; then
    echo "========================================="
    echo "✅ Build successful!"
    echo "========================================="
    echo ""
    echo "Next steps:"
    echo "1. Run: docker-compose up -d"
    echo "2. Access: http://localhost:8501"
    echo "3. View logs: docker-compose logs -f"
    echo ""
else
    echo "========================================="
    echo "❌ Build failed!"
    echo "========================================="
    echo ""
    echo "Troubleshooting:"
    echo "1. Check the error messages above"
    echo "2. Ensure all required files exist"
    echo "3. Try: docker system prune -a"
    echo "4. Check disk space: df -h"
    echo ""
    exit 1
fi
