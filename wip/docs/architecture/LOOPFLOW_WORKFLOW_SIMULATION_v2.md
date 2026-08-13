# LoopFlow 2.0 — 模擬執行流程

本文件把 `LOOPFLOW_DATA_ECOSYSTEM_DECISIONS.md` 的建議轉成可實際理解的操作鏈，協助判斷這些原則是否符合工作習慣。CodeX 流程已用使用者提供的 `loopflow_1.0_YT.txt` 逐步操作說明重新檢核；Claude Code 流程保留獨立靜態複核視角，兩者並列以便對照。

- 決策項目與建議強度：`LOOPFLOW_DATA_ECOSYSTEM_DECISIONS.md`（`ECO-*`／`ED-*` 編號皆指向該表）
- 資料實體、真相邊界與現況盤點：`LOOPFLOW_DATA_ECOSYSTEM.md`
- 本文件不維護決策答案；使用者的裁決一律寫在決策表，不在此重複。

文中明列為「1.0」的 `LF_*` 是既有指令；明列為「2.0」或「概念」的 `LF_*` 則不是已完成按鈕或最終命名。`! _Clipping*` 是 Rhino 8 內建指令。1.0 操作順序已有錄影說明作為使用者流程證據；2.0 建議行為仍尚未經 Rhino 實機驗證。

> 本檔目前是依 1.0 實際操作重新檢核的 v2 草案。現有 `LOOPFLOW_WORKFLOW_SIMULATION.html` 仍由未加 `_v2` 的主檔產生，**不會自動反映本草案**；待本版確認後，再決定取代主檔或另外產生 v2 HTML。

---

# CodeX 模擬執行流程

這一版以 `loopflow_1.0_YT.txt` 記錄的實際操作為基準，再把 2.0 的安全機制放回相同的操作節點。範例仍使用住宅主臥室的磁磚牆（Type `WL-14`，高 240 cm）與開關面板（Type `EL-05`，高程基準 `BC`）。

閱讀時要區分兩件事：

- **1.0 實際操作**：已存在的 `LF_Nexus` 子功能、`LF_Anchor_Frame`、`LF_Extract_CP`、Tagger、Infuser 與顏色回饋。
- **2.0 建議責任**：尚未實作的 Scan／Apply、穩定 View ID、revision、唯讀 Health 與可復原 Repair。它們改善安全性，但不能刪掉使用者原本的選取、確認與分段操作。

Tag 部分另以使用者提供的 8 份 Block 參數文字，對照 1.0 的 `_LoopFlow_Config.py`、`LF_Tagger_*`、`LF_Infuser_*` 與 `LF_TAG-O.py`。因此下文會把「畫面可見參數」與 Python 動態加入的隱藏綁定資料分開。這次沒有 `TAG_DW` 的參數文字，也沒有在 Rhino 內開啟 `Tag_Blocks.3dm`；使用者已確認 `TAG_DW` 後來改為純手動輸入，所以 Python 內仍存在的 `attr_dw_id`、`Source_UUID` 與 `.Auto_DW_ID` 路徑只視為歷史程式，不再當成現行資料契約。

## 檢核結論｜原流程需要補回的操作事實

| 1.0 錄影中的操作事實 | 原 CodeX 版的落差 | 本版調整 |
| --- | --- | --- |
| `LF_Nexus > SpaceBoundary` 由使用者選取 closed curves 定義空間 | 只在 Scan 中抽象提到 Space，沒有建立空間的操作節點 | 獨立成「建立／維護 Space Boundary」階段 |
| `TagTrigger` 寫完資料後，使用者立即跑 `TagChecker` | 只在最末端安排 Health | 補回模型資料的前置檢查點；通過後才發布 Registry |
| 建模後可用 `Layer to Dict.` 反向匯出 layer 狀態供人工對照 | 完全省略 | 列為選用支線，明確禁止自動覆寫 Dictionary |
| Anchor Frame 是所有 Tagger 的固定靶心；不能刪，圖面移動時要一起移 | 直接以 `LF_View_Register` 取代，沒有交代現行操作 | 保留 1.0 規則，並說明 2.0 如何用正式 View Registration 取代脆弱依賴 |
| `LF_Extract_CP` 按顏色把 Section 線稿拆至新 layer，之後由使用者整理 | 只寫抽象的 Drawing Materialize | 補回按顏色拆圖、重設 layer／樣式與 Anchor 同步移動 |
| Layout 先由使用者準備，再用 `LF_Tagger_Layout_ID` 批次編號 | 假設由 `LF_Sheet_Create` 自動建立 | 改回人工建立／複製 Layout，再執行編號；2.0 metadata 只作安全升級方案 |
| Tag Block 可用 `x / X` 將單一 Tag 切為人工模式 | 只提抽象 `lock_state` | 補回使用者何時設定人工保護及同步時的效果 |
| Infuser 後以紫／橘／紅顯示 linked、unlinked、broken | 沒有描述使用者看到的 1.0 回饋 | 補回顏色判讀與對應的人工作業；2.0 再由正式狀態取代顏色真相 |
| 各 Tag Block 的可見欄位與 Python 寫入清單高度耦合 | 只用通用 Tag Template 描述，沒有辨認 `TAG_ELEV_0`、Index 與資料 Tag 的差異 | 補上欄位所有權、隱藏 binding、Block family 與 Infuser 寫入結果 |
| Cabinet 與三個 2D Generator 不屬於強制主鏈 | 混在建模步驟，界線不清 | Cabinet 列為建模選用工具；2D Generator 列為可隨時使用的獨立工具 |

## 前提｜資料可跨越 3D 與 2D 工作內容

| 角色 | 主要責任 | 使用者掌握的控制點 |
| --- | --- | --- |
| 3D 模型文件 | Dictionary layer、建模、Space、模型資料、Registry、Section 定義 | 何時寫入模型資料、何時檢查、何時發布 |
| 2D／Layout 文件 | 可編輯線稿、Layout、圖框、Tag、出圖 | 哪些圖要抽出、如何整理、Tag 綁誰、何時同步 |
| Registry／交換層 | 把已確認的模型資料提供給 Tag／Infuser | 只有明確 Publish 才產生新版；2D 端不回寫模型真相 |
| Worksession／3D 參照 | 讓出圖端看見模型並供 Grab／Laser 定位 | 可更新參照，但不能取代 Object ID 與 Registry |

1.0 錄影重點是操作責任，沒有要求所有專案一定使用同一種檔案拆法；2.0 應明確辨識目前文件的角色，不依檔名或所在資料夾猜測。

---

## 前置階段｜開案檢查（2.0 新增，不取代 1.0 工作步驟）

**2.0 概念指令 `LF_Project_Open`** → 解析 `%LOOPFLOW_WORKFILES_ROOT%` → 確認 Dictionary、exchange、文件單位與專案身分 → 顯示本次實際生效設定。

1.0 沒有獨立的開案指令；各工具從目前文件位置與設定自行推導路徑。2.0 增加這一步，是為了讓兩台電腦路徑不同時仍能得到一致專案，並在進入工作鏈前就擋住缺檔或錯誤單位。

> **使用者介入**：只在設定缺失或專案辨識不明時處理；正常開案不增加日常操作負擔。
>
> **安全停點**：失敗時不建立空 Registry、不修改模型。

## 階段 1｜Dictionary 建立建模 Layer（3D）

**1.0：`LF_Nexus > Dict. to Layer`** → 使用者選擇執行 → 從 Dictionary 直接建立 Rhino layers → 開始依分類建模。

**2.0：`LF_Dictionary_Validate` → `LF_Type_Sync`** → 先顯示 Validation Report → 通過後才建立／更新 layers。這保留原本「Dictionary 定義一次、Nexus 建 layer」的操作精神，只把驗證從執行中錯誤提前。

> **使用者介入**：決定何時同步 Dictionary；驗證有問題時回 Excel 修正，再重跑。
>
> **安全停點**：layers 建立完成即可存檔、關閉或換機，不必接著跑完整流程。

## 階段 2｜建立與修改 3D 模型（3D）

**Rhino 一般建模** → 使用者在 Dictionary 建出的 M3D layers 上建立牆、地坪、家具、門窗與設備。

**選用 `LF_Cabinet_Suite`** → 從 30 種櫃身、門片與層板組合建立櫃體並寫入 BOM 尺寸。1.0 的 Suite 產物可在任何 layer；手工建立的櫃體若要用 BOM Update，必須位於 `M3D::04_CB`，全選模型也可以，非櫃體 layer 會被忽略。1 mm 板件間隙是刻意保留的 render gap，BOM 計算會補償。

> **使用者介入**：建模本身完全由使用者控制；LoopFlow 不在背景自動注入或發布資料。
>
> **安全停點**：只完成幾何也可以正常存檔；下游繼續使用上一份已發布 Registry。

## 階段 3｜建立或維護 Space Boundary（3D）

**1.0：`LF_Nexus > SpaceBoundary`** → 使用者選取代表空間的 closed curves → 讓後續 TagTrigger 能把空間資料寫到模型物件。

這不是 Scan 的隱藏前置，而是一個明確的人工建模步驟。使用者可能在平面改動、房間邊界改變或新增樓層後回到這裡重新整理，再進行資料注入。

**2.0 建議** → Boundary 保存穩定 `space_id`、顯示名稱與必要的 level／priority；未命中、室外與多重命中分開報告，不再全部寫成 `EXT`。

> **使用者介入**：選取哪些 closed curves 是有效空間邊界，並處理重疊、缺口或錯誤範圍。
>
> **安全停點**：Boundary 完成後可獨立存檔；尚未重跑資料注入前，既有物件資料不會自行改變。

## 階段 4｜把 Dictionary 與模型資料寫入 M3D 物件（3D）

**1.0：`LF_Nexus > TagTrigger`** → 使用者明確按下執行 → 程式掃描所有 M3D layers 上的 3D 物件，寫入 Dictionary、空間、尺寸、高程與 UUID。依錄影說明，作用範圍**不受物件可見或鎖定狀態影響**；使用者不必逐件選取。

這是重要的操作契約：使用者決定「什麼時候對整個 M3D 範圍寫資料」，程式不能在建模途中背景自動執行。

**2.0：`LF_Nexus_Scan` → 使用者檢視 Impact Report → `LF_Nexus_Apply`**：

1. Scan 先列出將新增／更新的物件、重複 ID、未知 Type、Space 未命中與高程前置錯誤，不寫入模型。
2. 使用者確認全部、勾選部分或取消。
3. Apply 才寫入；ID 若變更，保存 `old_id → new_id` mapping。

> **使用者介入**：1.0 是決定何時全量寫入；2.0 再增加「看報告後決定是否套用」的停留點。
>
> **安全停點**：Scan 後可直接停止，模型零變更；Apply 完成後尚未 Publish，2D 端仍讀上一版資料。

## 階段 5｜立即檢查模型資料（3D）

**1.0：`LF_Nexus > TagChecker`** → 緊接 TagTrigger 後檢查資料完整性 → 找出缺少或錯誤屬性的模型物件 → 使用者回到 layer、boundary、Dictionary 或物件本身修正 → 再跑 TagTrigger／TagChecker。

原 CodeX 版只在出圖末端安排 Health，會失去 1.0 已經存在的重要停點。模型資料必須先通過自己的檢查，才能發布給圖面端；下游 Health 不能代替這一步。

**2.0 概念責任 `LF_Model_Data_Check`** → 唯讀驗證本次 Apply 的 Model Objects、列出阻擋發布的錯誤與可接受警告。

> **使用者介入**：判斷哪些問題要回模型修正；在必要欄位或 ID 尚未通過前，不執行 Publish。
>
> **安全停點**：Checker 只讀；可保存報告後中止，不改模型與 Registry。

## 選用支線｜建模後反向對照 Dictionary（3D → Excel）

**1.0：`LF_Nexus > Layer to Dict.`** → 使用者在建模過程新增、刪除或調整 layer 後，主動反向匯出目前 Rhino layer 狀態到 Excel → 人工核對並整理 Dictionary。

這是一條**選用的維護支線**，不是每次 Publish 的必要前置。2.0 仍應保留「從模型現況提出 Dictionary 差異」的意圖，但輸出必須是差異／候選檔；不能把 `[NEW]`、`[DELETED]` 等狀態混入正式主鍵，也不能未經使用者確認自動覆寫正式 Dictionary。

> **使用者介入**：人工決定哪些 layer 變化應正式納入 Type Catalog。
>
> **返回主鏈**：Dictionary 若有修改，回到階段 1 驗證與同步；沒有修改則繼續發布。

## 階段 6｜發布 Project Registry（3D → 2D）

**1.0：`LF_Push_3D_to_JSON`** → 使用者在模型資料確認後執行 → 將 M3D 物件資料寫入 `Project_Registry.json` → 供 Tagger／Infuser 使用。

**2.0：`LF_Publish_Registry`** → 把已驗證資料寫入 pending → validate → atomic replace current → 保留 previous → 產生明確 revision。

> **使用者介入**：只有使用者確認模型已到可供出圖的狀態，才發布；存檔與 Publish 是兩件事。
>
> **安全停點**：發布完成是最重要的跨電腦／跨文件停點。若新發布失敗，2D 端繼續使用 last-good revision。

## 階段 7｜建立 Section／Clipping Drawing（含 3D 參照的文件）

**Rhino 內建 `! _ClippingSections`** → 使用者放置剖面／立面／平面所需的 Clipping Plane，決定方向與範圍。

**Rhino 內建 `! _ClippingDrawings`** → 使用者選擇要建立的 Section → Rhino 產生 linked 2D linework。

這兩個按鈕是 Rhino 8 內建功能的工具列捷徑，不是 LoopFlow Python。LoopFlow 必須保留「使用者決定在哪裡切、要產生哪一張圖」的操作，不將所有 View 在 Publish 後自動生成。

> **使用者介入**：Clipping Plane 的位置、視線方向、顯示範圍及要輸出的圖。
>
> **安全停點**：linked Section 可以先保留、更新與檢查，尚未 Extract 或 Tag 也不影響模型資料。

## 階段 8｜建立 Anchor Frame／註冊 View（Section 圖面）

**1.0：`LF_Anchor_Frame`** → 以 Section 的 2D output 建立 bounding frame → 後續 Tagger 把它當成固定靶心，用來定位這張圖。

1.0 必須遵守兩條規則：

1. **不可刪除 Anchor Frame**，否則後續 Tagger 失去定位基準。
2. **移動 2D 圖面時，Anchor Frame 必須與圖面一起移動**；只移線稿會造成錯位或斷鏈。

**2.0：`LF_View_Register`** → 由使用者確認 Clipping Plane、Generated Drawing 與 Detail 的配對 → 保存 `view_id` 與穩定 2D↔3D transform。2.0 的目標不是要求使用者永遠保護一條脆弱框線，而是把 Anchor 所承擔的「固定定位」意圖升級為可檢查、可修復的正式 View 資料。

> **使用者介入**：確認這個 Anchor／View 屬於哪一張 Section 與哪個 Detail。
>
> **安全停點**：定位關係不唯一時停止，不建立看似完成但實際配錯的 View。

## 階段 9｜視需要抽出可獨立編輯的圖面（2D）

**1.0：`LF_Extract_CP`** → 依 Section Tools output 的顏色，把不同 linework 類別複製到新的 2D layers → 使用者選取、改 layer、改樣式、補線或刪線。

錄影把這項列為 Extra，表示不是每次操作都必須抽圖；但只要圖面要脫離 linked output 並進行人工整理，它就是主鏈上的必要轉換。抽出後若移動圖面，1.0 的 Anchor Frame 必須同步移動。

**2.0：`LF_Drawing_Materialize`** → 先辨識同一 View 的前次產出 → 讓使用者選擇新增、預覽後取代或略過 → 保存 `drawing_id`、來源 revision 與 `generated / modified / detached / stale` 狀態。

> **使用者介入**：決定是否抽出、哪些線要保留、如何重新分層，以及重跑時要保留舊人工成果還是建立新版。
>
> **安全停點**：人工整理完成即可停工；更新來源時不得靜默覆寫。

## 階段 10｜準備 Layout、圖框與 Tag Blocks（2D／Layout）

**1.0 實際順序**：使用者先建立或整理 Layout、Detail、圖框與需要的 Tag Blocks → 視需要複製 Layout → 再執行 **`LF_Tagger_Layout_ID`**，批次編號全部 Layout 並把 drawing number 寫入 title blocks。編號格式由 `NamingRules_Config.json` 控制。

因此 2.0 不能假設 `LF_Sheet_Create` 一定自動包辦建頁。較貼近實務的設計是：

- 使用者可以手動建立／複製 Layout，也可以日後使用輔助指令。
- 系統以 `sheet_id` 與 Sheet metadata 辨識既有頁面。
- `LF_Sheet_Number`（概念名稱）只負責檢查 metadata、計算 Layout 名稱／圖號、寫入圖框。
- 複製後建立新的 Sheet／Drawing／Tag ID；Index Tag 的目標必須重新確認。

**Tag Block 的人工模式**：1.0 可在個別 Tag 使用 `x / X` 啟用 write protection，使它從自動更新切為人工維護。2.0 應保留同樣的使用意圖，但以單一正式 `lock_state` 呈現，讓使用者清楚看出哪些欄位不會被 Infuser／Sync 覆寫。

> **使用者介入**：建立頁面與 Detail、放置正確 Tag Blocks、確認命名設定、決定哪些 Tag 要人工保護。
>
> **安全停點**：Layout 編號完成但尚未綁 Tag 也可正常存檔；2.0 應明確保存 pending，1.0 則在下一次 Infuser 執行後把未綁定 Tag 標為橘色。

## Tag Block 實際參數｜1.0 Block 與 Python 的交界

Tag Block 不是被動圖形。Block 內的 `%<UserText("block", ...)>%` 會直接顯示該 instance 的 UserText，而 Python 依**固定 Block 名稱與固定 key**決定怎麼綁定、寫值、鎖定及標色。只改 Block key 或 Python 任一邊，都可能造成畫面空白但程式沒有報錯。

### 各 Block family 的可見參數與責任

> `tag_elev.txt` 對應 `TAG_ELEV_1`～`TAG_ELEV_4`，是依參數檔名與 `_LoopFlow_Config.py` 的 family 清單推定；這次尚未直接開啟 `Tag_Blocks.3dm` 核對 Block Definition。

| Block family／提供的參數檔 | 畫面可見的自動欄位 | 使用者保留欄位 | Python 動態加入的隱藏資料 | 1.0 行為 |
| --- | --- | --- | --- | --- |
| `TAG_SECTION_DETAIL`／`tag_section_detail.txt` | `Category`、`REF_ID` | `Detail_NO`、lock | `.Target_DV_ID` | Index 綁定 Detail；Infuser 依目標所在 Layout 重算 `Category`／`REF_ID`；`Detail_NO` 沒有 Python writer |
| `TAG_ELEV_1`～`TAG_ELEV_4`／`tag_elev.txt` | `Category`、`REF_ID` | `Detail_NO`、lock | `.Target_DV_ID` | 與 Section Detail 使用相同參數契約，差異主要在 Block 圖形／名稱 |
| `TAG_ELEV_0`／`tag_elev_0.txt` | `Category`（由 Layout ID 寫入） | `1-Elev_num`、`2-Elev`、`3-Top`、`4-Left`、`5-Bottom`、`6-Right`、lock | 目前無 binding key | 它不是一般 Index Tag；不在 Infuser 與 TAG-O 清單內，六個方向／編號欄目前沒有 Python writer |
| `TAG_HEIGHT_GRAB`／`TAG_HEIGHT_LASER` | `attr_ch_key`、`attr_ch_val`、`attr_mat_key`、`attr_mat_val`、`attr_note` | `attr_manual_補充說明`、lock | `Source_UUID` | Infuser 由 Registry 寫高程基準、計算值、Type 編號兩段與名稱；Grab／Laser 只決定來源 |
| `TAG_FINISH_GRAB`／`TAG_FINISH_LASER` | `attr_mat_key`、`attr_mat_val`、`attr_note` | `attr_manual_補充說明`、lock | `Source_UUID` | Infuser 由 Registry 寫 Type 編號兩段與名稱；Grab／Laser 只決定來源 |
| `TAG_ITEM`／`Tag_Item.txt` | `attr_item_key`、`attr_item_val`、`attr_note` | `attr_manual_補充說明`、lock | `Source_UUID`、`.Auto_Item_Key`、`.Auto_Item_Val`、`.Auto_Item_Note` | Grab 可讀一般 UUID，也可從命名為 `KEY-VALUE__NOTE` 的 Block 解析 shadow fields，再由 Infuser 回填 |
| `TAG_DW` | 無；不由 Python 自動寫入 | 所有顯示欄位（目前純手動） | 現行流程無 binding；`Source_UUID`、`.Auto_DW_ID` 僅為歷史程式欄位 | 不執行 Grab／Infuser 綁定；Block 的完整欄位仍待實機核對 |

`Tag_Finish_*` 與 `Tag_Height_*` 參數檔中的 `Grab`／`Laser` 是固定畫面標示，不是 UserText key。兩者顯示欄位相同，主要差別是允許的綁定方式與 Block 名稱。

### 四種欄位所有權不能再混在一起

| 所有權 | 1.0 例子 | 允許的寫入者 | 2.0 要求 |
| --- | --- | --- | --- |
| Binding metadata | `Source_UUID`、`.Target_DV_ID`、`.Auto_*` | Grab／Laser／Index／migration | 不一定顯示在 Block 上；要有 typed schema、來源類型與有效性檢查 |
| Render output | `Category`、`REF_ID`、`attr_ch_*`、`attr_mat_*`、`attr_item_*`、`attr_note` | Layout ID／Infuser／Sync | 可重算；來源失效時顯示錯誤，但不能碰人工欄位 |
| Manual content | `Detail_NO`、`attr_manual_補充說明`、`TAG_ELEV_0` 六個方向／編號欄 | 使用者 | Sync、錯誤處理與 Block 升級都不得覆寫；如未來要自動化，需另行裁決 |
| Control／state | `attr_Lock_不更新>寫入x或X`、物件顏色 | 使用者設定 lock；Infuser 設顏色 | lock 與 health 必須分開；鎖定不應讓 stale／broken 狀態消失 |

提供的 8 份 Block 都使用同一個 lock key：`attr_Lock_不更新>寫入x或X`。它同時含有 `Lock` 與「不更新」，所以 Grab、Laser、Index、Infuser 的現行偵測都能辨認 `x / X`。各支 Python 的備援判斷仍不一致，但對這批正式 Block 而言是**潛在改名／舊 Block 相容風險**，不是目前已證實的鎖定失效。

### `LF_Tagger_Layout_ID` 對不同 Block 的寫入也不相同

- 一般資料 Tag（Height／Finish／DW／Item）：清除不屬於它的 `DWG_NAME`、`DWG_NO`、`REF_ID`、`Category`。
- Index Tag（Section Detail／Elev 1～4）：清除 `DWG_NAME`、`DWG_NO`；`Category`、`REF_ID` 留給 Index／Infuser 表示**目標頁**。
- `TAG_ELEV_0`：清除 `DWG_NAME`、`DWG_NO`、`REF_ID`，只把**目前頁**的 `Category` 寫入 Block。
- 圖框或其他 Block：寫入目前頁的 `DWG_NO`／`DWG_NAME`，並清除 `Category`／`REF_ID`。

因此 `Category` 在不同 Block 具有不同上下文：`TAG_ELEV_0` 是目前頁類別，Index Tag 是被引用目標頁類別。2.0 schema 不能只因 key 同名就假設語意相同。

## 階段 11｜以 Grab、Laser、Index 綁定 Tag（2D／Layout）

三種 1.0 操作都必須保留，因為使用者介入方式不同：

| 1.0 指令 | 預期 Block | 使用者實際動作 | 1.0 定位依據 | 2.0 安全升級 |
| --- | --- | --- | --- | --- |
| `LF_Tagger_Grab` | Height／Finish 的 `_GRAB`、`TAG_ITEM` | 先選 Tag，再點進 Detail 選模型／Block 來源 | 一般物件用 UUID；Item 可解析 Block 名稱 | 保存正式 `source_object_id` 或正式 `source_type`；無法確認時不建立綁定 |
| `LF_Tagger_Laser` | Height／Finish 的 `_LASER` | 先選 Tag，再在 2D Section 點位置 | Anchor Frame、Clipping Plane 與幾何射線 | 經已註冊 View transform 找候選；多候選時由使用者選擇 |
| `LF_Tagger_Index` | `TAG_SECTION_DETAIL`、`TAG_ELEV_1`～`4` | 先選 Index Tag，再從可搜尋清單選 Detail View | `.Target_DV_ID` 保存 Detail GUID | 保存 `target_view_id`／`target_sheet_id`，圖號由 Sheet metadata 產生 |
| 不需綁定 | `TAG_ELEV_0` | 使用者維護方向／編號欄；Layout ID 寫目前頁 Category | 目前頁 Layout | 另定 Elevation group schema 前，不把它誤送進 Grab／Laser／Index |
| 不需綁定 | `TAG_DW` | 使用者直接填寫 Block 顯示內容 | 無 | 保持純手動 Tag；不建立來源、不由 Sync 覆寫 |

使用者可以逐張圖、逐批 Tag 執行，不要求一次綁完全部 Layout。取消選取時 Tag 保持原狀；重新綁定既有 Tag 前應先顯示目前來源。1.0 主要以 Block 名稱中的 `GRAB`／`LASER` 和數個 hard-coded 清單防止用錯指令，但 guard 並不完整；2.0 應由 Tag Template manifest 明列每種 Block 允許的 binding mode，而不是靠名稱字串猜測。

> **使用者介入**：選 Tag、選來源、點 Laser 位置、選 Index 目標，並解決多候選。
>
> **安全停點**：每完成一批綁定即可存檔；尚未綁的 Tag 留給下一時段處理。

## 階段 12｜用 Infuser 寫入 Tag Block（2D／Layout）

**1.0：`LF_Infuser_Part`** → 只更新目前 Layout；**`LF_Infuser_All`** → 更新全部 Layout。使用者依工作範圍自行選擇，不要求每次都全案同步。

Infuser 從 `Project_Registry.json` 與 Detail／Tag binding 取得資料，依 Block family 的固定欄位清單寫進 Tag Block。啟用 `x / X` write protection 的個別 Tag 在處理最前面就被跳過：所有自動欄位與人工內容都維持原狀，但 1.0 也不會替它重新判斷或更新顏色，因此「locked」不等於「來源仍健康」。

執行後，1.0 以顏色提供立即回饋：

| 顏色 | 1.0 意義 | 使用者下一步 |
| --- | --- | --- |
| 紫色（Purple） | 已綁定且資料已寫入；程式實際是清除警示色、恢復 `ByLayer`，紫色來自目前 Block／layer 顯示設定 | 檢查顯示內容；沒有問題即可繼續 |
| 橘色（Orange） | 沒有 `Source_UUID` 或 `.Target_DV_ID` | 自動顯示欄被寫成 `?`；回階段 11 建立來源 |
| 紅色（Red） | UUID 不在 Registry，或 Index 的目標 Detail 已不存在 | 自動顯示欄被寫成 `?`；修復來源或重新綁定，再跑 Part／All |

錯誤時被改成 `?` 的只有各 family 的自動欄位：Height 的 `attr_ch_*`／`attr_mat_*`／`attr_note`、Finish 的 `attr_mat_*`／`attr_note`、Item 的 `attr_item_*`／`attr_note`、Index 的 `Category`／`REF_ID`。`attr_manual_補充說明`、`Detail_NO` 與 `TAG_ELEV_0` 的方向／編號欄不在 Infuser 寫入清單中，必須保持使用者內容。`TAG_ELEV_0` 本身也不參加 Infuser／TAG-O 狀態掃描。

**2.0：`LF_Sync_Current_Sheet`／`LF_Sync_All`** → 延續 Part／All 兩種範圍 → 先依 Template manifest 驗證 Block 名稱、欄位、所有權與 binding type → 只更新 render output → 保存 `last_synced_revision`。顏色只作可還原提示；正式狀態由 metadata 判定，不修改使用者原色。鎖定的 Tag 仍可由唯讀 Health 判定為 `manual_locked + stale` 或 `manual_locked + orphaned`，只是不自動改內容。

> **使用者介入**：選擇只同步當前頁或全部頁，並依結果決定要不要回頭補綁／修復。
>
> **安全停點**：Part 完成就是合法停點；不必為了同步一頁而強迫全案重跑。

## 階段 13｜交付前確認與修復（2D／Layout）

**1.0 實際方式** → Infuser 後查看紫／橘／紅狀態；需要時使用 `LF_TAG-O` 檢查 Tag 存活與空間覆蓋 → 對橘色 Tag 補綁、對紅色 Tag 重新連結、對人工模式 Tag 保留原值 → 再跑 Infuser 確認。`LF_TAG-O` 只掃 Config 中的 Index／Data Tag 清單，不包含 `TAG_ELEV_0`，而 locked Tag 也可能保留上次顏色，因此不能只用「面板沒有問題」推定所有 Block 都健康。

**2.0：`LF_Health_Check`** → 不先改 Tag 或塗色，直接以 Object／View／Sheet ID、revision、template 與 lock state 產生 Issue Report。**`LF_Repair_Preview` → `LF_Repair_Apply`** → 使用者逐項決定重新綁定、同步、保留、脫離或略過。

> **使用者介入**：決定哪些問題必須在本次交付前關閉；刻意保留的人工內容或舊圖要記錄理由。
>
> **完成條件**：不是「畫面沒有紅色」，而是本次交付範圍內每個問題都有可追蹤結果。

---

## 實際可停留的位置與下次接續方式

| 停留點 | 已完成且可保存的成果 | 下次從哪裡開始 |
| --- | --- | --- |
| Dictionary／Layer 完成 | 可建模 layer 樹 | 直接繼續建模 |
| 3D 建模完成 | 尚未發布的幾何成果 | 建立／檢查 Space Boundary |
| Space Boundary 完成 | 空間判定前置 | TagTrigger，或 2.0 Scan |
| TagTrigger／Apply 完成 | 模型已帶資料，但未發布 | TagChecker／Model Data Check |
| TagChecker 通過 | 可發布的模型資料 | Push／Publish Registry |
| Registry 發布完成 | 2D 可使用的 last-good 資料 | 建 Section，或直接更新既有 Tag |
| Section＋Anchor／View 完成 | 可定位的 linked drawing | Extract／Materialize，或開始 Layout |
| Extract／人工整理完成 | 可獨立編輯線稿 | 建立／整理 Layout |
| Layout ID 完成 | 圖框與圖號已寫入 | 分批綁定 Tag |
| 部分 Tag 綁定完成 | 已建立的綁定不需重做 | 繼續綁剩餘 Tag，或先跑 Infuser Part |
| Infuser Part 完成 | 當前 Layout 已同步 | 換下一張 Layout，或交付前檢查 |
| Health／修復完成 | 問題與處理結果可追蹤 | 出圖或等待下一次模型修改 |

## 變更循環 A｜修改模型資料，但不影響 Section 線稿

例如只修改材料名稱、建構狀態或備註：

```text
修改 3D 物件／Dictionary
→ 若資料需重新注入：TagTrigger＋TagChecker（2.0：Scan→Apply→Check）
→ LF_Push_3D_to_JSON（2.0：Publish 新 revision）
→ LF_Infuser_Part 或 All（2.0：Sync Current Sheet 或 All）
→ 檢查紫／橘／紅（2.0：Health Report）
```

錄影的「修改 3D 物件 → re-push → re-run Infuser」是最短路徑；若改動涉及 Nexus 計算的空間、尺寸或高程，必須先重新執行資料注入與 Checker，否則只是把舊 UserText 再次 Push。

## 變更循環 B｜修改模型幾何，Section 也必須更新

例如把磁磚牆高度由 240 cm 改為 260 cm：

1. 修改 3D 幾何。
2. 重跑 TagTrigger／TagChecker；2.0 改為 Scan → 使用者確認 → Apply → Model Data Check。
3. Push／Publish 新 Registry revision。
4. 執行 Rhino `! _UpdateClippingDrawings` 更新 linked Section。
5. 若仍使用 linked output，檢查結果後繼續；若已有 Extract／人工編輯圖面，使用者決定保留、另建新版或明確取代。2.0 不靜默覆寫 `modified` Drawing。
6. 1.0 若移動或重建線稿，確認 Anchor Frame 仍存在且與圖面一起移動；2.0 驗證 View Registration。
7. 執行 Infuser Part／All 或 2.0 Sync。
8. 檢查 Tag 狀態；未處理的舊圖保留 stale／detached 理由。

## 變更循環 C｜Detail View 被刪除或 Layout 重整

錄影明確示範 Detail View 刪除後 Tag 會變紅，使用者必須重新連結：

1. Infuser／Health 找出 broken Detail／Index binding。
2. 如果 Detail 只是換位置，確認它是否仍是同一 View；不可只靠新位置猜測。
3. 如果 Detail 已重建，執行 `LF_Tagger_Index` 重新選目標；一般 Tag 視來源情況使用 Grab／Laser 重新綁定。
4. Layout 重新排序或改名後，執行 `LF_Tagger_Layout_ID` 更新圖號與 title blocks。
5. 複製 Layout 時，一般 Tag 可保留同一模型來源，但新的 Sheet／Drawing／Tag 要有新 ID；Index Tag 的目標必須逐一確認。
6. 再跑 Infuser／Sync，直到 broken 狀態關閉或被使用者明確保留。

## 獨立工具｜不阻擋主工作鏈

以下工具依錄影說明可獨立使用，不應成為 Nexus、Registry 或 Tag 的強制前置：

- `LF_2D_DW_Gen`：8 種門、3 種窗的 2D 符號。
- `LF_2D_Cabinet_Gen`：高櫃、下櫃、衣櫃等 2D 符號。
- `LF_2D_Shelf_Gap`：依指定間距產生等距層板分隔線。

`LF_Cabinet_Suite` 屬於 3D 建模選用工具；若使用，其 BOM 資料仍要經模型資料檢查與 Registry 發布，才會進入主資料鏈。

## 從開案到交付的一條線

```text
2.0 開案檢查
→ Nexus Dict. to Layer（2.0：Validate → Type Sync）
→ Rhino／Cabinet 建立 3D 模型
→ Nexus SpaceBoundary：使用者選 closed curves
→ Nexus TagTrigger（2.0：Scan → 人工確認 → Apply）
→ Nexus TagChecker：模型資料通過後才前進
→ 選用 Layer to Dict.：人工核對 Dictionary 差異
→ Push 3D to JSON（2.0：Publish Registry revision）
→ Rhino ClippingSections／ClippingDrawings
→ LF_Anchor_Frame（2.0：View Register）
→ 視需要 LF_Extract_CP（2.0：Drawing Materialize）＋人工整理
→ 使用者準備 Layout／圖框／Tag Blocks
→ LF_Tagger_Layout_ID：批次編號與寫圖框
→ LF_Tagger_Grab／Laser／Index：逐批人工綁定
→ LF_Infuser_Part／All：使用者選同步範圍
→ 查看紫／橘／紅並修復（2.0：唯讀 Health → Previewed Repair）
```

這條鏈保留 1.0 最重要的產品精神：**使用者決定何時寫資料、何時發布、切哪張圖、抽哪些線、Tag 綁誰，以及只更新當前頁或全部頁。**2.0 的責任是讓每次決定都有預覽、穩定 ID、revision、可重跑與可復原，而不是把這些停留點合併成一個全自動按鈕。

---

# Claude Code 模擬執行流程

這一版走同一條資料鏈，但在三件事上刻意寫得比較細：**每一步在哪個 Rhino 文件執行**、**失敗或取消時會停在哪裡**、以及**哪些是第一階段就必須有、哪些可以晚點補**。

全文用同一個案子當例子：一間住宅，主臥室有一面磁磚牆（Type `WL-14`，`02_Wall_牆面::Tiles.磁磚`，高 240 cm）和一個開關面板（Type `EL-05`，`06_EL_電控系統::Switch.開關面板`，Block instance，高程基準 `BC`）。

## 前提：這條流程同時跑在兩個文件上

兩版都把這項分工視為核心前提；Claude 版以下會進一步從現行程式與改造風險解釋原因。

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

每個 Tag 都保存共同 identity（`tag_id`、`sheet_id`、`template_version`、`lock_state`），再依類型保存不同 binding：模型資料 Tag 使用 `source_object_id` 與所在的 `view_id`／`drawing_id`；Index Tag 使用 `target_view_id`／`target_sheet_id`；`TAG_ELEV_0` 目前只有所在 Sheet context，不應被強迫建立模型來源。

依 ED-02，鎖定仍應改成單一 `lock_state`。程式的備援條件確實不一致，但本次提供的正式 Block key 是 `attr_Lock_不更新>寫入x或X`，同時含有 `Lock` 與「不更新」，所以 Grab、Laser、Index、Infuser 都能辨認。真正問題是契約散落：若 Block 改名、匯入舊版或使用另一種 key，結果可能不同；另外 Infuser 對 locked Tag 完全跳過，也不重新判斷 stale／broken。

家具 Tag 不再使用 `NAME_PARSED` 這個哨兵值假裝有來源，改為正式的 source type。`TAG_DW` 則不建立來源或 source type，所有顯示內容維持手動；舊 Python 中的門窗名稱解析只供歷史資料辨識或一次性 migration 參考，不進入 2.0 日常同步流程。

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
  attr_manual_補充說明 <- user manual content（Sync 不寫入）
```

`type.category` / `type.sequence` 直接來自階段 2 拆好的欄位，不需要在這裡對 `_03` 字串做 `split("-", 1)`——這也順帶解掉「ID 本身含連字號會被誤拆」的問題。

`lock_state` 為鎖定的 Tag 不更新 render output，人工填的值原樣保留；Health 仍需唯讀檢查來源是否 stale／orphaned。Template manifest 也要保存 Block family、允許的 Grab／Laser／Index mode、每個欄位的 owner、缺值顯示與 migration mapping，避免 Block 定義、Config 清單與 Infuser hard-coded 寫入表各自漂移。

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
| 閱讀視角 | 以 1.0 錄影的實際操作、使用者介入與停留點為骨架 | 以現有程式盤點、風險與第一階段施工範圍深入補充 |
| 1.0 對照 | 每一階段並列現有指令與 2.0 建議責任 | 主要直接描述 2.0 目標行為 |
| Nexus | 保留 Dict-to-Layer、SpaceBoundary、TagTrigger、TagChecker、Layer-to-Dict 的操作節奏，再把 Trigger 拆成 Scan → Apply | 聚焦 Scan → Apply，並明列 Impact Report 與三個現況問題 |
| Section／圖面 | 明列 Anchor 不可刪、圖框與線稿一起移動、Extract 依顏色拆圖等現行規則 | 聚焦正式 View Registration、Materialize 與來源索引提案 |
| Laser | 用固定 View transform 定位 | 相同，另提議在 Materialize 時建立來源索引，讓 Laser 退化成查表（需 spike 驗證） |
| Layout／Sheet | 使用者先準備 Layout／Tag Blocks，再由 Layout ID 批次編號；metadata 是 2.0 升級，不預設自動建頁 | 以 `LF_Sheet_Create`／Duplicate 描述 metadata-first 目標 |
| Tag Block 契約 | 逐一對照 8 份實際參數、隱藏 binding、Python writer 與手填欄位；辨認 `TAG_ELEV_0` 特例 | 以 Template manifest 與 canonical binding／render schema 描述目標 |
| Tag 人工控制 | 補回 `x / X` write protection、Part／All 範圍與紫／橘／紅回饋，並說明 locked Tag 不會更新狀態 | 聚焦 canonical `lock_state`、revision 與正式 Health 狀態 |
| 變更循環 | 分開資料變更、幾何／Section 變更、Detail 刪除與 Layout 重整 | 以磁磚牆高度變更走一條完整新架構流程 |
| 施工順序 | 先確認 1.0 操作節奏沒有被架構重寫，再依交接點拆 feature | 給出最小可用範圍與建議最先動工項目 |

兩版都指向同一個核心：**每個階段都有明確 ID、revision、預覽與人工停點，任何更新都不以「方便」為理由靜默換 ID、重綁來源或覆蓋人工成果。**
