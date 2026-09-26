$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "Webshare credential setup for ytgrab.py" -ForegroundColor Cyan
Write-Host "The password will not be displayed or written into this repository."
Write-Host ""

$proxyUser = Read-Host "Webshare proxy username"
if ([string]::IsNullOrWhiteSpace($proxyUser)) {
    throw "Proxy username cannot be empty."
}

$secureProxyPassword = Read-Host "New Webshare proxy password" -AsSecureString
$passwordPointer = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secureProxyPassword)

try {
    $plainProxyPassword = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($passwordPointer)
    if ([string]::IsNullOrWhiteSpace($plainProxyPassword)) {
        throw "Proxy password cannot be empty."
    }

    [Environment]::SetEnvironmentVariable("WEBSHARE_USER", $proxyUser, "User")
    [Environment]::SetEnvironmentVariable("WEBSHARE_PASS", $plainProxyPassword, "User")

    # Make the values available to a connection test launched from this window.
    $env:WEBSHARE_USER = $proxyUser
    $env:WEBSHARE_PASS = $plainProxyPassword
}
finally {
    if ($passwordPointer -ne [IntPtr]::Zero) {
        [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($passwordPointer)
    }
    $plainProxyPassword = $null
    $secureProxyPassword = $null
}

Write-Host ""
Write-Host "Saved WEBSHARE_USER and WEBSHARE_PASS for your Windows account." -ForegroundColor Green
Write-Host "Open a new PowerShell or Command Prompt before running ytgrab.py." -ForegroundColor Yellow
Write-Host ""
Read-Host "Press Enter to close"
