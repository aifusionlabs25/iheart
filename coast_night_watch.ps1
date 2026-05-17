param(
    [int]$DurationSeconds = 300,
    [int]$DeviceIndex = 16,
    [string]$Url = "https://www.iheart.com/live/newsradio-830-khvh-4748/",
    [ValidateSet("edge", "chrome")]
    [string]$Browser = "edge",
    [switch]$ConfirmBrowserRoutedToMonitor,
    [switch]$PreflightOnly,
    [switch]$SkipVerify,
    [int]$MinRms = 100
)

$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Root
$LogDir = Join-Path $Root "logs"
New-Item -ItemType Directory -Path $LogDir -Force | Out-Null
$TranscriptPath = Join-Path $LogDir ("coast_night_watch_{0}.log" -f (Get-Date -Format "yyyyMMdd_HHmmss"))
$script:TranscriptStarted = $false

function Stop-CoastTranscript {
    if ($script:TranscriptStarted) {
        try {
            Stop-Transcript | Out-Null
        } catch {
        }
        $script:TranscriptStarted = $false
    }
}

function Exit-Coast {
    param([int]$Code)
    Stop-CoastTranscript
    exit $Code
}

trap {
    Write-Host "Coast night watch failed: $($_.Exception.Message)" -ForegroundColor Red
    Stop-CoastTranscript
    exit 1
}

Start-Transcript -Path $TranscriptPath -Append | Out-Null
$script:TranscriptStarted = $true
Write-Host "Transcript: $TranscriptPath"

$PythonCandidates = @(
    $env:IHEART_PYTHON,
    "C:\Users\AI Fusion Labs\AppData\Local\Programs\Python\Python311\python.exe",
    "C:\Users\AI Fusion Labs\AppData\Local\Microsoft\WindowsApps\python.exe"
) | Where-Object { $_ -and (Test-Path $_) }

$PythonExe = $PythonCandidates | Select-Object -First 1
if (-not $PythonExe) {
    $PythonCommand = Get-Command python -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($PythonCommand) {
        $PythonExe = $PythonCommand.Source
    }
}
if (-not $PythonExe) {
    throw "Python was not found. Set IHEART_PYTHON or install Python 3.11."
}
Write-Host "Python: $PythonExe"

if ($Browser -eq "edge") {
    $EdgePaths = @(
        "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        "C:\Program Files\Microsoft\Edge\Application\msedge.exe"
    )
    if (-not ($EdgePaths | Where-Object { Test-Path $_ } | Select-Object -First 1)) {
        throw "Microsoft Edge was not found in the expected install locations."
    }
}

$DeviceProbe = @'
import json
import sounddevice as sd

default_input, default_output = sd.default.device
devices = sd.query_devices()
payload = {
    "default_input": default_input,
    "default_output": default_output,
    "devices": [
        {
            "index": i,
            "name": d.get("name", ""),
            "hostapi": sd.query_hostapis()[d.get("hostapi", 0)].get("name", ""),
            "max_input_channels": int(d.get("max_input_channels", 0)),
            "max_output_channels": int(d.get("max_output_channels", 0)),
        }
        for i, d in enumerate(devices)
    ],
}
print(json.dumps(payload))
'@

$DeviceJson = $DeviceProbe | & $PythonExe -

$DeviceInfo = $DeviceJson | ConvertFrom-Json
$DefaultOutput = [int]$DeviceInfo.default_output
$DefaultOutputDevice = $DeviceInfo.devices | Where-Object { $_.index -eq $DefaultOutput } | Select-Object -First 1
$CaptureDevice = $DeviceInfo.devices | Where-Object { $_.index -eq $DeviceIndex } | Select-Object -First 1

Write-Host "Coast night watch preflight"
Write-Host "Default output: [$DefaultOutput] $($DefaultOutputDevice.name)"
Write-Host "Capture device:  [$DeviceIndex] $($CaptureDevice.name)"
Write-Host "Browser:         $Browser"

if (-not $CaptureDevice) {
    throw "Capture device index $DeviceIndex was not found."
}

if ($CaptureDevice.name -notmatch "Sceptre|NVIDIA") {
    throw "Capture device $DeviceIndex does not look like the Sceptre/NVIDIA monitor audio route."
}

if (-not $ConfirmBrowserRoutedToMonitor) {
    Write-Host ""
    Write-Host "Safety stop: confirm the dedicated browser is routed to the Sceptre monitor output." -ForegroundColor Yellow
    Write-Host "Leave your Windows default speakers alone." -ForegroundColor Yellow
    Write-Host "In Windows Volume Mixer, route $Browser output to Sceptre F27 / NVIDIA High Definition Audio." -ForegroundColor Yellow
    Write-Host "Then rerun with -ConfirmBrowserRoutedToMonitor." -ForegroundColor Yellow
    exit 2
}

if ($PreflightOnly) {
    Write-Host ""
    Write-Host "Preflight passed. No browser or recording mission started."
    Exit-Coast 0
}

Write-Host ""
Write-Host "Starting mission for $DurationSeconds seconds..."
& $PythonExe run_mission.py --browser $Browser --duration $DurationSeconds --device $DeviceIndex --url $Url

if ($LASTEXITCODE -ne 0) {
    Exit-Coast $LASTEXITCODE
}

if (-not $SkipVerify) {
    $MinDuration = [Math]::Max(1, [Math]::Floor($DurationSeconds * 0.90))
    Write-Host ""
    Write-Host "Verifying newest recording (minimum duration: $MinDuration seconds, minimum RMS: $MinRms)..."
    & $PythonExe verify_latest_recording.py --root $Root --min-duration $MinDuration --min-rms $MinRms
    if ($LASTEXITCODE -ne 0) {
        Exit-Coast $LASTEXITCODE
    }
}

Exit-Coast 0
