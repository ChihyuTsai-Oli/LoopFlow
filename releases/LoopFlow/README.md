### Installation

1. Download the latest release from [Releases](https://github.com/ChihyuTsai-Oli/LoopFlow/releases/latest)
2. Extract the ZIP, then install the scripts (choose one):
   - **2a.** Run `install_LoopFlow.bat` — copies `.py` files to the scripts folder automatically
   - **2b.** Manually copy all `.py` files from `Data/` to `%AppData%\McNeel\Rhinoceros\8.0\scripts\LoopFlow\`
3. Drag `LoopFlow.rhc` into the Rhino viewport — toolbar appears
4. All of the above can be done while Rhino is open

### Included Files

| File | Description |
|---|---|
| `Data/` | All LoopFlow `.py` scripts |
| `install_LoopFlow.bat` | Auto-installer — copies scripts to the correct Rhino folder |
| `LoopFlow.rhc` | Rhino toolbar definition |
| `LoopFlow_Dictionary.xlsx` | Default attribute dictionary |
| `Tag_Blocks.3dm` | Pre-configured Tag Block library — **must be included in the ZIP when packaging a release** |
