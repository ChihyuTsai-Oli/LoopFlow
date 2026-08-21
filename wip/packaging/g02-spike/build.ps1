# G02 最小 yak：只登錄 LFDocument。不上架。
# 需要本機 Rhino 8 的 RhinoCode.exe 與 yak.exe。
$ErrorActionPreference = "Stop"
$Spike = Split-Path -Parent $MyInvocation.MyCommand.Path
$Build = Join-Path $Spike "build"
$Yak = "C:\Program Files\Rhino 8\System\Yak.exe"
$RhinoCode = "C:\Program Files\Rhino 8\System\RhinoCode.exe"
$Rhproj = Join-Path $Spike "LoopFlow.rhproj"

New-Item -ItemType Directory -Force -Path $Build | Out-Null

if (-not (Test-Path $Rhproj)) {
    Write-Error @"
找不到 LoopFlow.rhproj。
請在 Rhino 8 開 ScriptEditor → 新增專案 → 把 commands\LFDocument.py 加為 Rhino 指令（名稱 LFDocument）→ 把 wip\src 加到 Libraries → 另存成這個資料夾的 LoopFlow.rhproj。
然後再跑本腳本。不要改 wip\src\entrypoints\LF_Document.py 的檔名。
"@
}

& $RhinoCode project build $Rhproj --buildversion 0.1.0 --buildtarget 8.* --buildpath $Build
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Push-Location $Build
try {
    Copy-Item -Force (Join-Path $Spike "manifest.yml") .
    & $Yak build --platform win
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    Get-ChildItem *.yak | ForEach-Object { Write-Host "built $($_.FullName)" }
}
finally {
    Pop-Location
}
