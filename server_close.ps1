# PowerShell script to close server on port 8000
# Run with: .\server_close.ps1
# Or: powershell -ExecutionPolicy Bypass -File server_close.ps1

Write-Host "Closing server on port 8000..."

$connections = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue

if ($connections) {
    $connections | ForEach-Object {
        Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue
    }
    Write-Host "Server closed."
} else {
    Write-Host "No server found on port 8000."
}

Read-Host "Press Enter to exit"
