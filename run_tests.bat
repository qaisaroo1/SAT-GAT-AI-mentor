@echo off
title SAT & GAT AI Mentor System Verification
cd /d "%~dp0"
echo Running System Verification Tests...
set PYTHONPATH=%~dp0
call venv\Scripts\activate
python test_system.py
pause
