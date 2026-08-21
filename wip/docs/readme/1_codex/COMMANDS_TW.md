# LoopFlow 2.0 Rhino 指令

本頁依工作鏈順序說明 LoopFlow 2.0 的正式 Rhino 指令。指令名稱採安裝後在 Rhino 命令列輸入的無底線形式。

## 快速索引

| 階段 | 指令 | 用途 |
|---|---|---|
| Dictionary | **LFOpenDictionary** | 開啟目前專案的正式 Dictionary |
| Dictionary | **LFOpenDictionaryExport** | 開啟 Type Layer 差異匯出檔 |
| Project / Model | **LFNexus** | 開案、同步 Layers、登記框線、寫入與檢核 Metadata |
| Dictionary | **LFExportTypeLayers** | 匯出 Rhino Type Layers 與 Dictionary 的差異 |
| Registry | **LFPublishExchange** | 發布新的 Registry revision |
| Inspect | **LFDataViewer** | 唯讀查看單一物件資料 |
| View | **LFAnchorFrame** | 登記固定的 2D↔3D View 對應 |
| Drawing | **LFExtractCP** | 從 Section 線稿建立可編輯 Drawing |
| Sheet | **LFDuplicateLayout** | 複製 Layout 並依契約重設身分與 Tag 狀態 |
| Sheet | **LFTaggerLayoutID** | 編排 Sheet、命名 Layout、寫入圖框與本頁圖號 Tag |
| Catalog | **LFCatalog** | 依 Sheet metadata 建立圖目錄 |
| Tag | **LFTaggerLaser** | 從剖面位置射線綁定 3D 物件 |
| Tag | **LFTaggerGrab** | 直接選取物件、剖面線或家具圖塊作為來源 |
| Tag | **LFTaggerIndex** | 綁定其他 Layout 的 Detail View |
| Tag | **LFInfuserPart** | 注入目前 Layout 頁的 Tag 顯示資料 |
| Tag | **LFInfuserAll** | 注入全檔所有 Layout 頁 |
| Health | **LFTagO** | 檢查 Tag 正常、過期或斷連 |
| Worksession | **LFSyncWorksession** | 監看同資料夾 3dm 並 Refresh Worksession |
| Help | **LFDocument** | 開啟 GitHub 文件入口 |

## 工具鏈建議順序

~~~text
01 LFOpenDictionary
02 LFOpenDictionaryExport（需要核對差異時）
03 LFExportTypeLayers（需要核對差異時）
04 LFNexus
05 LFPublishExchange
＊ Rhino Section Tools
06 LFAnchorFrame
A3 LFExtractCP（需要可編輯線稿時）
A4 LFDuplicateLayout（通常在編號前）
07 LFTaggerLayoutID
08 LFCatalog（需要圖目錄時）
09 LFTaggerLaser
10 LFTaggerGrab
11 LFTaggerIndex
12 LFInfuserPart 或 13 LFInfuserAll
14 LFTagO
~~~

Laser、Grab 與 Index 是不同來源的綁定方式，不需要三支都依序執行。Infuser Part 與 All 也是同一動作的不同範圍，擇一即可。

---

## LFOpenDictionary

開啟目前 3dm 已記住的正式 Excel Dictionary。

### 使用前

- 目前文件已完成 LoopFlow 開案設定
- 正式 Dictionary 位於 LoopFlow 工作檔根目錄

### 操作

1. 執行 **LFOpenDictionary**。
2. 系統用 Windows 預設程式開啟正式 Excel。
3. 編輯後在 Excel 儲存。
4. 回到 Rhino，以 LFNexus 同步 Type Layers。

### 結果與限制

- 只開啟檔案，不修改 Rhino
- 不建立不存在的 Dictionary
- 不會自動把 Excel 變更同步進 Rhino
- 找不到檔案時，請在 LFNexus 的同步步驟重新指定

---

## LFOpenDictionaryExport

開啟與正式 Dictionary 同資料夾的 Type Layer 差異匯出檔。

### 使用前

先執行 **LFExportTypeLayers** 產生 **原檔名_Export.xlsx**。

### 結果與限制

- 只開啟匯出檔，不修改 Rhino
- 匯出檔只能人工核對
- 匯出檔不能當正式 Dictionary，也不能直接覆寫正式檔

---

## LFExportTypeLayers

比較 Rhino Type Layers 與正式 Dictionary，建立人工核對用的 Excel。

### 使用前

- 開案檢查可以通過
- 目前專案已指定正式 Dictionary

### 操作

1. 執行 **LFExportTypeLayers**。
2. 系統完成開案檢查。
3. 在正式 Dictionary 同一資料夾建立或更新 **原檔名_Export.xlsx**。
4. 用 LFOpenDictionaryExport 開啟匯出檔。
5. 依 <code>diff_status</code> 人工比較。
6. 把確認後的內容手動修改回正式 Dictionary。

### 差異狀態

- <code>unchanged</code>：相同
- <code>modified</code>：對應 Type 有差異
- <code>missing_in_rhino</code>：Dictionary 有、Rhino 沒有
- <code>added_in_rhino</code>：Rhino 有、Dictionary 沒有

### 結果與限制

- 不覆寫正式 Dictionary
- 不彙總 3D 物件 UserText
- Rhino 新增 Layer 要納入正式 Dictionary 時，必須人工分配新的 Type ID

Dictionary 的完整操作見 [Excel Dictionary](./DICTIONARY_TW.md)。

---

## LFNexus

LoopFlow 的 Project Console，負責開案檢查、Type Layer 同步、高程／空間框，以及模型 Metadata 的寫入與檢核。

### 選單

| 選項 | 功能 | 是否寫入 |
|---|---|---|
| 1 | 開案檢查 | 不寫入 |
| 2 | 從字典同步 Type Layers | 寫入 Layer 與系統參考點；不改 3D instance |
| 3 | 登記高程框 | 寫入所選封閉曲線 |
| 4 | 登記空間框 | 寫入所選封閉曲線 |
| 5 | 寫入模型 Metadata | 寫入符合範圍的 3D 物件 |
| 6 | 檢核模型 Metadata | 不寫入；選取不符物件 |

### 1　開案檢查

檢查：

- 工作檔根目錄
- Dictionary 與 exchange 位置
- 專案身分與 schema
- Rhino 文件單位

非 cm 文件會警告但不強制停止。未存檔會請先存檔。尚未填專案名稱不擋開案；缺 schema 會順便寫入。未知 schema 仍停止。

### 2　從字典同步 Type Layers

1. 第一次使用或原檔找不到時，選取正式 Dictionary。
2. 系統驗證版本、15 欄、Type ID、類別、高程基準與計量規則。
3. 預覽要建立或更新的 Type Layers。
4. 確認後執行。

同步只建立 Layer mapping 與初始預設，不覆寫已存在物件的建構狀態、備註或 UUID。

### 3　登記高程框

1. 選取代表樓層範圍的封閉曲線。
2. 輸入該樓層高程。
3. 系統建立樓層身分並寫入框線。

高程框必須能明確界定樓層；取消或選取不合規曲線時不寫入。

### 4　登記空間框

1. 選取位於高程框內的封閉空間曲線。
2. 輸入人類可讀的空間名稱。
3. 系統配對樓層並建立空間身分。

同層空間框重疊時會停止，避免物件命中結果不確定。

### 5　寫入模型 Metadata

依 Dictionary Type、物件所在 Layer、空間框、高程框與幾何位置，對 3D 物件寫入：

- 物件 UUID
- Type ID
- 空間與空間 ID
- 高程基準與計算高程
- 建構狀態
- 備註
- Type 類別與序號
- 資料版次

LoopFlow 2.0 不寫入寬、深、高或數量。

### 6　檢核模型 Metadata

重新計算預期結果並與物件現況比較：

- 全部相符：顯示通過
- 有不符：一次選取不符物件並列出原因

檢核不會改物件。請先回到選項 5 寫入修正，再重新執行檢核。

---

## LFPublishExchange

把已檢核的模型資料發布成新的 Registry revision。

### 使用前

- 開案檢查通過
- 模型 Metadata 已寫入
- Metadata 檢核通過
- 正式 Registry 路徑可用

### 操作

1. 執行 **LFPublishExchange**。
2. 系統重新檢查發布條件。
3. 不合規時顯示與 Nexus 檢核一致的清單，不發布。
4. 通過後建立新的 Registry revision。

### 結果與安全

- Registry 是唯讀發布快照
- 發布成功才增加 revision
- 寫入前保留上一份有效資料
- 發布失敗不會先刪正式檔
- 正式檔占用時短暫重試；仍失敗則保留上一份

---

## LFDataViewer

唯讀查看所選 Rhino 物件目前的 LoopFlow 資料。

### 操作

1. 執行 **LFDataViewer**。
2. 點選一個物件。
3. 查看 Type、UUID、空間、高程、資料版次、圖塊名稱等現況。
4. 繼續查看其他物件，或按 Esc 結束。

### 結果與限制

- 不修改物件 UserText
- 沒有 LoopFlow 資料的物件也只顯示可讀現況
- 適合在寫入、檢核、發布或 Tag 綁定前後人工確認

---

## Rhino Section Tools

LoopFlow 保留 Rhino 8 原生 Section 工具作為主工作鏈的一部分，但不重新封裝 Section 功能。

常用原生功能包括：

- Clipping Sections
- Clipping Drawings
- Edit Clipping Drawings
- Update Clipping Drawings
- Clear Clipping Sections

先用 Rhino 產生同步剖面，再以 LFAnchorFrame 登記 View。

---

## LFAnchorFrame

在 2D 模型空間登記一張剖面或 View 的固定 2D↔3D 對應。

### 使用前

- Rhino Section 已建立剖面圖
- 剖面旁有恰好一個 Text Dot
- Text Dot 名稱能完整對到唯一 Clipping Plane

### 操作

1. 切到 2D 模型空間。
2. 執行 **LFAnchorFrame**。
3. 框選剖面物件與對應 Text Dot。
4. 輸入外擴距離；預設 50。
5. 確認後建立 Anchor Frame。

反射天花平面請先完成左右鏡射，再登記。

### 結果

- 在 LoopFlow Anchor Frame 圖層建立框線
- 建立唯一 View ID
- 記住 Clipping Plane 與固定 2D↔3D transform
- 後續 Laser 依此 transform 射線

### 停止條件

- 沒有或有多個 Text Dot
- Text Dot 對不到唯一 Clipping Plane
- 沒有剖面幾何
- 使用者取消

---

## LFExtractCP

把 Rhino Section 的同步線稿複製成可獨立編輯的 Drawing。

### 使用前

- 位於 2D 模型空間
- Section 已產生包含 Visible、Hatch、Curve 的剖面圖層
- 對應 View 已用 LFAnchorFrame 登記

### 操作

1. 執行 **LFExtractCP**。
2. 從清單勾選要擷取的剖面根圖層。
3. 若同一來源已有 Drawing，選擇取代、新增或略過。
4. 確認後產生 LoopFlow_Extract 圖層與線稿。

### 結果與安全

- 線稿可列印、移動與人工編輯
- 保存 Drawing ID、來源 View、來源 revision 與來源索引
- 不移動或破壞原始 Section
- 不把 3D 物件的 Metadata 複製到 2D 線
- 已標為人工修改的 Drawing 不會被靜默取代

---

## LFDuplicateLayout

複製一張或多張 Layout，並為新頁建立新的身分。

### 建議時機

通常在正式執行 LFTaggerLayoutID 編號之前使用。

### 操作

1. 執行 **LFDuplicateLayout**。
2. 用 Ctrl／Shift 選取一張或多張來源 Layout。
3. 輸入每張來源要複製的份數，範圍 1～100。
4. 確認後建立新頁。

### 結果

- 複製 Layout、Detail、圖框與 Tag
- 新頁圖名加上 <code>_CopyN</code>
- 新建 Sheet、Drawing、Tag 與 Catalog 身分
- 圖框比例保留，圖號與圖名清空，等待 Layout ID
- 不使用或改動系統剪貼簿

### Tag 處理

- 除 TAG_DW 外，來源綁定清除
- 自動欄改為 <code>?</code> 並標成斷連
- 人工欄保留欄位但清成空白
- 鎖定狀態不改
- TAG_DW 的人工編號、寬與高保留

任一步驟失敗時會清掉半成品頁，不留下部分完成的 Layout。

---

## LFTaggerLayoutID

依 Layout 名稱規則建立 Sheet metadata、整理 Layout 名稱，並寫入圖框與 TAG_ELEV_0。

### Layout 命名規則

系列第一頁：

<code>**圖類別__圖號__圖名</code>

例如：

- <code>**IN__201__立面圖</code>
- <code>**IN__A01__平面</code>

同系列後續頁只填圖名，由系統接續編號。

手動保留頁：

<code>//S__901__結構平面圖</code>

以 <code>//</code> 開頭的頁不參與自動接續編號，但仍可寫圖框。

### 操作

1. 確認每個 Layout 有恰好一個正式圖框。
2. 在系列起點頁加上 <code>**</code> 與完整三欄名稱。
3. 執行 **LFTaggerLayoutID**。
4. 檢查三欄核對表：原始名稱、修改後名稱、狀態。
5. 若有未登錄圖框，勾選真正的圖框 Block；預設不勾。
6. 確認後一次寫入。

### 結果

- 維持系列起點的 <code>**</code>
- 後續頁輸出三欄正式名稱
- 建立或維持 Sheet ID
- 寫入圖框圖號與圖名
- 寫入 TAG_ELEV_0 的本頁圖號
- 不寫圖框比例

取消核對清單時整批零寫入。一頁沒有圖框或有兩個圖框時，該頁跳過並報告。

---

## LFCatalog

依 Sheet metadata 建立或更新圖目錄。

### 使用前

- 已完成 LFTaggerLayoutID
- Sheet metadata 是最新狀態
- 模型空間有可作為圖號與圖名定位點的獨立 Point

### 操作

1. 執行 **LFCatalog**。
2. 選取圖號定位點與圖名定位點。
3. 在 Sheet 清單選取要列入圖目錄的頁面。
4. 用 Build 預覽並建立文字。
5. 日後 Sheet 內容變更時使用 Refresh。

### 結果

- 圖號與圖名文字建立在不可列印的 LoopFlow 圖層
- 定位點綁定 Sheet ID，不綁當下圖號
- Refresh 只改內容，不把人工移動過的文字拉回原位
- 可匯出 UTF-8 的「圖名, 圖號」文字檔

新 Layout 不會自動加入既有圖目錄，須重新選擇或 Refresh。

---

## LFTaggerLaser

從剖面圖上的點位沿 View transform 射線，綁定 Height 或 Finish Laser Tag 到 3D 物件。

### 適用圖塊

- TAG_HEIGHT_LASER
- TAG_FINISH_LASER

### 使用前

- 在 Layout 上操作
- Tag 位於可進入的 Detail
- 對應剖面已完成 LFAnchorFrame
- 來源 3D 物件已有 UUID

### 操作

1. 執行 **LFTaggerLaser**。
2. 在 Layout 選取 Laser Tag。
3. 進入目標 Detail。
4. 點選剖面上的來源位置。
5. 若射線命中多個候選，從清單選正確物件。

### 結果與限制

- 寫入 Tag 身分與來源物件 ID
- 不填畫面顯示欄；之後仍須執行 Infuser
- 點位必須落在唯一 Anchor Frame 內
- 沒打到、命中歧義、來源無 UUID、Tag 鎖定或選錯圖塊時不寫入

進階除錯選項 DebugRay 可暫時畫出洋紅射線；日常工作維持 No。

---

## LFTaggerGrab

直接選取來源物件、剖面線或家具圖塊，建立 Tag binding。

### 適用圖塊

- TAG_HEIGHT_GRAB
- TAG_FINISH_GRAB
- TAG_ITEM

### 操作

1. 在 Layout 執行 **LFTaggerGrab**。
2. 先選 Tag。
3. 點入目標 Detail。
4. 選取來源剖面線、3D 物件或家具 Block instance。
5. 完成後系統回到 Layout。

### 綁定規則

- Height／Finish：綁定來源物件 UUID
- Extract 產生的圖面 B：可由來源索引回到恰好一個 3D 物件
- TAG_ITEM：記住家具 Block 名稱與特定實例

家具名稱格式：

<code>分類-編號__名稱</code>

例如：

<code>FF-01__Chair-1</code>

### 結果與限制

- 只建立 binding，不填 Infuser 顯示欄
- 來源不明或對到兩個以上物件時停止，不猜測
- TAG_DW、Laser、Index、圖框或鎖定 Tag 不接受 Grab

---

## LFTaggerIndex

把 Section Detail 或 Elevation Index Tag 綁定到其他 Layout 的 Detail View。

### 適用圖塊

- TAG_SECTION_DETAIL
- TAG_ELEV_1
- TAG_ELEV_2
- TAG_ELEV_3
- TAG_ELEV_4

### 操作

1. 在 Layout 執行 **LFTaggerIndex**。
2. 選取 Index Tag。
3. 從可搜尋清單選取目標 Layout 與 Detail。
4. 選取清單項目時可跳頁並 Zoom 檢查。
5. 確認目標。

### 結果

- 記住目標 View ID
- 記住所選 Layout 名稱作為綁定提示
- 不寫 Detail GUID
- 不直接寫圖號文字；之後由 Infuser 依 Sheet metadata 注入

### 停止條件

- TAG_ELEV_0、Grab／Laser、TAG_DW 或圖框
- 目標 Detail 對不到唯一已登記 View
- 沒有 Layout／Detail
- Tag 已鎖定
- 使用者取消

---

## LFInfuserPart

把來源資料注入目前 Layout 頁的 LoopFlow Tag。

### 使用前

- Height／Finish／Item／Index Tag 已完成適用的綁定
- 模型 Metadata 與 Registry 已更新
- Sheet metadata 已建立

### 操作

1. 切到要更新的 Layout。
2. 執行 **LFInfuserPart**。
3. 查看完成摘要。
4. 再執行 LFTagO 檢查。

### 會更新

- Height：高程基準、高程顯示、Type 編號、Type 名稱
- Finish：Type 編號與 Type 名稱
- Item：家具分類、編號、名稱
- Index：目標 Sheet 圖類別與圖號
- Tag 的同步 revision 與所在 Sheet 身分

### 不會覆寫

- 鎖定 Tag
- TAG_DW
- TAG_ELEV_0
- 圖框
- Detail 編號
- 比例
- 人工備註與其他 manual 欄

未綁定顯示 <code>-</code>。已被 TAG-O 判定斷連的 Tag 不會直接灌回；需先重新綁定。

---

## LFInfuserAll

規則與 LFInfuserPart 相同，但一次處理全檔所有 Layout。

### 適用時機

- 發布新 Registry 後要更新整份圖面
- Layout ID 大幅調整後要刷新所有 Index
- 全案檢查前需要統一同步

可在模型空間執行。完成後顯示全檔摘要。

---

## LFTagO

檢查所有 Layout 上已綁定的 LoopFlow Tag，並依狀態上色。

### 操作

1. 執行 **LFTagO**。
2. 在面板查看正常、過期、斷連與鎖定狀態。
3. 點選項目可切換到 Tag 所在 Layout 並拉近。
4. 依狀態人工處理。

### 狀態

| 狀態 | 畫面 | 處理方式 |
|---|---|---|
| 正常 | 綠色狀態 | 不需處理 |
| 過期 | 橘色、<code>!</code> | 再執行 Infuser |
| 斷連 | 紅色、<code>?</code> | 重新 Grab／Laser／Index，再執行 Infuser |
| 鎖定 | 面板標示鎖定 | 檢查人工內容；系統不改文字與顏色 |

### 限制

- 只檢查與上色，不自動 Repair
- 未綁定 Tag 不列入面板
- TAG_DW 與 TAG_ELEV_0 不列入
- 斷連 Tag 不會被下一輪 Infuser 自動灌回

---

## LFSyncWorksession

監看目前 3dm 同資料夾的其他 3dm，變動後自動 Refresh Worksession。

### 操作

1. 先儲存目前 3dm。
2. 執行 **LFSyncWorksession**。
3. 彈窗確認開始監看。
4. 同資料夾 3dm 變動後，系統等待短暫同步並在 Rhino idle 時 Refresh。
5. 再執行一次可停止監看。

### 結果與限制

- 只做 Refresh
- 不 Attach、Detach 或修改 rws
- 失敗會延後重試，不拆除上一份有效參照
- 略過名稱含暫存標記的檔案
- 另存到不同資料夾後，再執行可切換監看位置

---

## LFDocument

用系統瀏覽器開啟 LoopFlow GitHub 文件入口。

### 結果與限制

- 文件入口中英並列
- 使用者自行選擇語言
- 不修改 Rhino 模型
- 瀏覽器開啟失敗時只顯示說明

---

## Tag 鎖定

支援鎖定的 Tag 可在 Attribute UserText 的鎖定欄輸入 <code>x</code> 或 <code>X</code>。鎖定後：

- Grab／Laser／Index 不改綁定
- Infuser 不覆寫顯示
- TAG-O 仍列出狀態，但不改文字與顏色

畫面上的預設提示文字不是鎖定；必須是實際輸入的 x 或 X。

完整圖塊規則見 [Tag Blocks](./TAG_BLOCKS_TW.md)。

## 相關文件

- [工作流程與快速開始](./README_TW.md)
- [Excel Dictionary](./DICTIONARY_TW.md)
- [Tag Blocks](./TAG_BLOCKS_TW.md)
- [文件入口](./README.md)
