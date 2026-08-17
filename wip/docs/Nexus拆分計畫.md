# LoopFlow 2.0 — Nexus 拆分計畫

本文件是 LF-C02 的唯一工作包清單。C02 必須依本表逐項開 `codex/v2-<scope>` 分支，不得一次重寫 `LF_Nexus.py`。資料語意以 `資料契約.md` 為準；使用者步驟以 `工作流程.md` 第 1～6 步為準。

## 範圍

Nexus 在 2.0 只做 **Project Console**：讓使用者查看開案狀態，並逐項執行「字典／圖層 → 空間 → 資料化 → 發布」這段核心資料鏈。

```text
開案檢查
→ 驗證 Dictionary／同步 Type Layers
→ 建立 Space Boundaries
→ Apply → Verify → 寫回字典
→ Publish Registry
```

不屬於 Nexus、不得塞進 C02：

- Tag、Infuser、Health、View、Drawing、Sheet、Worksession（D／E 軌）
- 三個 2D 工具（F01）
- Cabinet／BOM／`_CB.*`（ED-18）
- Dictionary 欄位解析本體（C01）
- Registry lock／pending／atomic replace 本體（C03）
- 尺寸／數量計算（不屬 2.0；數量欄留在 Dictionary 給 GH）

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
| `get_dimensions` | 1.x 有 local 寬深高 | **不進 2.0**；數量交給後續 GH |
| `func_tag_checker` | 寫入前／後的唯讀報告 | NX-04～05 的 Scan／Verify |
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
**做**：每一次同步都彈出視窗問專案名稱（第一次不預填 `M3D`，之後預填已記住的 `lf_layer_prefix`）；Dictionary 有、Rhino 無的 layer 建立並帶 `construction_default`；已有同名 layer 保留既有 UserText；依圖層代號前綴套用顯示色，並建立相對路徑同名、顏色相同的材質（不含專案前綴）；`DNA_REF_` 為原點點物件，依 `type_id` 更新不累積；`20_DW` 排除 child layer；選單「寫回字典」在字典目錄匯出獨立 XLSX，不覆寫正式檔。  
**不做**：寫物件 instance、覆寫正式 Dictionary、改物件 instance 顏色、ZoomExtents。  
**fixtures／驗收**：新 layer、既有 layer 保留 UserText、顯示色／材質、DNA_REF 取代、反向匯出不碰 Object UserText；取消／失敗還原 visibility 與 selection。

### NX-03 Space Boundary／`nexus-space`

**前置**：NX-01、B03。  
**模組**：`features/model_data/` 的 space。  
**做**：有效封閉曲線 → `space_id`／`level_id`／`space_display`；高程框先彈出清單點選 FFL／FL，再彈出視窗輸入高程（寫 `_15_樓層高程*`）；空間框可複選後彈出視窗輸入名稱（寫 `_01_空間名稱*`）；框線不寫物件名稱；選線只用曲線過濾，不鎖全檔非曲線物件；樓層 ID 由 FFL／FL 高程框配對（高程差 ±20、空間整圈在高程框內）；共邊允許、**同一 `level_id`** 面積重疊則停止並列出全部衝突；不同樓層平面重疊通過並警告。  
**不做**：改既有物件的空間欄（那是 NX-05 Apply）；不手填樓層 UUID；不把高程或空間名稱寫進 ObjectName。  
**fixtures／驗收**：多樓層、共邊、重疊、無效曲線、同高程 ±20 命中、差 21 不命中、空間超出樓層擋。

### NX-04 Object ID 與 Type 資料化／`nexus-object-id`

**前置**：C01、NX-02、B03。  
**模組**：`features/model_data/` 的 identity。  
**做**：Scan 不寫入；報告待建／重複／失效 ID、未知 Type、預計寫入欄；使用者確認後 Apply `object_id`、`type_id`、`construction_status`、`remarks`、`data_revision`；ID 變更有 mapping 與 rollback。  
**不做**：Space、高程、尺寸、quantity、`_CB.*`。  
**fixtures／驗收**：複製碰撞、hidden／locked 仍納入正式 Scan、局部 Scan 不能標「可發布」、中斷後重跑顯示剩餘工作。

### NX-05 Space 命中與高程／`nexus-space-elev`

**前置**：NX-03、NX-04。  
**模組**：`features/model_data/` 的 space hit 與 elevation。  
**做**：命中 `space_id` 或 `EXT`（四種原因都要列出）；BH／TH／CH／BC；非 Block 用 BC 直接報錯；Apply 寫空間／高程欄。選單 Verify 在記憶體算出 Apply 結果後比對 UserText，不符則選取並彈窗。  
**不做**：用 World bbox 猜尺寸；不寫寬深高／數量。  
**fixtures／驗收**：EXT 四因、重疊已在 NX-03 擋住故命中時不再 silent 取第一個、`TH/BH` 只出現在 migration 報告。

### NX-06 尺寸與數量／已取消

**不做**。2.0 只要圖面表達（高程、材料編號、空間）。寬深高／面積／長度／數量留給後續 GH。既有 `features/dimension` 已刪。

### NX-07 Verify 與發布交接／`nexus-publish-handoff`

**前置**：NX-04～05、C03。  
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
| C04 Data Viewer | **已完成**；只讀，不是 Nexus 步驟；顯示 NX-04 以後的 canonical 值、缺值與殘留尺寸警告 |
| C05 | **不屬 2.0**；`Q_04`／`Q_05` 仍由 C01 驗證量綱 |
| A06 | **已完成**；Dictionary／UUID／Space／local frame／Registry 形狀已在 `wip/fixtures/contract/`；各 NX 包再補該包的 Scan 報告案例 |
| D～E | 使用已發布 revision，不回寫 Nexus |

## 分段實機（C02 期間）

Rhino 實機不必等整條鏈。每包在隔離測試 `.3dm` 至少走：正常、取消、失敗。全案 hidden／locked、last-good、人工成果保護留到 NX-07 與 G03。
