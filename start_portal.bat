@echo off
title MMTPL - Store & Inventory Management ERP Portal
cls
echo ======================================================================
echo           MMTPL Store ^& Inventory Management ERP Portal
echo ======================================================================
echo Starting local ERP web server on http://127.0.0.1:8000 ...
echo.

python run_portal.py
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] Failed to start portal. Please verify Python is installed.
    pause
)
