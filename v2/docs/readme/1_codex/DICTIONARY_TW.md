# LoopFlow 2.0 Excel Dictionary 使用說明

Dictionary 是 LoopFlow 的 **Type Catalog**。它集中管理專案中各類建材、設備與物件 Type 的分類、穩定 ID、顯示名稱、建構狀態預設、高程規則與後續計量規則。

Dictionary 不是 3D 物件資料庫，也不保存每一個物件的 UUID、空間、實際高程或數量。

## 先理解 Dictionary 與 3dm 的關係

~~~text
Excel Dictionary
  每列是一個 Type
  定義 Type ID、名稱、Layer、預設與規則
        │
        │ LFNexus「從字典同步 Type Layers」
        ▼
Rhino Type Layers
  以 lf_type_id 連回 Dictionary Type
  保存建立 Layer 時的 Type 預設
        │
        │ 建模後執行 LFNexus「寫入模型 Metadata」
        ▼
3D Model Objects
  每個物件有自己的 object_id、空間、實際高程、
  建構狀態、備註與資料版次
        │
        │ 檢核通過後 LFPublishExchange
        ▼
Registry Revision
  經驗證的唯讀模型快照
        │
        │ LFInfuserPart / LFInfuserAll
        ▼
Tag Blocks
  顯示 Type、空間、高程、Sheet 等資料
~~~

這條鏈有三個重要原則：

1. **Dictionary 管 Type，3D 物件管 instance。**
2. **Layer 是人類分類入口，不是永久身分。** 永久對應依靠 Type ID。
3. **重新同步 Dictionary 不會覆寫物件的 instance 現值。** 例如同一 Layer 上的兩個物件可以有不同建構狀態與備註。

## 檔案與版本

- 預設檔名：**LoopFlow_Dictionary.xlsx**
- 預設位置：LoopFlow 工作檔根目錄
- 正式表格第一列必須是 **LoopFlow Dictionary v2.0**
- 目前參考版本為單一工作表、15 欄、92 筆 Type
- 第一次同步或原檔改名後，由 LFNexus 選取正式 Dictionary
- Rhino 文件只記住檔名，不把特定電腦的磁碟路徑寫進專案

> **不要選錯檔**
>
> 名稱以 **_Export.xlsx** 結尾的檔案只供差異核對，不能當作正式 Dictionary，也不能直接覆寫正式檔。

## 表格結構

正式 Dictionary 使用一張表：

- 第 1 列：版本標題
- 第 2 列：固定欄名
- 第 3 列起：每列一個 Type

請不要：

- 新增、刪除或重新命名固定欄位
- 合併資料列
- 在 Type ID 欄使用重複值
- 把物件 UUID、計算高程或實作數量填進 Dictionary
- 把 Rhino 匯出差異檔直接改名成正式 Dictionary

## 15 個欄位

| Excel 欄位 | 用途 | Dictionary 中如何填 |
|---|---|---|
| <code>__Rhino Layer</code> | Type 對應的 Rhino Layer path | 必填；使用 <code>::</code> 表示父子層 |
| <code>_01_空間名稱</code> | 物件命中空間後的顯示值 | 留白；由 3dm 計算 |
| <code>_02_建構狀態</code> | 新建 Type Layer 的預設狀態 | 填 Type 預設，例如 <code>Existing</code> 或 <code>New</code> |
| <code>_03_ID編號</code> | Type 的穩定身分 | 必填且不可重複，例如 <code>WL-14</code> |
| <code>_04_ID名稱</code> | Type 顯示名稱 | 必填；可修改，不承擔永久身分 |
| <code>_05_高程基準</code> | 決定物件高程取樣點 | 必填；只允許 <code>BH</code>、<code>TH</code>、<code>CH</code>、<code>BC</code> |
| <code>_06_高程計算</code> | 物件的實際計算高程 | 留白；由 3dm 計算 |
| <code>_07_UUID</code> | 3D instance 的穩定 UUID | 留白；由 LoopFlow 對物件建立 |
| <code>_08_備註</code> | 新物件的備註預設 | 可填提示；現行預設為「(手動輸入備註)」 |
| <code>Q_01_寬度W</code> | 後續 GH 計算欄 | 留白；LoopFlow 2.0 不計算 |
| <code>Q_02_深度D</code> | 後續 GH 計算欄 | 留白；LoopFlow 2.0 不計算 |
| <code>Q_03_高度H</code> | 後續 GH 計算欄 | 留白；LoopFlow 2.0 不計算 |
| <code>Q_04_單位</code> | 工程估算單位 | 填 Type 規則，例如 <code>cm</code>、<code>坪</code>、<code>組</code> |
| <code>Q_05_計量規則</code> | 後續 GH 採用的量綱規則 | 填允許的規則 token |
| <code>Q_06_實作數量</code> | 後續 GH 計算結果 | 留白；LoopFlow 2.0 不計算 |

### 哪些欄位是 Type 規則

這些值由 Dictionary 擁有：

- <code>__Rhino Layer</code>
- <code>_02_建構狀態</code> 的初始預設
- <code>_03_ID編號</code>
- <code>_04_ID名稱</code>
- <code>_05_高程基準</code>
- <code>_08_備註</code> 的初始預設
- <code>Q_04_單位</code>
- <code>Q_05_計量規則</code>

### 哪些欄位要保持空白

這些值屬於 instance 或計算結果，不應在 Dictionary 預填：

- <code>_01_空間名稱</code>
- <code>_06_高程計算</code>
- <code>_07_UUID</code>
- <code>Q_01_寬度W</code>
- <code>Q_02_深度D</code>
- <code>Q_03_高度H</code>
- <code>Q_06_實作數量</code>

## 新增一個 Type

以新增一種牆面飾材為例：

1. 在相同類別附近新增一列，或複製最相近的 Type 列。
2. 將 <code>__Rhino Layer</code> 改成新的完整 Layer path。
3. 為 <code>_03_ID編號</code> 指定尚未使用的新 ID，例如 <code>WL-18</code>。
4. 在 <code>_04_ID名稱</code> 填寫人類可讀的 Type 名稱。
5. 確認 <code>_02_建構狀態</code> 的初始預設。
6. 依幾何意義選擇 <code>_05_高程基準</code>。
7. 填寫 <code>Q_04_單位</code> 與相容的 <code>Q_05_計量規則</code>。
8. 確認 instance／計算欄仍為空白。
9. 儲存 Excel。
10. 回到 Rhino，執行 **LFNexus → 從字典同步 Type Layers**。
11. 檢查預覽與結果後，再開始把物件放到新 Layer。

## 修改既有 Type

### 可以安全修改

- Type 顯示名稱
- 建構狀態預設
- 備註預設
- 高程基準
- 單位與計量規則

修改後仍應重新同步並檢核模型。Type 顯示名稱可變，但 Type ID 才是穩定身分。

### 修改前要特別小心

- Type ID
- Layer path
- 類別碼
- 已被大量 3D 物件或 Tag 使用的 Type

Type ID 變更會影響 3D 物件、Registry 與 Tag。不要只在 Excel 把舊 ID 改成新 ID 後直接繼續工作；應先確認影響範圍與更新方式。

## Type ID 與類別

Type ID 格式為「類別碼－類別內序號」。例如：

- <code>WL-14</code>：Wall 類別第 14 個 Type
- <code>EL-05</code>：Electrical 類別第 5 個 Type
- <code>DW-01</code>：Door / Window Type

目前 Dictionary 的 12 個頂層群組與 ID 前綴：

| Rhino 頂層群組 | Type ID 前綴 | 用途 |
|---|---|---|
| <code>00_STR_結構</code> | <code>EX</code> | 結構與既有條件 |
| <code>01_Ceiling_天花</code> | <code>CL</code> | 天花 |
| <code>02_Wall_牆面</code> | <code>WL</code> | 牆面與飾材 |
| <code>03_Floor_地坪</code> | <code>FL</code> | 地坪 |
| <code>04_CB_櫃體</code> | <code>CB</code> | 櫃體的一般材質 Type |
| <code>05_LT_燈帶</code> | <code>LS</code> | 燈帶 |
| <code>06_EL_電控系統</code> | <code>EL</code> | 電控與弱電 |
| <code>07_MEP_空調機電</code> | <code>MP</code> | 空調與機電 |
| <code>08_SAN_衛浴設備</code> | <code>SA</code> | 衛浴設備 |
| <code>09_EQP_專用設備</code> | <code>EQ</code> | 專用設備與電器 |
| <code>10_FP_消防系統</code> | <code>FP</code> | 消防設備 |
| <code>20_DW</code> | <code>DW</code> | 門窗 |

<code>04_CB_櫃體</code> 在 2.0 中只是一般材質分類。Cabinet Suite、BOM 與舊版 <code>_CB.01</code>～<code>_CB.04</code> 製作欄不屬於 LoopFlow 2.0。

## Rhino Layer path

使用 <code>::</code> 表示 Rhino 父子 Layer，例如：

<code>02_Wall_牆面::Tiles.磁磚</code>

同步時：

- Dictionary 有、Rhino 沒有：建立 Type Layer
- Dictionary 與 Rhino 已有相同 Layer：保留 Rhino Layer 既有資料
- Layer 上寫入穩定 Type 對應
- 系統建立參考點，避免空 Type Layer 被 Purge
- 不覆寫已存在 3D 物件的 instance 建構狀態或備註

## 高程基準

| 值 | 取樣位置 | 適用例 |
|---|---|---|
| <code>BH</code> | 物件 Bounding Box 底部 | 牆、落地設備、一般物件 |
| <code>TH</code> | 物件 Bounding Box 頂部 | 地坪面、門檻等以頂面標示者 |
| <code>CH</code> | 天花物件底部 | 天花、天花設備 |
| <code>BC</code> | Block instance 基準點 | 開關、面板、設備圖塊 |

<code>BC</code> 只能用於 Block instance；若一般幾何使用 BC，Metadata 寫入與檢核會報錯，不會偷偷改用其他基準。

舊版的 <code>TH/BH</code> 不屬於 2.0 合法值。

## 單位與計量規則

LoopFlow 2.0 會驗證規則，但不計算寬、深、高或數量。允許的計量規則：

| 規則 | 量綱 |
|---|---|
| <code>COUNT</code> | 件、組、台、座、片等計數 |
| <code>LEN_W</code> | 寬度方向長度 |
| <code>LEN_D</code> | 深度方向長度 |
| <code>LEN_H</code> | 高度方向長度 |
| <code>AREA_WD</code> | 寬 × 深面積 |
| <code>AREA_WH</code> | 寬 × 高面積 |
| <code>AREA_DH</code> | 深 × 高面積 |
| <code>VOL_WDH</code> | 寬 × 深 × 高體積 |

單位與規則的量綱必須一致。例如：

- <code>組 + COUNT</code>：正確
- <code>cm + LEN_W</code>：正確
- <code>坪 + AREA_WH</code>：正確
- <code>m3 + VOL_WDH</code>：正確
- <code>組 + AREA_WH</code>：錯誤，Dictionary 會停止載入

## Rhino → Dictionary 差異核對

需要比較 Rhino 現況時：

1. 執行 **LFExportTypeLayers**。
2. 系統在正式 Dictionary 同一資料夾建立 **原檔名_Export.xlsx**。
3. 用 **LFOpenDictionaryExport** 開啟匯出檔。
4. 依 <code>diff_status</code> 核對 Rhino 與正式 Dictionary。
5. 由使用者人工判斷後，把需要的變更寫回正式 Dictionary。
6. 再同步 Type Layers。

| diff_status | 意義 | 建議處理 |
|---|---|---|
| <code>unchanged</code> | Dictionary 與 Rhino 相同 | 不需處理 |
| <code>modified</code> | 對應 Type Layer 有差異 | 人工比較後決定正式值 |
| <code>missing_in_rhino</code> | Dictionary 有、Rhino 沒有 | 確認是否應重新同步或已不再使用 |
| <code>added_in_rhino</code> | Rhino 有、Dictionary 沒有 | 若要納入，必須分配新的 Type ID |

匯出檔只包含 Layer defaults 與差異，不會彙總每個 3D 物件的 UserText。

## Dictionary 寫入 3dm 後會發生什麼

### Type Layer

Type Layer 保存：

- 對應的 Type ID
- 建構狀態初始預設
- Layer 顯示與材質等 Rhino 設定

### 3D 物件

執行 LFNexus「寫入模型 Metadata」後，物件會取得或更新：

- 空間名稱
- 建構狀態 instance 現值
- Type ID
- 高程基準與計算高程
- 物件 UUID
- 人工備註
- 空間 ID
- Type 類別與序號
- 高程顯示
- 資料版次

物件不會取得 Dictionary 的 <code>Q_01</code>～<code>Q_06</code> 欄。

### Space 與樓層

空間名稱、高程與樓層不是靠 Layer 名稱猜測。使用者先登記高程框與空間框，LoopFlow 再依物件位置計算：

- 命中空間：寫入空間名稱與空間 ID
- 未命中：使用 <code>EXT</code> 並在檢核中回報
- 高程：樓層高程加上物件相對取樣高度

### Registry 與 Tag

Metadata 檢核通過後，LFPublishExchange 才能發布新的 Registry revision。Infuser 會從正式 Registry 讀取 Type、高程與其他顯示資料，並寫入已綁定 Tag。

因此正確順序是：

~~~text
修改 Dictionary
→ 同步 Type Layers
→ 寫入模型 Metadata
→ 檢核
→ 發布 Registry
→ Infuser
→ TAG-O
~~~

## 常見錯誤

| 情況 | 原因 | 處理方式 |
|---|---|---|
| Dictionary 無法載入 | 標題、欄名、欄數或版本不符 | 回復正式 15 欄結構 |
| Type ID 重複 | 兩列使用相同 <code>_03_ID編號</code> | 為新增 Type 指定未使用的新 ID |
| 高程基準錯誤 | 使用非 BH／TH／CH／BC 值 | 改成適用的合法值 |
| BC 物件檢核失敗 | BC Type 被用在非 Block 幾何 | 改用 Block instance 或修正 Type 高程基準 |
| 計量規則錯誤 | 單位和規則量綱不一致 | 修正 <code>Q_04</code>／<code>Q_05</code> |
| 找不到 Dictionary | 檔案改名、移動或工作檔設定不同 | 在 LFNexus 同步步驟重新選取正式檔 |
| 誤開匯出檔 | 選到 <code>_Export.xlsx</code> | 改用正式 Dictionary |
| Excel 有變更但 Rhino 沒更新 | 尚未同步 Type Layers | 儲存 Excel 後重新執行同步 |
| Tag 顯示舊資料 | 尚未寫入、檢核、發布或 Infuse | 依資料鏈補做後續步驟 |

## 相關文件

- [工作流程與快速開始](./README_TW.md)
- [Rhino 指令](./COMMANDS_TW.md)
- [Tag Blocks](./TAG_BLOCKS_TW.md)
- [文件入口](./README.md)
