# G02 最小 yak：只登錄 LFDocument。不上架。
# 需要本機 Rhino 8 的 RhinoCode.exe 與 yak.exe。
$ErrorActionPreference = "Stop"
$Spike = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoWip = Split-Path -Parent (Split-Path -Parent $Spike)
$Src = Join-Path $RepoWip "src"
$Build = Join-Path $Spike "build"
$Yak = "C:\Program Files\Rhino 8\System\Yak.exe"
$RhinoCode = "C:\Program Files\Rhino 8\System\RhinoCode.exe"
$Rhproj = Join-Path $Spike "LoopFlow.rhproj"
$CommandPy = Join-Path $Spike "commands\LFDocument.py"

if (-not (Test-Path $Rhproj)) { throw "找不到 LoopFlow.rhproj" }
if (-not (Test-Path $CommandPy)) { throw "找不到 commands\LFDocument.py" }
if (-not (Test-Path $Src)) { throw "找不到 wip\src" }

New-Item -ItemType Directory -Force -Path $Build | Out-Null
$Prepared = Join-Path $Build "LoopFlow.prepared.rhproj"
$Prepare = Join-Path $Spike "prepare_rhproj.py"
python $Prepare $Rhproj $CommandPy $Prepared
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

& $RhinoCode project build $Prepared --buildversion 0.1.2 --buildtarget 8.* --buildpath $Build
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

$Stage = Get-ChildItem -Path $Build -Recurse -Filter "LoopFlow.rhp" | Select-Object -First 1
if (-not $Stage) { throw "RhinoCode 沒有產生 LoopFlow.rhp（專案可能沒有指令）" }
$StageDir = $Stage.Directory.FullName

$Lib = Join-Path $StageDir "lib"
if (Test-Path $Lib) { Remove-Item $Lib -Recurse -Force }
New-Item -ItemType Directory -Force -Path $Lib | Out-Null
Copy-Item -Recurse (Join-Path $Src "loopflow") (Join-Path $Lib "loopflow")
Get-ChildItem (Join-Path $Lib "loopflow") -Recurse -Directory -Filter "__pycache__" | Remove-Item -Recurse -Force
$GeneratedSrc = Join-Path $StageDir "src"
if (Test-Path $GeneratedSrc) { Remove-Item $GeneratedSrc -Recurse -Force }
# Do not pack LoopFlow.rui. It switches Rhino off the user's mori LoopFlow toolbar.
$RuiPath = Join-Path $StageDir "LoopFlow.rui"
if (Test-Path $RuiPath) { Remove-Item $RuiPath -Force }
if (Test-Path $RuiPath) { throw "LoopFlow.rui still present; refuse to pack yak" }
Get-ChildItem $StageDir -Filter "*.yak" | Remove-Item -Force

Copy-Item -Force (Join-Path $Spike "manifest.yml") (Join-Path $StageDir "manifest.yml")

Push-Location $StageDir
try {
    & $Yak build --platform win
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    $Built = Get-ChildItem *.yak | Sort-Object LastWriteTime -Descending | Select-Object -First 1
    if (-not $Built) { throw "yak build 沒有產生 .yak" }
    Add-Type -AssemblyName System.IO.Compression.FileSystem
    $Zip = [System.IO.Compression.ZipFile]::OpenRead($Built.FullName)
    try {
        $RuiInside = $Zip.Entries | Where-Object { $_.FullName -like "*.rui" }
        if ($RuiInside) { throw "yak still contains rui; refuse to install" }
    }
    finally {
        $Zip.Dispose()
    }
    Copy-Item -Force $Built.FullName $Build
    Write-Host "built $(Join-Path $Build $Built.Name)"
}
finally {
    Pop-Location
}
