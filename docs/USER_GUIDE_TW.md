# LoopFlow 使用說明

> 所有 LoopFlow 指令皆在 Rhino 8 (CPython 3.9) 環境中執行。
> 帶有底線前綴（`_`）的 .py 為系統模組，不得直接執行或修改。

最後更新：2026-04-22

---

## 目錄

1. [主工作流程](#主工作流程)
2. [獨立輔助指令](#獨立輔助指令)
3. [設定檔與系統模組](#設定檔與系統模組)

---

## 主工作流程

<img src="./images/guide/USER_GUIDE.svg" alt="LoopFlow Workflow Diagram" width="100%">

以下指令在整個設計流程中有順序依賴關係，需依序執行。

```
LF_Nexus (建圖層 / 標記3D)
  → LF_Cabinet_Suite (建立系統櫃)
  → LF_Push_3D_to_JSON (推送至資料庫)
  → [Rhino Section Tools] + LF_Anchor_Frame (生成2D圖面)
  → LF_Tagger_Layout_ID (命名圖號)
  → LF_Tagger_Laser / LF_Tagger_Grab / LF_Tagger_Index (綁定Tag)
  → LF_Infuser_Part / LF_Infuser_All (寫入Tag資料)
```

---

### LF_Nexus

資料中樞，內含以下 5 個子指令：

| 子指令 | 說明 |
|---|---|
| **Dict. to Layer** | 根據字典 Excel，在 Rhino 中生成對應圖層 |
| **SpaceBoundary** | 選取封閉線段，定義空間名稱資料 |
| **TagTrigger** | 根據字典，將資料寫入 M3D 圖層的所有 3D 模型中，不論圖層狀態及物件狀態（隱藏、鎖定） |
| **TagChecker** | 若 3D 模型的資料有誤或不齊全，跳出警告。重新執行 TagTrigger 即可修正 |
| **Layer to Dict.** | 將 Rhino 圖層逆向轉出為 Excel（LoopFlow_Dictionary_Export.xlsx），作為更新原字典的依據。建模過程一定會對圖層進行編輯，逆向匯出後會有兩份 Excel，可依個人習慣手動更新字典 |

---

### LF_Cabinet_Suite

系統櫃生成器，共 30 種模型組合，包含櫃體、門片、層板，以及 BOM 計算尺寸。

BOM Update 支援兩種資料寫入模式：

1. **由 LF_Cabinet_Suite 生成模型** — 自動寫入尺寸資料（模型可在任意圖層）
2. **手動建立模型** — 透過 BOM Update 按鈕寫入尺寸資料（模型必須在 `M3D::04_CB` 圖層中）

BOM Update 只會針對櫃體圖層（`M3D::04_CB`）的物件寫入資料，不在此圖層中的物件不會被寫入。因此，執行 BOM Update 時，可以放心全選所有物件。

> **注意**：LF_Cabinet_Suite 生成的模型，板材間有 1mm 空隙，這是為 Render 效果而設。BOM 寫入的尺寸資料會自動補償此空隙。

---

### LF_Push_3D_to_JSON

將 3D 模型的資料推送至 `Project_Registry.json`（在 .3dm 同目錄生成）。後續所有 2D 系列指令都從此檔讀取資料。

> **重要**：3D 模型有任何更新後，必須重新執行此指令，確保 2D/3D 資料保持一致。

此指令也會在 TagTrigger 執行完畢後自動詢問是否推送。若在 Dropbox 環境作業，可能因讀取速度導致第一次推送失敗；稍待幾秒後會出現詢問視窗，再推送一次通常即可成功。

---

### [ Rhino 8 Section Tools ]（Rhino 內建）

以下為 Rhino 8 內建工具，非 LoopFlow 指令。執行後會生成 2D 剖面圖面，供後續 LoopFlow 流程使用：

- Create clipping sections
- Create clipping section drawings
- Clear clipping sections
- Edit clipping drawings
- Update clipping drawings

---

### LF_Anchor_Frame

根據選取的 2D 圖面生成外框，作為後續 Tagger 系列指令的錨點。

> **此框務必保留，不可刪除。**
> 概念上，Anchor Frame 是一個「標靶」，Tagger 系列指令會瞄準這個標靶發射。若需移動 2D 圖面位置，Anchor Frame 必須一起移動。

---

### LF_Tagger_Layout_ID

自動命名 Layout 圖號並寫入圖框。

指令列提供以下選項：

- **Rule** — 預設編號系統說明
- **CreateTemplate** — 產生 `NamingRules_Config.json` 至 .3dm 目錄，編輯後即可自訂編號邏輯，重新執行指令即生效

> CreateTemplate 的編號自由度可能仍有不足，歡迎提供建議。

---

### LF_Tagger_Laser / LF_Tagger_Grab

將材料、傢俱、門窗的 Tag Block 與 2D 圖面的資料綁定，後續由 Infuser 寫入。

- **Laser** — 雷射定位模式（適用剖面 DV）
- **Grab** — 點選拾取模式

> **Tag Block 防覆寫機制**：手動鎖定的 Tag Block，後續執行 Infuser 時不會覆寫其資料（由自動改為手動）。

---

### LF_Tagger_Index

將立面、剖面的 Tag Block（索引標籤）與 Layout Detail View 的資料綁定，後續由 Infuser 寫入。

> 同樣具備防覆寫機制。

---

### LF_Infuser_Part / LF_Infuser_All

針對 Tag Block 寫入資料。Tag Block 有以下三種顯示狀態：

| 顏色 | 狀態 | 說明 |
|---|---|---|
| 紫色 | 正確綁定 | 資料已成功寫入 |
| 橘色 | 未綁定 | 尚未執行 Tagger 綁定 |
| 紅色 | 綁定後斷連 | 已綁定的 3D 物件或 DV 被刪除 |

- **Infuser_Part** — 只針對目前 Layout 的 Tag Block 寫入
- **Infuser_All** — 對所有 Layout 的 Tag Block 一次寫入

---

## 獨立輔助指令

以下指令可獨立使用，不依賴主工作流程的執行順序。

---

### LF_2D_DW_Gen

快速生成基本型門窗：8 種門樣式、3 種窗樣式。

### LF_2D_Cabinet_Gen

一鍵生成 2D 櫃體圖例：高櫃、矮櫃、衣櫃。

### LF_2D_Shelf_Gap

快速生成等距隔間。

### LF_Sync_Worksession

多人協同作業與自動更新。

### LF_Dictionary_Editor

快速開啟字典 Excel。

> .3dm 與 .xlsx 必須存放在同一目錄。
>
> 字典的欄位說明、撰寫規則及完整資料表，請參閱 [`Dictionary_GUIDE_TW.md`](./Dictionary_GUIDE_TW.md)。

### LF_Data_Viewer

快速檢視 3D 模型身上的 UserText 資料。

### LF_Extract_CP

將 Section Tools 生成的 2D 圖面，依照顏色萃取至新圖層，方便選取及替換至目標圖層。

> **注意**：萃取出來的 2D 線若需移動至不同位置，Anchor Frame 外框必須一起移動，後續 Tagger 指令需要根據此框錨定目標。

### LF_Duplicate_Layout

將選取的 Layout 一次複製多個。

### LF_TAG-O

檢視整個檔案中所有 Tag Block 的狀態（綁定 / 未綁定 / 斷連）。

---

## 設定檔與系統模組

### `_LoopFlow_Config.py` — 全域設定中心（可編輯）

集中管理所有可客製化的常數，包含圖層命名、顏色、檔名、命名規則等。改完後在 Rhino 重新執行對應腳本即可生效，不需重啟。

### 系統模組（不得修改）

| 檔案 | 說明 |
|---|---|
| `_LF_Debug.py` | 例外記錄器，將錯誤寫入 `cursor_LF_debug_log.txt` |
| `_LF_NamingRules.py` | 圖面命名規則管理器，透過 `NamingRules_Config.json` 間接調整，不改本檔 |
| `_LF_Registry.py` | `Project_Registry.json` 讀寫橋接，含 lock 防寫衝突機制 |
