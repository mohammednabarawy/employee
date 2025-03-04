@echo off
echo Employee Management System - Stress Testing Suite
echo ================================================
echo.
echo This batch file will help you run the stress testing tools.
echo.

:menu
echo Please select an option:
echo 1. Install dependencies
echo 2. Run Test Runner GUI
echo 3. Run Stress Tests directly
echo 4. Run Fix Issues script directly
echo 5. Run Performance Monitor
echo 6. Exit
echo.

set /p choice=Enter your choice (1-6): 

if "%choice%"=="1" goto install
if "%choice%"=="2" goto runner
if "%choice%"=="3" goto stress
if "%choice%"=="4" goto fix
if "%choice%"=="5" goto monitor
if "%choice%"=="6" goto end

echo Invalid choice. Please try again.
echo.
goto menu

:install
echo.
echo Installing dependencies...
pip install -r stress_test_requirements.txt
echo.
echo Dependencies installed.
echo.
pause
goto menu

:runner
echo.
echo Running Test Runner GUI...
python run_tests.py
goto menu

:stress
echo.
echo Running Stress Tests directly...
python stress_test.py
echo.
pause
goto menu

:fix
echo.
echo Running Fix Issues script...
python fix_issues.py
echo.
pause
goto menu

:monitor
echo.
echo Running Performance Monitor...
python monitor_performance.py
goto menu

:end
echo.
echo Thank you for using the Stress Testing Suite.
echo.
pause
