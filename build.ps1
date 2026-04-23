# LoopFlow Build Script
# 用途：將 releases/LoopFlow/ 打包成發布用 ZIP
# 使用方式：在專案根目錄執行 .\build.ps1
# 可加版本號：.\build.ps1 -Version "1.2.0"

param(
    [string]$Version = ""
)

$Root       = $PSScriptRoot
$ReleaseDir = Join-Path $Root "releases\LoopFlow"

# 1. 決定 ZIP 檔名
if ($Version -ne "") {
    $ZipName = "LoopFlow_v$Version.zip"
} else {
    $ZipName = "LoopFlow.zip"
}
$ZipPath = Join-Path (Join-Path $Root "releases") $ZipName

# 2. 刪除舊 ZIP（若存在）
if (Test-Path $ZipPath) {
    Remove-Item $ZipPath -Force
}

# 3. 打包 ZIP
Write-Host "Packing $ZipName..."
Compress-Archive -Path $ReleaseDir -DestinationPath $ZipPath -Force
Write-Host "  -> $ZipPath"

Write-Host ""
Write-Host "Build complete: $ZipName"
