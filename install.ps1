# --- UPDATE THESE TWO LINES ---
$user = "Anzi001"
$repo = "File-Encrypter-Software"

$dest = "$HOME\Desktop\FileEncrypter.exe"

Write-Host "Connecting to GitHub API..." -ForegroundColor Cyan

try {
    # 1. Ask GitHub for info on the latest release
    $releaseInfo = Invoke-RestMethod -Uri "https://github.com"
    
    # 2. Find the download link for the Windows .exe
    $asset = $releaseInfo.assets | Where-Object { $_.name -like "*Win.exe" } | Select-Object -First 1
    
    if ($null -eq $asset) {
        throw "Could not find a file ending in 'Win.exe' in the latest release."
    }

    # 3. Download the actual binary file
    Write-Host "Downloading $($asset.name)..." -ForegroundColor Cyan
    Invoke-WebRequest -Uri $asset.browser_download_url -OutFile $dest -UserAgent "Mozilla/5.0"

    Write-Host "Success! App is on your Desktop." -ForegroundColor Green
    Start-Process $dest
}
catch {
    Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "Check that your Release is Public and contains 'FileEncrypter_Win.exe'." -ForegroundColor Yellow
}
