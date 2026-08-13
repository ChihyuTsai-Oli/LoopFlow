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

## 重構工作檔根目錄

- 本機環境變數：`LOOPFLOW_WORKFILES_ROOT`
- 公司電腦：`D:\Dropbox\LoopFlow_Series\Workfiles\WIP_loopflow`
- 採用 Dictionary：`%LOOPFLOW_WORKFILES_ROOT%\LoopFlow_Dictionary.xlsx`
- 交換 JSON：`%LOOPFLOW_WORKFILES_ROOT%\exchange\`

重構採用 Dropbox 的中文欄位／中英雙語 layer Dictionary。`releases/LoopFlow/LoopFlow_Dictionary.xlsx` 的英文版本保留為 1.x 參考，不作 2.0 的即時工作來源。程式只讀環境變數，不寫死公司路徑；環境變數缺少或目錄不存在時，應停止相關操作並顯示設定方式。

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
    architecture/LOOPFLOW_DATA_ECOSYSTEM.md
    architecture/LOOPFLOW_DATA_ECOSYSTEM_DECISIONS.md
    architecture/LOOPFLOW_WORKFLOW_SIMULATION.md       # 現行流程草案
    architecture/LOOPFLOW_WORKFLOW_SIMULATION.html     # 衍生檔，由 tools 產生，勿手改
    architecture/NEXUS_DICTIONARY_DECISION_MENU.md
    architecture/DEVELOPMENT_ROADMAP.md
    architecture/PROGRESS.md
    architecture/ref/    # 已合併的原始評閱與歷史參考，不是現行 SSOT
    loopflow_1.0_workflow_YT.txt  # 1.0 逐步操作說明；操作邏輯參考，不是 2.0 流程契約
    tag_block_text/       # 從實際 Rhino Block instance 擷取的 9 Tag＋1 圖框文字證據
  tools/
    build_workflow_html.py  # 預設由 v2 流程 md 產生 v2 html；`--check` 可驗證是否過期
    擷取tag_block文字.py    # Rhino 內唯讀擷取 Block／巢狀 Block 原始文字公式
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

目前預計的**核心主鏈**使用者入口如下；共用模組 `_LoopFlow_Config.py`、`_LF_Debug.py`、`_LF_NamingRules.py`、`_LF_Registry.py` 不建立按鈕：

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
LF_Sync_Worksession.py
```

三個 2D Generator 是彼此獨立、也不依賴 Cabinet Suite 的工具；其重構工作軌啟動時再建立下列測試入口，1.x 版本在此之前可繼續使用：

```text
LF_2D_Cabinet_Gen.py
LF_2D_Shelf_Gap.py
LF_2D_DW_Gen.py
```

`LF_Cabinet_Suite.py` 與 BOM 是延後工作軌，不列入核心主鏈測試按鈕。它是否必須包含在 2.0 首次正式安裝包，仍待 ED-18 裁決：

```text
LF_Cabinet_Suite.py
```

這是開發期暫定清單，不是凍結的公開契約。功能增減、入口檔名或 repo 內路徑改變時，應同步更新本節與測試工具列。2.0 正式版會封裝為完整安裝檔／可安裝套件，不要求使用者逐一建立按鈕或管理 Python 路徑；RC 才在隔離位置驗證該安裝成果。封裝技術到發佈階段再決定，不預先鎖定 RHI、Package Manager 或獨立安裝器。

### Rhino 內建 Section 按鈕

目前工具列中複製排列的 Section 按鈕只包含簡單 Rhino Macro，例如 `! _ClippingSections`。2.0 保留這種快捷入口，但它們不列入 Python entrypoint 清單：

```text
! _ClippingSections
! _ClippingDrawings
! _ClearClippingSections
! _EditClippingDrawings
! _UpdateClippingDrawings
```

正式安裝包部署 LoopFlow 自有工具列資源；Macro 仍由 Rhino 8 內建指令執行。不得複製 Rhino Section 程式本體，也不以 Rhino 預設 Macro／bitmap GUID 作長期必要相依。安裝與升級只管理 LoopFlow 工具列，不覆蓋使用者完整 workspace。圖示是否自製或引用可驗證的原生資源，與 RUI／RHC／其他安裝技術一起延後決定。

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
| Cabinet Suite | 延後的櫃體建模與 BOM 工作軌；不向主鏈注入 `_CB.*` |
| 2D Generator 系列 | 彼此獨立的櫃體、層板與門窗圖面幾何工具 |
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
- Block definitions：Index、Height、Finish、Item、Door/Window 與 title frame。現行 `TAG_DW` 已改純手動，但 1.x Config／Infuser 仍把它列為資料 Tag；2.0 不承接這個衝突。
- `WHITE_LIST`：TagTrigger／Checker 不覆寫的 UserText key。
- Layout 命名：`LAYOUT_NAME_SEPARATOR`、copy suffix、baseline marker。
- Ceiling／mirror keywords 與 `INVERT_Y`。

完整實際值以 `_LoopFlow_Config.py` 為準；文件改動時必須核對程式，不建立第二份可執行設定。

上表描述 1.x 現況。2.0 的 Dictionary resolver 改由 `LOOPFLOW_WORKFILES_ROOT` 加固定檔名取得；Rhino 文件所在資料夾不再是 Dictionary 的主要搜尋位置。

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
- 2.0 build 最終需產生完整可安裝套件、檔案清單、版本 manifest 與 checksum，並驗證所有 shared resources；實際封裝技術於發佈階段評估。
- RHP 需等 package 穩定後重新做 Rhino 8 spike；不可沿用舊的攤平腳本假設。

## 文件與程式註解規則

- 維護 SSOT：本文件、`_LoopFlow_使用說明.md`、`_LoopFlow_重構計畫.md`、`architecture/PROGRESS.md`。
- 任務切分、依賴順序與雙機安全停點：`architecture/DEVELOPMENT_ROADMAP.md`。
- Dictionary、命名與 schema SSOT：`_LoopFlow_命名與資料契約.md`。
- 完整工作鏈、資料實體、真相邊界與 23 支現行程式意圖：`architecture/LOOPFLOW_DATA_ECOSYSTEM.md`。
- 依 1.0 實際操作、Tag／圖框參數與現行程式複核的目前流程：`architecture/LOOPFLOW_WORKFLOW_SIMULATION.md`；同名 `.html` 是衍生閱讀版。已過時的初版內容已刪除，不再作為追溯來源。
- 使用者可直接編輯的上位原則與實務待決事項：`architecture/LOOPFLOW_DATA_ECOSYSTEM_DECISIONS.md`。
- 已合併的原始藍圖與獨立複核：`architecture/ref/`；只供追溯，不取代整合後藍圖。
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
