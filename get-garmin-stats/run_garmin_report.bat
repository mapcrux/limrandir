@echo off
setlocal

REM Optional override if GARMIN_REPORT_OUTPUT_TEMPLATE is not already defined.
if "%GARMIN_REPORT_OUTPUT_TEMPLATE%"=="" set GARMIN_REPORT_OUTPUT_TEMPLATE=C:\Users\codet\OneDrive\Documents\Garmin Reports\{report-date}.json

python "%~dp0garmin_report.py"
set EXITCODE=%ERRORLEVEL%

if not "%EXITCODE%"=="0" (
  echo Garmin report failed with exit code %EXITCODE%.
)

exit /b %EXITCODE%
