<#
.SYNOPSIS
    Runs the Sonos Math Alarm via uv.
.DESCRIPTION
    This script automatically changes its execution context to the project root,
    locates the 'uv' package manager, and runs the Sonos Math Alarm. It is fully
    optimized to run non-interactively within the Windows Task Scheduler environment.
.NOTES
    HOW TO SCHEDULE THIS IN WINDOWS TASK SCHEDULER:
    -----------------------------------------------
    1. Open "Task Scheduler" (search in Start menu).
    2. Click "Create Task..." (or "Create Basic Task...").
    3. In the "General" tab:
       - Give it a name: "Sonos Math Alarm".
       - Choose "Run only when user is logged on" or "Run whether user is logged on or not".
    4. In the "Triggers" tab:
       - Click "New..."
       - Set your desired alarm schedule (e.g., Daily at 7:00 AM).
    5. In the "Actions" tab:
       - Click "New..."
       - Action: "Start a program"
       - Program/script: powershell.exe
       - Add arguments: -NoProfile -ExecutionPolicy Bypass -File "D:\_CodingProjects\smart_alarm\run_alarm.ps1"
       - Start in (optional but recommended): D:\_CodingProjects\smart_alarm
    6. Click OK to save the task.
#>

# Determine the directory where this script resides to ensure correct context
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

# Fall back to current working location if script path is unresolved
if ([string]::IsNullOrEmpty($ScriptDir)) {
    $ScriptDir = Get-Location
}

# Change directory to the smart_alarm project root
Set-Location $ScriptDir

Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "   Starting Sonos Math Alarm Scheduler   " -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "Working Directory: $ScriptDir" -ForegroundColor Gray

# Attempt to locate 'uv' in environment PATH
$UvPath = Get-Command uv -ErrorAction SilentlyContinue

# If not in default PATH, check common installation directory paths
if (-not $UvPath) {
    # Check cargo bin path
    $CargoUvPath = Join-Path $env:USERPROFILE ".cargo\bin\uv.exe"
    if (Test-Path $CargoUvPath) {
        $UvPath = $CargoUvPath
    } else {
        # Check standard UV AppData path
        $LocalUvPath = Join-Path $env:LOCALAPPDATA "Programs\uv\uv.exe"
        if (Test-Path $LocalUvPath) {
            $UvPath = $LocalUvPath
        } else {
            # Check standard UV Roaming AppData path
            $RoamingUvPath = Join-Path $env:APPDATA "uv\bin\uv.exe"
            if (Test-Path $RoamingUvPath) {
                $UvPath = $RoamingUvPath
            }
        }
    }
}

if (-not $UvPath) {
    Write-Error "Error: 'uv' package manager could not be found. Please ensure uv is installed."
    Exit 1
}

Write-Host "Using uv executable: $UvPath" -ForegroundColor Gray

# Execute the alarm application using uv
& $UvPath run smart_alarm
