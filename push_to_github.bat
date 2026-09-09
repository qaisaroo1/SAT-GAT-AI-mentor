@echo off
cd /d D:\sat-gat-ai-mentor
echo ===================================================
echo   Pushing SAT-GAT AI Mentor to GitHub (qaisaroo1)
echo ===================================================
echo.
git branch -M main
git push -u origin main
echo.
if %ERRORLEVEL% equ 0 (
    echo [SUCCESS] Code successfully pushed to GitHub!
) else (
    echo [NOTICE] If prompted above, please sign in or authorize with GitHub.
)
echo.
pause
