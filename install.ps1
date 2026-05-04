# --- CONFIGURATION ---
$user = "Anzi001"
$repo = "File-Encrypter-Software"
$dest = "$HOME\Desktop\FileEncrypter.exe"

Write-Host "Connecting to GitHub API for $user/$repo..." -ForegroundColor Cyan

try {
    # 1. Fetch latest release info
    $releaseInfo = Invoke-RestMethod -Uri "https://github.com"
    
    # 2. List all found files for debugging
    Write-Host "Files found in release:" -ForegroundColor Gray
    $releaseInfo.assets | ForEach-Object { Write-Host " - $($_.name)" }

    # 3. Find the first file that contains "Win" and ends in ".exe"
    $asset = $releaseInfo.assets | Where-Object { $_.name -match "Win" -and $_.name -like "*.exe" } | Select-Object -First 1

    if ($null -eq $asset) {
        # Fallback: Just grab the first .exe if "Win" isn't found
        $asset = $releaseInfo.assets | Where-Object { $_.name -like "*.exe" } | Select-Object -First 1
    }

    if ($null -eq $asset) {
        throw "No .exe files found in this release. Please check your GitHub Actions build output."
    }

    # 4. Download
    Write-Host "Downloading $($asset.name)..." -ForegroundColor Cyan
    Invoke-WebRequest -Uri $asset.browser_download_url -OutFile $dest -UserAgent "Mozilla/5.0"

    Write-Host "SUCCESS! App is on your Desktop." -ForegroundColor Green
    Start-Process $dest
}
catch {
    Write-Host "ERROR: $($_.Exception.Message)" -ForegroundColor Red
}
