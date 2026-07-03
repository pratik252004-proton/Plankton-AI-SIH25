@echo off
REM Quick start script for TSV to YOLO conversion

echo ========================================
echo TSV to YOLO Converter - Quick Start
echo ========================================
echo.

REM Check if TSV file exists
if not exist "..\101138.tsv" (
    echo ERROR: TSV file not found at ..\101138.tsv
    echo Please make sure the TSV file is in the parent directory
    pause
    exit /b 1
)

REM Check if image directory exists
if not exist "..\101141\individual_images" (
    echo ERROR: Image directory not found at ..\101141\individual_images
    echo Please update the path in this script
    pause
    exit /b 1
)

echo Found TSV file and image directory
echo.
echo Starting conversion...
echo This may take a while depending on dataset size
echo.

REM Run conversion with default settings
python convert_tsv_to_yolo.py ^
    --tsv ..\101138.tsv ^
    --images ..\101141\individual_images ^
    --output yolo_dataset ^
    --train-split 0.8 ^
    --max-per-class 500

echo.
echo ========================================
echo Conversion Complete!
echo ========================================
echo.
echo Dataset created at: yolo_dataset\
echo.
echo Next steps:
echo 1. Review conversion_stats.json for statistics
echo 2. Install ultralytics: pip install ultralytics
echo 3. Train YOLO: yolo train data=yolo_dataset/data.yaml model=yolov8n.pt epochs=50
echo.
pause
