# LoopFlow 2.0 — 模擬執行流程

本文件把 `LOOPFLOW_DATA_ECOSYSTEM_DECISIONS.md` 的建議轉成可實際理解的操作鏈，協助判斷這些原則是否符合工作習慣。兩份流程由不同 AI 獨立推導，走同一條資料鏈但在細節與優先序上有差異，並列以便對照。

- 決策項目與建議強度：`LOOPFLOW_DATA_ECOSYSTEM_DECISIONS.md`（`ECO-*`／`ED-*` 編號皆指向該表）
- 資料實體、真相邊界與現況盤點：`LOOPFLOW_DATA_ECOSYSTEM.md`
- 本文件不維護決策答案；使用者的裁決一律寫在決策表，不在此重複。

`LF_*` 名稱是 **2.0 概念指令名稱，不是已完成的按鈕或最終命名**；`! _Clipping*` 則是 Rhino 8 內建指令。兩份流程都尚未經 Rhino 實機驗證。

> 本文件有一份深色好讀版 `LOOPFLOW_WORKFLOW_SIMULATION.html`，是**由本檔產生的衍生檔，不要手動編輯**。修改本檔後執行 `python wip/tools/build_workflow_html.py` 重新產生；`--check` 可驗證兩者是否一致。

---

# CodeX 模擬執行流程

## 第一次建立模型到完成圖面

| 步驟 | 使用的指令／動作 | 做了什麼 | 產生的結果與下一步 |
| --- | --- | --- | --- |
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

## 模型修改後，資料如何延續到最末端

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

---

# Claude Code 模擬執行流程

這一版走同一條資料鏈，但在三件事上刻意寫得比較細：**每一步在哪個 Rhino 文件執行**、**失敗或取消時會停在哪裡**、以及**哪些是第一階段就必須有、哪些可以晚點補**。

全文用同一個案子當例子：一間住宅，主臥室有一面磁磚牆（Type `WL-14`，`02_Wall_牆面::Tiles.磁磚`，高 240 cm）和一個開關面板（Type `EL-05`，`06_EL_電控系統::Switch.開關面板`，Block instance，高程基準 `BC`）。

## 前提：這條流程同時跑在兩個文件上

CodeX 版流程沒有明講這一點，但它決定了很多步驟為什麼要那樣設計。

| 角色 | 檔案 | 負責 |
| --- | --- | --- |
| 3D 文件 | `LoopFlow_3D.3dm` | 建模、資料化、剖面定義、發布 Registry |
| 2D 文件 | `LoopFlow_2D.3dm` | 圖面整理、Layout、圖框、Tag、出圖 |
| 交換層 | `%LOOPFLOW_WORKFILES_ROOT%\exchange\` | Registry 快照，兩個文件之間唯一的資料通道 |
| Worksession | `LoopFlow.rws` | 讓 2D 文件看得到 3D 幾何（給對照與定位用） |

現行 1.x 的隱性要求是「3D、2D、Registry 必須同資料夾」，因為程式從目前作用中的 `.3dm` 推導路徑。2.0 改成由 `%LOOPFLOW_WORKFILES_ROOT%` 解析，這個限制才會消失——但**兩個文件的分工本身要保留**，因為使用者實際就是這樣工作的。

---

## 階段 1｜開案與環境檢查（3D 文件）

**指令 `LF_Project_Open`** → 解析本機環境變數、確認工作檔根目錄存在、載入 Dictionary 與 `exchange/` 位置、讀取 `doc.ModelUnitSystem` → 建立本次工作階段的 `project_id` context，並在命令列印出**實際生效的設定值**（Dictionary 路徑、Registry 路徑、文件單位、規則來源）。

這一步刻意做兩件現況沒有的事：

- **印出實際生效值**。現況 config 有 import fallback（`_LF_Registry` 的 8.0／120.0 vs config 的 20.0／30.0），加上各腳本 reload 時機不一，使用者無法確認「我改的設定到底有沒有生效」。
- **偵測文件單位**。依 ED-12 我的建議，這裡**一定要偵測並顯示**；至於非 cm 時是擋下還是只警告，屬於可調策略。

失敗行為：環境變數缺失或目錄不存在 → 顯示變數名稱與設定方式後**停止**，不猜測磁碟機、不建立任何檔案。

## 階段 2｜Type Catalog 與 Layer（3D 文件）

**指令 `LF_Dictionary_Validate`** → 讀取中文 Dictionary，檢查 `schema_version`、欄位完整性、Type ID 唯一性、`type_category` 與 layer 群組是否相符、估算單位是否在允許清單內 → 產生**唯讀** Validation Report。

依 ED-01，`_03_ID編號` 在載入時就拆成 `type_category` + `type_sequence`（Excel 仍維持單欄，使用者維護方式不變）。於是這裡多出一條免費的檢查：`WL-14` 必須位於 `02_Wall_牆面` 底下；如果有人把它放進 `03_Floor_地坪`，這一步就會擋下來。現況沒有任何機制會發現這件事。

**指令 `LF_Type_Sync`** → 依 Type Catalog 建立或更新 Rhino layer，並把 `type_id` 寫成 layer 的正式屬性 → 使用者得到可建模的 layer 樹。

與現況 Dict-to-Layer 的差別（依 ECO-10 與 ED-11）：

- 不再每次新增 92 條 `DNA_REF_` 參考線。若你確認這些線有用途，改由獨立的 `LF_Type_Sample` 產生，且重跑時**先清除前次產物**再重建。
- 材質建立與 layer 建立分開成兩個明確動作，不是一個指令的隱藏副作用。
- 不執行 `ZoomExtents`——不改變使用者的視圖。

## 階段 3｜建模（3D 文件）

使用者用 Rhino 一般工具或 `LF_Cabinet_Suite` 在對應 layer 建立幾何。這階段 LoopFlow 不介入，只有一個約束：**Cabinet 產生前先確認目標 layer**，避免現況「在當前 layer 產生櫃體 → Nexus 把 `_CB.*` 全部清成 `-`」的靜默清空。

## 階段 4｜資料化：先掃描，後套用（3D 文件）

這是整條流程中我認為最需要改變操作習慣的一段。現況 `TagTrigger` 是「一鍵掃描全模型並直接寫入」；2.0 拆成兩個指令。

**指令 `LF_Nexus_Scan`** → 依 Type、幾何、Space、Elevation 前置條件掃描全部 M3D 物件，但**不寫入任何東西** → 產生 Impact Report，例如：

```text
待建立 Object ID：18 個
重複 Object ID：2 組（4 個物件）
  · 主臥磁磚牆 (WL-14)  ← 原件，已被 3 個 Tag 引用
  · 主臥磁磚牆 (WL-14)  ← 2026-08-10 複製產生，無 Tag 引用
未知 Type：1 個（layer 不在 Dictionary 內）
前置條件不成立：1 個
  · 開關面板 (EL-05) 高程基準為 BC，但此物件不是 Block instance
空間未命中：3 個（區分「室外」與「未涵蓋」）
```

**指令 `LF_Nexus_Apply`** → 使用者在報告上逐項決定後才執行寫入 → 產生帶穩定 ID 的 Model Objects，並保存 `old_id → new_id` mapping。

這樣做直接解掉三個現況問題：

| 現況 | 2.0 行為 | 對應建議 |
| --- | --- | --- |
| 重複 UUID 時原件與複本**都**被換新號，既有 Tag 一起斷，只回報數量 | 報告列出雙方、標示哪一個有 Tag 引用；預設保留有引用的一方，另一方發新號 | ECO-11 |
| `BC` 用在非 Block 物件上時靜默退回 BH，Tag 仍顯示 BC | 前置條件不成立**直接列為錯誤**，不寫入該物件的高程 | ED-06 |
| 空間未命中一律寫 `EXT`，之後無法分辨「室外」與「漏掉」 | 兩者分成不同結果，TAG-O 的覆蓋檢查才可信 | ED-07 |

`_05`／`_06`／`_07` 依 ED-08 的建議，這階段先**寫入但標為「規則未定義」**，等確定有 consumer 後再回頭定方向規則。

失敗行為：Apply 過程中斷 → 已寫入部分保留、mapping 已落地，重跑 Scan 會顯示剩餘項目，不需要從頭來。

## 階段 5｜發布 Registry（3D 文件 → `exchange/`）

**指令 `LF_Publish_Registry`** → 把已驗證的 Type／Object／Space 寫入 `registry.pending.json`，驗證通過後 atomic replace 成 `registry.current.json`，前一版保留為 `registry.previous.json` → 得到 revision `42`。

三個與現況的差異：

- **只發布有 consumer 的欄位**。現況 18 欄裡有 11 欄沒有任何行為 consumer，卻全部被寫進 Registry 變成事實上的公開 API。2.0 把它們放進明確的 extension 區，或先不發布。
- **不建立沒有 consumer 的區段**。現況的 `Layout_Map` 只寫不讀、`Tag_Links` 連呼叫者都沒有。
- **Reader 永不寫入**。這是 ECO-06 的實作重點，下一階段就會用到。

## 階段 6｜剖面與 View 註冊（3D 文件）

**Rhino 內建 `! _ClippingSections`** → 建立 Clipping Plane → Rhino 產生剖面定義。

**Rhino 內建 `! _ClippingDrawings`** → 產生 linked Generated Drawing → 得到可由 Rhino 自行更新的原始剖面成果。

**指令 `LF_View_Register`** → 把 Clipping Plane、Generated Drawing、目標 Detail 綁在一起，保存 `view_id`、視線方向、比例與**固定的 2D↔3D 轉換矩陣** → 之後所有定位都用這個矩陣。

這一步是我在複核裡認為最值得投資的地方。現況 Laser 的對位基準是**每次執行時重算**的兩個 bbox 中心：3D 側把所有可見 brep 與剖面求交、2D 側取 anchor frame 內所有 curve/hatch。結果是——你在剖面圖上多畫一條線，之後所有 Laser 綁定的落點就偏移，而且沒有任何紀錄能看出偏移了多少。

需要的資訊 Rhino 都已經提供（Clipping Plane 自帶 `Plane`，Detail 自帶 `PageToWorldTransform`，現行程式也已經在用）。缺的只是**把它固化下來**，而不是每次重猜。

## 階段 7｜圖面化（2D 文件）

**指令 `LF_Drawing_Materialize`** → 先查詢同一個 `view_id` 是否已有前次產出 → 若有，讓使用者選「新增版本 / 取代 / 略過」；若無，直接建立 → 產生 `drawing_id`、記錄來源 `view_id` 與 Registry revision `42`、狀態設為 `generated`。

依 ED-05，這個「先辨識前次產出」是 Drawing lifecycle 的第一個功能，先於任何狀態機。現況 Extract 每次無條件複製，跑兩次就是兩份完全重疊的線，且無法分辨。同時要修掉一個現況副作用：`ensure_layer()` 會把目標 layer 解鎖且不還原。

### 一個順帶解決 Laser 的提案

既然 Materialize 這一刻同時握有「3D 物件」與「剛生成的 2D 線」，建議在這裡**一次算出每條線的來源 `object_id`，存成 drawing 的來源索引**。

這樣 Laser 就從「每次對全模型求交後射線判斷」變成「點選最近的已標記線，讀出它的 `object_id`」：

| 比較項目 | 現況 Laser | 改用來源索引 |
| --- | --- | --- |
| 每次綁定的計算量 | 全模型 brep × 剖面求交 | 查表 |
| 對位是否會漂移 | 會（見階段 6） | 不會，關聯在生成當下就固定 |
| 多候選如何處理 | 依距離聚類，容差 200 cm（=2 公尺，過寬） | 該點附近有幾條不同來源的線，直接列出 |
| 是否需要 Worksession 附掛 3D | 必須 | 不必（但仍建議附掛以便對照） |

計算量其實沒有增加——只是把現在每次綁定都做一遍的事，改成生成時做一次。

**但這一項需要 Rhino 實機 spike 驗證**：要確認 Rhino 的 Clipping Drawing 輸出能不能穩定對應回來源物件，或者退而由 LoopFlow 自行以剖面交線做鄰近比對。在 spike 通過前，先按階段 6 的固定 transform 做即可，兩者不衝突。

**使用者接著做人工整理** → 補線、刪除不需要的內容、調整圖層 → Drawing 狀態轉為 `modified`，LoopFlow 從此不會靜默取代它。

## 階段 8｜Sheet 與圖框（2D 文件）

**指令 `LF_Sheet_Create`** → 建立 Layout、Detail、圖框，寫入 Sheet metadata（discipline / level / series / sequence / title …）→ Layout 名稱 `IN 101.01__一樓平面配置圖` 由 metadata **算出來**，不是資料本身。

依我對 ECO-05 的評估（一般建議、可分階段），第一階段只要做到「metadata 是產生名稱的來源」就夠了，完整的 Sheet 管理介面可以晚一點；因為這條的失敗是可回復的——名稱弄亂了，重跑一次就會修好。

**指令 `LF_Sheet_Duplicate`** → 複製版面 → **建立全新的 `sheet_id`／`drawing_id`／`tag_id`**，並產出一份待確認清單。

依 ED-13，這裡有一個必須當場處理、不能留給事後 Health 的項目：**Index Tag 的目標必須清除或重新指定**。現況複製後 Index Tag 沿用來源頁的 `.Target_DV_ID`，Infuser 認為「目標找得到、綁定正常」而不標紅，於是新頁的剖面索引安靜地指向來源頁的圖號。這是整份複核裡唯一連 Health 檢查都抓不到的錯誤。

另外不使用系統剪貼簿複製（現況 `_-CopyToClipboard` 會覆蓋使用者剪貼簿內容且不還原）。

## 階段 9｜Tag 綁定（2D 文件）

三種綁定意圖都保留，因為它們對應三種不同的使用情境：

| 指令 | 使用者做的動作 | 結果 |
| --- | --- | --- |
| `LF_Tag_Grab` | 直接點選要標的模型物件 | Tag 存下 `source_object_id`，來源明確無歧義 |
| `LF_Tag_Laser` | 在剖面圖上點位置 | 經固定 transform（或來源索引）找到候選；多候選時列出讓使用者選定，並記錄這是 `ambiguous` 解法 |
| `LF_Tag_Index` | 選另一張圖 / 另一個 View | Tag 存下 `target_view_id`／`target_sheet_id`，顯示的圖號由 Sheet metadata 產生 |

每個 Tag 一律保存：`tag_id`、`source_object_id`、`view_id`、`drawing_id`、`sheet_id`、`template_version`、`lock_state`。

依 ED-02，鎖定改成單一 `lock_state`。現況三支程式規則不一致——Laser 只認 `NoUpdate`、Infuser／Grab／Index 只認「不更新」——所以一個用「不更新」鎖住的 Tag，Infuser 會尊重，Laser 卻允許你重新綁定。

門窗與家具 Tag 不再使用 `NAME_PARSED` 這個哨兵值假裝有來源，改為正式的 source type。

## 階段 10｜同步顯示值（2D 文件）

**指令 `LF_Sync_Current_Sheet`（或 `LF_Sync_All`）** → 讀 Registry revision `42`，依 Tag Template 把欄位對應成顯示值 → Tag 記錄 `last_synced_revision = 42`。

以磁磚牆的高度 Tag 為例，Template 宣告的對應是：

```text
TAG_HEIGHT
  attr_ch_key  <- elevation.basis.label     → "BH"
  attr_ch_val  <- elevation.display         → "+240"
  attr_mat_key <- type.category             → "WL"
  attr_mat_val <- type.sequence             → "14"
  attr_note    <- type.display_name         → "磁磚牆面"
```

`type.category` / `type.sequence` 直接來自階段 2 拆好的欄位，不需要在這裡對 `_03` 字串做 `split("-", 1)`——這也順帶解掉「ID 本身含連字號會被誤拆」的問題。

`lock_state` 為鎖定的 Tag 完全跳過，人工填的值原樣保留。

## 階段 11｜健康檢查與修復（2D 文件）

**指令 `LF_Health_Check`** → **完全唯讀**掃描，依 metadata 判定狀態 → 產生 Issue Report。

這一步與現況 TAG-O 有本質差異。現況 TAG-O 只比對物件的 RGB 顏色，因此：必須先跑 Infuser 塗色才能檢查（先改資料才能檢查資料）、使用者自訂過顏色的 Tag 會誤判、而 Infuser 清除提示時會把 ColorSource 設回 ByLayer，**破壞使用者原本的物件顏色**。

第一階段能可靠判定的狀態只有這幾種，建議先只做這些：

| 狀態 | 判定依據 | 第一階段可做 |
| --- | --- | --- |
| `unbound` | 沒有 `source_object_id` | 可 |
| `orphaned` | `source_object_id` 不在 Registry | 可 |
| `manual_locked` | `lock_state` | 可 |
| `stale_data` | Tag revision < Registry revision | 可 |
| `drawing_stale` | Drawing source revision < 目前 revision | 可 |
| `ambiguous` / `view_missing` / `template_outdated` / `schema_mismatch` | 需要候選集合、`view_id`、`template_version`、`schema_version` | 待對應契約完成 |

**指令 `LF_Repair_Preview` → `LF_Repair_Apply`** → 先顯示「會改哪些 ID／Tag／Drawing、原值是什麼」，使用者逐項選擇重新綁定 / 同步 / 保留 / 脫離 / 略過 → 每項修復保存結果與復原資訊。

---

## 完整變更循環：把磁磚牆從 240 改成 260

這是實務上最常發生的事，也是檢驗整條鏈是否成立的標準案例。

| # | 在哪 | 指令／動作 | 發生什麼 | 結果 |
| --- | --- | --- | --- | --- |
| 1 | 3D | Rhino 一般編輯 | 使用者把牆拉高 20 cm | 幾何改變，`object_id` 不變 |
| 2 | 3D | `LF_Nexus_Scan` | 比對後發現此物件的高程與尺寸已變 | 報告顯示「1 個物件資料需更新」，**不建立新 ID、不寫入** |
| 3 | 3D | `LF_Nexus_Apply` | 使用者確認後寫入新高程 | Model Object 更新，ID 與既有 Tag 關聯完全不動 |
| 4 | 3D | `LF_Publish_Registry` | pending → validate → replace | 產生 revision `43`，`previous` 保留 `42` |
| 5 | 2D | `LF_Health_Check` | Tag 的 `last_synced_revision=42` < `43`；Drawing source revision 也是 `42` | 報告：3 個 Tag `stale_data`、1 張圖 `drawing_stale`。**此時什麼都還沒被改** |
| 6 | 2D | `! _UpdateClippingDrawings` | Rhino 更新 linked Generated Drawing | 原始剖面成果變新，**已人工修改的 Editable Drawing 不受影響** |
| 7 | 2D | `LF_Drawing_Materialize` | 偵測到既有 Drawing 狀態是 `modified` | 要求選擇：另建 revision `43` 版本 / 預覽後取代 / 標為 detached / 這次略過 |
| 8 | 2D | `LF_Sync_Current_Sheet` | 未鎖定的 Tag 從 revision `43` 取值 | 高度 Tag 從 `+240` 變成 `+260`；鎖定的 Tag 原值不動 |
| 9 | 2D | `LF_Health_Check` | 重新判定 | 已同步的 Tag 回到 healthy；若第 7 步選了「略過」，報告會**繼續保留** `drawing_stale` 與原因，不假裝問題消失 |

關鍵在第 5 步和第 7 步：**檢查不修改任何東西**，而**任何可能覆蓋人工成果的動作都要先問**。現況這兩點都不成立——TAG-O 要先靠 Infuser 塗色才能檢查，Extract 則是直接再複製一份。

---

## 中斷、取消與失敗時停在哪裡

這是 ECO-08 的實際意義，也是現況最薄弱的地方。每個階段都要能明確回答「我按了 Esc 之後現在是什麼狀態」。

| 階段 | 中途取消 | 執行失敗 |
| --- | --- | --- |
| 開案 | 無副作用 | 顯示缺少的設定，不建立任何檔案 |
| Dictionary 驗證 | 無副作用（唯讀） | 列出全部錯誤列，不部分套用 |
| Type Sync | 已建立的 layer 保留，重跑補齊 | 報告哪些 layer 失敗，不留半套 |
| Nexus Scan | 無副作用（唯讀） | 同上 |
| Nexus Apply | 已寫入部分保留、mapping 已落地，重跑 Scan 顯示剩餘 | 同左，並標明中斷點 |
| Publish | `current` 不變，`pending` 留著供檢查 | `current` 與 `previous` 都完好 |
| Materialize | 不留半份圖 | 已建立的部分可用同一 `drawing_id` 辨識並清除 |
| Sheet 複製 | 不留半頁 | 待確認清單仍產出 |
| Tag 綁定 | Tag 維持原綁定 | 同左 |
| 同步 | 已同步的 Tag 保留其 revision，未處理的維持舊值 | 同左，報告列出未完成範圍 |
| Health | 無副作用（唯讀） | 部分結果仍可顯示，標明未檢查範圍 |
| Repair | 未套用的項目不變 | 已套用項目可依復原資訊回退 |

另外三個現況會「順手改掉使用者東西」的行為，在 2.0 都要還原：selection、layer lock／visibility、物件顏色。

---

## 第一階段最小可用範圍

這條鏈不需要全部做完才能開始用。若要讓「模型 → 圖面 → Tag」跑通一次，最少需要：

**必須有**（缺一條鏈就斷）

1. `LF_Project_Open`：路徑解析 + 單位偵測
2. `LF_Dictionary_Validate` + `LF_Type_Sync`：Type Catalog 與 layer
3. `LF_Nexus_Scan` / `LF_Nexus_Apply`：Object ID 與資料（含 ID 變更預覽）
4. `LF_Publish_Registry`：安全發布 + revision
5. `LF_View_Register`：固定 transform
6. `LF_Drawing_Materialize`：冪等的可編輯圖面
7. `LF_Tag_Grab` + `LF_Sync_*`：最簡單的綁定與同步
8. `LF_Health_Check`：前述五種可靠狀態

**可以晚一輪**

- `LF_Tag_Laser`（有 Grab 就能出圖，Laser 是效率工具）
- `LF_Sheet_Duplicate`（可以先手動建頁）
- 完整 Drawing 狀態機（先有冪等就夠）
- Cabinet／2D 工具重建（現有 1.x 版本可以繼續用到最後）
- `_09_實作數量`、`_05`/`_06`/`_07` 的方向規則（都還沒有 consumer）

**建議最先動工的一項**：階段 4 的 Scan／Apply 拆分。它同時解掉 UUID 不可逆損失（ECO-11）、BC 靜默錯誤（ED-06）與空間未命中歧義（ED-07），而且不依賴其他任何新契約。

---

## 與 CodeX 流程的主要差異

兩版的資料鏈結論一致，差異在細節與優先序：

| 項目 | CodeX 版 | Claude 版 |
| --- | --- | --- |
| 文件分工 | 未區分 3D／2D | 每步標明執行文件，並說明 Worksession 角色 |
| Nexus | Scan → Apply 兩步 | 相同，但明列 Impact Report 實際內容與三個現況問題的對應 |
| Laser | 用固定 View transform 定位 | 相同，另提議在 Materialize 時建立來源索引，讓 Laser 退化成查表（需 spike 驗證） |
| Sheet metadata | 強烈建議、一次到位 | 一般建議、可分階段（失敗可回復） |
| 非 cm 專案 | 直接阻擋 | 偵測與顯示是必須；阻擋只是可調的預設策略 |
| Health 狀態 | 列出十種 | 第一階段只做五種可靠判定的，其餘標註前置需求 |
| 失敗行為 | 未展開 | 每階段列出取消與失敗時的狀態 |
| 施工順序 | 未排 | 給出最小可用範圍與建議最先動工項目 |

兩版都指向同一個核心：**每個階段都有明確 ID、revision、預覽與人工停點，任何更新都不以「方便」為理由靜默換 ID、重綁來源或覆蓋人工成果。**
