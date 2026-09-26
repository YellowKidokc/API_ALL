[CmdletBinding()]
param(
  [Parameter(Mandatory)]
  [ValidateSet("Subtitles","Audio","Video","All","Menu","Troubleshoot")]
  [string]$Mode,

  [string]$Url,
  [string]$OutputRoot = "$env:USERPROFILE\yt_captures",
  [string]$DownloaderRoot = "D:\GitHub\yt-bulk-subtitles-downloader"
)

$ErrorActionPreference = "Stop"
$VenvPython = Join-Path $DownloaderRoot "venv\Scripts\python.exe"
$MenuBat = Join-Path $DownloaderRoot "YTBSD_MENU.bat"
$TroubleshootBat = Join-Path $DownloaderRoot "TROUBLESHOOT_YTBSD.bat"

function Ensure-Ready {
  if (-not (Test-Path -LiteralPath $DownloaderRoot)) {
    throw "Downloader root not found: $DownloaderRoot"
  }
  if (-not (Test-Path -LiteralPath $VenvPython)) {
    $setup = Join-Path $DownloaderRoot "setup.bat"
    if (-not (Test-Path -LiteralPath $setup)) {
      throw "Virtual environment is missing and setup.bat was not found."
    }
    Write-Host "Virtual environment missing. Running setup..."
    & $setup
  }
  if (-not (Test-Path -LiteralPath $VenvPython)) {
    throw "Virtual environment still missing after setup: $VenvPython"
  }
}

function New-CaptureFolder {
  param([string]$ModeName)
  $stamp = Get-Date -Format "yyyy-MM-dd_HH-mm-ss"
  $folder = Join-Path $OutputRoot "$stamp - YouTube $ModeName"
  New-Item -ItemType Directory -Path $folder -Force | Out-Null
  return $folder
}

function Invoke-YtDlp {
  param([string[]]$Args)
  Ensure-Ready
  Write-Host ""
  Write-Host "Running yt-dlp..."
  Write-Host ($Args -join " ")
  & $VenvPython -m yt_dlp @Args
  return $LASTEXITCODE
}

function Require-Url {
  if ([string]::IsNullOrWhiteSpace($Url)) {
    throw "No YouTube URL was provided."
  }
}

function Test-CommandExists {
  param([string]$Name)
  $null -ne (Get-Command $Name -ErrorAction SilentlyContinue)
}

try {
  if ($Mode -eq "Menu") {
    if (-not (Test-Path -LiteralPath $MenuBat)) { throw "Menu not found: $MenuBat" }
    & $MenuBat
    exit $LASTEXITCODE
  }

  if ($Mode -eq "Troubleshoot") {
    if (-not (Test-Path -LiteralPath $TroubleshootBat)) { throw "Troubleshooter not found: $TroubleshootBat" }
    & $TroubleshootBat
    exit $LASTEXITCODE
  }

  Require-Url
  Ensure-Ready
  New-Item -ItemType Directory -Path $OutputRoot -Force | Out-Null

  $modeFolder = New-CaptureFolder -ModeName $Mode
  $common = @(
    "--no-playlist",
    "--windows-filenames",
    "--write-info-json",
    "--paths", $modeFolder,
    "--output", "%(upload_date>%Y-%m-%d)s - %(title).180B [%(id)s].%(ext)s"
  )

  Write-Host "URL: $Url"
  Write-Host "Output: $modeFolder"

  if ($Mode -eq "Subtitles" -or $Mode -eq "All") {
    Write-Host ""
    Write-Host "Downloading subtitles/transcript files..."
    $subArgs = @(
      "--skip-download",
      "--write-subs",
      "--write-auto-subs",
      "--sub-langs", "en.*,en",
      "--sub-format", "srt/best"
    ) + $common + @($Url)
    $code = Invoke-YtDlp -Args $subArgs
    if ($code -ne 0 -and $Mode -eq "Subtitles") { exit $code }
  }

  if ($Mode -eq "Audio" -or $Mode -eq "All") {
    Write-Host ""
    Write-Host "Downloading audio..."
    if (Test-CommandExists "ffmpeg") {
      $audioArgs = @(
        "--extract-audio",
        "--audio-format", "mp3",
        "--audio-quality", "0",
        "--embed-metadata"
      ) + $common + @($Url)
    } else {
      Write-Host "ffmpeg not found on PATH. Saving best available audio without mp3 conversion."
      $audioArgs = @("-f", "bestaudio/best") + $common + @($Url)
    }
    $code = Invoke-YtDlp -Args $audioArgs
    if ($code -ne 0 -and $Mode -eq "Audio") { exit $code }
  }

  if ($Mode -eq "Video" -or $Mode -eq "All") {
    Write-Host ""
    Write-Host "Downloading video..."
    if (Test-CommandExists "ffmpeg") {
      $videoArgs = @("-f", "bv*+ba/b", "--merge-output-format", "mp4") + $common + @($Url)
    } else {
      Write-Host "ffmpeg not found on PATH. Saving best single-file video format."
      $videoArgs = @("-f", "best") + $common + @($Url)
    }
    $code = Invoke-YtDlp -Args $videoArgs
    if ($code -ne 0 -and $Mode -eq "Video") { exit $code }
  }

  Write-Host ""
  Write-Host "Done."
  Write-Host "Saved under: $modeFolder"
  exit 0
} catch {
  Write-Error $_
  exit 1
}
