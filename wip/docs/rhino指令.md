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

Grab：在 **Layout** 先選 Tag 圖塊，再在目標 Detail 內點一下進入模型空間，然後選來源（剖面 2D 線、3D 物件或家具圖塊）。Height／Finish 綁物件 `_07_UUID`；家具 Item 綁 Block 名稱（`FF-01__Chair-1`）。Esc、點在 Detail 外、鎖定、`TAG_DW`、Laser／Index／圖框圖塊都不寫入。結束後回到 Layout。不填 Infuser 顯示欄。來源沒有 UUID 時不猜測對應的 3D 物件。

Laser：在 **Layout** 先選 Height／Finish 的 Laser Tag，再在目標 Detail 內點一下剖面位置。用該點所在 View 框上已寫死的 `lf_view_transform` 射出 3D 射線，打到帶 `_07_UUID` 的物件後寫 `lf_source_object_id`。不靠名稱／bbox 重算。Esc、點在 Detail 外、鎖定、Grab／Item／`TAG_DW`／Index／圖框、0 或 ≥2 個重疊 View、沒打到、來源無 UUID，都不寫入。多個近距離命中時讓使用者選一個，清單只顯示圖層名（有物件名稱才附上），不顯示 GUID。圖塊名不分大小寫。不填 Infuser 顯示欄。本批不接 Extract 來源索引。

Index：在 **Layout** 選 `TAG_SECTION_DETAIL` 或 `TAG_ELEV_1`～`4`，再從可搜尋清單選全檔任一 Layout 的 Detail（顯示頁名＋Detail 名，不顯示 GUID；點選時跳頁並 zoom）。用該 Detail 模型空間中心對已登記 View 框，恰好一個才寫 `lf_target_view_id`。Esc、鎖定、Grab／Laser／`TAG_ELEV_0`／圖框／`TAG_DW`、模型空間、沒有 Detail、0 或 ≥2 個 View、取消清單，都不寫入。不寫 Detail GUID、不寫圖號顯示欄、不寫 `lf_sheet_id`。圖塊名不分大小寫。不進 Nexus。

Layout ID：跑全檔 Layout。系列第一頁寫 `**圖類別__圖號__圖名`（例如 `**IN__201__立面圖`、`**IN__A01__平面`），後面的頁只寫圖名。`//S__901__結構平面圖` 不編號但仍寫圖框，執行後保留 `//`。圖號只要尾端是數字就放行；`101.9` 下一頁為 `101.10`。核對清單確認才寫入；取消整批零寫入。Layout 起點頁名保留 `**`，接續頁為三欄無星號；圖框 `lf_drawing_no` 寫空格格式（不含 `**`／`//`），並寫 `lf_drawing_name`、`lf_sheet_id`。不寫 `lf_scale`。在 D08 之前一併寫舊欄 `DWG_NO`／`DWG_NAME`。`TAG_ELEV_0` 寫目前頁編號。未登錄 Block 勾選真正的圖框（預設全不勾）。只改圖名：改第三欄再跑。要改編號：該頁再加 `**` 再跑。圖框已就緒但缺 `**`（也沒有可寫入的 `//`）時停止，警告只顯示命名規則與 Sample。詳細命名與操作見 `工作流程.md` §9。一頁沒有圖框或有兩個圖框則跳過。不進 Nexus。**家中 Rhino 8 已測（2026-08-18）。**

註冊 View：在 **2D 模型空間**框選剖面物件與恰好一個 Text Dot，再輸入外擴距離（預設 50）。框畫在 `LoopFlow::Anchor_Frame`。寫入 `lf_view_id`、Clipping Plane 物件 ID 與固定 2D↔3D transform。名稱對不到或對到兩個以上 Clipping Plane、沒有 Text Dot、沒有幾何、Esc，都不寫入。不進 Nexus。本批不射線。

圖目錄：開 Eto 面板。選獨立 Point 作為圖號（紅 `LoopFlow::Drawing_Number`）與圖名（綠 `LoopFlow::Drawing_Name`）定位點，再勾選要列入的 Sheet，Build 預覽後寫 `lf_catalog_sheet_id` 並產生文字。Refresh 不改綁定，只依 Sheet metadata 重建文字。匯出 TXT 為 `圖名, 圖號`（UTF-8）。定位點綁 `sheet_id` 不綁目前圖號；空位可不綁。選到 Block、逐頁數量不符、同列失敗、Sheet 多於空位、metadata 過期、Esc／取消，都不寫入。missing／orphan Sheet 略過並報告。新 Layout 不會自動納入。不進 Nexus。**待家中 Rhino 8 實機。**

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

| 指令 | 用途 | 前置條件 |
|---|---|---|
| `LF_Help` | 開啟 GitHub 說明頁，分中／英文版 | GitHub 說明頁尚未建立。**頁面建好後才實作**入口與按鈕，本階段不登錄為可跑指令 |

Tagger／Infuser／Extract／Layout／Worksession 等其餘指令已在 `資料契約.md` 登錄 ID，但 2.0 尚未實作；按了只會回報尚未實作。它們進入可跑狀態時再列入本文件上方清單。
