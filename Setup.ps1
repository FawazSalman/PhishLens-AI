$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
function Run-Step {
    param([string]$Program, [string[]]$Arguments)
    & $Program @Arguments
    if ($LASTEXITCODE -ne 0) { throw "Command failed: $Program $Arguments" }
}
Run-Step -Program 'py' -Arguments @('-3.12', '-m', 'venv', '.venv')
$Python = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
Run-Step -Program $Python -Arguments @('-m', 'pip', 'install', '--upgrade', 'pip')
Run-Step -Program $Python -Arguments @('-m', 'pip', 'install', '-r', 'requirements.txt')
Run-Step -Program $Python -Arguments @('-m', 'phishlens', 'train')
Run-Step -Program $Python -Arguments @('-m', 'unittest', 'discover', '-s', 'tests', '-v')
Run-Step -Program $Python -Arguments @('-m', 'phishlens', 'challenge')
Write-Host 'Setup complete. Run: .\.venv\Scripts\python.exe -m phishlens serve' -ForegroundColor Green
