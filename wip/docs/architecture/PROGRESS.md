# LoopFlow 2.0 重構進度

- 建立日期：2026-08-12
- 目標版本：`v2.0.0`
- 整合分支：`v2-development`
- 建立基準：`main` / `b09d650d5ba1a618c0ce8de154af2b961292e066`
- 穩定回復點：`v1.0.0` / `1479ba5f57d79f4048dd858f8afb0ff439c9fe66`
- 狀態：現行 workflow v2 已依 1.0 操作說明、全部 23 支 Python、9 份 Tag 與 1 份圖框重新檢核；結果已同步回寫非 `ref/` 維護文件與公開 1.x 指南，尚未修改產品程式碼

## AI 接手入口

本 repo 已建立自足的繁中維護文件。AI 開始前依序讀取根目錄 `AGENTS.md` 與該檔列出的 `wip/docs/` 文件；其中 `architecture/LOOPFLOW_DATA_ECOSYSTEM.md` 是完整工作鏈與資料真相邊界的總體起點，`architecture/LOOPFLOW_WORKFLOW_SIMULATION_v2.md` 是依 1.0 操作與 Block 證據複核後的現行流程，最後讀本文件確認即時進度。外部分析檔不再是必要輸入。

## Release 回復資產

| 項目 | 值 |
|---|---|
| 檔案 | `releases/LoopFlow_v1.0.0.zip` |
| 大小 | 1,031,813 bytes |
| ZIP 項目數 | 28 |
| SHA-256 | `de4f064966f697167cae2f996c518a2cbc2ce4dfe46e52ff5397149ef4e8f0c5` |

此 ZIP 已能正常開啟，並與 GitHub `v1.0.0` Release 資產的大小一致。Tag 與 Release 不移動、不覆寫。

## 分支規則

- `main`：2.0 正式發布前維持可發布的 1.x。
- `v2-development`：2.0 的唯一整合線。
- 每批工作從 `v2-development` 建立 `codex/v2-<scope>` 短期分支，檢查通過後才合入。
- `main` 原則上凍結，僅在使用者明確要求維護 1.x 時，才另開獨立 hotfix 分支並將必要修正同步至 `v2-development`。
- `v2.0.0` 只在 RC 與實機驗收完成、合回 `main` 後建立。

## Golden workflow 基準

合約盤點期間，先從穩定版與既有範例整理可自動比對的 fixture、預期輸出與必要畫面基準。新版主要工作流串接完成後，再使用隔離的 Rhino 8、測試 `.3dm` 與測試資料，依下列清單進行完整實機端到端驗證：

- Tag：Grab、Index、Layout ID、Laser、TAG-O、Data Viewer。
- Dictionary：讀取、編輯、缺檔與錯誤資料。
- Registry：正常 push、取消、壞 JSON、lock、replace 失敗與最後有效資料。
- Nexus：UUID、boundary、dimensions、elevation、space、XLSX 與 JSON。
- Layout / Infuser / Worksession：完整與部分同步、warning、重複執行與復原。
- Cabinet / 2D：Suite、Cabinet、Shelf Gap、DW 的代表性輸入與輸出。

fixture 與預期結果應在對應功能建造前完成；實機結果則在主要工作流串接後集中補入本文件。未驗證項目不得標記為通過。

## 第一階段順序

1. 盤點完整工作流、每一步的輸入輸出，以及所有命名與 Dictionary 相依點。
2. 完成命名、Dictionary、UserText、圖層、Registry、Tag 與跨 repo 資料契約。
3. 固定 schema version、fixture、預期輸出與舊專案轉換邊界；舊名稱只由獨立遷移工具辨識。
4. 建立新版最小架構並驗證 Rhino import / reload，不移植正式功能。
5. 契約確認後，依真實操作順序逐段接入功能並同步建立自動化與契約測試。
6. 主流程串接完成後，集中進行 Rhino 實機端到端測試，再建立遷移工具、安裝包與 RC。

## 驗證紀錄

| 日期 | 分支 / commit | 檢查 | 結果 | 限制 |
|---|---|---|---|---|
| 2026-08-12 | `v2-development` 建立基準 | Git 同步、Release ZIP 完整性與 SHA-256、23 支 Python 靜態語法、RHC XML | 通過 | Rhino 8 實機流程由後續批次逐項驗證 |
| 2026-08-12 | 文件 SSOT 建置 | 建立繁中使用說明、系統設定、重構計畫與 repo AI 規則；Markdown 本機連結檢查 | 通過 | 既有大型程式標頭與英文註解依 feature 批次遷移，不做一次性翻譯 |
| 2026-08-12 | 重構模式裁決 | 新版乾淨重建、一次切換；命名與 Dictionary 契約先於程式架構 | 通過 | 尚未開始命名盤點與產品程式碼修改 |
| 2026-08-12 | 開發測試入口 | Rhino 測試按鈕暫定直接指向 repo 的 `wip/src/entrypoints/`；功能或路徑變動時同步更新系統設定與工具列 | 已記錄 | 入口檔尚未建立；正式安裝／RC 另用隔離 `%APPDATA%` 路徑 |
| 2026-08-12 | WIP 工作路徑 | 重構文件移至 `wip/docs/`，未來程式／測試／fixtures 統一置於 `wip/`；Dropbox 工作檔以 `LOOPFLOW_WORKFILES_ROOT` 解析 | 已記錄 | 公司路徑已登錄；家中電腦路徑待補 |
| 2026-08-12 | Dictionary 工作來源 | 確認 Dropbox 的 `LoopFlow_Dictionary.xlsx` 為中文欄位／中英雙語 layer 版本，18 欄、92 筆；指定為重構來源 | 通過 | machine key 與顯示名稱是否分離仍待 ND-01 裁決；XLSX 未修改 |
| 2026-08-12 | 任務切分與開發路徑 | 建立 A–G 階段、任務依賴、分支 scope、完成檢查與雙機安全停點 | 已記錄 | Nexus 僅列核心工作軌；詳細拆分另建專用文件 |
| 2026-08-12 | Nexus／Dictionary 靜態盤點 | 逐檔閱讀 23 支 Python；檢查實際 XLSX 的 18 欄、92 列、值域與格式；對照公開指南；建立設定、衝突與 ND-01～ND-25 決策菜單 | 通過 | 尚未執行 Rhino 實機與舊專案資料抽樣；所有 ND 項目仍待使用者裁決，產品程式碼未修改 |
| 2026-08-12 | 資料生態與工作鏈藍圖 | 重新核對 23 支 Python 的功能、輸入輸出、UserText／Registry／Section／Tag／Layout 依賴；建立 Type→Object→Registry→View→Drawing→Sheet→Tag→Health 的總體說明 | 已建立 | 上位 ECO 原則與 Section 人工編修生命週期尚待使用者反覆討論、確立；未修改產品程式碼 |
| 2026-08-12 | 資料生態獨立複核與整合 | 合併 Codex 藍圖與 Claude Code 複核；校正 Anchor／Registry／Dict-to-Layer 現況，加入 18 欄所有權、View Registration 階段、Health 前置、P0／P1 風險、領域規則保存與 ECO-09～11；原文移入 `architecture/ref/` | 已建立 | 指令功能仍主要來自靜態讀碼，需實機驗證；產品程式碼與工作檔未修改 |
| 2026-08-12 | 2.0 正式交付形式 | 確認開發期可用逐支 entrypoint 測試按鈕；RC 與 2.0 正式版改以完整安裝檔／可安裝套件交付，不讓使用者管理 Python 路徑 | 已記錄 | 封裝技術延後至發佈階段，待核心功能、資產與 migration 需求穩定後評估 |
| 2026-08-12 | 工具列的 Rhino Section 入口 | 保留目前工具列中的 Section 快捷按鈕；Macro 直接呼叫 Rhino 8 內建 `Clipping*` 指令，不建立 Python entrypoint、不封裝 Rhino 功能本體 | 已記錄 | 正式版管理 LoopFlow 自有工具列且不覆蓋 workspace；圖示來源與 UI／安裝格式待發佈 spike 決定 |
| 2026-08-12 | 藍圖與決策表拆分 | 將 ECO-01～11、已有證據但待確認的建議及實務問題移至 `LOOPFLOW_DATA_ECOSYSTEM_DECISIONS.md`，供使用者直接編輯後由 AI 回寫 | 已建立 | 藍圖只保留架構說明與安全前置；待決答案不再雙重維護 |
| 2026-08-12 | 決策強度與端到端情境 | 決策表增加強烈／一般／輕鬆三種 AI 建議強度，並以概念指令描述首次建模至 Health／Repair，以及模型修改後沿 revision 更新圖面與 Tag 的完整流程 | 已建立 | 概念指令尚非最終命名或已實作入口；流程會隨使用者決策回寫調整 |
| 2026-08-13 | 1.0 實際操作流程複核 | 以錄影逐步說明核對使用者介入與停留點，補回 SpaceBoundary、TagTrigger→TagChecker、Layer-to-Dict、Anchor、Extract、人工建 Layout、Part／All 與三色回饋 | 通過文件對照 | 尚未執行完整 Rhino 指令端到端；`LOOPFLOW_WORKFLOW_SIMULATION_v2.md` 為現行流程草案 |
| 2026-08-13 | Tag／圖框 Block 契約證據 | 由 Rhino instance 擷取 9 份 Tag、1 份圖框文字，共 24 個唯一 UserText key；對照 Config、Grab／Laser／Index、Layout ID、Infuser、TAG-O 與 `Tag_Blocks.3dm` 畫面 | 24/24 欄位已追蹤 | 精確座標、字型、圖層與顏色值尚未結構化；不影響目前資料契約規畫 |
| 2026-08-13 | Tag 現況衝突與新決策輸入 | 確認 `TAG_DW` 為純手動但 1.x Infuser 會覆寫編號；lock 只認單一 `x/X` 且同時凍結重新綁定；家具 `FF-01` 與 Dictionary 為兩套編碼；圖框 `03-A3 Scale` 無 writer | 已回寫上位文件 | ED-14～16 尚待使用者裁決；產品程式碼與 Block 資產未修改 |
| 2026-08-13 | 非 `ref/` 文件一致性同步 | 將 workflow v2 設為現行流程來源；同步資料藍圖、決策表、契約、設定、roadmap、Nexus 菜單、WIP 導覽與繁中／英文 1.x 指南 | 文件與衍生 HTML 已同步 | 舊 workflow 保留並明確標示為歷史提案；尚未執行 Rhino 端到端測試 |
| 2026-08-13 | 工作鏈骨架與 Health 覆蓋補強 | 工作鏈補入 W3 建立空間並改為 W1～W12；資料化定為掃描→套用→再驗證且驗證通過才可發布；補上 TagTrigger 作用範圍契約、`TAG_ELEV_0` 未被任何清單涵蓋的 Health 盲區，以及 Block instance 命名慣例三種分段 | 已回寫藍圖、契約、使用說明與 roadmap | Laser 來源索引 spike 尚未排入 roadmap，待使用者決定 |
| 2026-08-13 | Cabinet／BOM 排除主鏈 | 使用者裁決 Cabinet 與 BOM 不進主工作流程、列入後續開發（BOM 功能過於零碎，會汙染核心契約）；2.0 Nexus／Registry／Tag／Health 都不處理 `_CB.*` | 已回寫 v2、藍圖、決策表、Nexus 菜單、roadmap、重構計畫、契約與使用說明 | ED-03、ND-23、ND-24、CF-21 一併延後；1.x 事實移入 v2 的「延後工作軌」保存 |
| 2026-08-13 | 1.0 操作證據的地位裁決 | 使用者確認錄影說明是操作邏輯參考、不是流程契約；1.0 用法有限制但無大問題，步驟順序應配合新架構重新思考。維持的是控制意圖，不是按鈕順序 | 已回寫 v2、藍圖、決策表、使用說明、系統設定與 WIP 導覽 | 證據檔已正式登錄於結構樹；後續若改動 1.0 行為須是明示裁決，不得順手更改 |

## 下一步

由使用者直接編輯 `LOOPFLOW_DATA_ECOSYSTEM_DECISIONS.md` 的「你的決定／說明」欄；新加入的 ED-14～16 分別處理家具 `FF-01`、圖框比例與 title-frame 辨識。AI 讀取修改後，先整理歧義與相依影響，再回寫 `LOOPFLOW_DATA_ECOSYSTEM.md`、`_LoopFlow_命名與資料契約.md`，並重排 `NEXUS_DICTIONARY_DECISION_MENU.md` 細項；接著建立現行領域規則清單、10 份 Block manifest fixtures、schema fixtures 與 validator 規格。使用者確認契約前，不開始正式功能程式碼。
