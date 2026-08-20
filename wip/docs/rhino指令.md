# LoopFlow 2.0 — Rhino 指令與按鈕巨集

本文件是**開發期**目前可跑的 Rhino 指令與測試按鈕巨集的單一來源，隨開發進度同步更新。指令 ID 的正式契約在 `資料契約.md`；本文件負責「現在有哪些按鈕、巨集怎麼寫」。日後要統一調整指令名稱，先改這份，再同步契約、入口檔名與程式。

規則：

- 入口檔名即指令 ID。入口只轉交 command，不放業務邏輯。
- 巨集路徑指向這台開發機的 repo 位置；換機只改路徑，不改指令名稱。程式與契約不得寫死任何電腦的絕對路徑。
- 改程式後須**完全關掉 Rhino 再開**。
- 不要按 1.x 工具列上的同名按鈕。

## 目前可跑的指令

```text
LF_Open_Dictionary
_-ScriptEditor _Run "E:\_GitHub\LoopFlow\wip\src\entrypoints\LF_Open_Dictionary.py"

LF_Open_Dictionary_Export
_-ScriptEditor _Run "E:\_GitHub\LoopFlow\wip\src\entrypoints\LF_Open_Dictionary_Export.py"

LF_Nexus
_-ScriptEditor _Run "E:\_GitHub\LoopFlow\wip\src\entrypoints\LF_Nexus.py"

LF_Export_Type_Layers
_-ScriptEditor _Run "E:\_GitHub\LoopFlow\wip\src\entrypoints\LF_Export_Type_Layers.py"

LF_Publish_Exchange
_-ScriptEditor _Run "E:\_GitHub\LoopFlow\wip\src\entrypoints\LF_Publish_Exchange.py"

LF_Data_Viewer
_-ScriptEditor _Run "E:\_GitHub\LoopFlow\wip\src\entrypoints\LF_Data_Viewer.py"

LF_Tagger_Grab
_-ScriptEditor _Run "E:\_GitHub\LoopFlow\wip\src\entrypoints\LF_Tagger_Grab.py"

LF_Tagger_Laser
_-ScriptEditor _Run "E:\_GitHub\LoopFlow\wip\src\entrypoints\LF_Tagger_Laser.py"

LF_Tagger_Index
_-ScriptEditor _Run "E:\_GitHub\LoopFlow\wip\src\entrypoints\LF_Tagger_Index.py"

LF_Tagger_Layout_ID
_-ScriptEditor _Run "E:\_GitHub\LoopFlow\wip\src\entrypoints\LF_Tagger_Layout_ID.py"

LF_Anchor_Frame
_-ScriptEditor _Run "E:\_GitHub\LoopFlow\wip\src\entrypoints\LF_Anchor_Frame.py"

LF_Catalog
_-ScriptEditor _Run "E:\_GitHub\LoopFlow\wip\src\entrypoints\LF_Catalog.py"

LF_Infuser_Part
_-ScriptEditor _Run "E:\_GitHub\LoopFlow\wip\src\entrypoints\LF_Infuser_Part.py"

LF_Infuser_All
_-ScriptEditor _Run "E:\_GitHub\LoopFlow\wip\src\entrypoints\LF_Infuser_All.py"

LF_TAG-O
_-ScriptEditor _Run "E:\_GitHub\LoopFlow\wip\src\entrypoints\LF_TAG-O.py"

LF_Extract_CP
_-ScriptEditor _Run "E:\_GitHub\LoopFlow\wip\src\entrypoints\LF_Extract_CP.py"

LF_Duplicate_Layout
_-ScriptEditor _Run "E:\_GitHub\LoopFlow\wip\src\entrypoints\LF_Duplicate_Layout.py"

LF_D08_Migrate_Display_Keys
_-ScriptEditor _Run "E:\_GitHub\LoopFlow\wip\src\entrypoints\LF_D08_Migrate_Display_Keys.py"
```

## 按鈕配置

| 按鈕 | 左鍵 | 右鍵 |
|---|---|---|
| 字典 | `LF_Open_Dictionary`（開啟原字典） | `LF_Open_Dictionary_Export`（開啟匯出字典） |
| Nexus | `LF_Nexus`（6 項選單） | — |
| 匯出字典 | `LF_Export_Type_Layers` | — |
| 發布 | `LF_Publish_Exchange` | — |
| 檢視 | `LF_Data_Viewer` | — |
| Grab | `LF_Tagger_Grab` | — |
| Laser | `LF_Tagger_Laser` | — |
| Index | `LF_Tagger_Index` | — |
| Layout ID | `LF_Tagger_Layout_ID` | — |
| 註冊 View | `LF_Anchor_Frame` | — |
| 圖目錄 | `LF_Catalog` | — |
| Infuser Part | `LF_Infuser_Part` | — |
| Infuser All | `LF_Infuser_All` | — |
| TAG-O | `LF_TAG-O` | — |
| Extract | `LF_Extract_CP` | — |
| Duplicate Layout | `LF_Duplicate_Layout` | — |

開發期輔助（**不是產品指令**，不進正式工具列）：`LF_D08_Migrate_Display_Keys` 全檔把圖塊舊顯示欄抄到 `lf_*` 後刪舊名字。鎖定欄若寫 `x`／`X` 會抄到 `lf_00_lock_state` 後刪舊名字；提示文字只刪不抄。圖塊公式改完後跑一次即可，不必逐張刪 UserText。

Grab：在 **Layout** 先選 Tag 圖塊，再在目標 Detail 內點一下進入模型空間，然後選來源（剖面 2D 線、3D 物件或家具圖塊）。Height／Finish 綁物件 `_07_UUID`；圖 B 已清掉 UUID 時改讀 `lf_source_object_ids`（恰好一個 UUID 或一個 3D 物件才綁；兩個以上停止、不猜測）。家具 Item 綁 Block 名稱（`FF-01__Chair-1`）**以及該實例**，之後 Infuser／TAG-O 才能跟改名與刪除。Esc、點在 Detail 外、鎖定（`lf_00_lock_state=true`／`1`，或鎖定欄寫 `x`／`X`）、`TAG_DW`、Laser／Index／圖框圖塊都不寫入。結束後回到 Layout。不填 Infuser 顯示欄。來源沒有 UUID 且索引也解不出時不猜測。舊鎖定欄 `x`／`X` **家中 Rhino 8 已測（2026-08-18）**。

Laser：在 **Layout** 先選 Height／Finish 的 Laser Tag，再在目標 Detail 內點一下剖面位置。點須落在已登記的 Anchor Frame 內；用框內剖面 Hatch／Curve 中心對位（不含 Visible 背景），3D 用 Anchor Frame 寫死的 transform，不跟現況 Clipping Plane 元件，沿 Clipping Plane 法線從剖平面稍後方射出（含 Mesh／SubD 與圖塊裡的 srf／燈具／壁面設備）。同一物件只算一次，穿過兩個物件就停止，清單最多兩個。沒有框時提示請先執行 Anchor Frame。框與圖一起平移不必重跑 Anchor Frame。Esc、點在 Detail 外、鎖定（同上）、Grab／Item／`TAG_DW`／Index／圖框、0 或 ≥2 個重疊 View、沒打到、來源無 UUID，都不寫入。多個命中時讓使用者選一個，清單只顯示圖層名（有物件名稱才附上），不顯示 GUID。圖塊名不分大小寫。不填 Infuser 顯示欄。本批不接 Extract 來源索引。舊鎖定欄 `x`／`X` **家中 Rhino 8 已測（2026-08-18）**。日常不畫測試線。**選 Tag 時**命令列會出現 `DebugRay=No`，點成 Yes 才畫洋紅線（`LoopFlow::Debug_Laser`，不列印，約 20 公尺）；關 Rhino 前會記住。`Select Option ( Edit Run Open )` 是 ScriptEditor 自己的提示，不是 Laser 選項。日後裝成真正指令後，可用 `-LF_Tagger_Laser DebugRay=Yes`。

Index：在 **Layout** 選 `TAG_SECTION_DETAIL` 或 `TAG_ELEV_1`～`4`，再從可搜尋清單選全檔任一 Layout 的 Detail（顯示頁名＋Detail 名，不顯示 GUID；點選時跳頁並 zoom）。用該 Detail 模型空間中心對已登記 View 框，恰好一個才寫 `lf_target_view_id` 與所選頁名 `lf_target_layout`。Esc、鎖定（同上）、Grab／Laser／`TAG_ELEV_0`／圖框／`TAG_DW`、模型空間、沒有 Detail、0 或 ≥2 個 View、取消清單，都不寫入。不寫 Detail GUID、不寫圖號顯示欄、不寫 `lf_sheet_id`。圖塊名不分大小寫。不進 Nexus。舊鎖定欄 `x`／`X` **家中 Rhino 8 已測（2026-08-18）**。

Layout ID：跑全檔 Layout。系列第一頁寫 `**圖類別__圖號__圖名`（例如 `**IN__201__立面圖`、`**IN__A01__平面`），後面的頁只寫圖名。`//S__901__結構平面圖` 不編號但仍寫圖框，執行後保留 `//`。圖號只要尾端是數字就放行；`101.9` 下一頁為 `101.10`。核對清單確認才寫入；取消整批零寫入。Layout 起點頁名保留 `**`，接續頁為三欄無星號；圖框 `lf_drawing_no` 寫空格格式（不含 `**`／`//`），並寫 `lf_drawing_name`、`lf_sheet_id`。不寫 `lf_scale`。不寫舊欄 `DWG_NO`／`DWG_NAME`。`TAG_ELEV_0` 寫目前頁編號。未登錄 Block 勾選真正的圖框（預設全不勾）。只改圖名：改第三欄再跑。要改編號：該頁再加 `**` 再跑。圖框已就緒但缺 `**`（也沒有可寫入的 `//`）時停止，警告只顯示命名規則與 Sample。詳細命名與操作見 `工作流程.md` §9。一頁沒有圖框或有兩個圖框則跳過。不進 Nexus。**家中 Rhino 8 已測（2026-08-18）。**

註冊 View：在 **2D 模型空間**框選剖面物件與恰好一個 Text Dot，再彈出視窗輸入外擴距離（預設 50）。框畫在 `LoopFlow::Anchor_Frame`。一個剖面一個框。天花反射平面先左右鏡射再登記。寫入 `lf_view_id`、Clipping Plane 物件 ID 與固定 2D↔3D transform。Text Dot 先對完整相同的 Clipping Plane 名稱；`LF_立面` 不會對到 `LF_立面2`。名稱對不到或對到兩個以上、沒有 Text Dot、沒有幾何、Esc／取消彈窗，都不寫入。不進 Nexus。本批不射線。

圖目錄：開 Eto 面板。選獨立 Point 作為圖號（紅 `LoopFlow::Drawing_Number`）與圖名（綠 `LoopFlow::Drawing_Name`）定位點；選 Sheet 為頁序／圖號／圖名／頁名四欄，Shift 連選、Ctrl 加選或取消，反白即選取。Build 預覽後寫 `lf_catalog_sheet_id` 並在 `LoopFlow::Drawing_Text`（`#CDB38B`）產生文字，左下角對齊定位點。Refresh 只改內容，已移動的文字留在原處。成功不另彈確認窗；失敗才彈窗。「清除定位點並還原圖層」會還原選取前的圖層並刪除目錄文字。匯出 TXT 為 `圖名, 圖號`（UTF-8）。定位點綁 `sheet_id` 不綁目前圖號；空位可不綁。`LoopFlow` 與其子圖層不列印（列印寬度設為 `No Print`／`PlotWeight = -1`）。選到 Block、逐頁數量不符、同列失敗、Sheet 多於空位、metadata 過期、Esc／取消，都不寫入。missing／orphan Sheet 略過並報告。新 Layout 不會自動納入。不進 Nexus。**家中 Rhino 8 已測（2026-08-18）。**

Infuser Part：在 **Layout** 跑 `LF_Infuser_Part`，只處理**目前這一頁**的 D08 Tag（含標在 Detail 圖上的）。其他圖塊略過。Height／Finish 先對 Registry 寫高程與 Type 顯示欄（UUID 不分大小寫）；對不到再讀模型上同一 `_07_UUID` 的現況（同 UUID 多筆取最齊的）。家具若有綁定實例，讀該實例現況名稱再拆三段（改名會更新；實例刪除寫 `?`、塗紅）；Index 先用 `lf_target_layout` 對目標頁，沒有才從 View 反查，寫 `lf_sheet_code`／`lf_sheet_ref`。同一 View 也打到本頁時用其他頁；其他頁拆不出圖號再改回本頁。記下的目標頁已刪、或該頁沒有對到目標 View 的 Detail，則寫 `?`、塗紅，摘要標「目標消失」，不改對到別頁。已標斷連的 Tag 不灌回；再綁定後跑 Infuser 可恢復。不必刪 Tag。`lf_detail_no` 是手填（A、B、1），不注入。會寫 `lf_host_sheet_id` 與 `lf_last_synced_revision`。鎖定、`TAG_DW`、圖框、`TAG_ELEV_0`、比例、Detail 編號與備註都不改。未綁定畫面為 `-`，不塗警示色。沒有正式 Registry 時改讀 last-good，Height／Finish 仍可從模型讀；檔案壞掉則整批不寫。結束會彈出摘要。**公司 Rhino 8 已測注入（2026-08-19）**；與 TAG-O 來回 **家中 Rhino 8 已測（2026-08-19）**。

Infuser All：跑 `LF_Infuser_All`，規則與 Part 相同，一次處理**全檔所有 Layout 頁**。不限目前頁，模型空間也可跑。結束彈出全檔摘要。**公司 Rhino 8 已測（2026-08-19）**；與 TAG-O 來回見上。

TAG-O：跑 `LF_TAG-O`，開 **TAG-O ~ Holy Cargo ~~** 深色面板（可捲動），依 Layout 頁序列出已綁定 Tag，頁與頁之間灰線。`[正常]` 綠 `#AADC78`；`[過期]` 橘 `#EA9328`（自動欄 `!`、整顆塗橘）；`[斷連]` 紅 `#D81C1C`（自動欄 `?`、整顆塗紅）。來源不在、目標頁／Detail 消失都顯示斷連。未綁定不列出。**點選項目會反白該列、切到該 Layout 並拉近，留出圖框周圍。** 只檢查 D08 Tag 圖塊。家具改名而未注入為過期，刪除綁定實例為斷連。並列出沒被 Finish Tag 涵蓋的空間。模型空間也可跑。鎖定的 Tag 仍列出並標「鎖定」，但不改文字與顏色。門窗與 `TAG_ELEV_0` 不列入。沒掃到 Tag 時不顯示「全部正常」。只檢查與上色，不自動修復；使用者依此自行修改。斷連再綁定後跑 Infuser 可恢復，不必刪 Tag。**家中 Rhino 8 已測（2026-08-19）。**

Extract：在 **2D 模型空間**跑 `LF_Extract_CP`。勾選 Clipping Drawing 的剖面根圖層（底下有 Visible／Hatch／Curve）。根名稱以 `//` 開頭的不列入。複製到 `LoopFlow_Extract::Visible`、`::Hatch`、`::Curve_#RRGGBB`，可列印；Visible／Hatch 列印色灰 `#BEBEBE`，其餘黑。抽出線只留 Drawing 的 `lf_*`，不含 3D 的 `_01`～`_14`。寫 `lf_drawing_id`、來源 `lf_view_id`（圖層前綴與框名完整相同，`LF_立面` 不會對到 `LF_立面2`）、來源 revision 與 `lf_source_object_ids`。同一 View／同一剖面若已有抽出，選取代／新增／略過。已人工修改（`lf_provenance_state=modified`）不會被取代覆蓋。Esc／取消、Layout 頁、找不到剖面圖層、兩個框完整同名，都不寫入。來源剖面圖層鎖定狀態會還原。不進 Nexus。**公司 Rhino 8 已測（2026-08-20）。**

Duplicate Layout：跑 `LF_Duplicate_Layout`。清單選來源 Layout，輸入份數（1～100）。以 Rhino API 複製整頁（含 Detail、圖框、Tag），**不改系統剪貼簿**。新頁名保留三欄，圖名加 `_CopyN`，不加 `**`／`//`。新頁發新的 `sheet_id`／`drawing_id`／`tag_id`／`catalog_id`。除 `TAG_DW` 外，綁定與自動欄、補充說明會清掉，lock 恢復未鎖。`TAG_DW` 編號／寬／高保留。圖框比例保留，圖號／圖名先清（之後跑 Layout ID）。Esc／取消、沒有 Layout、來源沒物件，都不寫入。失敗會刪掉已建的半成品頁。再跑可再複製。不進 Nexus。**待關 Rhino 再開再測。**

左鍵／右鍵由 Rhino 按鈕設定分別填入巨集，程式不偵測滑鼠鍵。正式工具列在 G02 封裝時才建立。

## Nexus 選單（開案檢查通過才出現）

```text
1  開案檢查
2  從字典同步 Type Layers
3  登記高程框（封閉曲線）
4  登記空間框（封閉曲線，須在高程框內）
5  寫入模型 Metadata
6  檢核模型 Metadata（不寫入）
```

匯出 Type Layers 為字典與發布串接資料已離開選單，改用上表的獨立指令。

## 開發輔助（非產品指令，不進正式工具列）

```text
LF_Test_Random_M3D_Layers
_-ScriptEditor _Run "E:\_GitHub\LoopFlow\wip\src\entrypoints\LF_Test_Random_M3D_Layers.py"
```

## Rhino 內建 Section 巨集（不是 Python 入口）

```text
! _ClippingSections
! _ClippingDrawings
! _ClearClippingSections
! _EditClippingDrawings
! _UpdateClippingDrawings
```

## 預定新增

剩餘開發順序：**Sync Worksession → Document。** Extract CP **公司 Rhino 8 已測（2026-08-20）**。Duplicate Layout 已實作，待關 Rhino 再開再測。

| 指令 | 用途 | 狀態 |
|---|---|---|
| `LF_Sync_Worksession` | 監看與更新 Worksession | 已登錄 ID；尚未實作 |
| `LF_Document` | 開啟 GitHub 上的 LoopFlow 文件頁 | 已登錄 ID；尚未實作。舊名 `LF_Help` 不登錄 |

Cabinet／三支 2D 工具不屬 2.0。
