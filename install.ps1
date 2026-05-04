# GitHub Details
$user = "Anzi001"
$repo = "File-Encrypter-Software"

# Paths
$url = "https://github.com"
$dest = "$HOME\Desktop\FileEncrypter.exe"

Write-Host "--- File Encrypter Installer ---" -ForegroundColor Cyan
Write-Host "Downloading latest version to Desktop..."

try {
    # Download the EXE
    Invoke-WebRequest -Uri $url -OutFile $dest
    Write-Host "Success! FileEncrypter.exe is now on your Desktop." -ForegroundColor Green
    
    # Optional: Run it immediately to trigger the UAC/Registry setup
    Start-Process $dest
}
catch {
    Write-Host "Error: Could not download the file. Make sure you have published a Release on GitHub." -ForegroundColor Red
}
