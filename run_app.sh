#!/bin/bash
# Plankton Detection System - Quick Start Script

echo "========================================"
echo " Plankton Detection System"
echo " Starting Streamlit Application..."
echo "========================================"
echo ""

cd "$(dirname "$0")"
streamlit run app/streamlit_app.py
