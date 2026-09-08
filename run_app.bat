@echo off
title SAT & GAT AI Mentor Web Dashboard
cd /d "%~dp0"
echo Starting SAT & GAT AI Mentor...
call venv\Scripts\activate
streamlit run app.py
pause
