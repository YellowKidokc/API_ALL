[CmdletBinding()]
param(
  [switch]$NoPrompt
)

$ErrorActionPreference = "Continue"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location -LiteralPath $Root

$LogDir = Join-Path $Root "logs"
if (-not (Test-Path -LiteralPath $LogDir)) {
  New-Item -ItemType Directory -Path $LogDir -Force | Out-Null
}

$Stamp = Get-Date -Format "yyyy-MM-dd-HH-mm-ss"
$Log = Join-Path $LogDir "troubleshoot-$Stamp.log"
$VenvPython = Join-Path $Root "venv\Scripts\python.exe"

function Write-Both {
  param([string]$Text = "")
  Write-Host $Text
  Add-Content -LiteralPath $Log -Value $Text
}

function Invoke-Check {
  param(
    [Parameter(Mandatory)][string]$Label,
    [Parameter(Mandatory)][scriptblock]$Script
  )

  Write-Both ""
  Write-Both "---- $Label ----"
  try {
    $global:LASTEXITCODE = 0
    $output = & $Script 2>&1
    $code = if ($LASTEXITCODE -is [int]) { $LASTEXITCODE } else { 0 }
    if ($output) {
      foreach ($line in $output) { Add-Content -LiteralPath $Log -Value ([string]$line) }
    }
    if ($code -eq 0) {
      Write-Host "OK" -ForegroundColor Green
      Add-Content -LiteralPath $Log -Value "EXIT_CODE=0"
    } else {
      Write-Host "CHECK FAILED, exit code $code" -ForegroundColor Yellow
      Add-Content -LiteralPath $Log -Value "EXIT_CODE=$code"
    }
  } catch {
    Write-Host "CHECK FAILED: $($_.Exception.Message)" -ForegroundColor Yellow
    Add-Content -LiteralPath $Log -Value "ERROR=$($_.Exception.Message)"
  }
}

Write-Both "============================================================"
Write-Both "YTBSD Troubleshooter"
Write-Both "============================================================"
Write-Both "Project: $Root"
Write-Both "Log: $Log"

Invoke-Check "Windows version" { cmd /c ver }
Invoke-Check "Python on PATH" { python --version }
Invoke-Check "Python launcher" { py --version }

if (Test-Path -LiteralPath $VenvPython) {
  Invoke-Check "Venv Python version" { & $VenvPython --version }
  Invoke-Check "Venv pip version" { & $VenvPython -m pip --version }
  Invoke-Check "Installed package summary" { & $VenvPython -m pip list }
  Invoke-Check "Python syntax compile" { & $VenvPython -m py_compile (Join-Path $Root "ytbsd.py") }
  Invoke-Check "Import dependency check" {
    & $VenvPython -c "import yt_dlp, requests, selenium, webdriver_manager, rich; from youtube_transcript_api import YouTubeTranscriptApi; print('imports ok')"
  }
} else {
  Write-Both ""
  Write-Both "MISSING: venv\Scripts\python.exe"
}

Invoke-Check "Chrome path check" { where.exe chrome }
Invoke-Check "Chrome default install check" {
  $paths = @(
    "$env:ProgramFiles\Google\Chrome\Application\chrome.exe",
    "${env:ProgramFiles(x86)}\Google\Chrome\Application\chrome.exe",
    "$env:LocalAppData\Google\Chrome\Application\chrome.exe"
  )
  $found = $paths | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1
  if ($found) { "found: $found" } else { throw "Chrome not found in default locations" }
}
Invoke-Check "Internet check - youtube.com" {
  $ok = Test-NetConnection -ComputerName "www.youtube.com" -Port 443 -InformationLevel Quiet
  if ($ok) { "TCP 443 reachable" } else { throw "Could not reach www.youtube.com:443" }
}
Invoke-Check "Internet check - pypi.org" {
  $ok = Test-NetConnection -ComputerName "pypi.org" -Port 443 -InformationLevel Quiet
  if ($ok) { "TCP 443 reachable" } else { throw "Could not reach pypi.org:443" }
}

Write-Both ""
Write-Both "============================================================"
Write-Both "Troubleshooting complete."
Write-Both "============================================================"
Write-Both "Log saved to: $Log"

if (-not $NoPrompt) {
  $repair = Read-Host "Run dependency repair now? [Y/N]"
  if ($repair -match "^(y|yes)$") {
    if (-not (Test-Path -LiteralPath $VenvPython)) {
      & (Join-Path $Root "setup.bat")
    } else {
      & $VenvPython -m pip install --upgrade pip
      & $VenvPython -m pip install --upgrade --force-reinstall -r (Join-Path $Root "requirements.txt")
    }
  }
}
