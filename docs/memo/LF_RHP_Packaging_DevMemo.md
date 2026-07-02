# LoopFlow RHP 打包 — 開發備忘錄

> 發想日期：2026-07-02
> 最後更新：2026-07-02
> 狀態：規劃完成，待執行

---

## 一、目標

將 `releases/LoopFlow/Python/` 下 24 個散裝 `.py` 打包為 Rhino 8 Script Plugin（`.rhp`），方便使用者直接拖入 Rhino 安裝，不再需要手動複製腳本或執行 `.bat`。

`Tag_Blocks.3dm` 與 `LoopFlow_Dictionary.xlsx` 為使用者專案附屬檔，**不嵌入 .rhp**，仍隨 ZIP 一起發布。

---

## 二、背景理解

- 24 個 `.py` 分兩類：
  - **20 個指令腳本**（無 `_` 前綴）→ 打包為 Rhino Command
  - **4 個共用函式庫**（`_` 前綴）→ 打包為 Library
- 現有 import 模式 `import _LoopFlow_Config as _CFG` **不需改動**（plugin 會直接嵌入 libraries）
- 工具列按鈕現在用 `_-ScriptEditor _Run "...\LF_Script.py"`，需改成 `! _LF_Nexus`

---

## 三、目標產出結構

```
releases/
├── LoopFlow.rhproj              ← 新增（Script Project 定義）
├── LoopFlow.zip                 ← 最終發布包（由 build.ps1 產生）
│    ├── LoopFlow.rhp            ← 新產出（取代 Python/ 資料夾）
│    ├── LoopFlow.rhc            ← 更新按鈕指令
│    ├── Tag_Blocks.3dm          ← 不變
│    └── LoopFlow_Dictionary.xlsx← 不變
└── build/                       ← rhinocode 暫存輸出（加入 .gitignore）
```

---

## 四、變更項目

### 1. 新增 `releases/LoopFlow.rhproj`

Rhino 8 Script Project JSON，結構：

```json
{
  "type": "project",
  "name": "LoopFlow",
  "id": "<new-guid>",
  "version": "1.0",
  "author": { "name": "LoopFlow" },
  "commands": [
    { "id": "<guid>", "script": "LoopFlow/Python/LF_Nexus.py" },
    { "id": "<guid>", "script": "LoopFlow/Python/LF_Cabinet_Suite.py" },
    ...（其餘 18 個指令腳本）
  ],
  "libraries": [
    { "id": "<guid>", "script": "LoopFlow/Python/_LoopFlow_Config.py" },
    { "id": "<guid>", "script": "LoopFlow/Python/_LF_Registry.py" },
    { "id": "<guid>", "script": "LoopFlow/Python/_LF_Debug.py" },
    { "id": "<guid>", "script": "LoopFlow/Python/_LF_NamingRules.py" }
  ]
}
```

> `.rhproj` 放在 `releases/` 下，路徑相對於它

### 2. 每個指令 `.py` 加入 shebang

Rhino 8 Script Project 要求每個指令腳本第一行為：

```python
#! python3
```

目前 24 個腳本第一行都是 `# -*- coding: utf-8 -*-`，需在最頂加一行。

### 3. 更新 `releases/LoopFlow/LoopFlow.rhc`

每個 LoopFlow 按鈕的 `<Macro>` 從：
```
_-ScriptEditor _Run "%AppData%\...\LoopFlow\LF_Nexus.py" _Enter
```
改為：
```
! _LF_Nexus
```

- 指令名稱 = Python 檔名去掉 `.py`
- 圖示不動

### 4. 更新 `build.ps1`

```powershell
# 1. 呼叫 rhinocode 打包 .rhp
$rhinocode = "C:\Program Files\Rhino 8\System\rhinocode.exe"
& $rhinocode project build "$Root\releases\LoopFlow.rhproj" `
    --buildversion $Version --buildpath "$Root\releases\build"

# 2. 將 .rhp 複製到 releases/LoopFlow/
Copy-Item "$Root\releases\build\LoopFlow.rhp" "$ReleaseDir\LoopFlow.rhp" -Force

# 3. 打包 ZIP（LoopFlow.rhp + Tag_Blocks.3dm + LoopFlow_Dictionary.xlsx + LoopFlow.rhc）
Compress-Archive ...
```

### 5. 更新 `.gitignore`

```
releases/build/
```

---

## 五、指令名稱對照（20 個）

| Python 檔名 | Rhino 指令名 |
|---|---|
| `LF_Nexus.py` | `LF_Nexus` |
| `LF_Cabinet_Suite.py` | `LF_Cabinet_Suite` |
| `LF_Push_3D_to_JSON.py` | `LF_Push_3D_to_JSON` |
| `LF_Dictionary_Editor.py` | `LF_Dictionary_Editor` |
| `LF_Sync_Worksession.py` | `LF_Sync_Worksession` |
| `LF_2D_DW_Gen.py` | `LF_2D_DW_Gen` |
| `LF_2D_Cabinet_Gen.py` | `LF_2D_Cabinet_Gen` |
| `LF_2D_Shelf_Gap.py` | `LF_2D_Shelf_Gap` |
| `LF_Anchor_Frame.py` | `LF_Anchor_Frame` |
| `LF_Extract_CP.py` | `LF_Extract_CP` |
| `LF_Duplicate_Layout.py` | `LF_Duplicate_Layout` |
| `LF_Tagger_Layout_ID.py` | `LF_Tagger_Layout_ID` |
| `LF_Tagger_Grab.py` | `LF_Tagger_Grab` |
| `LF_Tagger_Laser.py` | `LF_Tagger_Laser` |
| `LF_Tagger_Index.py` | `LF_Tagger_Index` |
| `LF_Infuser_Part.py` | `LF_Infuser_Part` |
| `LF_Infuser_All.py` | `LF_Infuser_All` |
| `LF_TAG-O.py` | `LF_TAG_O`（連字號→底線） |
| `LF_Data_Viewer.py` | `LF_Data_Viewer` |

---

## 六、注意事項

- `importlib.reload(_CFG)` 在 plugin 中仍可運作（重載嵌入版本）
- `install_LoopFlow.bat` 不再需要（.rhp 直接拖入 Rhino 安裝），可保留作舊版相容
- rhinocode 路徑若不同需在 build.ps1 加入偵測邏輯
- `LF_TAG-O.py` 連字號不合 Rhino 指令命名規則，**檔名也需同步改為 `LF_TAG_O.py`**
