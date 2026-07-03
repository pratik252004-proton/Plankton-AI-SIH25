@echo off
REM Plankton Detection System - Quick Start Script
echo ========================================
echo  Plankton Detection System
echo  Starting Streamlit Application...
echo ========================================
echo.

cd /d "%~dp0"
streamlit run app/streamlit_app.py

pause
