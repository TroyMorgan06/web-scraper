# Build a distributable Windows app folder:
#   dist/ProductTracker/ProductTracker.exe
#   dist/ProductTracker/ms-playwright/   (Chromium for Playwright)
#
# Usage (from project root, venv activated):
#   .\build_exe.ps1

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

Write-Host "Installing/updating build dependency..."
python -m pip install -q "pyinstaller>=6.0"

Write-Host "Ensuring Chromium is installed for Playwright..."
python -m playwright install chromium

Write-Host "Running PyInstaller..."
python -m PyInstaller `
  --noconfirm `
  --clean `
  --windowed `
  --name ProductTracker `
  --paths . `
  --hidden-import app `
  --hidden-import app.config `
  --hidden-import app.db `
  --hidden-import app.scraper `
  --hidden-import app.tracker `
  --hidden-import app.alerts `
  --hidden-import app.export `
  --collect-all playwright `
  --collect-all greenlet `
  --collect-all bs4 `
  gui.py

$distApp = Join-Path "dist" "ProductTracker"
if (-not (Test-Path $distApp)) {
  throw "Build failed: $distApp not found"
}

# Copy Playwright browsers next to the exe (used via PLAYWRIGHT_BROWSERS_PATH)
$browserSrc = Join-Path $env:LOCALAPPDATA "ms-playwright"
$browserDst = Join-Path $distApp "ms-playwright"
if (-not (Test-Path $browserSrc)) {
  throw "Playwright browsers not found at $browserSrc. Run: playwright install chromium"
}

Write-Host "Copying Playwright browsers to dist (this can take a minute)..."
if (Test-Path $browserDst) {
  Remove-Item -Recurse -Force $browserDst
}
Copy-Item -Recurse -Force $browserSrc $browserDst

# Handy empty data dir so users know where the DB will live
New-Item -ItemType Directory -Force -Path (Join-Path $distApp "data") | Out-Null

Write-Host ""
Write-Host "Build complete."
Write-Host "App folder: $((Resolve-Path $distApp).Path)"
Write-Host "Zip that folder to host a download on your website."
