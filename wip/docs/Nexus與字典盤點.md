# LoopFlow 2.0 — Nexus／Dictionary 現況盤點

本文件只記錄 1.x 程式與實際 Dictionary 的靜態證據：欄位、producer／consumer、設定、衝突與風險。資料實體與真相邊界以 `資料生態藍圖.md` 為準；全部 `ECO-*`、`ED-*`、`ND-*` 待決與已裁決事項只在 `資料生態決策表.md` 編輯。它不是要沿用舊架構，也不代表所有現況都是正確規格。

## 盤點狀態

- 日期：2026-08-12
- 範圍：`releases/LoopFlow/Python/` 全部 23 支 Python、Dropbox 中文版 `LoopFlow_Dictionary.xlsx`、repo 英文舊版、繁中使用指南與 Dictionary 指南；另納入 9 份 Tag、1 份圖框的 Rhino Block 文字擷取與整體畫面
- 方法：逐檔閱讀、Python 靜態依賴搜尋、XLSX 結構與畫面檢查、Block UserText producer／consumer 對照
- 尚未執行：Rhino 指令端到端操作、舊專案資料抽樣、多人／雙機同時寫入測試；Block 文字與畫面已核對，不等同功能流程實機通過
- 結論：已足夠開始規格裁決；使用者確認關鍵語意前，不修改產品程式碼

## 現行資料流

```mermaid
flowchart LR
    D["Dictionary.xlsx<br/>layer defaults"] --> N["LF_Nexus<br/>合併 Dictionary、幾何與空間"]
    R["Rhino layer／geometry／boundary"] --> N
    N --> U["Object UserText"]
    U --> P["Push 3D to JSON"]
    P --> J["Project Registry.json"]
    J --> T["Tag／Infuser／Layout consumers"]
    C["Cabinet Suite"] --> U
    L["Layer UserStrings"] --> X["Layer to Dict export"]
    X --> D2["另一份 XLSX；目前須人工合併"]
```

上圖是 1.x 現況，不是 2.0 主鏈：部分欄位由 Dictionary 提供預設、部分由 Nexus 計算、部分保留物件既有值，Cabinet 另寫 `_CB.*`。核心欄位所有權須在重構前固定；`_CB.*` 已依 ED-18 從主鏈移除；Cabinet／BOM 不屬於 LoopFlow 2.0，不阻擋主鏈契約。

## 已閱讀的 23 支 Python

| 檔案 | 現行責任 | 與 Nexus／Dictionary 的關係 |
|---|---|---|
| `_LoopFlow_Config.py` | 檔名、layer、顏色、Block、時間常數 | 設定與內部契約目前混在一起 |
| `_LF_Debug.py` | debug log | 多支程式各有 fallback，路徑策略未統一 |
| `_LF_Registry.py` | JSON、lock、replace | 接收 Nexus／Push 資料；並行安全不足 |
| `_LF_NamingRules.py` | Layout 與 Tag 命名規則 | 需與 canonical 名稱、Tag identity 一起定義 |
| `LF_Nexus.py` | Dictionary、layer、UUID、space、尺寸、高程、檢查、反向匯出與 UI | 主要整合點，也是目前責任衝突最多的檔案 |
| `LF_Dictionary_Editor.py` | 尋找並開啟 Dictionary | 路徑與缺檔流程相依 |
| `LF_Data_Viewer.py` | 檢視物件 UserText | 會直接暴露新舊 schema 差異 |
| `LF_Push_3D_to_JSON.py` | 將 M3D 物件推入 Registry | 依賴 `_03_*`、`_12_UUID` 與全部 UserText |
| `LF_Sync_Worksession.py` | Worksession 事件同步 | Registry 的讀寫與生命週期 consumer |
| `LF_Tagger_Grab.py` | 以選取目標建立 Tag 關聯 | 依賴 `_12_UUID`、Tag Block 欄位 |
| `LF_Tagger_Laser.py` | 以射線目標建立 Tag 關聯 | 依賴 `_03_*`、`_04_*`、`_12_UUID` |
| `LF_Tagger_Index.py` | 建立／更新 Index Tag | 依賴 Block 名稱、鎖定與 warning 契約 |
| `LF_Tagger_Layout_ID.py` | Layout ID Tag | 依賴 Layout 與 Tag identity |
| `LF_TAG-O.py` | Tag 檢查與更新 | 讀 Registry、`_01_*`、`Space_Name` 與顏色狀態 |
| `LF_Infuser_Part.py` | Registry 資料寫入部分 Tag | 依賴 `_03_*`、`_04_*`、`_10_*`、`_11_*` |
| `LF_Infuser_All.py` | 批次 Infuser | 繼承 Part 的資料與 last-good 行為 |
| `LF_Anchor_Frame.py` | 產生圖面 anchor | 依賴 layer 與後續 Layout 流程 |
| `LF_Extract_CP.py` | 建立剖面／可見線輸出 | 依賴 layer、顏色與 Rhino 狀態 |
| `LF_Duplicate_Layout.py` | 複製 Layout | 依賴命名、Tag 與 Registry mapping |
| `LF_Cabinet_Suite.py` | 產生櫃體及 `_CB.*` | 依 ED-18 不屬於 2.0；`_CB.*` 四欄已從字典移除，1.x 現況只保留作 migration 辨識 |
| `LF_2D_DW_Gen.py` | 產生門窗 2D | 依賴 `20_DW` 特例與 2D layer |
| `LF_2D_Cabinet_Gen.py` | 產生櫃體 2D | 獨立 2D 幾何工具；不依賴 Cabinet Suite 或 `_CB.*` |
| `LF_2D_Shelf_Gap.py` | 產生層板間隙線 | 獨立 2D 幾何工具；只依使用者選取幾何、輸入與 2D layer |

## 實際 Dictionary 快照

重構採用 `%LOOPFLOW_WORKFILES_ROOT%\LoopFlow_Dictionary.xlsx`。公司電腦實際檔案為 `D:\Dropbox\LoopFlow_Series\Workfiles\WIP_loopflow\LoopFlow_Dictionary.xlsx`；repo release 內的英文版本只作比較。所選中文版的實際狀態：

- 工作表：`LoopFlow_Dictionary`
- 使用範圍：`A1:R94`
- 標題：`LoopFlow Dictionary v1.0`
- 資料列：92；`__Rhino Layer` 與 `_03_ID編號` 都沒有重複
- 欄位：18；沒有公式
- `_01`、`_05`、`_06`、`_07`、`_09`、`_11`、`_12` 與四個 `_CB` 欄目前全部留白
- 欄名採中文，例如 `_01_空間名稱`、`_02_建構狀態`、`_03_ID編號`
- `_13_備註` 原有 91 列為 `我是備註，UCCU`，依 ED-10 已於 2026-08-14 改為 `(手動輸入備註)`；`20_DW` 那列是正式操作說明，原樣保留
- 單位值實際包含 `cm`、`mm`、`m3`、`坪`、`座`、`才`、`樘`、`片`、`組`、`台`
- 沒有發現尾端空白值
- 1.x 高程基準的合法值為 `BH`、`TH`、`BC`、`CH`、`TH/BH`（`LF_Nexus.py:179`）；現行字典只用到前四種，`TH/BH` 已退場

### 現行欄位所有權（1.x 18 欄；現行字典為移除 `_CB.*`、新增 `(單位計量規則)` 後的 15 欄）

| 欄位 | 現行來源／寫入者 | 主要 consumer | 現況問題 |
|---|---|---|---|
| `__Rhino Layer` | Dictionary；Layer to Dict 反向匯出 | Nexus、layer 建立、Push 範圍 | 選定版本為中英雙語 path；同時是顯示 path 與主鍵，`M3D::` 前綴由程式另加 |
| `_01_空間名稱` | Nexus 由 boundary 計算 | TAG-O 空間覆蓋 | boundary 實際用另一個 key `Space_Name`；重疊與樓層未定義 |
| `_02_建構狀態` | Dictionary 預設；物件既有值受保護 | 無已知行為 consumer | 重設與未來報表規則不明 |
| `_03_ID編號` | Dictionary | Push、Laser、Infuser、Tag | 92 筆皆為類別碼-序號；Infuser 以第一個 `-` 拆分 |
| `_04_ID名稱` | Dictionary | Laser、Infuser、Nexus 輔助 UI | 92 筆中並非唯一，只能作顯示名稱 |
| `_05_寬度W` | Nexus bbox 計算 | 無已知行為 consumer | 世界座標與物件局部方向未定義；儲存為字串 |
| `_06_深度D` | Nexus bbox 計算 | 無已知行為 consumer | 同上 |
| `_07_高度H` | Nexus bbox 計算 | 無已知行為 consumer | 同上 |
| `_08_單位` | Dictionary | 無已知行為 consumer | 是工程估算單位，不是 Rhino 模型單位 |
| `_09_實作數量` | 無 producer，只在缺值時補 `-` | 無已知行為 consumer | 指南稱 Nexus 計算，但程式不存在 |
| `_10_高程基準` | Dictionary | Nexus、Infuser | 同時承擔幾何規則與顯示標籤；`CH` 取底面，非 Block 的 `BC` 靜默退回底面 |
| `_11_高程計算` | Nexus | Infuser | 是帶 `+`／`±0`／`TH / BH` 的顯示字串，不是單純數值 |
| `_12_UUID` | Nexus | Push、Grab、Laser、Infuser、TAG-O | 重複時原件與複本都可能換號並切斷 Tag；需 mapping／rollback |
| `_13_備註` | Dictionary 預設；物件既有值受保護 | 無已知行為 consumer | 原為 91 列 `我是備註，UCCU`；依 ED-10 已於 2026-08-14 改為提示字串 `(手動輸入備註)`，`20_DW` 的真操作說明保留 |
| `_CB.01`～`_CB.04` | Cabinet；Nexus 條件保留或清為 `-` | 無已知行為 consumer | **已於 2026-08-14 從字典移除**（ED-18）；僅作舊專案 migration 辨識 |

完整 producer／consumer、非 Dictionary key 與無 consumer 項目，以整合後的 `資料生態藍圖.md` 為準。

## 設定盤點

### 目前 `_LoopFlow_Config.py` 的全部設定群

| 設定群 | 名稱 | 2.0 應有位置 |
|---|---|---|
| Dictionary 檔案 | `DICTIONARY_FILENAME_XLSX` | 專案設定；需決定是否允許改名 |
| Dictionary schema | `DICTIONARY_KEY_COLUMN`、`DICTIONARY_SKIPROWS` | 版本化內部契約，不應當一般偏好設定 |
| 3D taxonomy | `LAYER_PREFIX_3D`、`LAYER_DATA_SUFFIX`、`LAYER_SPACE_BOUNDARIES`、`LAYER_LEVEL_FFL`、`LAYER_LEVEL_FL`、`LAYER_DW_PLAN`、`LAYER_CABINET_PREFIX`、`LAYER_CABINET_NAME` | layer contract；不可只改一個字串期待自動遷移 |
| 2D／Extract taxonomy | `LAYER_PREFIX_2D`、`LAYER_EXTRACT_ROOT`、`LAYER_EXTRACT_VISIBLE`、`LAYER_EXTRACT_HATCH`、`LAYER_ANCHOR_FRAME`、`LAYER_ANCHOR` | layer contract |
| 2D layer／顏色 | `LAYER_2D_DW_*`、`COLOR_2D_DW_*`、`LAYER_2D_FURN_*`、`COLOR_2D_FURN_*`、`LAYER_2D_DEFPOINTS`、`COLOR_2D_DEFPOINTS` | layer contract 與可調顯示偏好需分開 |
| 欄位覆寫 | `WHITE_LIST` | schema 欄位所有權，不是使用者自由設定 |
| 系統檔名 | `REGISTRY_FILENAME`、`REGISTRY_LOCK_FILENAME`、`DEBUG_LOG_FILENAME` | path／storage contract；log 名可為進階設定 |
| Tag／圖框 Block | `INDEX_BLOCKS`、`HEIGHT_BLOCKS`、`FINISH_BLOCKS`、`DW_BLOCKS`、`ITEM_BLOCKS`；另有 `Sample_Frame` | Tag／title-frame schema 與資產 manifest；`TAG_DW` 已確認純手動，1.x 清單屬歷史衝突 |
| 系統顏色 | `COLOR_LAYER_MAP`、`COLOR_DATA_LAYER`、`COLOR_EXTRACT_VISIBLE`、`COLOR_EXTRACT_HATCH`、`COLOR_WARNING`、`COLOR_BROKEN` | layer 顯示與狀態顯示分開；warning 不可只靠顏色辨識 |
| Layout 規則 | `LAYOUT_NAME_SEPARATOR`、`LAYOUT_COPY_SUFFIX`、`LAYOUT_BASELINE_MARK`、`CEILING_KEYWORDS`、`MIRROR_KEYWORDS`、`INVERT_Y` | naming／layout contract；顯示偏好另分 |
| 並行／事件 | `SYNC_INTERVAL`、`LOCK_TIMEOUT`、`STALE_LOCK_SECONDS` | 系統內部預設與進階設定；安全機制不能只靠 timeout |

### 散落在 config 外的隱性設定

- 專案目錄的 `NamingRules_Config.json` 另行控制 separator、baseline、圖號／REF_ID 格式與 prefix pattern。
- Space 預設值 `EXT`、boundary 命中採「第一個」與 bottom-center 取樣點。
- 高程 slab 關鍵字、`200.0`、`2000.0`、`50.0`、`0.01`、`+1.0` 等容差與補正值。
- 尺寸小數一位、UUID4 uppercase、缺值 sentinel `-`。
- Registry fallback timeout 為 `8 / 120` 秒，與 config 的 `20 / 30` 秒衝突。
- Cabinet 自行 fallback `04_CB`、多組舊 `_CB` aliases、幾何尺寸與 Windows Python site-packages bridge。
- Tag 的 `Source_UUID`、`NAME_PARSED`、`.Auto_*`、`.Target_DV_ID`、`attr_*`、`Category`、`REF_ID`、`DWG_*` 等 Block 欄位。
- 正式 8 種可鎖 Block 共用 `attr_Lock_不更新>寫入x或X`，所以現行四支程式都找得到；但偵測條件散落，且只有單一 `x`／`X` 生效。鎖定同時擋 Infuser 與 Grab／Laser／Index 重新綁定。
- `LF_Cabinet_Suite.py` 的最終錯誤訊息仍寫死 `C:\_RH_Tools\cursor_LF_debug_log.txt`。

以上都不能在搬檔時原樣散落到新版；需歸入 schema、feature 規則或真正可調的 setting。

## 已確認的衝突與風險

| ID | 衝突／風險 | 影響 |
|---|---|---|
| CF-01 | repo release 是英文 Dictionary，Dropbox 另有同檔名中文版本；重構已指定 Dropbox 中文版 | resolver 若仍從 repo 或 Rhino 文件資料夾找檔，會讀到錯誤版本 |
| CF-02 | 程式常用 `_01_` 等 prefix 找第一欄，不依賴完整欄名 | 同 prefix 多欄時會靜默選錯；改字尾看似成功卻無 schema 保證 |
| CF-03 | 指南稱 layer 重複列會略過；程式 dict mapping 實際是後列覆蓋前列 | 資料錯誤不會被清楚阻擋 |
| CF-04 | 過往指南曾稱 `_09_Quantity` 由 Nexus 計算，但程式沒有 producer；繁中／英文指南已於 2026-08-13 修正 | 2.0 若要新增估算功能，仍需另定單位與幾何規則 |
| CF-05 | 過往指南曾把 `_11` 說成 cm 數字，但程式寫入顯示字串；繁中／英文指南已於 2026-08-13 修正 | 2.0 schema 仍須分開可計算數值與顯示格式 |
| CF-06 | 指南沒列 `BC`，實際 XLSX 與程式使用；`CH` 又沒有獨立算法 | 高程結果可能語意錯誤 |
| CF-07 | 中文 Dictionary 與 repo 英文 Dictionary 的單位、layer path、備註與欄名不同 | 兩者不可混用或依同檔名推定 schema |
| CF-08 | `_01_*` 與 boundary 的 `Space_Name` 是兩套 key | 空間名稱來源與更新責任不清楚 |
| CF-09 | Space 只看 bottom-center XY 且取第一個 boundary | 重疊空間、多樓層、跨界物件結果不穩定 |
| CF-10 | 一般幾何以 World bbox 算 W／D／H；Block 使用另一套算法 | 旋轉後的同一物件可能得到不同尺寸 |
| CF-11 | 高程包含單位不明的 magic numbers 與 layer／名稱推測 | 不同模型單位或建模方式會產生錯值 |
| CF-12 | UUID checker 掃描全模型，但 Push／TagTrigger 又只處理特定 scope | 非 M3D 物件可能使 M3D UUID 被重建 |
| CF-13 | Push 註解稱物件必須有 `_03_*`；實際缺欄仍可能 Push，只有值為 `-` 才跳過 | Registry 收錄範圍與使用者預期不同 |
| CF-14 | Push 以 UUID 建 dict；若沒先 TagTrigger，重複 UUID 會後者覆蓋前者 | 可能無警告遺失物件資料 |
| CF-15 | Registry lock 是先檢查再建立，非排他建立；replace fallback 會先刪目標 | 雙機或多程序可能覆寫、短暫失去 last-good |
| CF-16 | Config 說可調，但 import／reload 行為不一致；Registry fallback 值也漂移 | 修改後是否生效不可預測 |
| CF-17 | `Layer to Dict` 讀 layer UserStrings，不是指南所稱 object UserText | 反向同步名稱容易造成錯誤期待 |
| CF-18 | 反向匯出使用 `[NEW]`、`[DELETED]`、`[MODIFIED]`、`[EXCLUDED]` 混入主鍵 | 主鍵同時承擔狀態顯示，不利機器驗證 |
| CF-19 | `_02`、`_09`、`_13` 以 prefix 保護，只驗存在或沿用物件值 | Dictionary 更新後無明確的繼承、覆寫、重設方式 |
| CF-20 | 中文版 `_13` 曾有 91 列為 `我是備註，UCCU` | **已處理**：2026-08-14 改為提示字串 `(手動輸入備註)`，不再是誤留的測試字串；`_13` 屬 WHITE_LIST，只寫入尚未填寫的物件 |
| CF-21 | Cabinet 產物可在 current layer，BOM 更新卻只處理 `04_CB`；Nexus 也靠 layer 判定 `_CB` | **已消解**：`_CB.*` 四欄已從字典移除、Cabinet／BOM 不屬 2.0，Nexus 不再有依 layer 清空製作資料的分支 |
| CF-22 | Infuser 把 `_03` 第一個 `-` 拆成兩個 Tag 值 | 一般 ID 若包含連字號會被誤解 |
| CF-23 | Tag lock、warning color 與缺值規則分散；正式 key 目前可共用，但非 `x/X` 值會靜默未鎖，locked Tag 又停止 health／顏色更新 | 重構單一 Tagger 時可能破壞其他 Tag 流程或讓使用者誤以為已保護 |
| CF-24 | Dictionary 沒有可執行的 `schema_version`、型別、允許值與 strict validator | 目前只能到執行中才發現格式問題 |
| CF-25 | `TAG_DW` 已改純手動且沒有 lock，仍在 `DW_BLOCKS`；Infuser 會把人工編號覆寫為 `?` | 1.x 全量同步可能破壞門窗編號；2.0 必須以 manual binding mode 排除 |
| CF-26 | `TAG_ITEM` 的 `FF-01__Chair-1` 來自 Block 名稱，不在 Dictionary 12 個類別碼內 | 同一 Tag 顯示欄有兩套未協調的編碼來源 |
| CF-27 | Layout ID 把所有未分類 Block 當圖框；`03-A3 Scale` 又把排序、圖幅與欄位語意混在 key | 未知 Block 可能被誤寫；圖幅變更可能迫使資料 key 改名 |

## 待決事項交接

原本位於本檔的 ND-01～ND-27 已完整移到 `資料生態決策表.md` 的「Nexus／Dictionary 細項決策」，包含選項、建議、已延後項目與回寫規則。之後：

1. 本檔只在發現新的 1.x 證據、欄位、設定、衝突或風險時更新。
2. 所有使用者答案與 AI 建議只更新 `資料生態決策表.md`。
3. 已確認的 canonical 結果再回寫 `_LoopFlow_命名與資料契約.md`。
4. 實作任務與前置順序只更新 `開發任務與路徑.md`。

不改變業務語意的安全要求（schema version、strict validator、Registry 原子發布、ID mapping／rollback、Rhino 狀態復原等）已由 `資料生態藍圖.md` 與 `_LoopFlow_重構計畫.md` 管理，不在此重複建立另一份實作清單。
