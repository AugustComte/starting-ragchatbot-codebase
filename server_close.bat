REM just double-click the file or run:
REM .\server_closebat                                                                                                                                                                                                                                                        
REM   It will find and kill any process listening on port 8000.
  


@echo off
echo Closing server on port 8000...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8000 ^| findstr LISTENING') do (
    taskkill /PID %%a /F
)
echo Done.
pause
