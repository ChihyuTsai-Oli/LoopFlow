# LoopFlow 2.0 — 介面語系（英文定稿）

Claude 與 Codex 各自翻譯並互相校對後的整合定稿，來源為 `2_claude/介面語系_EN.md` 與 `2_codex/介面語系.md`。繁中欄未動。

定稿採用的一致規則：
- 原表已核可的英文欄（60 列）逐字保留，不因語感重寫。
- 取消一律拼 `cancelled`（雙 L），與已核可欄位一致。
- 句中的程式識別字（`type_id`、`schema_version` 等）不加反引號，避免反引號被當成介面文字顯示出來。
- 引號後的句號放在引號外（`"%s".`），避免句號被誤讀成名稱的一部分。
- 標點跟著繁中：繁中沒有句號的短語，英文也不加句號。
- 術語固定：定位點 anchors、圖目錄 drawing index、斷連 Disconnected、高程框／樓層框 level boundary、正式 Registry primary Registry。
- 按鈕與選單標籤用句首大寫（Select all），資料欄位標籤用標題大寫（Elevation Basis）。

這份是給人核對用的句子表，**不是程式執行時會讀的語系檔**。程式目前仍顯示繁中；記住語系選擇後，畫面要等句子接上這份表才會真的切換。

抽出去的：彈窗、按鈕、清單標題、成功／失敗說明、選單給人看的字。
留在程式裡的：註解、指令 ID、JSON／machine key、物件 UserText 鍵、網址與檔名。

English 欄是定稿，可直接改這份檔。`%s` 是程式填入的數字或名稱，翻譯時請保留。

## 語系切換（本批畫面）

| id | 繁中 | English |
|---|---|---|
| locale.title | LoopFlow | LoopFlow |
| locale.choose | 選擇介面語言 / Choose interface language | Choose interface language / 選擇介面語言 |
| locale.zh | 正體中文 | Traditional Chinese |
| locale.en | English | English |
| locale.hint | Document 按鈕右鍵切換語言介面 (LFLanguage) / Right-click Document to switch the UI (LFLanguage) | Right-click Document to switch the UI (LFLanguage) / Document 按鈕右鍵切換語言介面 (LFLanguage) |
| locale.saved.zh | 介面語言已設為正體中文。 | Interface language set to Traditional Chinese. |
| locale.saved.en | 介面語言已設為 English。 | Interface language set to English. |
| locale.cancelled.first | 已取消選擇語系。尚未記住，下次仍會詢問。 | Language choice cancelled. Nothing was saved; you will be asked again next time. |
| locale.cancelled.switch | 已取消切換語系。 | Language switch cancelled. |

## Dictionary 顯示欄名

官方範本：`wip/docs/字典/LoopFlow_Dictionary_tw.xlsx`、`LoopFlow_Dictionary_en.xlsx`。鍵本身不翻譯。下表是句子表對照；載入器目前仍認繁中欄名。

| id | 繁中（現況標題） | English（預定顯示） |
|---|---|---|
| dict.col.layer | __Rhino Layer | Rhino Layer |
| dict.col.space | _01_空間名稱 | _01_Space Name |
| dict.col.construction | _02_建構狀態 | _02_Construction |
| dict.col.type_id | _03_ID編號 | _03_Type ID |
| dict.col.type_name | _04_ID名稱 | _04_Type Name |
| dict.col.elev_basis | _05_高程基準 | _05_Elevation Basis |
| dict.col.elev_calc | _06_高程計算 | _06_Elevation Value |
| dict.col.uuid | _07_UUID | _07_UUID |
| dict.col.remarks | _08_備註 | _08_Remarks |
| dict.col.w | Q_01_寬度W | Q_01_Width W |
| dict.col.d | Q_02_深度D | Q_02_Depth D |
| dict.col.h | Q_03_高度H | Q_03_Height H |
| dict.col.unit | Q_04_單位 | Q_04_Unit |
| dict.col.rule | Q_05_計量規則 | Q_05_Measurement Rule |
| dict.col.qty | Q_06_實作數量 | Q_06_Quantity |

## 指令轉交

| id | 繁中 | English |
|---|---|---|
| `dispatch.001` | 警告：%s | Warning: %s |
| `dispatch.002` | 未知指令：%s | Unknown command: %s |

## Catalog（圖目錄）

| id | 繁中 | English |
|---|---|---|
| `catalog.001` | 目錄定位點是持久控制物件，建立目錄後請勿刪除；移動目錄時請連同定位點一起移動。 | Drawing-index anchors are persistent control objects. Do not delete them after creating the drawing index. If you move the index, move its anchors with it. |
| `catalog.002` | 圖名, 圖號 | Drawing name, drawing no. |
| `catalog.003` | 已讀取定位點。 | Anchors loaded. |
| `catalog.004` | 定位點已配對。 | Anchors paired. |
| `catalog.005` | 已匯出圖目錄 TXT。 | Drawing-index TXT exported. |
| `catalog.006` | 匯出圖目錄 TXT | Export drawing-index TXT |
| `catalog.007` | 已關閉圖目錄面板。 | Closed the drawing-index panel. |
| `catalog.008` | 文件尚未寫入 schema，已停止，不寫入。 | This document has no schema. Operation stopped; no changes were made. |
| `catalog.009` | 已載入 Tag templates | Tag templates loaded. |
| `catalog.010` | 找不到成對的圖號／圖名定位點，已停止，不寫入。 | No paired drawing-number and drawing-name anchors were found. Operation stopped; no changes were made. |
| `catalog.011` | 定位點混入多個圖目錄身分，已停止，不寫入。 | The anchors belong to more than one drawing index. Operation stopped; no changes were made. |
| `catalog.012` | 圖目錄身分不是合法 UUID，已停止，不寫入。 | The drawing-index ID is not a valid UUID. Operation stopped; no changes were made. |
| `catalog.013` | 已取消選取定位點，未寫入。 | Anchor selection cancelled. No changes were made. |
| `catalog.014` | 沒有圖目錄定位點可清除。 | There are no drawing-index anchors to clear. |
| `catalog.015` | 已取消清除定位點，未寫入。 | Clear operation cancelled. No changes were made. |
| `catalog.016` | 圖號與圖名定位點的逐頁數量不一致，已停止，不寫入。 | The drawing-number and drawing-name anchor counts differ on at least one page. Operation stopped; no changes were made. |
| `catalog.017` | 圖名定位點不在對應圖號的同一列，已停止，不寫入。 | A drawing-name anchor is not on the same row as its drawing-number anchor. Operation stopped; no changes were made. |
| `catalog.018` | 已建立圖目錄，寫入 %s 個文字。 | Drawing index created with %s text items. |
| `catalog.019` | 已更新圖目錄文字 %s 個。 | Updated %s drawing-index text items. |
| `catalog.020` | 圖號與圖名定位點的綁定不一致，已停止，不匯出。 | The drawing-number and drawing-name anchor bindings do not match. Export stopped. |
| `catalog.021` | Sheet metadata 已過期，請先執行 Layout ID，已停止，不匯出。 | Sheet metadata is out of date. Run Layout ID first. Export stopped. |
| `catalog.022` | Rhino 檔尚未儲存，請選擇圖目錄 TXT 的儲存位置。 | The Rhino file has not been saved yet. Choose where to save the drawing-index TXT. |
| `catalog.023` | 圖目錄核對清單 | Drawing-index review list |
| `catalog.024` | 沒有可列入目錄的 Layout。請先執行 Layout ID。 | There are no Layouts to include in the drawing index. Run Layout ID first. |
| `catalog.025` | LF_Catalog 圖目錄 | LF_Catalog drawing index |
| `catalog.026` | （空位） | (empty) |
| `catalog.027` | 圖號定位點必須是 Layout 上的獨立 Point，已停止，不寫入。 | Drawing-number anchors must be standalone Points on a Layout. Operation stopped; no changes were made. |
| `catalog.028` | 圖名定位點必須是 Layout 上的獨立 Point，已停止，不寫入。 | Drawing-name anchors must be standalone Points on a Layout. Operation stopped; no changes were made. |
| `catalog.029` | 未知的目錄欄位：%s。 | Unknown drawing-index field: %s. |
| `catalog.030` | 選取的定位點屬於不同圖目錄，已停止，不寫入。 | The selected anchors belong to different drawing indexes. Operation stopped; no changes were made. |
| `catalog.031` | 已歸位 %s 個%s定位點。 | Restored %s %s anchors to their original positions. |
| `catalog.032` | 將清除所有圖目錄定位點上的資料，把點放回原來的圖層，並刪除目錄文字。確定？ | This will clear all data from the drawing-index anchors, return the points to their original layers, and delete the index text. Continue? |
| `catalog.033` | 清除定位點 | Clear anchors |
| `catalog.034` | 已還原 %s 個定位點，刪除 %s 個目錄文字。 | Restored %s anchors and deleted %s drawing-index text items. |
| `catalog.035` | 定位點無法配對，已停止，不寫入。 | The anchors could not be paired. Operation stopped; no changes were made. |
| `catalog.036` | 尚未選取 Sheet，已停止，不寫入。 | No Sheets are selected. Operation stopped; no changes were made. |
| `catalog.037` | 選取的 Sheet 多於可用定位點，已停止，不寫入。 | More Sheets are selected than there are available anchors. Operation stopped; no changes were made. |
| `catalog.038` | Sheet metadata 已過期，請先執行 Layout ID，已停止，不寫入。 | Sheet metadata is out of date. Run Layout ID first. Operation stopped; no changes were made. |
| `catalog.039` | 已取消圖目錄寫入。 | Drawing-index update cancelled. |
| `catalog.040` | 略過 %s 列。 | Skipped %s rows. |
| `catalog.041` | 圖號與圖名定位點的綁定不一致，已停止，不寫入。 | The drawing-number and drawing-name anchor bindings do not match. Operation stopped; no changes were made. |
| `catalog.042` | 找不到 Eto 介面，無法開啟圖目錄面板。 | Eto UI is not available; cannot open the drawing-index panel. |
| `catalog.043` | 圖號定位點 %s　圖名定位點 %s　已選 Layout %s | Drawing-number anchors: %s　Drawing-name anchors: %s　Selected Layouts: %s |
| `catalog.044` | 選取圖號定位點（獨立 Point，Esc 取消） | Select drawing-number anchors (standalone Points; Esc to cancel) |
| `catalog.045` | 選取圖名定位點（獨立 Point，Esc 取消） | Select drawing-name anchors (standalone Points; Esc to cancel) |
| `catalog.046` | 選到 Block 或其子物件，已停止，不寫入。定位點必須是獨立 Point。 | A Block or Block sub-object was selected. Operation stopped; no changes were made. Anchors must be standalone Points. |
| `catalog.047` | 選到的不是獨立 Point，已停止，不寫入。 | The selection is not a standalone Point. Operation stopped; no changes were made. |
| `catalog.048` | 無法綁定 Sheet，已停止，不寫入。 | Could not bind the Sheet. Operation stopped; no changes were made. |
| `catalog.049` | 選取圖號定位點 | Select drawing-number anchors |
| `catalog.050` | 選取圖名定位點 | Select drawing-name anchors |
| `catalog.051` | 選取 Layout | Select Layout |
| `catalog.052` | 生成 圖號/圖名 | Generate number/name |
| `catalog.053` | 清除定位點並還原圖層 | Clear anchors and restore layers |
| `catalog.054` | 匯出 TXT | Export TXT |
| `catalog.055` | 圖號 | Drawing no. |
| `catalog.056` | 圖名 | Drawing name |

## Dictionary／開字典／匯出

| id | 繁中 | English |
|---|---|---|
| `dictionary.001` | Dictionary 含有禁止的 _CB.* 欄，已停止。 | The Dictionary contains a prohibited _CB.* column. Operation stopped. |
| `dictionary.002` | Dictionary 欄名與 schema 1 不符，已停止。不靠欄名前綴猜測。 | The Dictionary columns do not match schema 1. Operation stopped; column prefixes will not be used to guess the schema. |
| `dictionary.003` | 已載入 Dictionary，%s 筆 Type。 | Dictionary loaded with %s Types. |
| `dictionary.004` | Dictionary 應為 15 欄，實際為 %s 欄。已停止。 | The Dictionary must have 15 columns; %s were found. Operation stopped. |
| `dictionary.005` | 未知 Dictionary 版本標題：%s。已停止，不猜測解析。 | Unknown Dictionary version header: %s. Operation stopped; the format will not be guessed. |
| `dictionary.006` | Dictionary 驗證失敗 %s 項，已停止。 | Dictionary validation failed with %s issues. Operation stopped. |
| `dictionary.007` | 已載入 Dictionary，%s 筆 Type，%s 則警告。 | Dictionary loaded with %s Types and %s warnings. |
| `dictionary.008` | 找不到 Dictionary 檔案 %s。請把它放回 .3dm 所在的資料夾，或改用該資料夾內的其他 .xlsx。不建立檔案。 | Dictionary file %s was not found. Put it back in the same folder as the .3dm file, or choose another .xlsx file in that folder. No file was created. |
| `dictionary.009` | (空白) | (blank) |
| `dictionary.010` | 第 %s 列計量規則未定義，quantity 將為空。 | The measurement rule is not defined on row %s. Quantity will be left blank. |
| `dictionary.011` | 第 %s 列計算欄 %s 應留白，已忽略。 | On row %s, calculation field %s should be blank and was ignored. |
| `dictionary.012` | 第 %s 列缺少 layer_path。 | Row %s is missing layer_path. |
| `dictionary.013` | 第 %s 列：%s | Row %s: %s |
| `dictionary.014` | 第 %s 列 type_id 與第 %s 列重複：%s | Row %s has a type_id that duplicates row %s: %s |
| `dictionary.015` | 第 %s 列 layer_path 與第 %s 列重複。 | Row %s has a layer_path that duplicates row %s. |
| `dictionary.016` | 第 %s 列高程基準不合法：%s | Row %s has an invalid elevation basis: %s |
| `dictionary.017` | 第 %s 列單位／計量規則量綱不符或未知：%s／%s | The unit and measurement rule on row %s have incompatible or unknown dimensions: %s / %s |
| `dictionary.018` | 第 %s 列缺少 type_display_name。 | Row %s is missing type_display_name. |
| `dictionary.019` | 這份檔案還沒指定 Dictionary，找不到要開的檔。請先存檔，再用 Nexus 選單 2 指定與 .3dm 同資料夾的 .xlsx。 | No Dictionary has been assigned to this file. Save the file first, then use Nexus menu 2 to choose an .xlsx file from the same folder as the .3dm file. |
| `dictionary.020` | 找不到 Dictionary 檔案 %s。請把字典移回 .3dm 所在的資料夾，或用 Nexus 選單 2 重新指定同資料夾內的 .xlsx。 | Dictionary file %s was not found. Put it back in the same folder as the .3dm file, or use Nexus menu 2 to choose another .xlsx file in that folder. |
| `dictionary.021` | 找不到匯出檔 %s。請先執行 LF_Export_Type_Layers。 | Export file %s was not found. Run LF_Export_Type_Layers first. |
| `dictionary.022` | 已找到 %s | Found %s. |
| `dictionary.023` | 已開啟匯出字典 %s。 | Opened exported Dictionary %s. |
| `dictionary.024` | 已開啟原字典 %s。 | Opened source Dictionary %s. |
| `dictionary.025` | 未知的字典檔種類：%s | Unknown Dictionary file type: %s |
| `dictionary.026` | 無法開啟 %s：%s | Could not open %s: %s |
| `dictionary.027` | 缺少 type_id。 | Missing type_id. |
| `dictionary.028` | 未知 type_category，無法拆分 type_id：%s | Unknown type_category; cannot split type_id: %s |
| `dictionary.029` | 已拆分 type_id | type_id split successfully. |
| `dictionary.030` | type_id 缺少序號：%s | type_id is missing a sequence number: %s |
| `dictionary.031` | 此檔只供核對，不能當正式字典開啟，也不可覆寫 %s。藍字 added_in_rhino 合併時必須給新的 _03_ID編號，不可沿用舊圖層編號。 | This file is for review only. It cannot be opened as the project Dictionary or overwrite %s. When merging blue added_in_rhino entries, assign each one a new _03_Type ID; do not reuse an old layer number. |
| `dictionary.032` | layer 已同步，可存檔。Scan／Apply／發布尚未實作。 | Layers are in sync and the file can be saved. Scan, Apply, and Publish are not implemented yet. |
| `dictionary.033` | Type layer 同步完成（%s）：新建 %s、保留 %s。 | Type Layer sync complete (%s): %s created, %s retained. |
| `dictionary.034` | 找不到字典 %s。請把字典移回 .3dm 所在的資料夾（字典可以改名），接著在開啟的視窗選這份專案要用的 .xlsx。 | Dictionary %s was not found. Put it back in the same folder as the .3dm file (the Dictionary may be renamed), then choose the .xlsx file for this project in the window that opens. |
| `dictionary.035` | 已匯出 layer 差異，未改正式 Dictionary。 | Layer differences exported. The project Dictionary was not changed. |
| `dictionary.036` | 使用者取消 Type layer 同步。 | Type Layer sync cancelled. |
| `dictionary.037` | 反向匯出不得覆寫正式 Dictionary。 | A reverse export cannot overwrite the project Dictionary. |
| `dictionary.038` | 匯出目錄不存在，不建立。 | The export folder does not exist and will not be created. |
| `dictionary.039` | 已在 .3dm 同資料夾匯出 %s，未改正式 Dictionary。 | Exported %s to the same folder as the .3dm file. The project Dictionary was not changed. |
| `dictionary.040` | Type layer 同步失敗，已還原本次新增圖層與參考線。 | Type Layer sync failed. Layers and reference lines created during this run were removed. |
| `dictionary.041` | 已排除 %s 個 20_DW 子圖層，不建 Type。 | Excluded %s sublayers under 20_DW; no Types were created for them. |
| `dictionary.042` | 專案名稱不能空白，也不能含 : \ / * ? " < > \| | The project name cannot be blank or contain `: \ / * ? " < > \|`. |
| `dictionary.043` | 匯出 Type Layers 不得覆寫正式 Dictionary。 | Export Type Layers cannot overwrite the project Dictionary. |
| `dictionary.044` | 使用者取消輸入專案名稱。 | Project-name entry cancelled. |
| `dictionary.045` | 使用者取消選擇 Dictionary。 | Dictionary selection cancelled. |

## Document／語系

| id | 繁中 | English |
|---|---|---|
| `document.001` | 正體中文 | Traditional Chinese |
| `document.002` | 介面語言已設為正體中文。 | Interface language set to Traditional Chinese. |
| `document.003` | 介面語言已設為 English。 | Interface language set to English. |
| `document.004` | 已取消選擇語系。尚未記住，下次仍會詢問。 | Language choice cancelled. Nothing was saved; you will be asked again next time. |
| `document.005` | 已取消切換語系。 | Language switch cancelled. |
| `document.006` | 找不到語系選單介面。 | Language menu is not available. |
| `document.007` | 已開啟 LoopFlow 使用說明。 | Opened the LoopFlow documentation. |
| `document.008` | 無法開啟 LoopFlow 文件頁。 / %s | Could not open the LoopFlow documentation page. / %s |

## Extract CP

| id | 繁中 | English |
|---|---|---|
| `extract_cp.001` | 沒有對到 View。 | No matching View was found. |
| `extract_cp.002` | 勾選要抽出的剖面圖層（可複選）： | Select the section layers to extract (multiple selection allowed): |
| `extract_cp.003` | 抽出可編輯線稿 | Extract editable linework |
| `extract_cp.004` | 辨識前次產出 | Previous output detected |
| `extract_cp.005` | 已抽出可編輯線稿。 | Editable linework extracted. |
| `extract_cp.006` | 沒有根圖層名。 | Missing root layer name. |
| `extract_cp.007` | 已對到 View。 | Matching View found. |
| `extract_cp.008` | 已抽出「%s」%s 個物件。 | Extracted "%s": %s objects. |
| `extract_cp.009` | 抽出完成：複製 %s 個物件。 | Extraction complete: %s objects copied. |
| `extract_cp.010` | 「%s」已有前次抽出。請選取代、新增或略過。 | A previous extraction exists for "%s". Choose Replace, Add New, or Skip. |
| `extract_cp.011` | 複製 %s 個物件到 %s。 | Copied %s objects to %s. |
| `extract_cp.012` | 來源索引：唯一 %s、無法辨識 %s、多來源 %s。 | Source index: %s unique, %s unidentified, %s with multiple sources. |
| `extract_cp.013` | 索引不完整仍已產出，不阻擋。 | Output was created despite an incomplete index. |
| `extract_cp.014` | 沒有 Rhino session。 | No Rhino session is available. |
| `extract_cp.015` | 剖面圖層「%s」對到兩個以上 View，已跳過，不猜測。 | Section layer "%s" matches more than one View and was skipped. No match was guessed. |
| `extract_cp.016` | 略過 %s 個已有產出的剖面。 | Skipped %s sections with existing output. |
| `extract_cp.017` | 請在 2D 模型空間執行 Extract，不要在 Layout 頁。 | Run Extract in 2D model space, not on a Layout page. |
| `extract_cp.018` | 找不到 Clipping Drawing 的 Visible／Hatch／Curve 圖層。 | No Visible, Hatch, or Curve layers were found for the Clipping Drawing. |
| `extract_cp.019` | 已取消抽出。 | Extraction cancelled. |
| `extract_cp.020` | 沒有勾選剖面圖層。 | No section layers are selected. |
| `extract_cp.021` | 已略過「%s」的前次產出。 | Skipped the previous output for "%s". |
| `extract_cp.022` | 未知的重跑選項。 | Unknown rerun option. |
| `extract_cp.023` | 此 Rhino session 不能複製物件。 | This Rhino session cannot copy objects. |
| `extract_cp.024` | 「%s」的 Drawing 已人工修改，不會覆蓋。若要另存一版請選新增。 | The Drawing for "%s" was edited manually and will not be overwritten. Choose Add New to create another version. |
| `extract_cp.025` | 取代前次產出 | Replace previous output |
| `extract_cp.026` | 新增一版（保留舊的） | Add a new version (keep the old one) |
| `extract_cp.027` | 略過 | Skip |

## TAG-O

| id | 繁中 | English |
|---|---|---|
| `tag_o.001` | （未分頁） | (no page) |
| `tag_o.002` | 正常 | OK |
| `tag_o.003` | 缺來源 | Source missing |
| `tag_o.004` | 斷連 | Disconnected |
| `tag_o.005` | 過期 | Out of date |
| `tag_o.006` | 未檢查 | Not checked |
| `tag_o.007` | （未存檔） | (unsaved) |
| `tag_o.008` | 過期會把自動欄改成 ! 並塗橘；斷連改成 ? 並塗紅。Repair 尚未實作。 | Out-of-date Tags show ! in auto-filled fields and are highlighted orange. Disconnected Tags show ? and are highlighted red. Repair is not implemented yet. |
| `tag_o.009` | 沒有空間框，略過覆蓋檢查 | No space boundaries; coverage check skipped |
| `tag_o.010` | 過期塗橘寫 !，斷連塗紅寫 ?。未綁定不列出。Repair 尚未實作。 | Out-of-date Tags show ! in orange; disconnected Tags show ? in red. Unbound Tags are not listed. Repair is not implemented yet. |
| `tag_o.011` | 已檢查 %s 個 Tag。 | Checked %s Tags. |
| `tag_o.012` | 活著 %s。 | Active: %s. |
| `tag_o.013` | 過期未同步 | Out of date and not synced |
| `tag_o.014` | 過期／歧義 | Out of date / ambiguous |
| `tag_o.015` | 這份檔案沒有 Layout 頁，已停止，不寫入。 | This file has no Layout pages. Operation stopped; no changes were made. |
| `tag_o.016` | 檔案：%s | File: %s |
| `tag_o.017` | 掃描：%s | Scan: %s |
| `tag_o.018` | 已掃描 %s 個 Tag | Scanned %s Tags |
| `tag_o.019` | ── Tag 綁定狀態  （%s 項）── | ── Tag binding status (%s items) ── |
| `tag_o.020` | （鎖定） | (locked) |
| `tag_o.021` | 點選項目可跳到該 Tag（略拉開以看見圖框） | Select an item to jump to its Tag (the view zooms out slightly to show the title block) |
| `tag_o.022` | ── 未被 Finish Tag 涵蓋的空間 ── | ── Spaces not covered by a Finish Tag ── |
| `tag_o.023` | 所有空間都有 Finish Tag | Every space has a Finish Tag |
| `tag_o.024` | 斷連：%s。 | Disconnected: %s. |
| `tag_o.025` | 鎖定仍斷連 %s。 | Locked but still disconnected: %s. |
| `tag_o.026` | 未檢查（未知圖塊）%s，不計入通過。 | Not checked (unknown Block): %s. These do not count as passing. |
| `tag_o.027` | 圖框 %s | Title blocks: %s |
| `tag_o.028` | 門窗 %s | Doors/windows: %s |
| `tag_o.029` | 涵蓋但不判 unbound：%s。 | Covered but not considered unbound: %s. |
| `tag_o.030` | 沒有掃到可檢查的 Tag | No checkable Tags were found |
| `tag_o.031` | 沒有已綁定的 Tag | No bound Tags were found |
| `tag_o.032` | （未命名頁） | (unnamed page) |
| `tag_o.033` | ── 未被 Finish Tag 涵蓋的空間  （%s）── | ── Spaces not covered by a Finish Tag (%s) ── |
| `tag_o.034` | ［說明］%s | [Details] %s |
| `tag_o.035` | 沒有 Registry，無法判斷過期，仍檢查來源是否還在。 | No Registry is available, so out-of-date status cannot be determined. Source availability will still be checked. |
| `tag_o.036` | 正式 Registry 不在，改用 last-good。 | The primary Registry is unavailable. Using last-good instead. |
| `tag_o.037` | 尚未填專案名稱，無法讀 Registry。請先跑 Nexus 選單 2。 | The project name has not been set, so the Registry cannot be read. Run Nexus menu 2 first. |

## Infuser

| id | 繁中 | English |
|---|---|---|
| `infuser.001` | 全檔 | Entire file |
| `infuser.002` | 有些 Height／Finish 是從模型現況讀的，尚未進 Registry。 | Some Height/Finish values are read from the model's current state and have not been written to the Registry yet. |
| `infuser.003` | 尚未進 Registry | Not in the Registry yet |
| `infuser.004` | 已處理 %s 頁 Layout。 | Processed %s Layout pages. |
| `infuser.005` | 已從目標 View 對到 Sheet。 | Matched the target View to a Sheet. |
| `infuser.006` | 已解析家具名稱。 | Furniture name resolved. |
| `infuser.007` | 目標 View 的頁沒有 Sheet metadata。請先跑 Layout ID。 | The target View's page has no Sheet metadata. Run Layout ID first. |
| `infuser.008` | 目標 View 對到兩個以上 Sheet，不猜測。 | The target View matches more than one Sheet. No match was guessed. |
| `infuser.009` | 目標 Sheet 沒有圖號資料。 | The target Sheet has no drawing-number data. |
| `infuser.010` | Index Tag 沒有目標 View。 | The Index Tag has no target View. |
| `infuser.011` | 綁定的目標 Detail 已不在。 | The bound target Detail no longer exists. |
| `infuser.012` | 家具 Tag 沒有來源 Block 名稱。 | The furniture Tag has no source Block name. |
| `infuser.013` | 已處理 Layout 頁「%s」。 | Processed Layout page "%s". |
| `infuser.014` | 已注入 %s 個 Tag。 | Updated %s Tags. |
| `infuser.015` | 鎖定 | Locked |
| `infuser.016` | 門窗／手動 | Door/window or manual |
| `infuser.017` | 圖框 | Title block |
| `infuser.018` | 未知圖塊 | Unknown Block |
| `infuser.019` | Registry 找不到物件 | Object not found in Registry |
| `infuser.020` | 沒有 Registry（請先發布） | No Registry (publish first) |
| `infuser.021` | 來源歧義 | Ambiguous source |
| `infuser.022` | 家具名稱不符 | Furniture name mismatch |
| `infuser.023` | 缺目標圖號 | Missing target drawing number |
| `infuser.024` | 目標消失 | Target no longer exists |
| `infuser.025` | 斷連未灌回 | Disconnected; values not updated |
| `infuser.026` | 請在 Layout 頁執行 Infuser Part。已停止，不寫入。 | Run Infuser Part on a Layout page. Operation stopped; no changes were made. |
| `infuser.027` | 無法判斷目前 Layout 頁，已停止，不寫入。 | The current Layout page could not be identified. Operation stopped; no changes were made. |
| `infuser.028` | 已從目標頁名讀到圖號。 | Drawing number read from the target page name. |
| `infuser.029` | 綁定的目標 Layout 已不在。 | The bound target Layout no longer exists. |
| `infuser.030` | 已用目標 Sheet。 | Used the target Sheet. |
| `infuser.031` | 家具 Block 名稱「%s」不符合 FF-01__Chair-1。 | Furniture Block name "%s" does not match the expected format FF-01__Chair-1. |
| `infuser.032` | 跳過：%s。 | Skipped: %s. |
| `infuser.033` | 警告：%s。 | Warning: %s. |
| `infuser.034` | …另有 %s 則。 | …and %s more. |
| `infuser.035` | 找不到 Registry，將只注入不需 Registry 的 Tag。 | No Registry was found. Only Tags that do not require the Registry will be updated. |
| `infuser.036` | 已讀取 Registry revision %s。 | Registry revision %s loaded. |
| `infuser.037` | 尚未填專案名稱，無法讀 Registry。請先跑 Nexus 選單 2 從字典同步 Type Layers。 | The project name has not been set, so the Registry cannot be read. Run Nexus menu 2 to sync Type Layers from the Dictionary first. |
| `infuser.038` | Registry 無法讀取：%s | Could not read the Registry: %s |
| `infuser.039` | Registry 不合規，已停止，不注入。%s | The Registry is invalid. Operation stopped; no Tags were updated. %s |
| `infuser.040` | 正式 Registry 不在，改用 last-good revision %s。 | The primary Registry is unavailable. Using last-good revision %s. |

## Nexus 寫入／檢核 Metadata

| id | 繁中 | English |
|---|---|---|
| `nexus_metadata.001` | Identity Verify 通過。Space／高程尚未資料化，不可發布。 | Identity verification passed. Space and elevation data are not ready, so publishing is unavailable. |
| `nexus_metadata.002` | 已使用注入的 Type Catalog。 | Using the injected Type Catalog. |
| `nexus_metadata.003` | 已 Apply %s 個物件的 ID／Type。未寫 Space／高程。不可發布。 | Applied ID and Type data to %s objects. Space and elevation data were not written. Publishing is unavailable. |
| `nexus_metadata.004` | 使用者取消 Scan。 | Scan cancelled. |
| `nexus_metadata.005` | 局部 Scan 完成，%s 個物件。不得宣告全案可發布。 | Partial scan completed for %s objects. This does not confirm that the entire project is ready to publish. |
| `nexus_metadata.006` | 正式 Scan 完成，%s 個物件。尚未寫入。不可發布。 | Full scan completed for %s objects. No data has been written, so publishing is unavailable. |
| `nexus_metadata.007` | 使用者取消 Apply。 | Apply cancelled. |
| `nexus_metadata.008` | Verify 仍有 %s 項未完成。不可發布。 | Verification still has %s unresolved issues. Publishing is unavailable. |
| `nexus_metadata.009` | 使用者取消 rollback。 | Rollback cancelled. |
| `nexus_metadata.010` | 沒有 ID mapping 可還原。 | No ID mapping to roll back. |
| `nexus_metadata.011` | 已還原 %s 個 object_id。 | Restored %s object_id values. |
| `nexus_metadata.012` | mapping 的新 ID 必須是小寫 UUID v4。 | The mapping's new ID must be a lowercase UUID v4. |
| `nexus_metadata.013` | Apply 後仍會發生 object_id 碰撞，已停止，不靜默換號。 | Applying this mapping would still create duplicate object_id values. Operation stopped; IDs were not reassigned automatically. |
| `nexus_metadata.014` | 沒有可寫入的物件。剩餘 %s 項需 mapping 或修正 Type。 | There are no objects ready to update. The remaining %s items need an ID mapping or Type correction. |
| `nexus_metadata.015` | 剩餘 %s 項。 | %s items remaining. |
| `nexus_metadata.016` | 此物件同時落在多個空間。請選擇所屬空間： | This object falls inside more than one space. Choose which space it belongs to: |
| `nexus_metadata.017` | 已 Apply Space／高程。不可發布。 | Space and elevation data applied. Publishing is unavailable. |
| `nexus_metadata.018` | Space／高程 Scan 完成，%s 個物件、%s 個 EXT。不可發布。 | Space/elevation scan completed: %s objects and %s EXT. Publishing is unavailable. |
| `nexus_metadata.019` | 使用者取消 Space／高程 Scan。 | Space/elevation scan cancelled. |
| `nexus_metadata.020` | 使用者取消 Space／高程 Apply。 | Applying Space/elevation data was cancelled. |
| `nexus_metadata.021` | 沒有可寫入的 Space／高程。 | No Space/elevation data to write. |
| `nexus_metadata.022` | 已登記 %s 個 Space Boundary。未改模型物件空間欄。 | Registered %s Space Boundaries. Model object Space fields were not changed. |
| `nexus_metadata.023` | 使用者取消高程框。 | Level-boundary selection cancelled. |
| `nexus_metadata.024` | 高程框請選 FFL 或 FL。 | Choose FFL or FL for the level boundary. |
| `nexus_metadata.025` | 高程必須是數字，例如 0 或 320。 | Elevation must be a number, e.g. 0 or 320. |
| `nexus_metadata.026` | 沒有選取高程框。請選取封閉曲線後按 Enter。 | No level boundaries are selected. Select closed curves, then press Enter. |
| `nexus_metadata.027` | 已登記 %s 個 %s 高程框（高程 %s）。 | Registered %s %s level boundaries at elevation %s. |
| `nexus_metadata.028` | 使用者取消 Space Boundary。 | Space Boundary registration cancelled. |
| `nexus_metadata.029` | 沒有選取 Space Boundary。請選取封閉曲線後再執行。 | No Space Boundaries are selected. Select closed curves, then run the command again. |
| `nexus_metadata.030` | 同一個 space_id 出現在多條 boundary，已停止，不靜默換號。 | The same space_id appears on multiple boundaries. Operation stopped; IDs were not reassigned automatically. |
| `nexus_metadata.031` | 平面重疊但樓層不同（已允許）：%s。同樓層請對到同一個樓層框。 | Plan overlap on different levels is allowed: %s. For the same level, use the same level boundary. |
| `nexus_metadata.032` | 有 %s 條無效曲線（未封閉或頂點不足）。 | %s curves are invalid (open or too few vertices). |
| `nexus_metadata.033` | 高程框類型 | Level boundary type |
| `nexus_metadata.034` | 請選擇高程框類型 | Choose the level boundary type |
| `nexus_metadata.035` | 使用者取消高程框類型。 | Level boundary type selection cancelled. |
| `nexus_metadata.036` | 使用者取消選取高程框。 | Level-boundary selection cancelled. |
| `nexus_metadata.037` | 高程（例如 0 或 320） | Elevation (e.g. 0 or 320) |
| `nexus_metadata.038` | 使用者取消輸入高程。 | Elevation entry cancelled. |
| `nexus_metadata.039` | 使用者取消選取空間框。 | Space-boundary selection cancelled. |
| `nexus_metadata.040` | 空間名稱 | Space name |
| `nexus_metadata.041` | 使用者取消輸入空間名稱。 | Space-name entry cancelled. |
| `nexus_metadata.042` | 有 %s 條無效曲線（未封閉、頂點不足、或缺名稱／樓層）。 | %s curves are invalid (open, too few vertices, or missing a name or level). |
| `nexus_metadata.043` | 有 %s 個空間同時對到多個同高程樓層框，已停止。 | %s spaces match multiple level boundaries at the same elevation. Operation stopped. |
| `nexus_metadata.044` | 有 %s 個空間對不到樓層框。空間框須與樓層框高程差在 ±%s 內，且整圈在樓層框裡面。 | %s spaces do not match a level boundary. A space boundary must be within ±%s in elevation of a level boundary and entirely inside it. |
| `nexus_metadata.045` | Space 面積重疊（同一樓層），已停止。衝突：%s | Spaces overlap on the same level. Operation stopped. Conflicts: %s |
| `nexus_metadata.046` | 請執行 Nexus 5 寫入模型 Metadata，把正確資料寫回。 | Run Nexus 5 — Write Model Metadata to write the correct data back to the model. |
| `nexus_metadata.047` | ID編號 | Type ID |
| `nexus_metadata.048` | 類型類別 | Type Category |
| `nexus_metadata.049` | 類型序號 | Type Sequence |
| `nexus_metadata.050` | 建構狀態 | Construction Status |
| `nexus_metadata.051` | 備註 | Remarks |
| `nexus_metadata.052` | 資料版次 | Data Revision |
| `nexus_metadata.053` | 空間ID | Space ID |
| `nexus_metadata.054` | 高程基準 | Elevation Basis |
| `nexus_metadata.055` | 高程計算 | Elevation Value |
| `nexus_metadata.056` | 高程顯示 | Elevation Display |
| `nexus_metadata.057` | 尚未寫入 UUID | UUID not assigned |
| `nexus_metadata.058` | UUID 格式不正確 | Invalid UUID format |
| `nexus_metadata.059` | UUID 重複 | Duplicate UUID |
| `nexus_metadata.060` | 未知 Type | Unknown Type |
| `nexus_metadata.061` | 圖層未對應 Dictionary | Layer not mapped in Dictionary |
| `nexus_metadata.062` | 空間命中不唯一 | Ambiguous space match |
| `nexus_metadata.063` | 高程基準 BC 但不是圖塊 | Elevation basis is BC, but the object is not a Block |
| `nexus_metadata.064` | 高程基準不合法 | Invalid elevation basis |
| `nexus_metadata.065` | 取不到範圍 | Bounding box unavailable |
| `nexus_metadata.066` | 殘留尺寸／數量欄 | Obsolete size/quantity fields |
| `nexus_metadata.067` | 檢核發現 %s 個物件不符。 | Verification found %s noncompliant objects. |
| `nexus_metadata.068` | 不符合的物件已選取： | The noncompliant objects are selected: |
| `nexus_metadata.069` | 檢核通過。%s 個物件的資料與寫入結果相符。 | Verification passed. Data for %s objects matches the written values. |
| `nexus_metadata.070` | 尚未通過檢核，不能發布。 | Verification has not passed. Publishing is unavailable. |
| `nexus_metadata.071` | …其餘 %s 項。 | …and %s more. |
| `nexus_metadata.072` | 使用者取消檢核。 | Verification cancelled. |
| `nexus_metadata.073` | %s 尚未寫入（應為 %s） | %s has not been written (expected %s) |
| `nexus_metadata.074` | %s 現值「%s」不應存在 | %s currently has "%s", which should not be there |
| `nexus_metadata.075` | %s「%s」應為「%s」 | %s is "%s"; expected "%s" |
| `nexus_metadata.076` | （空） | (empty) |

## Nexus

| id | 繁中 | English |
|---|---|---|
| `nexus.001` | 開案檢查完成。可執行 Type Layers、高程／空間框、寫入／檢核 Metadata。匯出字典與發布請用獨立指令。 | Open-project check complete. You can now sync Type Layers, register level and space boundaries, and write or verify metadata. Use the separate commands to export the Dictionary or publish. |
| `nexus.002` | 開案檢查 | Open-project check |
| `nexus.003` | 從字典同步 Type Layers | Sync Type Layers from Dictionary |
| `nexus.004` | 登記高程框（封閉曲線） | Register level boundaries (closed curves) |
| `nexus.005` | 登記空間框（封閉曲線，須在高程框內） | Register space boundaries (closed curves, inside a level boundary) |
| `nexus.006` | 寫入／檢核模型 Metadata | Write/verify model metadata |
| `nexus.007` | 沒有可寫入的欄位。 | No fields to write. |
| `nexus.008` | 不可發布。 | Publishing is unavailable. |
| `nexus.009` | Scan 完成，%s 個物件。尚未寫入。空間 %s 個 EXT。不可發布。 | Scan completed for %s objects. No data has been written. EXT spaces: %s. Publishing is unavailable. |
| `nexus.010` | 空間／高程 | Space/elevation |
| `nexus.011` | 已寫入 %s 個物件的 %s。 | Updated %s objects with %s. |
| `nexus.012` | 使用者取消開案檢查。 | Open-project check cancelled. |
| `nexus.013` | 目前不在 Rhino 內，無法讀取專案名稱與文件單位。不修改檔案。 | Rhino is not available, so the project name and document units cannot be read. No files were changed. |
| `nexus.014` | 尚未填專案名稱。請用選單 2 從字典同步 Type Layers。 | The project name has not been set. Use menu 2 to sync Type Layers from the Dictionary. |
| `nexus.015` | 找不到 Dictionary 檔案 %s。請把字典放回 .3dm 所在的資料夾，或用選單 2 重新指定。 | Dictionary file %s was not found. Put it back in the same folder as the .3dm file, or use menu 2 to choose it again. |
| `nexus.016` | 文件單位為 %s，不是 cm。可繼續，但量綱尚未保證安全，建議切換為 cm。 | The document unit is %s, not cm. You can continue, but dimension handling is not yet guaranteed to be safe. Switching to cm is recommended. |
| `nexus.017` | Console 步驟尚未實作：%s | Console step not implemented yet: %s |
| `nexus.018` | 未知 schema_version：%s。已停止，不猜測解析。 | Unknown schema_version: %s. Operation stopped; the format will not be guessed. |
| `nexus.019` | 未知 Identity 動作：%s | Unknown Identity action: %s |
| `nexus.020` | 請先登記高程框（3）與空間框（4）。 | Register level boundaries (3) and space boundaries (4) first. |
| `nexus.021` | 1  開案檢查 | 1  Open-project check |
| `nexus.022` | 2  從字典同步 Type Layers | 2  Sync Type Layers from Dictionary |
| `nexus.023` | 3  登記高程框（封閉曲線） | 3  Register level boundaries (closed curves) |
| `nexus.024` | 4  登記空間框（封閉曲線，須在高程框內） | 4  Register space boundaries (closed curves, inside a level boundary) |
| `nexus.025` | 5  寫入模型 Metadata | 5  Write model metadata |
| `nexus.026` | 6  檢核模型 Metadata（不寫入） | 6  Verify model metadata (no write) |
| `nexus.027` | 開案檢查已完成。選一個步驟；Esc 取消。 | Open-project check finished. Pick a step; Esc to cancel. |
| `nexus.028` | 取消 | Cancel |
| `nexus.029` | 已完成開案檢查。使用者取消後續步驟。 | Open-project check complete. The remaining steps were cancelled. |
| `nexus.030` | 請輸入專案名稱（圖層前綴） | Enter the project name (layer prefix) |
| `nexus.031` | 選這份專案的 Dictionary Excel（須與 .3dm 同資料夾） | Choose this project's Dictionary Excel file (must be in the same folder as the .3dm file) |
| `nexus.032` | Dictionary 檔名（.3dm 同資料夾內的 .xlsx） | Dictionary filename (.xlsx in the same folder as the .3dm file) |
| `nexus.033` | ID／Type | ID/Type |

## 發布 Registry

| id | 繁中 | English |
|---|---|---|
| `registry.001` | 使用者取消發布。 | Publishing cancelled. |
| `registry.002` | 局部選取不得發布。請先跑 Nexus 選單 6 檢核通過後再發布。 | A partial selection cannot be published. Run Nexus menu 6 and pass Verify before publishing. |
| `registry.003` | 尚未填專案名稱。請先跑 Nexus 選單 2 從字典同步 Type Layers。 | The project name has not been set. Run Nexus menu 2 to sync Type Layers from the Dictionary first. |
| `registry.004` | Registry 正被其他程序鎖定，不覆寫。 | The Registry is locked by another process and will not be overwritten. |
| `registry.005` | 已釋放 Registry lock | Registry lock released. |
| `registry.006` | 已取得 Registry lock | Registry lock acquired. |
| `registry.007` | 沒有 lock 可釋放 | No lock to release. |
| `registry.008` | lock 已易主，不刪除。 | The lock is now owned by another process and will not be deleted. |
| `registry.009` | 無法清除過期 lock：%s | Could not clear the stale lock: %s |
| `registry.010` | 無法釋放 lock：%s | Could not release the lock: %s |
| `registry.011` | 無法建立 lock：%s | Could not create the lock: %s |
| `registry.012` | 正式 Registry 檔被佔用（常見是雲端同步還在寫檔）。請等同步結束後再開 Rhino 發一次，不要刪 Project_Registry.json。 | The primary Registry file is in use, usually because cloud sync is still writing it. Wait for syncing to finish, then reopen Rhino and publish again. Do not delete Project_Registry.json. |
| `registry.013` | Registry payload 必須是 object。 | The Registry payload must be an object. |
| `registry.014` | project_id 必須是合法專案名稱（與圖層前綴相同）。請先跑 Nexus 選單 2。 | project_id must be a valid project name (matching the layer prefix). Run Nexus menu 2 first. |
| `registry.015` | 已發布 Registry revision %s。 | Published Registry revision %s. |
| `registry.016` | 無法建立 Registry 目錄：%s | Could not create the Registry folder: %s |
| `registry.017` | 正式 Registry 的 project_id 與本次發布不符。 | The primary Registry's project_id does not match this publication. |
| `registry.018` | pending 寫入後無法重讀：%s | Could not re-read the pending file after writing it: %s |
| `registry.019` | 發布中斷：%s | Publishing interrupted: %s |
| `registry.020` | 正式 Registry 無法讀取，已停止，未覆寫。%s | The primary Registry could not be read. Operation stopped; it was not overwritten. %s |
| `registry.021` | 無法更新 last-good，已停止，未覆寫正式檔。%s | Could not update last-good. Operation stopped; the primary Registry was not overwritten. %s |
| `registry.022` | 新內容已寫入 last-good，等同步後再發一次。 | The new data was written to last-good. Publish again after syncing finishes. |
| `registry.023` | atomic replace 失敗，正式檔未刪。%s | Atomic replace failed. The primary file was not deleted. %s |
| `registry.024` | 已發布 Registry revision %s，但 last-good 未寫入。 | Published Registry revision %s, but last-good was not written. |
| `registry.025` | Registry payload 通過驗證 | Registry payload passed validation. |
| `registry.026` | schema_version 必須是整數。 | schema_version must be an integer. |
| `registry.027` | project_id 必須是合法專案名稱（與圖層前綴相同，不可含路徑字元）。 | project_id must be a valid project name matching the layer prefix and cannot contain path characters. |
| `registry.028` | registry_revision 必須是從 1 起的正整數。 | registry_revision must be a positive integer starting at 1. |
| `registry.029` | 缺少 published_at。 | Missing published_at. |
| `registry.030` | 缺少 model_unit。 | Missing model_unit. |
| `registry.031` | extension 必須是 object。 | extension must be an object. |
| `registry.032` | types 必須是陣列。 | types must be an array. |
| `registry.033` | spaces 必須是陣列。 | spaces must be an array. |
| `registry.034` | objects 必須是陣列。 | objects must be an array. |
| `registry.035` | spaces[] 必須含保留列 EXT。 | spaces[] must include the reserved EXT entry. |
| `registry.036` | %s[%s] 必須是 object。 | %s[%s] must be an object. |
| `registry.037` | %s[%s] 含未知核心欄：%s。 | %s[%s] contains unknown core fields: %s. |
| `registry.038` | %s[%s] 缺少核心欄：%s。 | %s[%s] is missing core fields: %s. |
| `registry.039` | Registry 含未知核心欄：%s。非核心資料只放 extension。 | The Registry contains unknown core fields: %s. Store non-core data under extension only. |
| `registry.040` | Registry 缺少核心欄：%s。 | The Registry is missing core fields: %s. |
| `registry.041` | types[%s] 缺少 type_id。 | types[%s] is missing type_id. |
| `registry.042` | EXT 的 level_id 必須為 null。 | EXT's level_id must be null. |
| `registry.043` | EXT 的 space_display 必須為 EXT。 | EXT's space_display must be EXT. |
| `registry.044` | objects[%s] 必須是 object。 | objects[%s] must be an object. |
| `registry.045` | objects[%s] 不得含尺寸／數量欄：%s。 | objects[%s] must not contain size/quantity fields: %s. |
| `registry.046` | objects[%s] 的 object_id 必須是小寫 UUID v4。 | objects[%s].object_id must be a lowercase UUID v4. |
| `registry.047` | objects[%s] 的 type_id 不在本 revision 的 types[]。 | objects[%s].type_id is not in this revision's types[]. |
| `registry.048` | objects[%s] 的 space_id 必須是 UUID 或 EXT。 | objects[%s].space_id must be a UUID or EXT. |
| `registry.049` | spaces[%s] 的 space_id 必須是 UUID 或 EXT。 | spaces[%s].space_id must be a UUID or EXT. |

## Duplicate Layout

| id | 繁中 | English |
|---|---|---|
| `duplicate_layout.001` | 要複製幾份？ | How many copies? |
| `duplicate_layout.002` | 請重新綁定新頁 Tag，並視需要跑 Layout ID。 | Rebind the Tags on the new pages, then run Layout ID if needed. |
| `duplicate_layout.003` | 已複製 %s 份 Layout。 | Created %s Layout copies. |
| `duplicate_layout.004` | 來源 Layout 沒有物件。 | The source Layout has no objects. |
| `duplicate_layout.005` | 此 Rhino session 不能複製 Layout 頁。 | This Rhino session cannot duplicate Layout pages. |
| `duplicate_layout.006` | 來源：%s | Source: %s |
| `duplicate_layout.007` | 找不到 Layout「%s」。 | Layout "%s" was not found. |
| `duplicate_layout.008` | 目前文件沒有 Layout。請先建立至少一頁。 | This document has no Layouts. Create at least one page first. |
| `duplicate_layout.009` | 已取消複製 Layout。 | Duplicate Layout cancelled. |
| `duplicate_layout.010` | 來源 Layout 沒有物件：%s。整批未複製。 | Source Layout has no objects: %s. No copies were created. |
| `duplicate_layout.011` | 份數須為 %s 到 %s。 | The number of copies must be between %s and %s. |
| `duplicate_layout.012` | 無法建立 Layout「%s」。 | Could not create Layout "%s". |
| `duplicate_layout.013` | 複製「%s」的物件失敗。 | Could not copy objects from "%s". |
| `duplicate_layout.014` | 未定義的 Sheet 欄位：%s | Undefined Sheet field: %s |
| `duplicate_layout.015` | 無法遞增的圖編號：%s | Drawing number cannot be incremented: %s |

## Grab

| id | 繁中 | English |
|---|---|---|
| `grab.001` | 「%s」不是 Grab 可用的標籤，已停止，不寫入。 | "%s" is not supported by Grab. Operation stopped; no changes were made. |
| `grab.002` | 選取要綁定的 Tag（Esc 取消） | Select the Tag to bind (Esc to cancel) |
| `grab.003` | 選取模型來源（Esc 取消） | Select the source model object (Esc to cancel) |
| `grab.004` | 選取家具圖塊來源（Esc 取消） | Select the source furniture Block (Esc to cancel) |
| `grab.005` | 「%s」是純手動標籤，不接受 Grab 綁定。 | "%s" is a manual-only Tag and cannot be bound with Grab. |
| `grab.006` | 「%s」請用 Laser 綁定，Grab 不寫入。 | Use Laser to bind "%s". Grab made no changes. |
| `grab.007` | 「%s」請用 Index 綁定，Grab 不寫入。 | Use Index to bind "%s". Grab made no changes. |
| `grab.008` | 「%s」不綁模型來源，Grab 不寫入。 | "%s" does not bind to a model source. Grab made no changes. |
| `grab.009` | 請選 Tag 圖塊。已停止，不寫入。 | Select a Tag Block. Operation stopped; no changes were made. |
| `grab.010` | 此 Tag 已鎖定，請先解除鎖定再綁定。 | This Tag is locked. Unlock it before binding. |
| `grab.011` | 已綁定來源 UUID。 | Source UUID bound. |
| `grab.012` | 已綁定家具圖塊名稱。 | Furniture Block name bound. |
| `grab.013` | 未知圖塊「%s」，已停止，不寫入。 | Unknown Block "%s". Operation stopped; no changes were made. |
| `grab.014` | 來源對到兩個以上 3D 物件，已停止，不猜測。 | The source matches more than one 3D object. Operation stopped; no match was guessed. |
| `grab.015` | 來源物件尚未寫入 UUID。請先跑 Nexus 寫入模型 Metadata。 | The source object does not have a UUID. Run Nexus — Write Model Metadata first. |
| `grab.016` | 家具 Tag 請選家具圖塊當來源。已停止，不寫入。 | For a furniture Tag, select a furniture Block as the source. Operation stopped; no changes were made. |
| `grab.017` | 已取消 Grab。 | Grab cancelled. |
| `grab.018` | 找不到選取的 Tag。 | The selected Tag was not found. |
| `grab.019` | （未命名） | (unnamed) |
| `grab.020` | 家具圖塊名稱格式不正確：%s。應為 FF-01__Chair-1。 | Invalid furniture Block name: %s. Expected format: FF-01__Chair-1. |

## Index

| id | 繁中 | English |
|---|---|---|
| `index.001` | 「TAG_ELEV_0」請用 Layout ID 寫目前頁圖號，Index 不寫入。 | Use Layout ID to write the current page's drawing number to "TAG_ELEV_0". Index made no changes. |
| `index.002` | 家具 Tag 請用 Grab 綁定，Index 不寫入。 | Use Grab to bind furniture Tags. Index made no changes. |
| `index.003` | 「%s」不是 Index 可用的標籤，已停止，不寫入。 | "%s" is not supported by Index. Operation stopped; no changes were made. |
| `index.004` | （未命名 View） | (unnamed View) |
| `index.005` | （未命名 Detail） | (unnamed Detail) |
| `index.006` | 已對到目標 View。 | Target View found. |
| `index.007` | 選取要綁定的 Index Tag（Esc 取消） | Select the Index Tag to bind (Esc to cancel) |
| `index.008` | 已綁定目標 View。 | Target View bound. |
| `index.009` | 「%s」請用 Laser 綁定，Index 不寫入。 | Use Laser to bind "%s". Index made no changes. |
| `index.010` | 「%s」請用 Grab 綁定，Index 不寫入。 | Use Grab to bind "%s". Index made no changes. |
| `index.011` | 「%s」是純手動標籤，不接受 Index 綁定。 | "%s" is a manual-only Tag and cannot be bound with Index. |
| `index.012` | 「%s」不綁目標圖面，Index 不寫入。 | "%s" does not bind to a target drawing. Index made no changes. |
| `index.013` | 這個 Detail 對不到已登記 View。請先執行 Anchor Frame。 | This Detail does not match a registered View. Run Anchor Frame first. |
| `index.014` | 這個 Detail 對到兩個以上已登記 View，已停止，不猜測。 | This Detail matches more than one registered View. Operation stopped; no match was guessed. |
| `index.015` | 目標 View 沒有合法的 lf_view_id。請先執行 Anchor Frame。 | The target View has no valid lf_view_id. Run Anchor Frame first. |
| `index.016` | 請在 Layout 執行 Index。 | Run Index on a Layout. |
| `index.017` | 已取消 Index。 | Index cancelled. |
| `index.018` | 沒有 Detail View 可綁定。 | No Detail View to bind. |

## 其他

| id | 繁中 | English |
|---|---|---|
| `other.001` | attr_Lock_不更新>寫入x或X | attr_Lock_Do not update > enter x or X |
| `other.002` | x為不更新 | x = Do not update |
| `other.003` | 不更新 | Do not update |
| `other.004` | 已載入 %s 份 Tag template。 | Loaded %s Tag templates. |
| `other.005` | 找不到 Tag template manifest：%s | Tag template manifest not found: %s |
| `other.006` | 未知 schema_id：%s。應為 %s。已停止，不猜測解析。 | Unknown schema_id: %s. Expected %s. Operation stopped; the format will not be guessed. |
| `other.007` | 微軟正黑體 | Microsoft JhengHei |
| `other.008` | 已讀取工作表 | Worksheet loaded. |
| `other.009` | 已寫入工作表 | Worksheet saved. |
| `other.010` | xlsx 沒有工作表 | The .xlsx file contains no worksheets. |
| `other.011` | 找不到第一張工作表路徑 | The first worksheet path was not found. |
| `other.012` | xlsx 缺少標題列或欄名列。 | The .xlsx file is missing a title row or column-name row. |
| `other.013` | 一般 | General |
| `other.014` | 輸出目錄不存在，不建立。 | The output folder does not exist and will not be created. |
| `other.015` | 找不到 Dictionary 檔案 %s。不建立檔案。 | Dictionary file %s was not found. No file was created. |
| `other.016` | 無法讀取 xlsx：%s | Could not read the .xlsx file: %s |
| `other.017` | 無法寫入 xlsx：%s | Could not write the .xlsx file: %s |

## Laser

| id | 繁中 | English |
|---|---|---|
| `laser.001` | 家具 Tag 請用 Grab 綁定，Laser 不寫入。 | Use Grab to bind furniture Tags. Laser made no changes. |
| `laser.002` | 「%s」不是 Laser 可用的標籤，已停止，不寫入。 | "%s" is not supported by Laser. Operation stopped; no changes were made. |
| `laser.003` | 選取要綁定的 Laser Tag（Esc 取消） | Select the Laser Tag to bind (Esc to cancel) |
| `laser.004` | （無圖層） | (no layer) |
| `laser.005` | 多個重疊物件，請選要標註的來源 | Multiple objects overlap here. Choose the source to tag. |
| `laser.006` | 「%s」請用 Grab 綁定，Laser 不寫入。 | Use Grab to bind "%s". Laser made no changes. |
| `laser.007` | 「%s」是純手動標籤，不接受 Laser 綁定。 | "%s" is a manual-only Tag and cannot be bound with Laser. |
| `laser.008` | 「%s」請用 Index 綁定，Laser 不寫入。 | Use Index to bind "%s". Laser made no changes. |
| `laser.009` | 「%s」不綁模型來源，Laser 不寫入。 | "%s" does not bind to a model source. Laser made no changes. |
| `laser.010` | 已取消 Laser。 | Laser cancelled. |
| `laser.011` | 這一點不在任何已登記的 View 框內。請先執行 Anchor Frame。 | This point is not inside any registered View frame. Run Anchor Frame first. |
| `laser.012` | View 框沒有合法的固定 transform。請重新執行 Anchor Frame。 | The View frame has no valid fixed transform. Run Anchor Frame again. |
| `laser.013` | 射線沒有打到帶 UUID 的 3D 物件。 | The ray did not hit a 3D object with a UUID. |
| `laser.014` | 射線命中沒有物件 ID，已停止，不寫入。 | The object hit by the ray has no object ID. Operation stopped; no changes were made. |
| `laser.015` | 這一點落在 %s 個重疊的 View 框內，已停止，不猜測。 | This point is inside %s overlapping View frames. Operation stopped; no View was guessed. |
| `laser.016` | 已畫出射線。沒打到帶 UUID 的 3D 物件。請到 3D 視窗查看。 | Ray drawn. It did not hit a 3D object with a UUID. Check the 3D viewport. |

## Layout ID

| id | 繁中 | English |
|---|---|---|
| `layout_id.001` | 圖框已就緒，但尚未設定系列起點，因此未執行。 / 請將每個系列的第一頁按照下列規則命名： / **圖類別__圖號__圖名 / **IN__101.01__一樓平面圖 / **A__101__一樓平面圖 /  / --- / 1. ** 作為自動編號起點，勿刪 / 2. ** 之間的頁面為同一系列 / 3. ** 頁面之外的Layout名稱，只需要填寫圖名 / 4. // 頁面不參與自動編號，但仍需使用相同命名格式規範 / 5. 圖號、圖名 的編號與命名可以從Layout列表手動調整 / 　經由自動編號寫入圖框中，不可直接修改圖框內容 / --- /  / Sample / **IN__101.01__一樓平面圖 / 二樓平面圖 / 三樓平面圖 / **IN__201.01__立面圖1 / 立面圖2 / //S__901__結構平面圖 /  / （Layout自動編號如下） / **IN__101.01__一樓平面圖 / IN__101.02__二樓平面圖 / IN__101.03__三樓平面圖 / **IN__201.01__立面圖1 / IN__201.02__立面圖2 / //S__901__結構平面圖 | Title blocks are ready, but no series start has been set, so nothing was processed. / Name the first page of each series as follows: / **DrawingType__DrawingNumber__DrawingName / **IN__101.01__First Floor Plan / **A__101__First Floor Plan /  / --- / 1. ** marks the start of an auto-numbered series; do not remove it / 2. Pages between two ** markers belong to the same series / 3. For Layouts outside a ** series, enter only the drawing name / 4. Pages beginning with // are not auto-numbered, but must use the same naming format / 5. Drawing numbers and names can be edited in the Layout list / 　Auto-numbering writes them to the title block; do not edit the title block directly / --- /  / Example / **IN__101.01__First Floor Plan / Second Floor Plan / Third Floor Plan / **IN__201.01__Elevation 1 / Elevation 2 / //S__901__Structural Plan /  / Result after automatic numbering / **IN__101.01__First Floor Plan / IN__101.02__Second Floor Plan / IN__101.03__Third Floor Plan / **IN__201.01__Elevation 1 / IN__201.02__Elevation 2 / //S__901__Structural Plan |
| `layout_id.002` | 原始名稱 | Original name |
| `layout_id.003` | 修改後名稱 | New name |
| `layout_id.004` | 狀態 | Status |
| `layout_id.005` | 圖框已鎖定 | Title block locked |
| `layout_id.006` | 這一頁沒有圖框 | This page has no title block |
| `layout_id.007` | 這一頁有 %s 個圖框，無法決定身分 | This page has %s title blocks, so its identity cannot be determined |
| `layout_id.008` | 沒有可寫入的 Layout 頁。請確認每一頁只有一個已登錄的圖框。 | No Layout pages to write. Make sure each page has exactly one registered title block. |
| `layout_id.009` | 沒有可寫入的 Layout 頁。 | No Layout pages to write. |
| `layout_id.010` | 這份檔案沒有可編號的 Layout 頁。 | This file has no Layout pages that can be numbered. |
| `layout_id.011` | 系列起點 | Series start |
| `layout_id.012` | 手動頁，不編號 | Manual page; not numbered |
| `layout_id.013` | 重複的系列起點，已接續目前系列 | Duplicate series start; continuing the current series |
| `layout_id.014` | Layout ID 核對清單 | Layout ID review list |
| `layout_id.015` | 已寫入 %s 頁圖號；新建 %s 個 Sheet 身分，改名 %s 頁。 | Wrote drawing numbers to %s pages; created %s Sheet IDs and renamed %s pages. |
| `layout_id.016` | 沒有登錄的圖框（未登錄圖塊：%s） | No registered title block (unregistered Blocks: %s) |
| `layout_id.017` | …另有 %s 頁。 | …and %s more pages. |
| `layout_id.018` | 頁序中還沒有系列起點，未編號 | No series start appears before this page, so it was not numbered |
| `layout_id.019` | 圖號 %s → %s | Drawing number: %s → %s |
| `layout_id.020` | 圖名 %s → %s | Drawing name: %s → %s |
| `layout_id.021` | 跳過：%s | Skipped: %s |
| `layout_id.022` | 這份檔案沒有 Layout 分頁，已停止，不寫入。 | This file has no Layout tabs. Operation stopped; no changes were made. |
| `layout_id.023` | 已取消 Layout ID，未寫入。 | Layout ID cancelled. No changes were made. |
| `layout_id.024` | 跳過 %s 頁，詳見報告。 | Skipped %s pages. See the report for details. |
| `layout_id.025` | 頁名是空的 | Page name is blank |
| `layout_id.026` | 手動頁格式不正確，需 //圖類別__圖號__圖名 | Invalid manual-page format. Use //DrawingType__DrawingNumber__DrawingName. |

## Anchor Frame

| id | 繁中 | English |
|---|---|---|
| `anchor_frame.001` | 天花 | Ceiling |
| `anchor_frame.002` | 已登記 View。 | View registered. |
| `anchor_frame.003` | 輸入框線外擴距離 | Enter frame offset distance |
| `anchor_frame.004` | 請恰好選一個 Text Dot 作為剖面名稱提示。已停止，不寫入。 | Select exactly one Text Dot as the section-name label. Operation stopped; no changes were made. |
| `anchor_frame.005` | Text Dot 沒有文字，已停止，不寫入。 | The Text Dot is blank. Operation stopped; no changes were made. |
| `anchor_frame.006` | 選到多個既有 View 框，已停止，不猜測要升級哪一個。 | More than one existing View frame was selected. Operation stopped; no frame was chosen automatically. |
| `anchor_frame.007` | 沒有可用的剖面幾何，已停止，不寫入。 | No usable section geometry was found. Operation stopped; no changes were made. |
| `anchor_frame.008` | 無法計算剖面範圍，已停止，不寫入。 | The section bounds could not be calculated. Operation stopped; no changes were made. |
| `anchor_frame.009` | 找不到與 Clipping Plane 相交的 3D 模型，無法寫入固定 transform。 | No 3D model geometry intersects the Clipping Plane, so the fixed transform could not be written. |
| `anchor_frame.010` | 計算出的 View transform 不合法，已停止，不寫入。 | The calculated View transform is invalid. Operation stopped; no changes were made. |
| `anchor_frame.011` | 找不到名稱包含「%s」的 Clipping Plane。已停止，不寫入。 | No Clipping Plane with a name containing "%s" was found. Operation stopped; no changes were made. |
| `anchor_frame.012` | 名稱包含「%s」的 Clipping Plane 有 %s 個，已停止，不猜測。 | The name filter "%s" matches %s Clipping Planes. Operation stopped; no match was guessed. |
| `anchor_frame.013` | 已取消登記 View。 | View registration cancelled. |

## Data Viewer

| id | 繁中 | English |
|---|---|---|
| `data_viewer.001` | 找不到物件。 | Object not found. |
| `data_viewer.002` | 已結束檢視。 | Viewer closed. |
| `data_viewer.003` | 已檢視 %s 個物件。 | Viewed %s objects. |
| `data_viewer.004` | （缺） | (missing) |
| `data_viewer.005` | 專案設定尚未寫入 schema，仍可查看物件欄位。 | The project schema has not been written yet, but object fields can still be viewed. |
| `data_viewer.006` | 這個物件沒有 UserText。 | This object has no UserText. |
| `data_viewer.007` | 圖層：%s | Layer: %s |
| `data_viewer.008` | 名稱：%s | Name: %s |
| `data_viewer.009` | 專案：%s | Project: %s |
| `data_viewer.010` | 專案 schema 不完整：schema_id=%s，schema_version=%s。已停止，不猜測解析。 | The project schema is incomplete: schema_id=%s, schema_version=%s. Operation stopped; the format will not be guessed. |
| `data_viewer.011` | 未知 schema_id：%s。專案設定應為 %s。已停止，不猜測解析。 | Unknown schema_id: %s. Expected %s in the project settings. Operation stopped; the format will not be guessed. |
| `data_viewer.012` | 圖塊：%s | Block: %s |
| `data_viewer.013` | 文件 schema：%s %s | Document schema: %s %s |
| `data_viewer.014` | 文件 schema：%s | Document schema: %s |
| `data_viewer.015` | 字典名稱：%s | Dictionary name: %s |
| `data_viewer.016` | 缺值：%s | Missing values: %s |
| `data_viewer.017` | 殘留（不屬 2.0）：%s | Legacy fields (not part of 2.0): %s |
| `data_viewer.018` | 未知 schema_version：%s 的 %s。已停止，不猜測解析。 | Unknown schema_version: %s for %s. Operation stopped; the format will not be guessed. |
| `data_viewer.019` | 來源：物件名稱（舊檔相容） | Source: object name (legacy-file compatibility) |
| `data_viewer.020` | 覆寫（字典預設 %s） | Override (Dictionary default: %s) |
| `data_viewer.021` | 字典找不到 Type %s。 | Type %s was not found in the Dictionary. |
| `data_viewer.022` | 來源：舊 key %s | Source: legacy key %s |

## Sync Worksession

| id | 繁中 | English |
|---|---|---|
| `sync_worksession.001` | 已停止 Worksession 監看。 | Worksession monitoring stopped. |
| `sync_worksession.002` | Worksession 更新未成功，稍後再試。上一份參照未改動。 | The Worksession could not be updated. Try again later. The previous reference was left unchanged. |
| `sync_worksession.003` | 請先把檔案存到磁碟，再開始監看同資料夾的 .3dm。 | Save the file to disk before monitoring other .3dm files in the same folder. |
| `sync_worksession.004` | 偵測到檔案變動：%s | File change detected: %s |
| `sync_worksession.005` | 已更新 Worksession 參照。 | Worksession reference updated. |
| `sync_worksession.006` | 已開始監看：%s（延遲 %s 秒） | Monitoring started: %s (%s-second delay) |
| `sync_worksession.007` | 無法監看資料夾「%s」。 / %s | Could not monitor folder "%s". / %s |
| `sync_worksession.008` | 監看資料夾已變更，改監看：%s（延遲 %s 秒） | Monitoring folder changed to: %s (%s-second delay) |

## Foundation

| id | 繁中 | English |
|---|---|---|
| `foundation.001` | 已讀取 JSON | JSON loaded. |
| `foundation.002` | 輸出目錄不存在，不建立正式檔。 | The output folder does not exist, so the final file was not created. |
| `foundation.003` | 已寫入 %s | Wrote %s. |
| `foundation.004` | JSON 根物件必須是 object。 | The JSON root must be an object. |
| `foundation.005` | 找不到要複製的檔案。 | The file to copy was not found. |
| `foundation.006` | 找不到 JSON：%s | JSON file not found: %s |
| `foundation.007` | 無法寫入檔案：%s | Could not write the file: %s |
| `foundation.008` | 無法讀取 JSON：%s | Could not read the JSON file: %s |
| `foundation.009` | 無法讀取來源：%s | Could not read the source: %s |
| `foundation.010` | 使用內建進階設定 | Using built-in advanced settings. |
| `foundation.011` | 未知語系：%s | Unknown language: %s |
| `foundation.012` | 使用專案設定資料夾的 log 路徑 | Using the log path from the project-settings folder. |
| `foundation.013` | 已寫入 log | Log written. |
| `foundation.014` | 使用指定 log 路徑 | Using the specified log path. |
| `foundation.015` | 寫入 log 失敗：%s | Could not write the log: %s |
| `foundation.016` | 未知結果狀態：%s | Unknown result status: %s |
| `foundation.017` | 未知 schema_id：%s。已停止，不猜測解析。 | Unknown schema_id: %s. Operation stopped; the format will not be guessed. |
| `foundation.018` | 未知 schema_version：%s 的 %s（目前為 %s）。已停止，不猜測解析。 | Unknown schema_version: %s for %s (current: %s). Operation stopped; the format will not be guessed. |

## 路徑與工作資料夾

| id | 繁中 | English |
|---|---|---|
| `paths.001` | 目前不在 Rhino 內，無法取得 .3dm 位置。不修改檔案。 | Rhino is not available, so the .3dm location cannot be determined. No files were changed. |
| `paths.002` | 請先把這份檔案存成 .3dm。工作資料夾就是 .3dm 所在的資料夾；尚未存檔就沒有資料夾，無法建立設定、字典位置與 %s。 | Save this file as a .3dm first. The working folder is the folder containing the .3dm file; without it, settings, the Dictionary location, and %s cannot be created. |
| `paths.003` | 已確認 Dictionary 檔名 | Dictionary filename confirmed |
| `paths.004` | 已確認檔案所在資料夾 | File folder confirmed |
| `paths.005` | 已解析 .3dm 工作資料夾 | .3dm working folder resolved |
| `paths.006` | 已解析 Registry 路徑 | Registry path resolved |
| `paths.007` | Dictionary 檔名不能空白。 | The Dictionary filename cannot be blank. |
| `paths.008` | Dictionary 檔名不可含 \ / : * ? " < > \| | The Dictionary filename cannot contain `\ / : * ? " < > \|`. |
| `paths.009` | 不能把匯出檔當正式 Dictionary。 | An export file cannot be used as the project Dictionary. |
| `paths.010` | 已解析 %s 資料夾 | %s folder resolved |
| `paths.011` | 缺少專案名稱，停止解析 Registry。請先跑 Nexus 選單 2 填專案名稱。 | Project name is missing, so the Registry cannot be resolved. Run Nexus menu 2 and enter the project name first. |
| `paths.012` | 專案名稱不可含 \ / : * ? " < > \|，也不可當資料夾路徑。 | The project name cannot contain `\ / : * ? " < > \|` or be a folder path. |
| `paths.013` | 請只輸入檔名。完整路徑須先知道 .3dm 所在資料夾。 | Enter a filename only. The full path cannot be resolved until the .3dm folder is known. |
| `paths.014` | Dictionary 須和 .3dm 同一層，不能放在子資料夾。 | The Dictionary must be in the same folder as the .3dm, not a subfolder. |
| `paths.015` | 請只輸入檔名，不可含資料夾路徑。 | Enter a filename only, without a folder path. |
| `paths.016` | Dictionary 必須是 .xlsx 檔。 | The Dictionary must be an .xlsx file. |
| `paths.017` | Dictionary 必須和 .3dm 放在同一個資料夾。 / 選到：%s / 必須在：%s | The Dictionary must be in the same folder as the .3dm file. / Selected: %s / Required folder: %s |

## 專案設定

| id | 繁中 | English |
|---|---|---|
| `project_config.001` | 已讀取專案設定 | Project settings loaded. |
| `project_config.002` | 已更新專案設定 | Project settings updated. |
| `project_config.003` | 尚無專案設定檔 | No project settings file exists yet. |
| `project_config.004` | %s 內容不是設定物件。已停止，不猜測內容。 | %s does not contain a settings object. Operation stopped; the contents will not be guessed. |
| `project_config.005` | %s 無法解析：%s。已停止，不猜測內容。 | Could not parse %s: %s. Operation stopped; the contents will not be guessed. |
| `project_config.006` | 無法寫入 %s：%s | Could not write %s: %s |

## Rhino 平台訊息

| id | 繁中 | English |
|---|---|---|
| `rhino.001` | 已連接 Rhino 文件。live adapter 尚未實機驗證。 | Connected to the Rhino document. The live adapter has not yet been tested in Rhino. |
| `rhino.002` | 沒有作用中的 Rhino 文件 | No active Rhino document |
| `rhino.003` | 已連接 Rhino 文件。 | Connected to the Rhino document. |
| `rhino.004` | 無法載入 Rhino | Could not load Rhino |
| `rhino.005` | 無法建立目錄文字 | Could not create drawing-index text |
| `rhino.006` | 封閉框至少需要 3 點 | A closed boundary needs at least 3 points |
| `rhino.007` | 目前不在 Rhino 內：%s | Rhino is not available: %s |
| `rhino.008` | 未知圖層：%s | Unknown layer: %s |
| `rhino.009` | 未知物件：%s | Unknown object: %s |
| `rhino.010` | 已還原 Rhino 視圖狀態 | Rhino view state restored |
| `rhino.011` | 指令未回傳 Result，已還原 Rhino 狀態。 | The command returned no Result. Rhino state was restored. |
| `rhino.012` | 還原時找不到 %s 個快照物件，其餘狀態已寫回。 | %s objects from the snapshot could not be found during restore. All other state was restored. |
| `rhino.013` | 建立快照時發生例外。 / %s | An exception occurred while creating the snapshot. / %s |
| `rhino.014` | 執行中發生例外，已還原 Rhino 狀態。 / %s | An exception occurred during execution. Rhino state was restored. / %s |

## 共用彈窗與按鈕

| id | 繁中 | English |
|---|---|---|
| `prompts.001` | 選擇介面語言 / Choose interface language | Choose interface language / 選擇介面語言 |
| `prompts.002` | Document 按鈕右鍵切換語言介面 (LFLanguage) / Right-click Document to switch the UI (LFLanguage) | Right-click Document to switch the UI (LFLanguage) |
| `prompts.003` | 複製 Layout | Duplicate Layout |
| `prompts.004` | Index 綁定 | Index binding |
| `prompts.005` | 點選要查看的物件（Enter／Esc 結束） | Select objects to inspect (Enter or Esc to finish) |
| `prompts.006` | 選取圖塊（Esc 取消） | Select a Block (Esc to cancel) |
| `prompts.007` | 在目標 Detail 內點一下（Esc 取消） | Click inside the target Detail (Esc to cancel) |
| `prompts.008` | 框選剖面物件與對應的 Text Dot（Esc 取消） | Window-select the section objects and matching Text Dot (Esc to cancel) |
| `prompts.009` | 選取目錄定位點（獨立 Point，Esc 取消） | Select a drawing-index anchor (standalone Point; Esc to cancel) |
| `prompts.010` | 選取封閉曲線，按 Enter 完成 | Select closed curves, then press Enter |
| `prompts.011` | 可按住 Ctrl 或 Shift 一次選多頁。選取列會反白。 | Hold Ctrl or Shift to select multiple pages. Selected rows highlight. |
| `prompts.012` | 輸入圖名或圖號搜尋 | Type a drawing name or number to search |
| `prompts.013` | 這些圖塊還沒登錄為圖框。請勾選真正的圖框；沒勾選的會略過，不會寫入圖號。 | These Blocks are not registered as title blocks. Select the actual title blocks. Unselected Blocks will be skipped and will not receive drawing numbers. |
| `prompts.014` | Shift 連選、Ctrl 加選或取消選取。選取列會反白。未選的不納入；新增頁不會自動加入既有目錄。 | Use Shift to select a range, or Ctrl to add or remove items. Selected rows are highlighted. Unselected pages are excluded, and new pages are not added to an existing drawing index automatically. |
| `prompts.015` | 全選 | Select all |
| `prompts.016` | 清除選取 | Clear selection |
| `prompts.017` | 請在 Layout 執行 Grab。 | Run Grab on a Layout. |
| `prompts.018` | 點擊位置不在任何 Detail 內。 | The click point is not inside any Detail. |
| `prompts.019` | 請在 Layout 執行 Laser。 | Run Laser on a Layout. |
| `prompts.020` | 關閉 | Close |
| `prompts.021` | 距離不可小於 %s。 | Distance cannot be less than %s. |
| `prompts.022` | 請先選一個 Detail。 | Select a Detail first. |
| `prompts.023` | 頁序 | Page order |
| `prompts.024` | 頁名 | Page name |

## 尚未實作

| id | 繁中 | English |
|---|---|---|
| `runners.001` | 這是 2.0 測試入口「%s」，功能尚未實作（%s）。 | This is the 2.0 test entry point "%s"; the feature is not implemented yet (%s). |
| `runners.002` | 待排程 | To be scheduled |

## 不抽出（鍵名／圖層／內部識別）

這些字留在程式裡，不進語系表。

| 來源 | 字串 |
|---|---|
| `features/dictionary/schema.py` | `_01_空間名稱` |
| `features/dictionary/schema.py` | `_02_建構狀態` |
| `features/dictionary/schema.py` | `_03_ID編號` |
| `features/dictionary/schema.py` | `_04_ID名稱` |
| `features/dictionary/schema.py` | `_05_高程基準` |
| `features/dictionary/schema.py` | `_06_高程計算` |
| `features/dictionary/schema.py` | `_08_備註` |
| `features/dictionary/schema.py` | `Q_01_寬度W` |
| `features/dictionary/schema.py` | `Q_02_深度D` |
| `features/dictionary/schema.py` | `Q_03_高度H` |
| `features/dictionary/schema.py` | `Q_04_單位` |
| `features/dictionary/schema.py` | `Q_05_計量規則` |
| `features/dictionary/schema.py` | `Q_06_實作數量` |
| `foundation/usertext.py` | `_01_空間名稱*` |
| `foundation/usertext.py` | `_02_建構狀態*` |
| `foundation/usertext.py` | `_08_備註*` |
| `foundation/usertext.py` | `_09_空間ID` |
| `foundation/usertext.py` | `_10_樓層ID` |
| `foundation/usertext.py` | `_11_類型類別` |
| `foundation/usertext.py` | `_12_類型序號` |
| `foundation/usertext.py` | `_13_高程顯示` |
| `foundation/usertext.py` | `_14_資料版次` |
| `foundation/usertext.py` | `_15_樓層高程*` |
| `foundation/usertext.py` | `_05_寬度W` |
| `foundation/usertext.py` | `_06_深度D` |
| `foundation/usertext.py` | `_07_高度H` |
| `foundation/usertext.py` | `_09_實作數量` |
| `foundation/usertext.py` | `_14_座標框` |
| `foundation/usertext.py` | `_19_座標框` |
| `foundation/usertext.py` | `_10_高程基準` |
| `foundation/usertext.py` | `_11_高程計算` |
| `foundation/usertext.py` | `_13_備註` |
| `foundation/usertext.py` | `_01_空間ID` |
| `foundation/usertext.py` | `_14_空間ID` |
| `foundation/usertext.py` | `_01_樓層ID` |
| `foundation/usertext.py` | `_15_樓層ID` |
| `foundation/usertext.py` | `_03_類型類別` |
| `foundation/usertext.py` | `_16_類型類別` |
| `foundation/usertext.py` | `_03_類型序號` |
| `foundation/usertext.py` | `_17_類型序號` |
| `foundation/usertext.py` | `_11_高程顯示` |
| `foundation/usertext.py` | `_18_高程顯示` |
| `foundation/usertext.py` | `_15_資料版次` |
| `foundation/usertext.py` | `_20_資料版次` |
| `foundation/usertext.py` | `_15_樓層高程` |
