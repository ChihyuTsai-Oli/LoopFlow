# LoopFlow 2.0 Rhino 指令

本頁依工具鏈順序說明 LoopFlow 2.0 的正式 Rhino 指令。指令名稱採安裝後可在 Rhino 命令列輸入的無底線形式。

## 快速索引

| 編號 | 指令 | 用途 |
|---|---|---|
| 01 | **LFOpenDictionary** | 開啟目前專案的正式 Dictionary |
| 02 | **LFOpenDictionaryExport** | 開啟 Type Layer 差異匯出檔 |
| 03 | **LFExportTypeLayers** | 匯出 Rhino Type Layers 與 Dictionary 的差異 |
| 04 | **LFNexus** | 開案、同步 Layers、登記框線、寫入與檢核 Metadata |
| 05 | **LFPublishExchange** | 發布新的 Registry revision |
| — | **Rhino Section Tools** | 由 Rhino 8 原生功能建立同步剖面 |
| 06 | **LFAnchorFrame** | 登記固定的 2D↔3D View 對應 |
| 07 | **LFTaggerLayoutID** | 建立 Sheet 身分並寫入圖框與本頁圖號 |
| 08 | **LFCatalog** | 依 Sheet metadata 建立圖目錄 |
| 09 | **LFTaggerLaser** | 從剖面位置射線綁定 3D 物件 |
| 10 | **LFTaggerGrab** | 直接選取物件、剖面線或家具圖塊作為來源 |
| 11 | **LFTaggerIndex** | 綁定其他 Layout 的 Detail View |
| 12 | **LFInfuserPart** | 注入目前 Layout 頁的 Tag 顯示資料 |
| 13 | **LFInfuserAll** | 注入全檔所有 Layout 頁 |
| 14 | **LFTagO** | 檢查 Tag 正常、過期或斷連 |
| A1 | **LFSyncWorksession** | 監看同資料夾 3dm 並 Refresh Worksession |
| A2 | **LFDataViewer** | 唯讀查看單一物件資料 |
| A3 | **LFExtractCP** | 從 Section 線稿建立可編輯 Drawing |
| A4 | **LFDuplicateLayout** | 複製 Layout 並重設新頁身分與 Tag 狀態 |
| A5 | **LFDocument** | 開啟 GitHub 文件入口 |

建議主流程為：

<pre>
Dictionary → Nexus → Publish → Rhino Section → Anchor Frame
→ Layout ID → Tagger → Infuser → TAG-O
</pre>

- **Laser、Grab、Index** 是不同來源的綁定方式，依 Tag 類型擇一。
- **Infuser Part、All** 是相同注入規則的不同範圍，擇一。
- **Export → Open Export → Open Dictionary** 是人工核對差異的回寫迴圈，不會自動改正式 Dictionary。

---

## 01　LFOpenDictionary

開啟目前 3dm 已記住的正式 Excel Dictionary。

### 操作與結果

1. 執行 **LFOpenDictionary**。
2. 系統用 Windows 預設程式開啟正式 Excel。
3. 在 Excel 修改並儲存。
4. 回到 Rhino，以 LFNexus 的選項 2 同步 Type Layers。

此指令只開啟檔案，不修改 Rhino、不建立不存在的 Dictionary，也不會自動同步 Excel 變更。找不到檔案時，請從 LFNexus 重新指定。

---

## 02　LFOpenDictionaryExport

開啟與正式 Dictionary 同資料夾的 Type Layer 差異匯出檔。

先以 **LFExportTypeLayers** 產生 <code>原檔名_Export.xlsx</code>。匯出檔只供人工核對，不能當正式 Dictionary，也不能直接覆寫正式檔。

---

## 03　LFExportTypeLayers

比較 Rhino Type Layers 與正式 Dictionary，建立人工核對用的 Excel。

### 操作

1. 確認專案已指定正式 Dictionary。
2. 執行 **LFExportTypeLayers**。
3. 在正式 Dictionary 同一資料夾建立或更新 <code>原檔名_Export.xlsx</code>。
4. 用 LFOpenDictionaryExport 開啟匯出檔，依 <code>diff_status</code> 比較。
5. 用 LFOpenDictionary 開啟正式檔，人工回寫確認後的內容。

| <code>diff_status</code> | 意義 |
|---|---|
| <code>unchanged</code> | Dictionary 與 Rhino 相同 |
| <code>modified</code> | 對應 Type 有差異 |
| <code>missing_in_rhino</code> | Dictionary 有、Rhino 沒有 |
| <code>added_in_rhino</code> | Rhino 有、Dictionary 沒有 |

本指令不覆寫正式 Dictionary，也不彙總 3D 物件 UserText。Rhino 新增 Layer 若要納入正式 Dictionary，仍須人工分配新的 Type ID。

Dictionary 的欄位與回寫方式見 [Excel Dictionary](./DICTIONARY_TW.md)。

---

## 04　LFNexus

LoopFlow 的 Project Console，負責開案檢查、Type Layer 同步、高程／空間框，以及模型 Metadata 的寫入與檢核。

### 六個選單

| 選項 | 功能 | 寫入範圍 |
|---|---|---|
| 1 | 開案檢查 | 唯讀 |
| 2 | 從字典同步 Type Layers | Layer 與系統參考點；不改 3D instance |
| 3 | 登記高程框（封閉曲線） | 所選框線 |
| 4 | 登記空間框（封閉曲線，須在高程框內） | 所選框線 |
| 5 | 寫入模型 Metadata | 符合範圍的 3D 物件 |
| 6 | 檢核模型 Metadata（不寫入） | 唯讀；選取不符物件 |

### 1　開案檢查

檢查工作檔根目錄、Dictionary、目前 `.3dm` 旁的 exchange、專案名稱、schema 與 Rhino 文件單位。未存檔會請先存檔。非 cm 文件會警告。尚未填專案名稱不擋開案；缺 schema 會順便寫入。未知 schema 仍停止。

### 2　從字典同步 Type Layers

1. 第一次使用或原檔找不到時，選取正式 Dictionary。
2. 輸入專案 Layer 前綴。第一次不預填 <code>M3D</code>；儲存後會帶入上次值。未填時沿用標準 <code>M3D</code>。
3. 系統驗證版本、15 欄、Type ID、類別、高程基準與計量規則。
4. 預覽要建立或更新的 Type Layers，確認後執行。

同步建立 Layer mapping 與初始預設，不覆寫既有物件的建構狀態、備註或 UUID。

### 3　登記高程框

選取代表樓層範圍的封閉曲線，指定 **FFL** 或 **FL** 並輸入高程值。曲線必須能明確界定樓層；取消或曲線不合規時不寫入。

### 4　登記空間框

選取位於高程框內的封閉空間曲線並輸入空間名稱。系統依框線高程配對樓層，允許的高程差為模型單位 ±20；框線不在唯一樓層內或同層空間互相重疊時停止。

### 5　寫入模型 Metadata

依 Dictionary Type、物件所在 Layer、空間框、高程框與幾何位置，寫入物件 UUID、Type ID、空間、高程、建構狀態、備註、Type 類別／序號及資料版次。

LoopFlow 2.0 不寫入物件寬、深、高或數量。

### 6　檢核模型 Metadata

重新計算預期結果並與物件現況比較。全部相符時通過；有不符時一次選取問題物件並列出原因。檢核不修改物件，應回到選項 5 修正後再驗證。

---

## 05　LFPublishExchange

把已檢核的模型資料發布成新的 Registry revision，供 2D 文件讀取。

### 使用前

- 開案檢查通過
- 模型 Metadata 已寫入並檢核通過
- 正式 Registry 路徑可用

### 結果與安全

- 每次發布是全範圍、已驗證的唯讀快照，不是局部更新。
- 只有發布成功才增加 revision。
- 寫入前保留上一份有效資料；失敗不先刪正式檔。
- 正式檔占用時會短暫重試；仍失敗則停止並保留上一版。

---

## Rhino Section Tools

LoopFlow 以 Rhino 8 原生 Section 功能作為 3D→2D 的正式交接，不重新封裝幾何生成。

常用功能包括：

- Clipping Sections
- Clipping Drawings
- Edit Clipping Drawings
- Update Clipping Drawings
- Clear Clipping Sections

先用 Rhino 建立可更新剖面，再以 LFAnchorFrame 登記 View。

---

## 06　LFAnchorFrame

在 2D 模型空間登記一張剖面或 View 的固定 2D↔3D 對應。

### 使用前與操作

1. Rhino Section 已建立剖面，且剖面旁有恰好一個 Text Dot。
2. Text Dot 名稱能完整對到唯一 Clipping Plane。
3. 執行 **LFAnchorFrame**，框選剖面物件與 Text Dot。
4. 輸入外擴距離；預設 50。
5. 確認後建立 Anchor Frame。

反射天花平面應先完成左右鏡射，再登記。既有 LoopFlow 1.x Anchor Frame 可在此流程升級為 2.0 身分。

### 結果與停止條件

系統建立唯一 View ID，記住 Clipping Plane 與固定 transform，供後續 Laser 使用。沒有或有多個 Text Dot、名稱對不到唯一 Clipping Plane、沒有剖面幾何或使用者取消時，均不寫入。

---

## 07　LFTaggerLayoutID

依 Layout 名稱規則建立 Sheet metadata、整理 Layout 名稱，並寫入圖框與 TAG_ELEV_0。

### Layout 命名規則

系列第一頁：

<pre>**圖類別__圖號__圖名</pre>

例如 <code>**IN__201__立面圖</code>。同系列後續頁只填圖名，由系統接續編號。

手動保留頁：

<pre>//S__901__結構平面圖</pre>

以 <code>//</code> 開頭的頁不參與自動接續編號，但仍可寫圖框。

### 操作與安全

1. 確認每個 Layout 有恰好一個正式圖框。
2. 在系列起點頁加上 <code>**</code> 與完整三欄名稱。
3. 執行指令，檢查「原始名稱／修改後名稱／狀態」三欄核對表。
4. 若有未登錄圖框，人工勾選真正的圖框 Block；預設不勾。
5. 確認後一次寫入 Sheet ID、圖框圖號／圖名與 TAG_ELEV_0 本頁圖號。

本指令不寫圖框比例。取消核對清單時整批零寫入；一頁沒有圖框或有兩個圖框時，該頁跳過並報告。

---

## 08　LFCatalog

依 Sheet metadata 建立或更新圖目錄。

### 操作與結果

1. 先完成 LFTaggerLayoutID。
2. 在模型空間選取圖號與圖名的獨立定位 Point。
3. 從 Sheet 清單選取要列入的頁面，以 Build 預覽並建立文字。
4. Sheet 內容改變後使用 Refresh。

圖號與圖名文字建立在不可列印的 LoopFlow 圖層。定位點綁定 Sheet ID；Refresh 只改內容，不把人工移動過的文字拉回原位。新 Layout 不會自動加入既有圖目錄。

---

## 09　LFTaggerLaser

從剖面圖上的點位沿 View transform 射線，綁定 Laser Tag 到 3D 物件。

適用：**TAG_HEIGHT_LASER、TAG_FINISH_LASER**。

### 操作

1. 在 Layout 選取 Laser Tag。
2. 進入目標 Detail。
3. 點選剖面上的來源位置。
4. 射線若命中多個候選，從清單選擇正確物件。

系統只建立 Tag 身分與來源 binding，不立即填顯示欄；之後執行 Infuser。點位不在唯一 Anchor Frame、沒有命中、來源無 UUID、Tag 鎖定或使用者取消時不寫入。

---

## 10　LFTaggerGrab

直接選取來源物件、剖面線或家具圖塊，建立 Tag binding。

適用：**TAG_HEIGHT_GRAB、TAG_FINISH_GRAB、TAG_ITEM**。

### 綁定規則

- Height／Finish：綁定來源物件 UUID。
- LFExtractCP 產生的 Drawing 線：由來源索引回到唯一 3D 物件。
- TAG_ITEM：同時記住家具 Block 名稱與特定 instance。

家具名稱格式為 <code>分類-編號__名稱</code>，例如 <code>FF-01__Chair-1</code>。

來源不明、對到兩個以上物件、Tag 鎖定或類型不適用時停止，不猜測。此指令只綁定；顯示資料由 Infuser 寫入。

---

## 11　LFTaggerIndex

把 Section Detail 或 Elevation Index Tag 綁定到其他 Layout 的 Detail View。

適用：

- TAG_SECTION_DETAIL
- TAG_ELEV_1
- TAG_ELEV_2
- TAG_ELEV_3
- TAG_ELEV_4

### 操作與結果

1. 選取 Index Tag。
2. 從可搜尋清單選取目標 Layout 與 Detail。
3. 可先跳頁並 Zoom 檢查，再確認目標。

系統記住目標 View ID 與 Layout 名稱提示，不寫 Detail GUID，也不直接寫圖號文字；圖號由 Infuser 依 Sheet metadata 注入。TAG_ELEV_0、未登記 View、鎖定 Tag 或不唯一的目標均不寫入。

---

## 12　LFInfuserPart

把來源資料注入目前 Layout 頁的 LoopFlow Tag。

### 會更新

- Height：高程基準／顯示、Type 編號與名稱。
- Finish：Type 編號與名稱。
- Item：家具分類、編號與名稱。
- Index：目標 Sheet 圖類別與圖號。
- Tag 的同步 revision 與所在 Sheet 身分。

### 不會覆寫

- 鎖定 Tag
- TAG_DW、TAG_ELEV_0、圖框
- Detail 編號、比例、人工備註與其他 manual 欄

未綁定欄位顯示 <code>-</code>。已判定斷連的 Tag 不會被直接灌回，須先重新 Grab／Laser／Index。完成後應執行 LFTagO 檢查。

---

## 13　LFInfuserAll

規則與 LFInfuserPart 相同，但一次處理全檔所有 Layout，可在模型空間執行。

適合在發布新 Registry、Layout ID 大幅調整，或全案檢查前使用。若只需更新當前頁，使用 Part 可縮小操作範圍。

---

## 14　LFTagO

檢查所有 Layout 上已綁定的 LoopFlow Tag，並依狀態上色。

| 狀態 | 畫面 | 人工處理 |
|---|---|---|
| 正常 | 綠色 | 不需處理 |
| 過期 | 橘色、<code>!</code> | 再執行 Infuser |
| 斷連 | 紅色、<code>?</code> | 重新 Grab／Laser／Index，再 Infuser |
| 鎖定 | 面板標示鎖定 | 檢查人工內容；系統不改文字與顏色 |

TAG-O 只檢查與上色，不自動 Repair。未綁定 Tag、TAG_DW 與 TAG_ELEV_0 不列入；斷連 Tag 也不會被下一輪 Infuser 自動修復。

---

## A1　LFSyncWorksession

監看目前 3dm 同資料夾的其他 3dm；檔案變動後，在 Rhino idle 時 Refresh Worksession。

- 只做 Refresh，不 Attach、Detach 或修改 rws。
- 再執行一次可停止監看。
- 失敗會延後重試，不拆除上一份有效參照。
- 另存到不同資料夾後，再執行可切換監看位置。

---

## A2　LFDataViewer

唯讀查看單一 Rhino 物件的 LoopFlow 資料，包括 Type、UUID、空間、高程、資料版次與圖塊名稱等現況。

可連續點選物件，按 Esc 結束；不修改 UserText。適合在寫入、檢核、發布或 Tag 綁定前後人工確認。

---

## A3　LFExtractCP

把 Rhino Section 的同步線稿複製成可獨立編輯的 Drawing。

### 操作與安全

1. 在 2D 模型空間，確認 Section 已產生 Visible、Hatch、Curve 圖層，且 View 已登記 Anchor Frame。
2. 從清單勾選要擷取的剖面根圖層。
3. 同一來源已有 Drawing 時，選擇取代、新增或略過。

系統建立 LoopFlow_Extract 線稿及 Drawing ID，保存來源 View、revision 與來源索引。不移動原始 Section、不把 3D Metadata 複製到 2D 線，也不靜默取代已標為人工修改的 Drawing。

---

## A4　LFDuplicateLayout

複製一張或多張 Layout，並為新頁建立新的身分。通常在正式編號前使用。

### 結果

- 每張來源可複製 1～100 份，新頁圖名加上 <code>_CopyN</code>。
- 新建 Sheet、Drawing、Tag 與 Catalog 身分。
- 圖框比例保留，圖號與圖名清空，等待 LFTaggerLayoutID。
- 除 TAG_DW 外，來源 binding 清除；自動欄改為 <code>?</code>。
- 人工欄清空，鎖定狀態保留。
- TAG_DW 的人工編號、寬與高保留。

任一步驟失敗時會清除半成品頁，不留下部分完成的 Layout。

---

## A5　LFDocument

用系統瀏覽器開啟 LoopFlow GitHub 文件入口。此指令不修改 Rhino；瀏覽器無法開啟時只顯示提示。

---

## Tag 鎖定

支援鎖定的 Tag 可在 Attribute UserText 鎖定欄輸入 <code>x</code> 或 <code>X</code>。鎖定後 Tagger 不改 binding、Infuser 不覆寫顯示，TAG-O 也不改文字與顏色。

畫面上的預設提示不是鎖定，必須實際輸入 x 或 X。完整規則見 [Tag Blocks](./TAG_BLOCKS_TW.md)。

## 相關文件

- [一分鐘理解 LoopFlow 2.0](./README_TW.md)
- [Excel Dictionary](./DICTIONARY_TW.md)
- [Tag Blocks](./TAG_BLOCKS_TW.md)
- [文件入口](./README.md)
