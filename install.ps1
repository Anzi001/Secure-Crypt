$url = "https://github.com"
$dest = "$HOME\Desktop\FileEncrypter.exe"
Write-Host "Downloading File Encrypter to Desktop..." -ForegroundColor Cyan
Invoke-WebRequest -Uri $url -OutFile $dest
Write-Host "Done! You can now run the app from your Desktop." -ForegroundColor Green
