@echo off
title PDF to Markdown Converter
cd /d "%~dp0"
echo Converting PDF in data folder to Markdown...
call venv\Scripts\activate
python convert_pdf.py
pause
