# LoopFlow 2.0 — 資料生態決策表

這是 `LOOPFLOW_DATA_ECOSYSTEM.md` 的使用者編輯區。藍圖保存現況、工作鏈與架構說明；所有尚未定案、需要使用者確認或補充實務語意的事項集中在本文件。

## 使用方式

- 可以直接修改表格中的「你的決定／說明」，不需要使用固定回覆格式。
- 可以把 `待決定` 改成「採用」、「不採用」，或直接寫自己的規則。
- 可以改寫建議內容；若選項不符合實務，直接刪掉重寫也可以。
- 請保留 `ECO-*`／`ED-*` 編號，方便後續追蹤與回寫。
- AI 讀取你的修改後，先整理歧義與影響，再同步回寫藍圖、命名與資料契約、Nexus／Dictionary 細項及進度紀錄。
- 在回寫完成前，本文件是尚待確認事項的唯一來源；不要同時在藍圖與本文件維護兩份答案。

### AI 建議強度

| 強度 | 意義 |
|---|---|
| **強烈建議** | 最好照做；這通常關係到資料不斷鏈、可復原、避免靜默錯誤或能否長期擴充。若不採用，需要先設計同等安全的替代方案。 |
| **一般建議** | 可以改，但會增加相應的規則、操作或維護成本；決定時需明確接受代價。 |
| **輕鬆建議** | 原則上不影響核心資料鏈，可依實際習慣、時程或介面偏好調整。 |

## A. 上位生態原則

兩次獨立複核都支持以下方向，但仍由使用者決定是否採用或修改。

| ID | 建議原則 | AI 建議（強度） | 你的決定／說明 |
|---|---|---|---|
| ECO-01 | Dictionary 是 Type Catalog；3D Object 是 Instance truth | **強烈建議**：採用。避免 Type 預設與 Object 現值互相覆寫、形成兩份真相。 | 待決定 |
| ECO-02 | Layer 是人類分類入口，不是永久資料 ID | **強烈建議**：採用。Layer 改名或重組時，不應讓既有 Tag 與資料關聯一起斷線。 | 待決定 |
| ECO-03 | Section 圖面可獨立編輯；更新不得靜默覆寫人工成果 | **強烈建議**：採用。這是保護出圖人工成果的核心安全線。 | 待決定 |
| ECO-04 | Tag 綁定穩定 Object／View／Sheet ID；圖面位置只協助定位 | **強烈建議**：採用。否則名稱、位置或圖面調整都可能造成無法察覺的錯綁。 | 待決定 |
| ECO-05 | Sheet metadata 是圖框與命名真相；Layout 名稱是輸出 | **強烈建議**：採用。日後插頁、改圖號格式或多種交付格式才不需拆字串回推。 | 待決定 |
| ECO-06 | Registry 是版本化唯讀發布快照，不是另一份人工資料庫 | **強烈建議**：採用。避免 3D 模型與 JSON 可各自編輯後產生衝突。 | 待決定 |
| ECO-07 | 狀態、revision 與問題是正式資料；顏色只作可還原提示 | **強烈建議**：採用。顏色不能可靠判斷真實狀態，也不能破壞使用者原色。 | 待決定 |
| ECO-08 | 每階段可單獨執行、驗證、重跑與復原 | **強烈建議**：採用。符合雙機、分時工作與小批次測試，也降低一次大操作的風險。 | 待決定 |
| ECO-09 | 模型單位先驗證；工程估算單位分離；所有量綱常數具名並標註單位 | **強烈建議**：採用。單位混用會直接產生錯誤尺寸、搜尋距離與數量。 | 待決定 |
| ECO-10 | 每個產生幾何或改寫資料的指令都定義冪等重跑政策，並能辨識前次產出 | **強烈建議**：採用。避免 Extract、參考線或 Sheet 重跑後無限累積與複製身分。 | 待決定 |
| ECO-11 | ID 的產生與變更可追溯；自動換 ID 前先報告、預覽、建立 mapping 並可回復 | **強烈建議**：採用。這直接防止 UUID 重建造成既有 Tag 不可逆斷鏈。 | 待決定 |

## B. 證據已足、建議優先確認

這些已有明確程式或 Dictionary 證據；仍保留使用者翻案空間。

| ID | 現況與建議 | AI 建議（強度） | 你的決定／說明 |
|---|---|---|---|
| ED-01 | `_03_ID編號` 的 92 筆現值都是「類別碼-序號」；建議 2.0 拆成 `type_category` 與 `type_sequence`，組合字串只作顯示 | **強烈建議**：照此拆分。資料已證明兩段語意不同，可移除執行期拆字串的歧義。 | 待決定 |
| ED-02 | 現行 Tag lock 同時辨識 `LOCK`、`不更新`、`NoUpdate` 且各指令規則不一；建議統一為單一正式 `lock_state` | **強烈建議**：統一。否則同一 Tag 在不同指令中可能同時被視為鎖定與未鎖定。 | 待決定 |
| ED-03 | Cabinet 現有程式已持有 panel 的 true W／H／D，卻在寫入前排序抹除方向；建議 L／W／T 依 panel local frame | **強烈建議**：採 local frame。資訊已存在，不需要再靠三邊大小猜方向。 | 待決定 |
| ED-04 | Rhino 模型文件單位與 Dictionary `_08_單位` 是兩件事；建議拆成模型單位契約與工程估算單位契約 | **強烈建議**：拆分。兩者用途與量綱完全不同，合併只會製造錯誤推導。 | 待決定 |
| ED-05 | Drawing lifecycle 先完成「重跑時辨識前次產出，讓使用者選擇取代／新增／略過」，再建立完整狀態機 | **強烈建議**：先完成這個最小安全基礎。沒有冪等性，後續狀態機無法可靠運作。 | 待決定 |

## C. 需要實務語意的問題

這些無法只靠讀碼正確決定，可以直接在最右側「你的決定／說明」欄自由描述實際工作方式。

| ID | 需要確認 | 目前觀察／可參考方向 | AI 建議（強度） | 你的決定／說明 |
|---|---|---|---|---|
| ED-06 | 高程 `CH`／`BC` 的正式語意 | `CH` 現況顯示 CH、幾何取物件底面；`BC` 對 Block 取插入點，非 Block 卻靜默退回底面 | **一般建議**：保留 CH＝天花物件底面、BC＝Block 插入點，但把規則、顯示標籤與前置條件分開；非 Block 使用 BC 時直接報錯。代價是部分舊模型需修正。 | 待決定 |
| ED-07 | Space boundary 是否會重疊、是否同時有多樓層 | 現況取 bbox 底面中心命中的第一條 boundary；需要定 priority／level／衝突行為 | **一般建議**：Space 使用穩定 ID、level 與 priority；多重命中時停止並列出衝突。代價是 boundary 需要多幾個正式欄位。 | 待決定 |
| ED-08 | 不同 Type 的寬、深、高如何定義 | 現況一般物件偏 world bbox；建議依 Type 與 local frame 定義 | **一般建議**：以 local frame 為預設，再允許各 Type 指定尺寸規則。代價是前期要為主要 Type 建立規則與 fixtures。 | 待決定 |
| ED-09 | `_09_實作數量` 是否要實作 | 目前沒有 producer；若要實作，需定義每種 `_08_單位` 對應的長度／面積／體積／計數規則 | **輕鬆建議**：2.0 第一階段保留 schema，但先設為人工／外部值；等估算需求明確再逐種單位實作。主要代價只是暫時沒有自動數量。 | 待決定 |
| ED-10 | `_13_備註` 的預設與 `20_DW` 操作說明 | `我是備註，UCCU` 看似測試字串；`20_DW` 說明可移至獨立 instruction | **輕鬆建議**：備註預設空白，`20_DW` 操作說明移到 instruction。這主要影響資料整潔，不影響核心鏈。 | 待決定 |
| ED-11 | `DNA_REF_` 參考線是否仍需要 | Dict-to-Layer 每次建立帶完整 Dictionary UserText 的參考線且會累積；需確認原本用途 | **輕鬆建議**：日常 Dict-to-Layer 不再建立；若仍需要目視樣本，另做可重建、可清除的 Type Sample 指令。 | 待決定 |
| ED-12 | Rhino 文件不是 cm 時如何處理 | A. 直接阻擋；B. 明確換算並顯示；目前工具與常數全部按 cm 設計 | **強烈建議**：2.0 初版直接阻擋並清楚說明；待全部量綱規則有測試後再考慮換算。這會限制非 cm 專案，但安全且可預測。 | 待決定 |
| ED-13 | 複製 Sheet 時一般 Tag 是否保留原模型來源 | 同一模型物件可能合理地出現在多張圖；但新 `sheet_id`／`drawing_id`／`tag_id` 必須建立，Index Tag 目標必須重審 | **一般建議**：一般 Tag 保留 `source_object_id`，但建立新 Tag／Sheet／Drawing ID；Index Tag 清除或重新指定目標。代價是複製完成後需處理待確認清單。 | 待決定 |

## D. 已確認、不需在本表重複決定

- 2.0 正式版以完整安裝檔／可安裝套件交付；開發期才使用逐支 entrypoint 測試按鈕。
- 工具列保留 Rhino Section 快捷入口；Macro 直接呼叫 Rhino 8 內建指令，不建立 Python entrypoint、不封裝 Rhino Section 功能本體。
- 正式安裝不覆蓋使用者完整 Rhino workspace。
- 實際封裝技術、工具列格式與圖示來源延後至發佈階段評估。
- Dictionary 與即時交換 JSON 使用 Dropbox 工作檔根目錄，實體路徑由每台電腦的環境設定解析。

## AI 回寫檢查

使用者修改本文件後，AI 必須：

1. 逐項區分「已明確決定」、「仍待決定」與「答案會影響其他項目」。
2. 不擅自補完使用者沒有回答的語意。
3. 將已決定內容回寫 `LOOPFLOW_DATA_ECOSYSTEM.md` 與 `_LoopFlow_命名與資料契約.md`。
4. 對應重排 `NEXUS_DICTIONARY_DECISION_MENU.md`，避免同一問題出現兩套答案。
5. 更新 `DEVELOPMENT_ROADMAP.md`、`PROGRESS.md`、fixtures 與 migration 影響。
6. 回寫完成後保留本文件的決策結果與日期，作為可追溯紀錄。

## E. 依目前 AI 建議推導的完整工作流程

本節先把上述建議轉成一條可實際理解的操作鏈，協助判斷這些原則是否符合工作習慣。`LF_*` 名稱是 **2.0 概念指令名稱，不是已完成的按鈕或最終命名**；`! _Clipping*` 則是 Rhino 8 內建指令。

### 第一次建立模型到完成圖面

| 步驟 | 使用的指令／動作 | 做了什麼 | 產生的結果與下一步 |
|---|---|---|---|
| 1. 開啟專案 | `LF_Project_Open`／啟動檢查 | 解析這台電腦的 `%LOOPFLOW_WORKFILES_ROOT%`，找到 Dictionary、`exchange/`、3D／2D 工作檔；驗證 Rhino 文件單位與版本 | 若不是 cm，依 ED-12 建議先阻擋並說明，不讓錯誤單位進入資料鏈；通過後建立 `project_id` context |
| 2. 驗證 Dictionary | `LF_Dictionary_Validate` | 讀取中文 Dictionary，檢查 schema、18 欄、Type ID、重複值、估算單位與必要欄位 | 產生只讀 Validation Report；錯誤先修正，通過後得到版本化 Type Catalog |
| 3. 同步 Type 與 Layer | `LF_Type_Sync` | 依 Type Catalog 建立或更新人類可讀的中英雙語 Rhino layers；Type ID 與 layer path 分開保存 | 使用者得到建模 layer；不自動建立會累積的 `DNA_REF_` 線，也不因 layer 改名改變 Type ID |
| 4. 建立 3D 模型 | Rhino 一般建模／Cabinet 等 LoopFlow 工具 | 使用者在對應 layer 建立、修改 Block 或幾何；Cabinet 依 local frame 保存板件方向 | 此時幾何是設計成果，但尚未直接假設所有資料都正確；下一步先掃描預覽 |
| 5. 掃描資料影響 | `LF_Nexus_Scan` | 根據 Type、幾何、Space、Elevation 與既有 metadata，找出缺 ID、重複 ID、未知 Type、尺寸與前置條件問題 | 只產生 Impact Report，不修改模型；重複 UUID 會列出原件、複本與受影響 Tag，不立即換號 |
| 6. 套用模型資料 | `LF_Nexus_Apply` | 使用者確認報告後，才建立／修復 Object ID，寫入 Type reference、Space ID、高程、尺寸及允許的 Instance override | 形成可驗證的 Model Objects；任何 ID 變更同時保存 old→new mapping，失敗可回復 |
| 7. 發布 Registry | `LF_Publish_Registry` | 將已通過驗證的 Type／Object／Space 資料寫入 pending，驗證完成後 atomic replace 為 current revision | 例如產生 Registry revision `42`；2D 文件只讀這個快照，不直接修改 Registry，也不在找不到檔案時自建空檔 |
| 8. 建立剖面／平面 | `! _ClippingSections` | 從 LoopFlow 工具列直接呼叫 Rhino 8 內建 Section 指令，建立 Clipping Plane／Section | Rhino 產生剖面定義；LoopFlow 不複製 Rhino 功能本體，也不為此建立 Python entrypoint |
| 9. 建立連動圖面 | `! _ClippingDrawings` | Rhino 依 Clipping Plane 產生 linked Generated Drawing | 得到可由 Rhino 更新的原始 Section 成果；它仍不是供長期人工修改的 Editable Drawing |
| 10. 註冊 View | `LF_View_Register` | 綁定 Clipping Plane、Generated Drawing 與 Detail，保存 `view_id`、方向、比例及穩定 2D↔3D transform | 之後 Laser 由正式 transform 定位，不再用名稱包含與可變 bbox 中心猜測 |
| 11. 產生可編輯圖面 | `LF_Drawing_Materialize` | 檢查是否已有同一 `view_id` 的前次產出，讓使用者選擇「新增、取代、略過」；複製成 Editable Drawing | 產生 `drawing_id`、來源 Registry／View revision 與 `generated` 狀態；不改變使用者原有 layer lock、visibility、selection |
| 12. 人工整理圖面 | Rhino 一般 2D 編輯 | 使用者修改線稿、補線、刪除不需要內容或調整圖層 | Drawing 轉為 `modified`；LoopFlow 記得來源但不會靜默覆寫人工成果 |
| 13. 建立 Sheet | `LF_Sheet_Create` 或 `LF_Sheet_Duplicate` | 建立 Layout、Detail、圖框與 Sheet metadata；複製時產生新 `sheet_id`／`drawing_id`／`tag_id` | 圖號與 Layout 名稱由 metadata 算出；一般 Tag 可依 ED-13 保留模型來源，Index Tag 目標必須重審 |
| 14. 建立 Tag 綁定 | `LF_Tag_Grab`／`LF_Tag_Laser`／`LF_Tag_Index` | Grab 直接選模型來源；Laser 由圖面點位經 View transform 找候選；Index 選目標 View／Sheet | Tag 保存 `source_object_id`、`view_id`、`drawing_id`、`sheet_id` 與 template version；位置只協助定位，不作資料真相 |
| 15. 顯示最新資料 | `LF_Sync_Current_Sheet` 或 `LF_Sync_All` | 從 Registry revision `42` 依 Tag Template 產生高程、材料、圖號、圖名等顯示值 | Tag 記錄 `last_synced_revision=42`；`lock_state` 的人工鎖定值不被覆寫 |
| 16. 交付前檢查 | `LF_Health_Check` | 唯讀檢查 unbound、orphaned、stale、view missing、template outdated、schema mismatch 等狀態 | 產生 Issue Report；不必先由 Infuser 塗色，也不修改使用者物件色 |
| 17. 選擇性修復 | `LF_Repair_Preview` → `LF_Repair_Apply` | 先顯示問題原因、會改哪些 ID／Tag／Drawing，再由使用者選擇重新綁定、同步、保留、脫離或略過 | 每項修復保存結果與復原資訊；完成後重新跑 Health，直到交付範圍內問題關閉 |

### 模型修改後，資料如何延續到最末端

以下用一個具體例子串起變更循環：

1. 使用者把 3D 磁磚牆高度由 240 cm 改成 260 cm。
2. 執行 `LF_Nexus_Scan`，系統辨認同一個 `object_id` 的幾何與高程資料改變，只顯示影響，不建立新 ID。
3. 使用者確認後執行 `LF_Nexus_Apply`，模型物件更新為新資料；接著 `LF_Publish_Registry` 發布 revision `43`。
4. 既有 Tag 的 `last_synced_revision` 仍是 `42`，Health 因此判定 `stale_data`；既有 Editable Drawing 的 source revision 也是 `42`，判定 `drawing_stale`。
5. 使用者先用 Rhino 內建 `! _UpdateClippingDrawings` 更新 linked Generated Drawing。這一步只更新 Rhino 的原始 Section 成果，不直接覆寫已人工修改的 Editable Drawing。
6. 執行 `LF_Drawing_Materialize`，系統找到既有 `modified` Drawing，要求選擇：
   - 保留舊圖並另建 revision `43` 的 Drawing；
   - 預覽後明確取代；
   - 保留現況並標成 detached；
   - 這次略過，繼續保持 stale。
7. 使用者選擇後，執行 `LF_Sync_Current_Sheet`；未鎖定的 Tag 從 revision `43` 更新高度，人工鎖定欄位維持原值。
8. 再執行 `LF_Health_Check`，已同步的 Tag 回到 healthy；若 Drawing 刻意保留舊版，報告會保留其 stale／detached 狀態與理由，不假裝問題不存在。

因此完整資料鏈是：

```text
Dictionary Type
→ Rhino Layer／3D Object
→ Nexus Scan／Apply
→ Registry Revision
→ Rhino Clipping Section／Generated Drawing
→ View Registration
→ Editable Drawing
→ Sheet Metadata
→ Tag Binding／Template Render
→ Health Report
→ Previewed Repair
```

這條鏈的核心效果是：3D 資料可以一路傳到圖框與 Tag，但每個階段都有明確 ID、revision、預覽與人工停點；任何更新都不以「方便」為理由靜默換 ID、重綁來源或覆蓋人工圖面。
