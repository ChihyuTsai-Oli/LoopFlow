# LoopFlow 2.0 Tag Blocks 使用說明

LoopFlow 2.0 的正式 Tag 圖塊集中在 **Tag_Blocks.3dm**。只維護一份英文 Block library；繁中與英文文件說明同一組 Block，不另做中文圖塊檔。

本頁說明每個 Block 的內容、資料來源、適用範圍與配套指令。圖面上的固定字樣，例如 **Grab、Laser、W、H**，只是圖形標籤，不是資料欄位。

## 快速選擇

| 類別 | Block | 資料來源 | 建立／更新方式 |
|---|---|---|---|
| 高度 | <code>TAG_HEIGHT_GRAB</code> | 3D 物件或可回溯剖面線 | Grab → Infuser |
| 高度 | <code>TAG_HEIGHT_LASER</code> | 剖面點位射線命中的 3D 物件 | Laser → Infuser |
| 飾材 | <code>TAG_FINISH_GRAB</code> | 3D 物件或可回溯剖面線 | Grab → Infuser |
| 飾材 | <code>TAG_FINISH_LASER</code> | 剖面點位射線命中的 3D 物件 | Laser → Infuser |
| 家具／項目 | <code>TAG_ITEM</code> | Block 名稱與特定 instance | Grab → Infuser |
| 門窗 | <code>TAG_DW</code> | 全部人工 | 手動輸入 |
| 剖面索引 | <code>TAG_SECTION_DETAIL</code> | 其他 Layout 的 View／Sheet | Index → Infuser |
| 立面索引 | <code>TAG_ELEV_1</code>、<code>TAG_ELEV_2</code>、<code>TAG_ELEV_3</code>、<code>TAG_ELEV_4</code> | 其他 Layout 的 View／Sheet | Index → Infuser |
| 本頁立面 | <code>TAG_ELEV_0</code> | Current Sheet + 人工方向 | Layout ID |
| 圖框範例 | <code>Sample_Frame</code> | Current Sheet + 人工比例 | Layout ID |

## 資料權責

Tag 內的欄位分成三種：

| 權責 | 內容 | 維護方式 |
|---|---|---|
| 自動欄 | Type、高程、目標 Sheet、家具名稱、圖框圖號／圖名 | 由 Infuser 或 Layout ID 寫入 |
| 人工欄 | 備註、Detail 編號、門窗尺寸、立面方向、圖框比例 | 使用者在 Attribute UserText 輸入 |
| 系統欄 | Tag 身分、binding、來源／目標 ID、revision、health | 只供 LoopFlow 使用，不人工修改 |

Grab、Laser、Index 只建立 binding；除了 Layout ID 負責的本頁資料外，顯示值都由 Infuser 注入。Infuser 不覆寫人工欄。

## 共同行為

### 顯示狀態

| 狀態 | 自動欄 | TAG-O 顯示 | 處理 |
|---|---|---|---|
| 尚未綁定 | <code>-</code> | 不列為警示 | 使用適用的 Grab／Laser／Index |
| 正常 | 最新值 | 綠色 | 不需處理 |
| 過期 | <code>!</code> | 橘色 | 再執行 Infuser |
| 斷連 | <code>?</code> | 紅色 | 重新綁定，再 Infuser |

斷連代表來源物件、目標 Layout 或 Detail 已不存在。Infuser 不會直接替斷連 Tag 猜測新來源。

### 鎖定

支援鎖定的 Block，可在鎖定欄實際輸入 <code>x</code> 或 <code>X</code>：

- Grab／Laser／Index 不改 binding。
- Infuser 不覆寫顯示欄。
- TAG-O 仍列出狀態，但不改 Tag 的文字或顏色。

預設提示字不是鎖定。**TAG_DW 與 Sample_Frame 沒有鎖定欄。**

### Duplicate Layout

以 LFDuplicateLayout 建立新頁後：

- 新 Tag 取得新的 Tag ID。
- 除 TAG_DW 外，原 binding 清除，自動欄改為 <code>?</code>。
- 一般 Tag 的人工欄清空，鎖定狀態保留。
- TAG_DW 的人工編號、寬與高完整保留。
- TAG_ELEV_0 的方向欄清空，等待新頁重新輸入。

---

## Height Tags

### 適用 Block

- <code>TAG_HEIGHT_GRAB</code>
- <code>TAG_HEIGHT_LASER</code>

### 顯示內容

| 欄位 | 權責 | 來源 |
|---|---|---|
| 高程基準 | 自動 | Dictionary 的 elevation_basis |
| 計算高程 | 自動 | 3D instance 幾何與模型 Metadata |
| Type 類別／序號／名稱 | 自動 | Dictionary + Registry |
| 補充說明 | 人工 | 使用者 |

高程基準的意義：

| 值 | 計算基點 |
|---|---|
| <code>BH</code> | Bounding Box 底部 |
| <code>TH</code> | Bounding Box 頂部 |
| <code>CH</code> | 天花物件底部 |
| <code>BC</code> | Block instance 的插入基點（world Z） |

<code>BC</code> 不是 Bottom + Ceiling，也不是同時顯示底部與頂部。

### Grab 與 Laser

| 情況 | 使用 |
|---|---|
| 可直接點選 3D 物件、Section 線或 Extract 線稿 | TAG_HEIGHT_GRAB + LFTaggerGrab |
| 只能在剖面位置找 3D 來源 | TAG_HEIGHT_LASER + LFTaggerLaser |

Grab 的來源必須能回到唯一 3D UUID。Laser 必須先以 LFAnchorFrame 登記 View，點位也必須落在唯一 Anchor Frame；沒有唯一來源時停止，不猜測。

---

## Finish Tags

### 適用 Block

- <code>TAG_FINISH_GRAB</code>
- <code>TAG_FINISH_LASER</code>

### 顯示內容

| 欄位 | 權責 | 來源 |
|---|---|---|
| Type 類別／序號／名稱 | 自動 | Dictionary + Registry |
| 補充說明 | 人工 | 使用者 |

Finish Tag 適合牆面、地坪、天花與其他材質／Type 標示，不顯示高程。直接選來源時使用 Grab；從剖面點位射線找來源時使用 Laser。

---

## TAG_ITEM

用於家具或其他以 Block 名稱表達分類、編號與名稱的物件。

來源 Block 名稱格式：

<pre>分類-編號__名稱</pre>

例如 <code>FF-01__Chair-1</code> 會解析為：

| 欄位 | 顯示值 |
|---|---|
| Item 分類 | FF |
| Item 編號 | 01 |
| Item 名稱 | Chair-1 |
| 補充說明 | 人工輸入 |

使用 **LFTaggerGrab** 選取家具 Block instance，再執行 Infuser。LoopFlow 同時記住 Block 名稱與特定 instance；名稱格式錯誤或 instance 已刪除時不猜測。

---

## TAG_DW

門窗的純人工 Tag。LoopFlow 2.0 不替它尋找來源，也不從 Dictionary 或 Registry 填寫。

| 人工欄 | 用途 |
|---|---|
| ID | 門窗編號 |
| Width | 寬度 |
| Height | 高度 |

特殊規則：

- 不接受 Grab、Laser 或 Index。
- Infuser 不覆寫，TAG-O 不檢查 binding。
- 沒有鎖定欄。
- Duplicate Layout 完整保留三個人工欄。

---

## Index Tags

### 適用 Block

- <code>TAG_SECTION_DETAIL</code>
- <code>TAG_ELEV_1</code>
- <code>TAG_ELEV_2</code>
- <code>TAG_ELEV_3</code>
- <code>TAG_ELEV_4</code>

TAG_ELEV_1～4 只有方向圖形不同，資料契約與操作相同。

### 顯示內容

| 欄位 | 權責 | 來源 |
|---|---|---|
| 目標 Sheet 圖類別 | 自動 | 目標 Sheet metadata |
| 目標 Sheet 圖號 | 自動 | 目標 Sheet metadata |
| Detail 編號 | 人工 | 使用者 |

先登記目標 View、完成目標 Layout ID，再以 **LFTaggerIndex** 選取目標 Layout 與 Detail，最後執行 Infuser。

Index 綁定 View，不把 Detail GUID 當永久身分。目標 Sheet 重新編號後通常只需再 Infuser；目標 Layout 或 Detail 刪除後則會斷連。

---

## TAG_ELEV_0

顯示目前 Sheet 圖號及本頁立面方向。它不是連到其他頁的 Index Tag。

| 欄位 | 權責 |
|---|---|
| Current Sheet code | LFTaggerLayoutID 自動寫入 |
| dir_num | 人工 |
| elev | 人工 |
| top | 人工 |
| left | 人工 |
| bottom | 人工 |
| right | 人工 |

特殊規則：

- 不接受 LFTaggerIndex。
- Infuser 與 TAG-O 不處理。
- 可鎖定；鎖定後 Layout ID 不覆寫本頁圖號。
- Duplicate Layout 後方向欄清空。

---

## Sample_Frame

LoopFlow 提供的圖框範例，用來說明正式圖框如何接收 Sheet metadata。專案可以透過 LFTaggerLayoutID 登記自己的圖框，不必固定使用 Sample_Frame。

| 欄位 | 權責 |
|---|---|
| Drawing number | LFTaggerLayoutID 自動寫入 |
| Drawing name | LFTaggerLayoutID 自動寫入 |
| Scale | 人工 |

一頁應有恰好一個已登記圖框。Layout ID 不寫比例；Duplicate Layout 保留比例，並清空新頁圖號與圖名。Sample_Frame 沒有鎖定欄。

---

## Grab、Laser、Index 怎麼選

| 圖面情況 | 使用方式 |
|---|---|
| 可以直接點選清楚的來源 | Grab |
| 只有剖面位置，來源在 3D | Laser |
| 要連到另一張 Sheet 的 Detail | Index |
| TAG_DW | 全手動 |
| TAG_ELEV_0 | Layout ID 寫本頁圖號 |
| 圖框 | Layout ID 寫圖號與圖名 |

## Infuser Part 或 All

- **LFInfuserPart**：只更新目前 Layout，適合局部修改與確認。
- **LFInfuserAll**：更新全檔所有 Layout，適合發布後的全案同步。

兩者規則相同，不需依序執行。

## 不要直接修改系統欄

請不要人工更改 Tag ID、Template ID、binding mode、來源物件 ID、目標 View／Sheet／Layout、同步 revision、health state 或自動顯示欄。

Binding 錯誤時，應重新使用 Grab、Laser 或 Index。需要判讀 Tag 契約的寫入指令遇到未登錄 Block 時，會對該 Block 零寫入，並依指令報告或略過；系統不會用相似名稱猜測，也不會把一般 Block 自動登錄成圖框。

## 相關文件

- [一分鐘理解 LoopFlow 2.0](./README_TW.md)
- [Excel Dictionary](./DICTIONARY_TW.md)
- [Rhino 指令](./COMMANDS_TW.md)
- [文件入口](./README.md)
