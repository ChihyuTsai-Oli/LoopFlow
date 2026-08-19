# LoopFlow 2.0 — D08 Tag 圖塊文字欄

本文件是 **LF-D08** 的 Rhino 操作指示。編輯在 Rhino 進行；AI 不直接改 `.3dm`。資料欄位以 `資料契約.md` 的「顯示欄 owner」為準。

目標：圖塊畫面上的字改讀 `lf_*`，預設提示改英文。2.0 **只維護一份英文 `Tag_Blocks.3dm`**，日後不另做中文圖塊庫。

## 開始前

1. **不要改** Git 裡的 `releases/LoopFlow/Tag_Blocks.3dm`（那是 1.x 發布檔）。
2. 把它複製到這台電腦的工作檔根目錄（環境變數 `LOOPFLOW_WORKFILES_ROOT`），例如 `source/Tag_Blocks.3dm`。
3. 再開一份測試用副本，例如 `source/Tag_Blocks_d08.3dm`。只改副本。
4. 用 Rhino 8 開啟副本。改完存檔後，先在測試 `.3dm` 插入新圖塊驗證，不要直接改正式專案。

固定字不要動：`Grab`、`Laser`、`W.`、`H.`。圖框上的專案名與日期是專案內容，不是圖塊庫提示。

## 英文預設提示

公式第四段是空值時畫面上的提示，不是資料。這次連提示一起改成英文：

| 1.x | 2.0 |
|---|---|
| `x為不更新` | `x to lock` |
| `材質名稱` | `Type name` |
| `請輸入` | `Enter` |
| `編號` | `Code` |
| `家具` | `Furniture` |

`CH`、`000`、`PT`、`00`、`MT`、`FF`、`DW` 維持原樣。

鎖定欄這次也改：公式改讀 `lf_lock_state`，畫面上仍輸入 `x`／`X` 表示鎖定。空著或只看到 `x to lock` 都不算鎖定。

## 在 Rhino 怎麼改一個欄位

對每個要改的圖塊：

1. 選畫面上該圖塊的一個實例。
2. 指令列輸入 `BlockEdit`，Enter。
3. 點選那一行**會變動的字**（不要點固定標籤）。
4. 右側內容 → 文字。找到公式，形如：

```text
%<UserText("block", "舊名字", "", "舊提示")>%
```

5. 把**整行**換成下表對應的新公式（第二段是新 key，第四段是英文提示）。
6. 關閉 BlockEdit 並儲存定義。
7. 做完一個圖塊，在該實例上看字是否還在；再用 Data Viewer 對不到新 key 屬正常（值要等 Layout ID／Infuser 寫入）。

圖框改完後，可在測試頁跑一次 `LF_Tagger_Layout_ID`：圖號／圖名應出現在新欄 `lf_drawing_no`／`lf_drawing_name`。**比例不會被 Layout ID 填上**（見下節）。

### 不要整批刪掉 UserText

改公式後，Attribute User Text 請**改名**，不要全刪再跑指令：

- `DWG_NO` → 可刪（Layout ID 會寫 `lf_drawing_no`）
- `DWG_NAME` → 可刪（Layout ID 會寫 `lf_drawing_name`）
- `03-A3 Scale` → **改名成** `lf_scale`，值留下。這欄是每張圖框自己填的，指令不寫。

若已經刪光、畫面比例變成 `####`：選圖框 → Attribute User Text → 新增 Key `lf_scale` → Value 填你的比例（例如 `1:50`）。`####` 是 Rhino 找不到這個 key，不是 Layout ID 壞掉。

已插入的實例不要逐個改 UserText；公式改完後跑一次 `LF_D08_Migrate_Display_Keys`。

## 可貼上的新公式

### Height Grab／Laser（`Tag_Height_Grab`、`Tag_Height_Laser`）

| 舊公式 | 新公式 |
|---|---|
| `%<UserText("block", "attr_Lock_不更新>寫入x或X", "", "x為不更新")>%` | `%<UserText("block", "lf_lock_state", "", "x to lock")>%` |
| `%<UserText("block", "attr_ch_key", "", "CH")>%` | `%<UserText("block", "lf_elevation_basis", "", "CH")>%` |
| `%<UserText("block", "attr_ch_val", "", "000")>%` | `%<UserText("block", "lf_elevation_display", "", "000")>%` |
| `%<UserText("block", "attr_mat_key", "", "PT")>%` | `%<UserText("block", "lf_type_category", "", "PT")>%` |
| `%<UserText("block", "attr_mat_val", "", "00")>%` | `%<UserText("block", "lf_type_sequence", "", "00")>%` |
| `%<UserText("block", "attr_note", "", "材質名稱")>%` | `%<UserText("block", "lf_type_display_name", "", "Type name")>%` |
| `%<UserText("block", "attr_manual_補充說明", "", "請輸入")>%` | `%<UserText("block", "lf_remarks_manual", "", "Enter")>%` |

畫面固定字 `Grab`／`Laser` 不要改。

### Finish Grab／Laser（`Tag_Finish_Grab`、`Tag_Finish_Laser`）

| 舊公式 | 新公式 |
|---|---|
| `%<UserText("block", "attr_Lock_不更新>寫入x或X", "", "x為不更新")>%` | `%<UserText("block", "lf_lock_state", "", "x to lock")>%` |
| `%<UserText("block", "attr_mat_key", "", "MT")>%` | `%<UserText("block", "lf_type_category", "", "MT")>%` |
| `%<UserText("block", "attr_mat_val", "", "00")>%` | `%<UserText("block", "lf_type_sequence", "", "00")>%` |
| `%<UserText("block", "attr_note", "", "材質名稱")>%` | `%<UserText("block", "lf_type_display_name", "", "Type name")>%` |
| `%<UserText("block", "attr_manual_補充說明", "", "請輸入")>%` | `%<UserText("block", "lf_remarks_manual", "", "Enter")>%` |

### Item（`Tag_Item`）

| 舊公式 | 新公式 |
|---|---|
| `%<UserText("block", "attr_Lock_不更新>寫入x或X", "", "x為不更新")>%` | `%<UserText("block", "lf_lock_state", "", "x to lock")>%` |
| `%<UserText("block", "attr_item_key", "", "FF")>%` | `%<UserText("block", "lf_item_category", "", "FF")>%` |
| `%<UserText("block", "attr_item_val", "", "編號")>%` | `%<UserText("block", "lf_item_code", "", "Code")>%` |
| `%<UserText("block", "attr_note", "", "家具")>%` | `%<UserText("block", "lf_item_name", "", "Furniture")>%` |
| `%<UserText("block", "attr_manual_補充說明", "", "請輸入")>%` | `%<UserText("block", "lf_remarks_manual", "", "Enter")>%` |

### DW（`TAG_DW`／`Tag_DW`）

無鎖定欄。三欄都是人工輸入，Sync 不覆寫。`W.`／`H.` 不要改。

| 舊公式 | 新公式 |
|---|---|
| `%<UserText("block", "attr_dw_id", "", "DW")>%` | `%<UserText("block", "lf_dw_id", "", "DW")>%` |
| `%<UserText("block", "attr_DW-W_輸入門窗寬", "", "請輸入")>%` | `%<UserText("block", "lf_dw_width", "", "Enter")>%` |
| `%<UserText("block", "attr_DW-H_輸入門窗高", "", "請輸入")>%` | `%<UserText("block", "lf_dw_height", "", "Enter")>%` |

### Index（`tag_section_detail`、`TAG_ELEV_1`～`4`）

四個立面圖塊欄位相同，都要改。空提示維持空白。

| 舊公式 | 新公式 |
|---|---|
| `%<UserText("block", "attr_Lock_不更新>寫入x或X", "", "x為不更新")>%` | `%<UserText("block", "lf_lock_state", "", "x to lock")>%` |
| `%<UserText("block","Category","","")>%` | `%<UserText("block", "lf_sheet_code", "", "")>%` |
| `%<UserText("block","REF_ID","","")>%` | `%<UserText("block", "lf_sheet_ref", "", "")>%` |
| `%<UserText("block","Detail_NO","","")>%` | `%<UserText("block", "lf_detail_no", "", "")>%` |

`Category`／`REF_ID` 改完前，畫面圖號仍是舊欄；改完後要等 Infuser 才會填目標頁圖號。Layout ID **不**寫 Index 這兩欄。

### Elev 0（`tag_elev_0`／`TAG_ELEV_0`）

| 舊公式 | 新公式 | 誰寫入 |
|---|---|---|
| `%<UserText("block", "attr_Lock_不更新>寫入x或X", "", "x為不更新")>%` | `%<UserText("block", "lf_lock_state", "", "x to lock")>%` | 人工（`x`／`X` 鎖定） |
| `%<UserText("block","Category","","")>%` | `%<UserText("block", "lf_sheet_code", "", "")>%` | Layout ID（目前頁編號） |
| `%<UserText("block","1-Elev_num","","")>%` | `%<UserText("block", "lf_dir_num", "", "")>%` | 人工 |
| `%<UserText("block","2-Elev","","")>%` | `%<UserText("block", "lf_dir_elev", "", "")>%` | 人工 |
| `%<UserText("block","3-Top","","")>%` | `%<UserText("block", "lf_dir_top", "", "")>%` | 人工 |
| `%<UserText("block","4-Left","","")>%` | `%<UserText("block", "lf_dir_left", "", "")>%` | 人工 |
| `%<UserText("block","5-Bottom","","")>%` | `%<UserText("block", "lf_dir_bottom", "", "")>%` | 人工 |
| `%<UserText("block","6-Right","","")>%` | `%<UserText("block", "lf_dir_right", "", "")>%` | 人工 |

### 圖框（`Sample_Frame`，以及你專案裡真正使用的圖框）

專案圖框若不是 `Sample_Frame`，同樣三個欄位都要改，否則 Layout ID 寫了 `lf_*` 畫面仍空白。專案名與日期不要改成提示文字。

| 舊公式 | 新公式 | 誰寫入 |
|---|---|---|
| `%<UserText("block","DWG_NO","","")>%` | `%<UserText("block", "lf_drawing_no", "", "")>%` | Layout ID |
| `%<UserText("block","DWG_NAME","","")>%` | `%<UserText("block", "lf_drawing_name", "", "")>%` | Layout ID |
| `%<UserText("block","03-A3 Scale","","")>%` | `%<UserText("block", "lf_scale", "", "")>%` | **人工，每張自己填**；Layout ID 不寫。缺 key 時畫面會變 `####` |

## 改完怎麼確認

1. 仍用 `wip/tools/擷取tag_block文字.py` 選各圖塊實例，確認公式已是 `lf_*`、提示已是英文，且沒有 `DWG_NO`、`DWG_NAME`、`Category`、`attr_mat_*`、`attr_Lock_不更新>寫入x或X` 等舊名。
2. 測試檔插入**新**圖框 → 跑 Layout ID → 圖號／圖名有字。比例須自己在 `lf_scale` 填，畫面不可為 `####`。
3. 舊專案裡已經插入的實例：公式隨 Block 定義更新；舊 UserText 名稱用 `LF_D08_Migrate_Display_Keys` 一次清掉。驗證請用副本。
4. 圖塊定義的公式改完後，各張圖上已插入的實例仍帶舊 UserText。不要逐個刪。跑開發指令 `LF_D08_Migrate_Display_Keys`：先把舊值抄到 `lf_*`（已有新欄不覆蓋，所以比例會留下來），再刪舊名字。圖框上 1.x 殘留的 `Category`／`REF_ID` 會刪掉，不抄成 Index 欄。鎖定欄若寫 `x`／`X` 會抄到 `lf_lock_state` 後刪舊名字；畫面上的提示文字（`x為不更新`）只刪不抄。取消則什麼都不改。清完後先不要跑 Layout ID，否則會把 `DWG_NO`／`DWG_NAME` 寫回來。
5. 告訴 AI 結果。通過後才停止 Layout ID 雙寫 `DWG_NO`／`DWG_NAME`，並更新 `fixtures/legacy/tag_block_text/`。

## 不要做

- 不要改巢狀裝飾線、引線、固定標籤 `Grab`／`Laser`／`W.`／`H.`
- 不要開 Infuser／Extract／TAG-O
- 不要把改好的檔覆寫進 `releases/` 或正式專案
- 不要另存一份中文 `Tag_Blocks.3dm`；2.0 只維護這份英文圖塊庫
