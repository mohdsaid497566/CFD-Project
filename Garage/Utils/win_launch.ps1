# PowerShell script to launch the Intake CFD application in Windows

Write-Host "Intake CFD Optimization Suite - Windows Launcher" -ForegroundColor Blue
Write-Host "================================================" -ForegroundColor Blue
Write-Host

# Get the directory where this script is located
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
Write-Host "Script directory: $scriptPath"
Set-Location -Path $scriptPath

# Check if Python is installed
try {
    $pythonVersion = python --version
    Write-Host "Found Python: $pythonVersion"
}
catch {
    Write-Host "Python not found! Please install Python from https://www.python.org/downloads/" -ForegroundColor Red
    Write-Host "Make sure to check 'Add Python to PATH' during installation." -ForegroundColor Red
    Write-Host "Press any key to exit..."
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
    exit 1
}

# Check if required packages are installed
Write-Host "Checking required packages..."
$requiredPackages = @("numpy", "pandas", "matplotlib", "openmdao", "PIL", "tkinter")
$missingPackages = @()

foreach ($package in $requiredPackages) {
    try {
        python -c "import $package" | Out-Null
        Write-Host "  ✓ $package is installed" -ForegroundColor Green
    }
    catch {
        Write-Host "  ✗ $package is not installed" -ForegroundColor Yellow
        $missingPackages += $package
    }
}

# Install missing packages if any
if ($missingPackages.Count -gt 0) {
    Write-Host "`nSome required packages are missing. Do you want to install them now? (y/n)" -ForegroundColor Yellow
    $response = Read-Host
    if ($response -eq "y") {
        foreach ($package in $missingPackages) {
            Write-Host "Installing $package..." -ForegroundColor Cyan
            python -m pip install $package
            if ($LASTEXITCODE -ne 0) {
                Write-Host "Failed to install $package. Please install it manually." -ForegroundColor Red
            }
        }
    }
}

# Launch the direct launcher
Write-Host "`nLaunching Intake CFD application..." -ForegroundColor Cyan
python run_direct.py

if ($LASTEXITCODE -ne 0) {
    Write-Host "The application exited with an error. Exit code: $LASTEXITCODE" -ForegroundColor Red
}
else {
    Write-Host "Application closed successfully." -ForegroundColor Green
}

Write-Host "`nPress any key to exit..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
