# LoopFlow 2.0 — Nexus 拆分計畫

本文件是 LF-C02 的唯一工作包清單。C02 必須依本表逐項開 `codex/v2-<scope>` 分支，不得一次重寫 `LF_Nexus.py`。資料語意以 `資料契約.md` 為準；使用者步驟以 `工作流程.md` 第 1～6 步為準。

## 範圍

Nexus 在 2.0 只做 **Project Console**：讓使用者查看開案狀態，並逐項執行「字典／圖層 → 空間 → 資料化 → 發布」這段核心資料鏈。

```text
開案檢查
→ 驗證 Dictionary／同步 Type Layers
→ 建立 Space Boundaries
→ Scan → Apply → Verify
→ Publish Registry
```

不屬於 Nexus、不得塞進 C02：

- Tag、Infuser、Health、View、Drawing、Sheet、Worksession（D／E 軌）
- 三個 2D 工具（F01）
- Cabinet／BOM／`_CB.*`（ED-18）
- Dictionary 欄位解析本體（C01）
- Registry lock／pending／atomic replace 本體（C03）
- local frame 與 quantity 計算本體（C05）

`LF_Nexus.py` 入口只轉交 command catalog，不保存第二份業務邏輯。`LF_Push_3D_to_JSON` 可保留按鈕，但必須呼叫與 Console「發布」相同的 command。

## 1.x 對照（只作拆分依據）

1.x `LF_Nexus.py` 約 876 行，把 UI、Excel、幾何與發布寫在同一檔。2.0 不搬函式，只保留已驗證的控制點。

| 1.x 函式／按鈕 | 保留的意圖 | 2.0 去向 |
|---|---|---|
| `main`／`_NexusChooserDialog`／`Show_StatusInfo` | 一個可看、可選、可停的入口 | NX-01 Console |
| `get_dictionary_path`／`load_dict_from_path` | 找到並讀 Dictionary | C01；Console 只顯示結果 |
| `func_dict_to_layer`、`DNA_REF_` | 缺的 Type layer 建起來，空層不被 Purge | NX-02 |
| `func_rhino_to_xlsx` | 反向匯出給人核對，不自動覆寫正式字典 | NX-02 |
| `func_boundary_setter` | 使用者畫完邊界後給穩定空間身分 | NX-03 |
| `check_global_uuids`／`func_tag_trigger` 的 ID 段 | 建立／修復 Object ID，不可靜默換號 | NX-04 |
| `get_space_name_at_object` | 把物件歸到空間或 `EXT` | NX-05 |
| `get_elevation_value` | BH／TH／CH／BC | NX-05 |
| `get_dimensions` | local 寬深高 | C05；NX-06 只接線 |
| `func_tag_checker` | 寫入前／後的唯讀報告 | NX-04～06 的 Scan／Verify |
| `execute_push_to_json` | 明確發布 | NX-07 組 payload，C03 負責安全寫入 |
| 無差別寫入 Dictionary 每一欄、Zoom、亂改顏色 | 不保留 | 禁止 |

Scan 範圍已由 ED-17 鎖定：M3D 正式範圍內全部 3D 物件，含 hidden／locked。局部選取只作預覽，不得宣告全案可發布。

## 工作包順序

```text
B01–B03 骨架
→ C01 Dictionary reader
→ NX-01 Console 空殼
→ NX-02 Type layer 同步
→ NX-03 Space Boundary
→ NX-04 Object ID／Type 資料化
→ NX-05 Space 命中與高程
→ C05 Dimension／Quantity（可與 NX-05 並行準備，接線在 NX-06）
→ NX-06 把 C05 接進 Scan／Apply
→ C03 Registry 安全發布
→ NX-07 Verify 通過後組 payload 並呼叫 C03
```

每一包結束都必須能存檔、換機。使用者不必跑完整鏈。

### NX-01 Console 空殼／`nexus-console`

**前置**：B01–B03。  
**模組**：`entrypoints/LF_Nexus.py` → `features/project/`。  
**做**：開案檢查（路徑、`project_id`、schema、文件單位）；列出可執行步驟；缺設定就停。  
**不做**：讀寫物件、建 layer、發布。  
**fixtures／驗收**：環境變數缺失、目錄不存在、尚未有 `project_id`、非 cm 警告仍可進入；取消後 Rhino 狀態不變。

### NX-02 Type layer 同步／`nexus-layers`

**前置**：C01、NX-01。  
**模組**：`features/dictionary/`（sync／export；reader 已在 C01）。  
**做**：Dictionary 有、Rhino 無的 layer 建立並帶 `construction_default`；已有同名 layer 保留既有 UserText；依圖層代號前綴套用顯示色，並建立相對路徑同名、顏色相同的材質（不含 `M3D::`）；`DNA_REF_` 為原點點物件，依 `type_id` 更新不累積；`20_DW` 排除 child layer；選用反向匯出獨立 XLSX。  
**不做**：寫物件 instance、覆寫正式 Dictionary、改物件 instance 顏色、ZoomExtents。  
**fixtures／驗收**：新 layer、既有 layer 保留 UserText、顯示色／材質、DNA_REF 取代、反向匯出不碰 Object UserText；取消／失敗還原 visibility 與 selection。

### NX-03 Space Boundary／`nexus-space`

**前置**：NX-01、B03。  
**模組**：`features/model_data/` 的 space。  
**做**：有效封閉曲線 → `space_id`／`level_id`／`space_display`；共邊允許、**同一 `level_id`** 面積重疊則停止並列出全部衝突；不同樓層平面重疊通過並警告。  
**不做**：改既有物件的空間欄（那是 NX-05 Apply）。  
**fixtures／驗收**：多樓層、共邊、重疊、無效曲線；ObjectName 只顯示。

### NX-04 Object ID 與 Type 資料化／`nexus-object-id`

**前置**：C01、NX-02、B03。  
**模組**：`features/model_data/` 的 identity。  
**做**：Scan 不寫入；報告待建／重複／失效 ID、未知 Type、預計寫入欄；使用者確認後 Apply `object_id`、`type_id`、`construction_status`、`remarks`、`data_revision`；ID 變更有 mapping 與 rollback。  
**不做**：Space、高程、尺寸、quantity、`_CB.*`。  
**fixtures／驗收**：複製碰撞、hidden／locked 仍納入正式 Scan、局部 Scan 不能標「可發布」、中斷後重跑顯示剩餘工作。

### NX-05 Space 命中與高程／`nexus-space-elev`

**前置**：NX-03、NX-04。  
**模組**：`features/model_data/` 的 space hit 與 elevation。  
**做**：命中 `space_id` 或 `EXT`（四種原因都要列出）；BH／TH／CH／BC；非 Block 用 BC 直接報錯；Apply 寫 `lf_space_*` 與高程欄。  
**不做**：用 World bbox 猜尺寸。  
**fixtures／驗收**：EXT 四因、重疊已在 NX-03 擋住故命中時不再 silent 取第一個、`TH/BH` 只出現在 migration 報告。

### NX-06 接上尺寸與數量／`nexus-dimension-wire`

**前置**：C05、NX-04。  
**模組**：不複製 C05 規則；Scan／Apply 呼叫 C05。  
**做**：**已完成**。把 local frame／W／D／H／quantity 的成功、阻擋、沿用既有框寫進同一份 Scan 報告；無穩定 frame 時命令列標明。  
**不做**：另寫一套 bbox 後備、宣告可發布。  
**fixtures／驗收**：沿用 C05；Console 顯示「無穩定 local frame」為阻擋警告。

### NX-07 Verify 與發布交接／`nexus-publish-handoff`

**前置**：NX-04～06、C03。  
**模組**：`features/registry/` 的 payload 組裝；寫入走 C03。  
**做**：Verify＝全案再 Scan，無阻擋且警告已列出才允許發布；組 `loopflow.registry` payload（`types`／`spaces`／`objects`）；呼叫 C03。  
**不做**：自己做 lock 檔或先刪正式 JSON。  
**fixtures／驗收**：未 Verify 不能發布；payload 不含 Tag／任意 UserText；C03 失敗時 Console 顯示階段且 last-good 仍在。

## 共用驗收（每一 NX 包）

- 可單獨執行、取消、失敗、重跑。
- 改過的 selection、lock、visibility、顏色、modified 都要還原（B03）。
- 只寫 `資料契約.md` 的 canonical key，不雙寫 1.x 名稱。
- Git diff 不含私人工作檔；一批一個 scope。

## 與其他任務的界線

| 任務 | Nexus 怎麼用它 |
|---|---|
| C01 | 載入／驗證 Dictionary；NX-02 不得自己解析 Excel 欄名 |
| C03 | 唯一允許寫 Registry 檔的模組 |
| C04 Data Viewer | 只讀；不是 Nexus 步驟，但應能顯示 NX-04 以後的 canonical 值 |
| C05 | 唯一的尺寸／數量實作 |
| A06 | **已完成**；Dictionary／UUID／Space／local frame／Registry 形狀已在 `wip/fixtures/contract/`；各 NX 包再補該包的 Scan 報告案例 |
| D～E | 使用已發布 revision，不回寫 Nexus |

## 分段實機（C02 期間）

Rhino 實機不必等整條鏈。每包在隔離測試 `.3dm` 至少走：正常、取消、失敗。全案 hidden／locked、last-good、人工成果保護留到 NX-07 與 G03。
