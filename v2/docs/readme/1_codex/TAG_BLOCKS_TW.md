# LoopFlow 2.0 Tag Blocks 使用說明

LoopFlow 2.0 的 Tag 圖塊集中在 **Tag_Blocks.3dm**。正式版只維護一份英文 Block library；繁中與英文文件解釋同一組 Block，不另外建立中文圖塊檔。

本頁說明每種 Block 顯示什麼、資料從哪裡來、應搭配哪支指令，以及哪些欄位保留給使用者手動輸入。

## 先選對 Tag

| 想標示的內容 | 使用 Block | 綁定方式 | 指令 |
|---|---|---|---|
| 物件高度與 Type，直接選來源 | <code>TAG_HEIGHT_GRAB</code> | Object | **LFTaggerGrab** |
| 物件高度與 Type，從剖面位置找來源 | <code>TAG_HEIGHT_LASER</code> | Object | **LFTaggerLaser** |
| 材質／Type，直接選來源 | <code>TAG_FINISH_GRAB</code> | Object | **LFTaggerGrab** |
| 材質／Type，從剖面位置找來源 | <code>TAG_FINISH_LASER</code> | Object | **LFTaggerLaser** |
| 家具或命名 Block | <code>TAG_ITEM</code> | Block name + instance | **LFTaggerGrab** |
| 門窗編號、寬、高 | <code>TAG_DW</code> | Manual | 不綁定 |
| 剖面索引 | <code>TAG_SECTION_DETAIL</code> | View / Sheet | **LFTaggerIndex** |
| 四種立面索引方向 | <code>TAG_ELEV_1</code>～<code>TAG_ELEV_4</code> | View / Sheet | **LFTaggerIndex** |
| 本頁立面方向與圖號 | <code>TAG_ELEV_0</code> | Current Sheet + Manual | **LFTaggerLayoutID** |
| 圖框範例 | <code>Sample_Frame</code> | Current Sheet + Manual | **LFTaggerLayoutID** |

## 自動欄、人工欄與系統欄

Tag 內容分成三種所有權：

### 自動顯示欄

由 LoopFlow 指令寫入，使用者不應把它當作人工文字維護：

- Type 編號與名稱
- 高程基準與高程值
- 目標 Sheet 圖號
- 家具分類、編號與名稱
- 圖框圖號與圖名

Grab、Laser 與 Index 只建立 binding；真正的顯示值由 Infuser 或 Layout ID 寫入。

### 人工欄

由使用者直接在 Block Attribute UserText 編輯：

- 補充說明
- Detail 編號
- TAG_ELEV_0 的方向與編號
- TAG_DW 的門窗編號、寬與高
- 圖框比例

Infuser 不覆寫人工欄。

### 系統欄

LoopFlow 用來辨認 Tag 身分、來源、目標、同步版次與健康狀態。這些欄位不應人工修改。

## 共同行為

### 未綁定

尚未建立來源時，自動欄顯示 <code>-</code>，不塗警示色。請使用該 Block 對應的 Grab、Laser 或 Index。

### 過期

來源仍存在，但 Tag 顯示內容不是最新版：

- TAG-O 顯示橘色狀態
- 自動欄顯示 <code>!</code>
- 再執行 LFInfuserPart 或 LFInfuserAll

通常不需要重新綁定。

### 斷連

來源物件、目標 Layout 或 Detail 已不存在：

- TAG-O 顯示紅色狀態
- 自動欄顯示 <code>?</code>
- 重新 Grab、Laser 或 Index
- 再執行 Infuser

已標斷連的 Tag 不會被 Infuser 直接灌回，避免系統猜錯新來源。

### 鎖定

支援鎖定的 Block，在鎖定欄輸入 <code>x</code> 或 <code>X</code>：

- Grab／Laser／Index 不改 binding
- Infuser 不覆寫顯示欄
- TAG-O 仍列出狀態並標示鎖定，但不改文字或顏色

預設提示文字不是鎖定。只有使用者實際輸入 x 或 X 才生效。

### Duplicate Layout

使用 LFDuplicateLayout 後：

- 新 Tag 取得新的 Tag ID
- 除 TAG_DW 外，原 binding 清除
- 自動欄變成 <code>?</code> 並標斷連
- 人工欄保留欄位但清為空白
- 鎖定狀態保留
- TAG_DW 的人工內容完整保留

## TAG_HEIGHT_GRAB

### 適用範圍

需要標示物件高程與 Type，而且可以直接點選來源物件、剖面線或 Extract 線稿時。

常見用途：

- 牆、天花、地坪的高度標示
- 設備安裝高度
- 已抽出為可編輯 Drawing 的剖面線

### 使用方式

1. 在 Layout 選取 TAG_HEIGHT_GRAB。
2. 執行 **LFTaggerGrab**。
3. 進入 Detail 並選取來源。
4. 執行 Infuser。

### 顯示內容

- 高程基準，例如 BH、TH、CH、BC
- 計算高程
- Type 類別
- Type 序號
- Type 顯示名稱
- 人工補充說明

### 注意

- 來源必須能回到恰好一個 3D 物件 UUID
- Extract 線稿若包含多個來源 UUID，LoopFlow 會停止，不猜測
- 不適合從剖面位置射線找物件；那種情況使用 TAG_HEIGHT_LASER

## TAG_HEIGHT_LASER

### 適用範圍

需要標示物件高程與 Type，但不方便直接選取 3D 來源，適合從剖面圖的位置射線定位。

常見用途：

- 剖面中重疊較少的牆、板與設備
- 需要在 Layout Detail 內點位定位的標示

### 使用方式

1. 先以 LFAnchorFrame 登記剖面 View。
2. 在 Layout 選取 TAG_HEIGHT_LASER。
3. 執行 **LFTaggerLaser**。
4. 進入 Detail，在剖面位置點一下。
5. 如有候選清單，選取正確物件。
6. 執行 Infuser。

### 顯示內容

與 TAG_HEIGHT_GRAB 相同：

- 高程基準與計算高程
- Type 類別、序號與顯示名稱
- 人工補充說明

### 注意

- 點位必須位於唯一 Anchor Frame
- 沒打到物件或來源不明時不寫入
- 不適合沒有穩定 View transform 的圖面
- Anchor Frame 與圖面一起平移後仍可使用

## TAG_FINISH_GRAB

### 適用範圍

需要直接選取來源，標示材質或 Type，但不需要顯示高程。

常見用途：

- 牆面飾材
- 地坪材質
- 天花材質
- 可直接點選的剖面構件

### 使用方式

1. 在 Layout 選取 TAG_FINISH_GRAB。
2. 執行 **LFTaggerGrab**。
3. 選取來源物件或可回溯來源的剖面線。
4. 執行 Infuser。

### 顯示內容

- Type 類別
- Type 序號
- Type 顯示名稱
- 人工補充說明

### 注意

Finish Tag 不顯示高程。需要高程時請改用 Height Tag。

## TAG_FINISH_LASER

### 適用範圍

需要從剖面位置尋找 3D 物件，標示材質或 Type，但不需要顯示高程。

### 使用方式

1. 先完成 LFAnchorFrame。
2. 在 Layout 選取 TAG_FINISH_LASER。
3. 執行 **LFTaggerLaser**。
4. 點選剖面位置並確認來源。
5. 執行 Infuser。

### 顯示內容

- Type 類別
- Type 序號
- Type 顯示名稱
- 人工補充說明

### 注意

Laser 的命中與限制和 TAG_HEIGHT_LASER 相同。

## TAG_ITEM

### 適用範圍

標示家具或其他以 Block 名稱表達分類、編號與名稱的物件。

來源 Block 名稱格式：

<code>分類-編號__名稱</code>

例如：

<code>FF-01__Chair-1</code>

解析結果：

- 分類：FF
- 編號：01
- 名稱：Chair-1

### 使用方式

1. 在 Layout 選取 TAG_ITEM。
2. 執行 **LFTaggerGrab**。
3. 在 Detail 選取家具 Block instance。
4. 執行 Infuser。

### 顯示內容

- Item 分類
- Item 編號
- Item 名稱
- 人工補充說明

### 綁定邏輯

LoopFlow 同時記住：

- Block 名稱
- 被選取的特定 instance

因此：

- Instance 改名後再 Infuser，Tag 會更新
- Instance 刪除後，Tag 會斷連
- 名稱格式錯誤時停止，不猜測拆分方式

## TAG_DW

### 適用範圍

門窗的人工標示。LoopFlow 2.0 不替 TAG_DW 尋找來源，也不從 Dictionary 或 Registry 自動填寫門窗資料。

### 人工內容

- 門窗編號
- 寬度
- 高度

### 使用方式

1. 插入 TAG_DW。
2. 在 Attribute UserText 手動填寫三個欄位。
3. 不執行 Grab、Laser 或 Index。

### 特殊規則

- 純手動，不接受 binding
- 沒有鎖定欄
- Infuser 不覆寫
- TAG-O 不把沒有來源判成未綁定
- LFDuplicateLayout 完整保留門窗編號、寬與高

## TAG_SECTION_DETAIL

### 適用範圍

在圖面上標示剖面或 Detail 所在的目標 Sheet。

### 使用方式

1. 先用 LFAnchorFrame 登記目標 View。
2. 確保目標 Layout 已完成 LFTaggerLayoutID。
3. 在目前 Layout 選取 TAG_SECTION_DETAIL。
4. 執行 **LFTaggerIndex**。
5. 從清單選取目標 Layout 的 Detail。
6. 執行 Infuser。

### 顯示內容

- 目標 Sheet 圖類別
- 目標 Sheet 圖號
- 人工 Detail 編號

### 注意

- Detail 編號是 manual 欄，Infuser 不填
- Index 綁定 View，不把 Detail GUID 當永久身分
- 目標 Layout 或 Detail 刪除後，Tag 會斷連
- 重新編號後通常只需再 Infuser，不必重做 Index

## TAG_ELEV_1～TAG_ELEV_4

### 適用範圍

四種方向或圖形版本的立面索引 Tag。四個 Block 外觀不同，但資料契約與操作相同。

實際 Block 名稱：

- <code>TAG_ELEV_1</code>
- <code>TAG_ELEV_2</code>
- <code>TAG_ELEV_3</code>
- <code>TAG_ELEV_4</code>

### 使用方式

與 TAG_SECTION_DETAIL 相同：

1. 選取適用方向的 TAG_ELEV_1～4。
2. 執行 **LFTaggerIndex**。
3. 選取目標 Layout 與 Detail。
4. 執行 Infuser。

### 顯示內容

- 目標 Sheet 圖類別
- 目標 Sheet 圖號
- 人工 Detail 編號

### 選擇原則

依圖面需要的方向圖形選 1、2、3 或 4；資料來源不因方向版本而改變。

## TAG_ELEV_0

### 適用範圍

顯示目前 Sheet 圖號，以及本頁立面方向／編號。它不是一般 Index Tag。

### 使用方式

1. 把 TAG_ELEV_0 放在 Layout。
2. 依需求手動填寫立面編號與方向欄。
3. 執行 **LFTaggerLayoutID**。
4. Layout ID 把目前 Sheet 圖號寫入 TAG_ELEV_0。

### 顯示內容

自動：

- 目前頁圖號

人工：

- 立面編號
- Elev
- Top
- Left
- Bottom
- Right

### 特殊規則

- 不接受 LFTaggerIndex
- Infuser 不處理
- TAG-O 不列入
- 鎖定後 Layout ID 不覆寫本頁圖號
- Duplicate Layout 後方向欄清空，等待使用者重新填寫

## Sample_Frame

### 適用範圍

LoopFlow 提供的圖框範例，用來說明圖框如何接收 Sheet metadata。專案可以登錄其他正式圖框，不必永遠使用 Sample_Frame。

### 顯示內容

由 LFTaggerLayoutID 寫入：

- 圖號
- 圖名

由使用者手動維護：

- 比例

### 使用方式

1. 在 Layout 放置一個圖框。
2. 執行 LFTaggerLayoutID。
3. 若圖框尚未登錄，在清單勾選真正的圖框 Block。
4. 確認後寫入圖號與圖名。

### 特殊規則

- 一頁應有恰好一個已登錄圖框
- LFTaggerLayoutID 不寫比例
- LFDuplicateLayout 保留比例，清空新頁圖號與圖名
- 未登錄 Block 預設不勾選，避免一般圖塊被誤認成圖框

## Grab、Laser、Index 怎麼選

| 情況 | 建議 |
|---|---|
| 可以直接點選清楚的來源物件 | Grab |
| 只有剖面圖上的位置，來源在 3D | Laser |
| 要連到另一張 Sheet 的 Detail | Index |
| 是 TAG_DW | 全手動，不綁定 |
| 是 TAG_ELEV_0 | Layout ID 寫本頁圖號 |
| 是圖框 | Layout ID 寫圖號與圖名 |

## Infuser Part 還是 All

- **LFInfuserPart**：只更新目前 Layout，適合局部修改與確認
- **LFInfuserAll**：更新全檔所有 Layout，適合發布後的全案同步

兩者使用相同規則，不需要依序執行。

## 不要直接修改的內容

除文件標示為人工欄的項目外，請不要手動更改：

- Tag ID
- Template ID
- Binding mode
- 來源物件 ID
- 目標 View／Sheet／Layout
- 同步 revision
- Health state
- 自動顯示欄

若 binding 錯誤，請重新使用 Grab、Laser 或 Index，不要直接修改隱藏 ID。

## 未知 Block

LoopFlow 只處理 Tag_Blocks.3dm 契約中已登錄的 Block。遇到未知 Block：

- 報告名稱
- 不寫入該 Block
- 不把相似名稱猜成已知 Tag
- 不會把一般 Block 自動登錄成圖框

## 相關文件

- [工作流程與快速開始](./README_TW.md)
- [Excel Dictionary](./DICTIONARY_TW.md)
- [Rhino 指令](./COMMANDS_TW.md)
- [文件入口](./README.md)
