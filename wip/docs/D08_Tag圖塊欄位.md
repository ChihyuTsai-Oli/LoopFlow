# LoopFlow 2.0 — D08 Tag 圖塊文字欄

本文件是 **LF-D08** 的 Rhino 操作指示。編輯在 Rhino 進行；AI 不直接改 `.3dm`。資料欄位以 `資料契約.md` 的「顯示欄 owner」為準。

目標：圖塊畫面上的字改讀 `lf_*`，不再讀舊名 `DWG_NO`、`Category` 等。改完之後，Infuser 寫入的資料才看得到。

## 開始前

1. **不要改** Git 裡的 `releases/LoopFlow/Tag_Blocks.3dm`（那是 1.x 發布檔）。
2. 把它複製到這台電腦的工作檔根目錄（環境變數 `LOOPFLOW_WORKFILES_ROOT`），例如 `source/Tag_Blocks.3dm`。
3. 再開一份測試用副本，例如 `source/Tag_Blocks_d08.3dm`。只改副本。
4. 用 Rhino 8 開啟副本。改完存檔後，先在測試 `.3dm` 插入新圖塊驗證，不要直接改正式專案。

固定字不要動：`Grab`、`Laser`、`W.`、`H.`、圖框上的專案名與日期。

**鎖定欄先不要改。** 畫面上仍是 `attr_Lock_不更新>寫入x或X`，繼續輸入 `x`／`X`。程式已認得。等 Infuser 再說。

## 在 Rhino 怎麼改一個欄位

對每個要改的圖塊：

1. 選畫面上該圖塊的一個實例。
2. 指令列輸入 `BlockEdit`，Enter。
3. 點選那一行**會變動的字**（不要點固定標籤）。
4. 右側內容 → 文字。找到公式，形如：

```text
%<UserText("block", "舊名字", "", "預設提示")>%
```

5. 只改第二個引號裡的**舊名字**，改成下表的新名字。前後空格、預設提示都維持原樣。
6. 關閉 BlockEdit 並儲存定義。
7. 做完一個圖塊，在該實例上看字是否還在；再用 Data Viewer 對不到新 key 屬正常（值要等 Layout ID／Infuser 寫入）。

圖框改完後，可在測試頁跑一次 `LF_Tagger_Layout_ID`：圖號／圖名應出現在新欄 `lf_drawing_no`／`lf_drawing_name`。**比例不會被 Layout ID 填上**（見下節）。

### 不要整批刪掉 UserText

改公式後，Attribute User Text 請**改名**，不要全刪再跑指令：

- `DWG_NO` → 可刪（Layout ID 會寫 `lf_drawing_no`）
- `DWG_NAME` → 可刪（Layout ID 會寫 `lf_drawing_name`）
- `03-A3 Scale` → **改名成** `lf_scale`，值留下。這欄是每張圖框自己填的，指令不寫。

若已經刪光、畫面比例變成 `####`：選圖框 → Attribute User Text → 新增 Key `lf_scale` → Value 填你的比例（例如 `1:50`）。`####` 是 Rhino 找不到這個 key，不是 Layout ID 壞掉。

## 對照表（舊 → 新）

### Height Grab／Laser（`Tag_Height_Grab`、`Tag_Height_Laser`）

| 舊 | 新 | 預設提示（維持） |
|---|---|---|
| `attr_ch_key` | `lf_elevation_basis` | `CH` |
| `attr_ch_val` | `lf_elevation_display` | `000` |
| `attr_mat_key` | `lf_type_category` | `PT` |
| `attr_mat_val` | `lf_type_sequence` | `00` |
| `attr_note` | `lf_type_display_name` | `材質名稱` |
| `attr_manual_補充說明` | `lf_remarks_manual` | `請輸入` |

### Finish Grab／Laser（`Tag_Finish_Grab`、`Tag_Finish_Laser`）

| 舊 | 新 | 預設提示（維持） |
|---|---|---|
| `attr_mat_key` | `lf_type_category` | `MT` |
| `attr_mat_val` | `lf_type_sequence` | `00` |
| `attr_note` | `lf_type_display_name` | `材質名稱` |
| `attr_manual_補充說明` | `lf_remarks_manual` | `請輸入` |

### Item（`Tag_Item`）

| 舊 | 新 | 預設提示（維持） |
|---|---|---|
| `attr_item_key` | `lf_item_category` | `FF` |
| `attr_item_val` | `lf_item_code` | `編號` |
| `attr_note` | `lf_item_name` | `家具` |
| `attr_manual_補充說明` | `lf_remarks_manual` | `請輸入` |

### DW（`TAG_DW`／`Tag_DW`）

無鎖定欄。三欄都是人工輸入，Sync 不覆寫。

| 舊 | 新 | 預設提示（維持） |
|---|---|---|
| `attr_dw_id` | `lf_dw_id` | `DW` |
| `attr_DW-W_輸入門窗寬` | `lf_dw_width` | `請輸入` |
| `attr_DW-H_輸入門窗高` | `lf_dw_height` | `請輸入` |

### Index（`tag_section_detail`、`TAG_ELEV_1`～`4`）

四個立面圖塊欄位相同，都要改。

| 舊 | 新 |
|---|---|
| `Category` | `lf_sheet_code` |
| `REF_ID` | `lf_sheet_ref` |
| `Detail_NO` | `lf_detail_no` |

`Category`／`REF_ID` 改完前，畫面圖號仍是舊欄；改完後要等 Infuser 才會填目標頁圖號。Layout ID **不**寫 Index 這兩欄。

### Elev 0（`tag_elev_0`／`TAG_ELEV_0`）

| 舊 | 新 | 誰寫入 |
|---|---|---|
| `Category` | `lf_sheet_code` | Layout ID（目前頁編號） |
| `1-Elev_num` | `lf_dir_num` | 人工 |
| `2-Elev` | `lf_dir_elev` | 人工 |
| `3-Top` | `lf_dir_top` | 人工 |
| `4-Left` | `lf_dir_left` | 人工 |
| `5-Bottom` | `lf_dir_bottom` | 人工 |
| `6-Right` | `lf_dir_right` | 人工 |

### 圖框（`Sample_Frame`，以及你專案裡真正使用的圖框）

專案圖框若不是 `Sample_Frame`，同樣三個欄位都要改，否則 Layout ID 寫了 `lf_*` 畫面仍空白。

| 舊 | 新 | 誰寫入 |
|---|---|---|
| `DWG_NO` | `lf_drawing_no` | Layout ID |
| `DWG_NAME` | `lf_drawing_name` | Layout ID |
| `03-A3 Scale` | `lf_scale` | **人工，每張自己填**；Layout ID 不寫。缺 key 時畫面會變 `####` |

## 改完怎麼確認

1. 仍用 `wip/tools/擷取tag_block文字.py` 選各圖塊實例，確認公式已是 `lf_*`，且沒有 `DWG_NO`、`DWG_NAME`、`Category`、`attr_mat_*` 等舊名（鎖定欄除外）。
2. 測試檔插入**新**圖框 → 跑 Layout ID → 圖號／圖名有字。比例須自己在 `lf_scale` 填，畫面不可為 `####`。
3. 舊專案裡已經插入的實例：公式隨 Block 定義更新；舊 UserText 名稱用 `LF_D08_Migrate_Display_Keys` 一次清掉。驗證請用副本。
4. 圖塊定義的公式改完後，各張圖上已插入的實例仍帶舊 UserText。不要逐個刪。跑開發指令 `LF_D08_Migrate_Display_Keys`：先把舊值抄到 `lf_*`（已有新欄不覆蓋，所以比例會留下來），再刪舊名字。鎖定欄不刪。取消則什麼都不改。清完後先不要跑 Layout ID，否則會把 `DWG_NO`／`DWG_NAME` 寫回來。
5. 告訴 AI 結果。通過後才停止 Layout ID 雙寫 `DWG_NO`／`DWG_NAME`，並更新 `fixtures/legacy/tag_block_text/`。

## 不要做

- 不要改巢狀裝飾線、引線、固定標籤
- 不要在這次改鎖定欄
- 不要開 Infuser／Extract／TAG-O
- 不要把改好的檔覆寫進 `releases/` 或正式專案
