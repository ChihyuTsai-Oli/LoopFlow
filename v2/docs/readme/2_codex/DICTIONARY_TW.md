# LoopFlow 2.0 — Excel Dictionary

> 本文件說明 **LoopFlow_Dictionary.xlsx** 的格式、欄位、撰寫規則，以及 Dictionary、Rhino Layer、3D 物件、Registry 與 Tag 之間的資料關係。整體概念見[使用說明總覽](./README_TW.md)，操作指令見 [Commands](./COMMANDS_TW.md)。

## 1　Dictionary 是什麼

Dictionary 是 LoopFlow 的 **Type Catalog**。每一列代表一種材質、工項或設備 Type，定義：

- 穩定 Type ID
- 人類可讀名稱
- 對應 Rhino Layer path
- 建構狀態初始預設
- 高程基準
- 備註初始提示
- 後續估算單位與計量規則

Dictionary 不保存每個 3D 物件的 UUID、所在空間、實際高程、人工備註或數量。

| 資料層級 | 主要責任 |
|---|---|
| Dictionary Type | Type 的身分、名稱、Layer、預設與規則 |
| Rhino Layer | 人類分類入口與 Type mapping；不是永久身分 |
| 3D object instance | UUID、空間、實際高程、建構狀態、人工備註、資料版次 |
| Registry revision | 通過檢核後發布的唯讀模型快照 |
| 2D Tag | 讀取 Registry／Sheet 資料並顯示；人工欄由使用者維護 |

## 2　檔案格式與位置

| 項目 | 規則 |
|---|---|
| 預設檔名 | <code>LoopFlow_Dictionary.xlsx</code> |
| 格式 | 只支援 <code>.xlsx</code> |
| 位置 | <code>LOOPFLOW_WORKFILES_ROOT</code> 指向的工作檔根目錄 |
| 工作表 | 讀取第一張工作表；目前名稱為 <code>LoopFlow_Dictionary</code> |
| 第 1 列 | 版本標題：<code>LoopFlow Dictionary v2.0</code> |
| 第 2 列 | 固定 15 欄欄名 |
| 第 3 列起 | 每列一個 Type |
| 繁中字型 | 微軟正黑體 10 |

目前參考 Dictionary 為 15 欄、92 筆 Type、12 個頂層群組。Type 筆數可隨正式 Dictionary 調整，但標題、欄名、欄數與類別契約必須通過驗證。

第一次執行 Nexus 的「從字典同步 Type Layers」時選取正式 Dictionary。Rhino 文件只記住檔名 <code>lf_dictionary_filename</code>；檔案找不到或改名後才重新選取。系統不掃描整個資料夾，也不從 3dm 所在位置猜測。

> 檔名以 <code>_Export.xlsx</code> 結尾的是人工核對檔，不能當正式 Dictionary，也不能直接覆寫正式檔。

## 3　Dictionary 與 3dm 的資料流

~~~text
Excel Dictionary
  每列一個 Type：ID、名稱、Layer、預設、規則
        │
        │ LFNexus：從字典同步 Type Layers
        ▼
Rhino Type Layers
  lf_type_id + 建構狀態初始預設
        │
        │ 建模後執行 LFNexus：寫入模型 Metadata
        ▼
3D objects
  object_id、Type、空間、高程、備註、資料版次
        │
        │ 檢核通過後 LFPublishExchange
        ▼
Registry revision
  經驗證的唯讀模型快照
        │
        │ LFInfuserPart / LFInfuserAll
        ▼
2D Tag Blocks
  顯示 Type、高程與其他模型資料
~~~

這是一條有明確所有權的資料流：

- Dictionary 改 Type，不直接改既有 object instance。
- 3D 物件保存 instance 現值，不回寫 Dictionary。
- Registry 只由發布建立，不人工編輯。
- 2D Tag 讀取資料，不反向修改 3D Type 或物件。

## 4　15 個欄位

| Excel 欄位 | 是否填寫 | 用途 |
|---|---|---|
| <code>__Rhino Layer</code> | 必填 | 完整 Layer path；同步時建立人類分類入口 |
| <code>_01_空間名稱</code> | 留白 | 由 3dm 空間命中計算 |
| <code>_02_建構狀態</code> | 建議填 | 新建 Type Layer 的初始預設，例如 <code>New</code>、<code>Existing</code> |
| <code>_03_ID編號</code> | 必填 | Type 的穩定唯一 ID，例如 <code>WL-14</code> |
| <code>_04_ID名稱</code> | 必填 | 人類可讀的 Type 顯示名稱 |
| <code>_05_高程基準</code> | 必填 | 只允許 <code>BH</code>、<code>TH</code>、<code>CH</code>、<code>BC</code> |
| <code>_06_高程計算</code> | 留白 | 由 3dm 依空間、樓層與幾何計算 |
| <code>_07_UUID</code> | 留白 | object instance 身分，由 LoopFlow 建立 |
| <code>_08_備註</code> | 選填 | 新物件的備註提示，現行預設為「(手動輸入備註)」 |
| <code>Q_01_寬度W</code> | 留白 | 後續 Grasshopper 計算欄 |
| <code>Q_02_深度D</code> | 留白 | 後續 Grasshopper 計算欄 |
| <code>Q_03_高度H</code> | 留白 | 後續 Grasshopper 計算欄 |
| <code>Q_04_單位</code> | 必填 | 工程估算單位，不是 Rhino 文件單位 |
| <code>Q_05_計量規則</code> | 必填 | 後續 Grasshopper 採用的量綱規則 |
| <code>Q_06_實作數量</code> | 留白 | 後續 Grasshopper 計算結果 |

### Type 規則與 instance 結果

Dictionary 擁有：

- <code>__Rhino Layer</code>
- <code>_02_建構狀態</code> 初始預設
- <code>_03_ID編號</code>
- <code>_04_ID名稱</code>
- <code>_05_高程基準</code>
- <code>_08_備註</code> 初始提示
- <code>Q_04_單位</code>
- <code>Q_05_計量規則</code>

下列欄位必須留白，因為它們屬於 object instance 或計算結果：

- <code>_01_空間名稱</code>
- <code>_06_高程計算</code>
- <code>_07_UUID</code>
- <code>Q_01</code>～<code>Q_03</code>
- <code>Q_06_實作數量</code>

## 5　高程基準

| 值 | 正式語意 | 適用例 |
|---|---|---|
| <code>BH</code> | 物件 Bounding Box 底部世界 Z | 牆、落地設備、一般物件 |
| <code>TH</code> | 物件 Bounding Box 頂部世界 Z | 地坪面、門檻等以頂面標示者 |
| <code>CH</code> | 天花物件底部世界 Z | 天花、天花設備 |
| <code>BC</code> | **Block instance 基準點世界 Z** | 開關、面板、設備 Block |

<code>BC</code> 只能用於 Block instance。一般幾何使用 BC 時會列為錯誤，不會偷偷退回 BH。舊版的 <code>TH/BH</code> 不屬於 2.0 合法值。

物件高程為：

~~~text
空間所屬樓層高程
+ 物件取樣點相對高程框曲線的高度
~~~

<code>_05_高程基準</code> 決定取樣點；<code>_06_高程計算</code> 與顯示字串由 3dm 端產生，不在 Dictionary 預填。

## 6　Layer path 與 Type ID

Layer path 格式：

~~~text
頂層群組::英文名稱.中文名稱
~~~

例如：

<code>02_Wall_牆面::Tiles.磁磚</code>

Type ID 格式：

~~~text
類別碼-類別內序號
~~~

例如 <code>WL-14</code>、<code>EL-05</code>、<code>DW-01</code>。

| 頂層群組 | Type ID 前綴 | 用途 |
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

<code>_03_ID編號</code> 是穩定身分，必須唯一；<code>_04_ID名稱</code> 是顯示文字，可以修改。Layer 是人類分類入口，不可取代 Type ID。

<code>04_CB_櫃體</code> 只保留一般材質 Type。Cabinet Suite、BOM 與舊版 <code>_CB.01</code>～<code>_CB.04</code> 製作欄不屬於 LoopFlow 2.0。

### 20_DW 特例

<code>20_DW</code> 維持單一 Type。門窗的人工編號、寬與高寫在 TAG_DW Block，不寫在 Dictionary 子圖層；同步時不把 <code>20_DW</code> 下的子圖層當成其他 Type。

## 7　新增或修改 Type

### 新增 Type

1. 在同類別附近新增一列，或複製最相近的 Type。
2. 填寫新的完整 Layer path。
3. 分配尚未使用的 Type ID。
4. 填寫顯示名稱、建構狀態預設與高程基準。
5. 填寫相容的估算單位與計量規則。
6. 確認 instance／計算欄保持空白。
7. 儲存 Excel。
8. 回到 Rhino，以 LFNexus 同步 Type Layers。

### 修改既有 Type

通常可以修改：

- 顯示名稱
- 建構狀態初始預設
- 備註初始提示
- 高程基準
- 單位與計量規則

修改 Type ID、Layer path 或類別碼前，必須先確認 3D 物件、Registry 與 Tag 的影響。不要只改 Excel ID 後直接繼續工作。

### 不要做

- 改欄名、欄數或版本標題
- 合併資料列
- 使用重複 Type ID
- 在 Dictionary 填 UUID、計算高程、寬深高或實作數量
- 把 <code>_Export.xlsx</code> 改名成正式 Dictionary

## 8　同步到 Rhino 時的行為

執行 LFNexus「從字典同步 Type Layers」：

- Dictionary 有、Rhino 沒有：建立 Type Layer，寫入 Type ID 與建構狀態初始預設。
- Rhino 已有同名 Layer：保留既有 UserText 與 construction 資料；顯示色仍依 Type 類別規則重套。
- 不修改已存在 3D object instance 的建構狀態、備註、UUID 或高程。
- 不把物件現況回寫 Dictionary。
- 在原點維護 <code>DNA_REF_</code> 參考點，避免空 Type Layer 被 Purge；重新同步不累加。
- 新建 Layer 依類別套用顯示色與材質；既有同名材質只掛接，不覆寫使用者已調整的材質顏色。

接著執行「寫入模型 Metadata」時，Nexus 才依 Type Layer、空間框、高程框與物件幾何寫入 object instance 資料。

## 9　Q_01～Q_06 的定位

LoopFlow 2.0 不計算寬、深、高或數量，也不把 Q 欄下放物件或寫入 Registry objects。

但載入 Dictionary 時仍驗證 <code>Q_04_單位</code> 與 <code>Q_05_計量規則</code> 的量綱是否一致：

| 計量規則 | 量綱 | 常見單位 |
|---|---|---|
| <code>COUNT</code> | 計數 | 樘、片、組、台、座 |
| <code>LEN_W</code>／<code>LEN_D</code>／<code>LEN_H</code> | 長度 | cm、mm |
| <code>AREA_WD</code>／<code>AREA_WH</code>／<code>AREA_DH</code> | 面積 | 坪、才 |
| <code>VOL_WDH</code> | 體積 | m3 |

規則與單位不相容時會阻擋載入。實際幾何求值留給後續 Grasshopper 工作流。

## 10　Rhino → Dictionary 差異核對

1. 執行 **LFExportTypeLayers**，建立 <code>{原檔名}_Export.xlsx</code>。
2. 用 **LFOpenDictionaryExport** 開啟匯出檔。
3. 依 <code>diff_status</code> 人工比較。
4. 用 **LFOpenDictionary** 開啟正式 Dictionary。
5. 把確認後的變更人工寫回正式檔。
6. 再執行同步。

| diff_status | 意義 | 顏色 |
|---|---|---|
| <code>unchanged</code> | Dictionary 與 Rhino 相同 | 黑 |
| <code>modified</code> | 對應 Type Layer 有差異 | 橙 |
| <code>missing_in_rhino</code> | Dictionary 有、Rhino 沒有 | 紅 |
| <code>added_in_rhino</code> | Rhino 有、Dictionary 沒有 | 藍 |

<code>added_in_rhino</code> 要納入正式 Dictionary 時，必須分配尚未使用的新 Type ID。匯出檔只比較 Layer defaults，不彙總 object UserText，也不會自動合併。

## 11　中途切換 Dictionary

中途更換 Dictionary 不建議。新檔若缺少既有 Type ID，3D 物件會失去可驗證的 Type 對應。

若必須切換：

1. 先匯出並核對 Rhino 現況。
2. 比較新舊 Dictionary 的 Type ID、欄位與類別。
3. 確認所有既有 object Type ID 都能在新檔找到。
4. 再於 Nexus 同步步驟重新選取檔案。

## 12　常見錯誤

| 情況 | 原因 | 處理 |
|---|---|---|
| Dictionary 無法載入 | 標題、欄名、欄數或版本不符 | 回復正式 15 欄結構 |
| Type ID 重複 | 兩列使用相同 ID | 分配新的唯一 ID |
| 高程基準不合法 | 不是 BH／TH／CH／BC | 改為適用的正式值 |
| BC 物件檢核失敗 | Type 套用到非 Block 幾何 | 改成 Block instance 或修正基準 |
| 計量規則錯誤 | 單位與量綱不一致 | 修正 Q_04／Q_05 |
| 找不到 Dictionary | 檔案改名、移動或設定不同 | 在 Nexus 同步步驟重新選檔 |
| 誤選 Export | 使用核對檔當正式檔 | 改選正式 Dictionary |
| Excel 已改、Rhino 未更新 | 尚未同步 Type Layers | 儲存 Excel 後重新同步 |
| Tag 仍顯示舊資料 | 尚未寫入、檢核、發布或 Infuse | 依工作鏈補做後續節點 |

## 相關文件

- [使用說明總覽](./README_TW.md)
- [Commands](./COMMANDS_TW.md)
- [Tag Blocks](./TAG_BLOCKS_TW.md)
- [文件入口](./README.md)
