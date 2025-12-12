@echo off
setlocal

:: Check if a file was provided
if "%~1"=="" (
    echo Drag and drop a file onto this script.
    pause
    exit /b
)

:: Get full path, filename, and extension
set "input=%~1"
set "filename=%~n1"
set "ext=%~x1"
set "path=%~dp1"

:: Define output file name
set "output=%path%%filename%%ext%.NEW"

:: Run auracomp with arguments
auracomp.exe -compress -in "%input%" -out "%output%" -algo HWGZ -level optimal -endian Big

echo.
echo Done! Output: "%output%"
pause
