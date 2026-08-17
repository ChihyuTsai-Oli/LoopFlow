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

LF_Anchor_Frame
_-ScriptEditor _Run "E:\_GitHub\LoopFlow\wip\src\entrypoints\LF_Anchor_Frame.py"
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
| 註冊 View | `LF_Anchor_Frame` | — |

Grab：在 **Layout** 先選 Tag 圖塊，再在目標 Detail 內點一下進入模型空間，然後選來源（剖面 2D 線、3D 物件或家具圖塊）。Height／Finish 綁物件 `_07_UUID`；家具 Item 綁 Block 名稱（`FF-01__Chair-1`）。Esc、點在 Detail 外、鎖定、`TAG_DW`、Laser／Index／圖框圖塊都不寫入。結束後回到 Layout。不填 Infuser 顯示欄。來源沒有 UUID 時不猜測對應的 3D 物件。

註冊 View：在 **2D 模型空間**框選剖面物件與恰好一個 Text Dot，再輸入外擴距離（預設 50）。寫入 `lf_view_id`、Clipping Plane 物件 ID 與固定 2D↔3D transform。名稱對不到或對到兩個以上 Clipping Plane、沒有 Text Dot、沒有幾何、Esc，都不寫入。不進 Nexus。本批不射線。

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
