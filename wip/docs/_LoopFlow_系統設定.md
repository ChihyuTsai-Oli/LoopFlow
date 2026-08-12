# LoopFlow — 系統設定

本文件是 LoopFlow 維護設定與現況結構的權威來源。重構目標與遷移順序另見 `_LoopFlow_重構計畫.md`。

## Repo 與版本

| 項目 | 設定 |
|---|---|
| 穩定分支 | `main`（1.x） |
| 2.0 整合分支 | `v2-development` |
| 短期工作分支 | `codex/v2-<scope>` |
| 穩定 tag | `v1.0.0` |
| 目標版本 | `v2.0.0` |
| Runtime | Rhino 8 / CPython 3.9 / Windows |

## 2.0 開發模式

- `main`、`v1.0.0` 與 `releases/LoopFlow/` 作為舊版行為與回復參考，不在重構過程逐支改造成半新半舊系統。
- 2.0 在新的 `wip/src/`、隔離安裝、設定、資料與測試專案中乾淨建立，正式發布時一次切換。
- 開始建立 feature 前，先完成 `_LoopFlow_命名與資料契約.md` 的工作流、Dictionary、UserText、layer、Registry 與 Tag 定義。
- 新核心只接受 2.0 canonical contract；舊專案支援由獨立 migration 工具負責。
- 每個建造階段仍須有自動測試；完整 Rhino 實機測試於主要工作流接通後執行。

## 目前 Repo 結構

```text
releases/LoopFlow/
  Python/                 # 目前 23 支可直接執行或共用的 Python
  LoopFlow_Dictionary.xlsx
  LoopFlow.rhc
  Tag_Blocks.3dm
  install_LoopFlow.bat
docs/
  USER_GUIDE*.md          # 公開使用指南
  Dictionary_GUIDE*.md    # 公開 Dictionary 指南
wip/
  README.md
  docs/
    _LoopFlow_*.md        # 重構維護 SSOT
    architecture/NEXUS_DICTIONARY_DECISION_MENU.md
    architecture/DEVELOPMENT_ROADMAP.md
    architecture/PROGRESS.md
  src/                    # 2.0 原始碼（後續建立）
  tests/                  # 自動測試（後續建立）
  fixtures/               # 可提交的輕量測試資料（後續建立）
build.ps1
```

目前 `releases/LoopFlow/Python/` 同時是可編輯來源與 release payload。只有在 package 骨架、import spike 與 build 驗證完成後，才切換為 `wip/src/` 唯一來源。

## 重構期間的 Rhino 測試入口

重構期間直接從 repo 執行開發中的入口，不必先複製到 `%APPDATA%`。Rhino 測試按鈕固定指向 `entrypoints/`，不要直接指向仍會調整的 `features/`、`platform/` 或 `foundation/` 內部模組：

```text
E:\_GitHub\LoopFlow\wip\src\entrypoints\
```

按鈕巨集格式：

```text
_-ScriptEditor _Run "E:\_GitHub\LoopFlow\wip\src\entrypoints\LF_Nexus.py"
```

目前預計的使用者入口如下；共用模組 `_LoopFlow_Config.py`、`_LF_Debug.py`、`_LF_NamingRules.py`、`_LF_Registry.py` 不建立按鈕：

```text
LF_Nexus.py
LF_Dictionary_Editor.py
LF_Data_Viewer.py
LF_Push_3D_to_JSON.py
LF_Tagger_Grab.py
LF_Tagger_Laser.py
LF_Tagger_Index.py
LF_Tagger_Layout_ID.py
LF_TAG-O.py
LF_Infuser_Part.py
LF_Infuser_All.py
LF_Anchor_Frame.py
LF_Extract_CP.py
LF_Duplicate_Layout.py
LF_Cabinet_Suite.py
LF_2D_Cabinet_Gen.py
LF_2D_Shelf_Gap.py
LF_2D_DW_Gen.py
LF_Sync_Worksession.py
```

這是開發期暫定清單，不是凍結的公開契約。功能增減、入口檔名或 repo 內路徑改變時，應同步更新本節與測試工具列；正式安裝／RC 驗證才改用隔離的 `%APPDATA%` 開發安裝位置。

## 模組責任

| 模組／功能群 | 責任 |
|---|---|
| `_LoopFlow_Config.py` | 使用者可調設定、layer／檔名／顏色／時間常數 |
| `_LF_Registry.py` | Registry lock、JSON 讀寫與發布 |
| `_LF_NamingRules.py` | 命名規則 |
| `_LF_Debug.py` | Debug／錯誤紀錄 |
| Tagger 系列 | UserText／Tag Block 建立與更新 |
| `LF_Nexus.py` | Dictionary、幾何、UUID、space、Registry 與 Excel 的整合流程 |
| Infuser 系列 | 將資料寫入圖面 Tag Blocks |
| Cabinet／2D 系列 | 櫃體與圖面幾何產生 |
| Layout／Section 系列 | Layout、anchor、section curve 與複製流程 |
| `LF_Sync_Worksession.py` | Worksession 事件生命週期與同步 |

目前大型檔案仍混合 UI、規則、Rhino API 與 I/O；這是重構對象，不表示可以一次拆完。

## `_LoopFlow_Config.py` 可編輯設定

### Dictionary

| 設定 | 預設值 | 用途 |
|---|---|---|
| `DICTIONARY_FILENAME_XLSX` | `LoopFlow_Dictionary.xlsx` | Dictionary 檔名 |
| `DICTIONARY_KEY_COLUMN` | `__Rhino Layer` | layer 主鍵欄 |
| `DICTIONARY_SKIPROWS` | `1` | 資料前略過列數 |

### Layer

| 設定 | 預設值／規則 |
|---|---|
| `LAYER_PREFIX_3D` | `M3D` |
| `LAYER_DATA_SUFFIX` | `_Data` |
| `LAYER_SPACE_BOUNDARIES` | `M3D::_Data::Space_Boundaries` |
| `LAYER_LEVEL_FFL` | `M3D::_Data::Level_Boundaries_FFL` |
| `LAYER_LEVEL_FL` | `M3D::_Data::Level_Boundaries_FL` |
| `LAYER_DW_PLAN` | `M3D::20_DW` |
| `LAYER_CABINET_PREFIX` | `04_CB` |
| `LAYER_PREFIX_2D` | `M2D` |
| `LAYER_ANCHOR` | `M2D::Anchor_Frame` |

修改 3D prefix 不會自動改名既有 layer，且部分值需要重啟 Rhino；不得把它視為無風險文字設定。

### 系統檔案與並行

| 設定 | 預設值 |
|---|---|
| `REGISTRY_FILENAME` | `Project_Registry.json` |
| `REGISTRY_LOCK_FILENAME` | `Project_Registry.lock` |
| `DEBUG_LOG_FILENAME` | `cursor_LF_debug_log.txt` |
| `SYNC_INTERVAL` | `0.5` 秒 |
| `LOCK_TIMEOUT` | `20.0` 秒 |
| `STALE_LOCK_SECONDS` | `30.0` 秒 |

Registry P0 完成前，以上 timeout 不代表 lock／replace 已達安全規格。

### 其他設定

- 2D layer 與顏色：門窗、櫃體、Defpoints、Extract。
- Tag Block definitions：Index、Height、Finish、Door/Window、Item。
- `WHITE_LIST`：TagTrigger／Checker 不覆寫的 UserText key。
- Layout 命名：`LAYOUT_NAME_SEPARATOR`、copy suffix、baseline marker。
- Ceiling／mirror keywords 與 `INVERT_Y`。

完整實際值以 `_LoopFlow_Config.py` 為準；文件改動時必須核對程式，不建立第二份可執行設定。

## 不屬於使用者設定的契約

下列內容應集中於所屬 module 並測試，但不因「硬編碼」就移至 config：

- Rhino command 字串與 API type mask。
- 完整 layer path 組裝規則與 legacy alias。
- Registry schema、pending 檔案命名與 result stage。
- UUID／UserText canonical key。
- Tag Block 內部欄位與幾何容差。

## Build 與 Release

- `build.ps1` 將 `releases/LoopFlow/` 打包成 ZIP。
- 現有穩定資產為 `releases/LoopFlow_v1.0.0.zip`。
- 2.0 build 最終需產生 payload、ZIP、檔案清單與 SHA-256，並驗證 RHC／shared resources。
- RHP 需等 package 穩定後重新做 Rhino 8 spike；不可沿用舊的攤平腳本假設。

## 文件與程式註解規則

- 維護 SSOT：本文件、`_LoopFlow_使用說明.md`、`_LoopFlow_重構計畫.md`、`architecture/PROGRESS.md`。
- 任務切分、依賴順序與雙機安全停點：`architecture/DEVELOPMENT_ROADMAP.md`。
- Dictionary、命名與 schema SSOT：`_LoopFlow_命名與資料契約.md`。
- Nexus／Dictionary 的 1.0 靜態盤點、衝突與待決定選項：`architecture/NEXUS_DICTIONARY_DECISION_MENU.md`。
- 內部維護文件與新增／修改註解使用繁體中文。
- 模組整體目的、流程、設定、契約、副作用與回復方式寫入 docs。
- 程式只保留必要 docstring、難以由程式本身看出的原因、API 限制與安全 invariant。
- 現有 23 支 Python 都有大型標頭，且有大量英文註解；隨 feature 重構逐批遷移，禁止一次大量翻譯造成無法審查的 diff。
- 公開英文 README／Guide 為對外翻譯，不是 AI 維護指令；功能事實須與繁中版本一致。

## 基準檢查

目前 repo 沒有 CI／pytest 設定。每批至少執行：

- Python 靜態語法解析。
- RHC XML 解析。
- ZIP 完整性與 release 檔案清單（涉及 build 時）。
- 對應 golden workflow 的 Rhino 8 實機測試。
- `git diff --check`、秘密與非預期產物檢查。

未在 Rhino 執行的項目不得寫成實機通過。
