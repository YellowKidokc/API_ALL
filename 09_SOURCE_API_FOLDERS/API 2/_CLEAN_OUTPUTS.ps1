# Clean all output/cache/state folders in engines directory
# Keeps scripts, configs, templates — deletes results and runtime artifacts

$root = "D:\GitHub\pipeline-workflows\engines"

# Patterns to clean (delete contents, keep the folder)
$cleanPatterns = @(
    "OUTBOX", "_outbox", "_processed", "_exports", 
    "_logs", "_state", "__pycache__", "INBOX_FULL",
    "output", "discoveries", "ISOMORPHISMS"
)

$totalDeleted = 0

Get-ChildItem -Path $root -Directory -Recurse | Where-Object {
    $cleanPatterns -contains $_.Name
} | ForEach-Object {
    $items = Get-ChildItem -Path $_.FullName -File -ErrorAction SilentlyContinue
    $count = ($items | Measure-Object).Count
    if ($count -gt 0) {
        Write-Host "Cleaning: $($_.FullName) ($count files)"
        Remove-Item "$($_.FullName)\*" -Recurse -Force -ErrorAction SilentlyContinue
        $totalDeleted += $count
    }
}

Write-Host "`nDone. Deleted contents of $totalDeleted files from output/cache folders."
Write-Host "Scripts, configs, and templates preserved."
