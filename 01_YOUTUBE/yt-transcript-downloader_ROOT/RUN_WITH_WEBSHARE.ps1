$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
foreach ($name in @('WEBSHARE_USER', 'WEBSHARE_PASS')) {
    if ([string]::IsNullOrWhiteSpace([Environment]::GetEnvironmentVariable($name, 'Process'))) {
        [Environment]::SetEnvironmentVariable($name, [Environment]::GetEnvironmentVariable($name, 'User'), 'Process')
    }
    if ([string]::IsNullOrWhiteSpace([Environment]::GetEnvironmentVariable($name, 'Process'))) {
        throw "Missing $name. Run SET_WEBSHARE_CREDENTIALS.bat first."
    }
}
Write-Host 'YouTube transcript download: direct first, saved Webshare proxy if needed.'
Write-Host ''
while ($true) {
    $videoUrl = Read-Host 'Paste a video/playlist/channel URL (or Q to quit)'
    if ([string]::IsNullOrWhiteSpace($videoUrl)) { continue }
    if ($videoUrl.Trim().ToUpper() -eq 'Q') {
        Write-Host 'Done.'
        break
    }
    & "$PSScriptRoot\venv\Scripts\python.exe" "$PSScriptRoot\ytgrab.py" $videoUrl
    Write-Host ''
    Write-Host '---------------------------------------------------'
    Write-Host 'Ready for next URL. Type Q to quit.'
    Write-Host '---------------------------------------------------'
    Write-Host ''
}
exit 0
