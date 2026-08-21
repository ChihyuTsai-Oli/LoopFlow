# G02 yak: register official commands and pack the product LoopFlow.rui.
# Delete the RhinoCode-generated RUI first; that file is not the product toolbar.
$ErrorActionPreference = "Stop"
$Spike = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoWip = Split-Path -Parent (Split-Path -Parent $Spike)
$Src = Join-Path $RepoWip "src"
$Build = Join-Path $Spike "build"
$Yak = "C:\Program Files\Rhino 8\System\Yak.exe"
$RhinoCode = "C:\Program Files\Rhino 8\System\RhinoCode.exe"
$Rhproj = Join-Path $Spike "LoopFlow.rhproj"
$CommandsDir = Join-Path $Spike "commands"
$ProductRui = Join-Path $RepoWip "docs\toolbar\LoopFlow.rui"
$Version = "0.2.1"

if (-not (Test-Path $Rhproj)) { throw "找不到 LoopFlow.rhproj" }
if (-not (Test-Path (Join-Path $CommandsDir "LFDocument.py"))) { throw "找不到 commands\LFDocument.py" }
if (-not (Test-Path $Src)) { throw "找不到 wip\src" }
if (-not (Test-Path $ProductRui)) { throw "找不到 wip\docs\toolbar\LoopFlow.rui" }
if ((Get-Item $ProductRui).Length -lt 1000) { throw "LoopFlow.rui looks empty" }

New-Item -ItemType Directory -Force -Path $Build | Out-Null
$Prepared = Join-Path $Build "LoopFlow.prepared.rhproj"
$Prepare = Join-Path $Spike "prepare_rhproj.py"
python $Prepare $Rhproj $Prepared
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

& $RhinoCode project build $Prepared --buildversion $Version --buildtarget 8.* --buildpath $Build
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
if (Test-Path $GeneratedSrc) { Remove-Item $GeneratedSrc -Force -Recurse }
# Replace generated LoopFlow.rui with the product toolbar from docs/toolbar.
$RuiPath = Join-Path $StageDir "LoopFlow.rui"
if (Test-Path $RuiPath) { Remove-Item $RuiPath -Force }
Copy-Item -Force $ProductRui $RuiPath
if (-not (Test-Path $RuiPath)) { throw "product LoopFlow.rui was not copied into the yak stage" }
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
        $RuiInside = @($Zip.Entries | Where-Object { $_.FullName -like "*.rui" })
        if ($RuiInside.Count -ne 1) { throw "yak must contain exactly one rui" }
        if ($RuiInside[0].FullName -ne "LoopFlow.rui") { throw "yak rui must be named LoopFlow.rui" }
        if ($RuiInside[0].Length -lt 1000) { throw "packed LoopFlow.rui looks empty" }
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
