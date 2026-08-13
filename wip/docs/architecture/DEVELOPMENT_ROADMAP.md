# LoopFlow 2.0 — 任務切分與開發路徑

本文件把 2.0 重構拆成可在單一工作時段完成、驗證、提交與推送的工作單位。功能細節以所屬契約文件為準；進度狀態只記錄於 `PROGRESS.md`。現行順序建立於資料生態藍圖之前；`LOOPFLOW_DATA_ECOSYSTEM.md` 確立後，須依確認的工作鏈與依賴重新排序，不能把本表當成不可變架構。

## 執行規則

- 一次只修改一個 repo；同一 repo 同一時間只由一台電腦／一個 AI 作業。
- 每項任務從 `v2-development` 建立 `codex/v2-<scope>` 短期分支，不直接在整合分支施工。
- 任務開始前確認 upstream、乾淨工作樹與 `pull --ff-only`；結束前完成檢查、commit、push 與交接。
- 任務須小到能留下可驗證的完整狀態。若超過一個工作時段，先拆成子任務，不以未提交檔案換機。
- `%APPDATA%` 只用於正式安裝／RC 隔離驗證；開發期 Rhino 按鈕直接指向 repo 的 `wip/src/entrypoints/`。
- 下表是開發路徑，可隨功能增減、實測結果與架構調整；改動時同步更新本文件、系統設定與 `PROGRESS.md`。

## 階段與任務

| ID | 任務／建議分支 scope | 前置 | 主要產出 | 完成檢查與安全停點 |
|---|---|---|---|---|
| LF-A01 | 現況工作流與依賴盤點／`workflow-inventory` | 無 | `LOOPFLOW_DATA_ECOSYSTEM.md`：完整工作鏈、資料實體，以及 23 支現行程式的 producer、consumer、副作用與保留意圖 | 盤點表可追溯至現行程式；只改文件，可安全換機 |
| LF-A02 | Dictionary 欄位盤點／`dictionary-inventory` | A01 | 現行 XLSX 欄位、型別、版本列、允許值、使用者顯示名稱與 consumer 對照 | 範例檔與指南交叉核對；未裁決欄位明確標記 |
| LF-A03 | 命名與識別契約／`naming-contract` | A01–A02 | canonical UserText key、UUID、完整 layer path、Space identity、指令與檔名規則 | 使用者裁決已記錄；禁止直接改正式資料 |
| LF-A04 | Registry／Tag／圖框資料契約／`registry-tag-contract` | A01–A03 | schema version、Registry object、10 份 Block template manifest、欄位 owner、binding mode、Producer／Consumer 與 migration 邊界 | 24 個現行 key 可追溯；manual `TAG_DW`、lock、Item 雙編碼、title-frame role 與未知 Block 行為可描述 |
| LF-A05 | Nexus 專用拆分計畫／`nexus-plan` | A01–A04 | 一份獨立 Nexus 工作包、依賴、fixtures 與分段驗收文件 | 本任務只規劃，不一次重寫 Nexus；詳細拆分另文維護 |
| LF-A06 | Fixtures 與 golden baseline／`contract-fixtures` | A02–A05 | Dictionary／UserText／UUID／Space／Registry，以及 9 Tag＋1 圖框的合法、錯誤、缺值、重複與舊版 fixtures | fixtures 不含私人正式專案；24 個 Block key 與預期 writer／owner 可機器比對 |
| LF-B01 | 最小 source 與測試骨架／`source-skeleton` | A03–A06 | `wip/src/loopflow/`、`wip/src/entrypoints/`、`wip/tests/`、bootstrap 與 import smoke test | `LF_Nexus.py` 測試入口可載入但不假裝功能完成 |
| LF-B02 | Result／Logging／Version／Config／Path／`foundation-core` | B01 | 共用結果、錯誤階段、log、版本、設定與無 UI path resolver | 純 Python 測試通過；沒有個人硬編碼路徑 |
| LF-B03 | Rhino platform 與狀態復原／`rhino-platform` | B01–B02 | selection、lock、visibility、color、modified state 的 adapter 與 snapshot／restore | 成功、取消、失敗路徑有測試；未實機部分明示 |
| LF-C01 | Dictionary reader／validator／`dictionary-core` | A06、B02 | 2.0 schema loader、validator 與明確錯誤 | fixtures 與版本拒絕行為通過 |
| LF-C02 | Nexus 重建工作軌／依 Nexus 專用文件逐項開分支 | A05–A06、B02–B03、C01 | Nexus 的 UI、資料處理、UUID／Space、payload 與發布整合 | 不作單一大型提交；子任務與驗收由 Nexus 專用文件定義 |
| LF-C03 | Registry 安全發布 P0／`registry-publisher` | A04、B02、C02 所需 payload | exclusive lock、pending、validate、atomic replace、last good | 雙程序、中斷、壞 JSON、replace 失敗測試通過 |
| LF-C04 | Data Viewer／`data-viewer` | A03–A04、B03、C01 | 只讀檢視 canonical 資料的 feature 與入口 | 不修改來源；缺值與未知版本可理解 |
| LF-D01 | Tagger Grab／`tagger-grab` | A04、B03、C01–C03 | Grab feature、入口與 fixtures | Rhino 狀態復原、重複執行與取消通過；Item 的模型／Block 來源分流正確，manual `TAG_DW` 不接受綁定 |
| LF-D02 | Tagger Laser／`tagger-laser` | D01 共用契約 | Laser feature、入口與 fixtures | 同上，且不複製共用規則 |
| LF-D03 | Tagger Index／`tagger-index` | D01 共用契約 | Index feature、入口與 fixtures | 同上 |
| LF-D04 | Tagger Layout ID／`tagger-layout-id` | D01、Layout 契約 | Layout ID feature、入口與 fixtures | Layout／Tag identity 一致；只對宣告的 title frame 寫 `DWG_*`，人工比例欄不動，未知 Block 零寫入 |
| LF-D05 | TAG-O／`tag-o` | D01–D04 | TAG-O feature、入口與 fixtures | Tag consumer 行為及錯誤路徑通過；manual Tag 不判 unbound，locked Tag 仍可唯讀判斷 stale／orphaned |
| LF-D06 | Infuser Part／`infuser-part` | D01–D05、C03 | Part feature、入口與 fixtures | 部分更新、last good 與警告狀態通過；所有 manual 欄位、manual `TAG_DW` 與 locked 內容均不覆寫 |
| LF-D07 | Infuser All／`infuser-all` | D06 | All feature、入口與 fixtures | 全量／重複更新及復原通過 |
| LF-E01 | Anchor Frame／`anchor-frame` | B03、A03 | Anchor feature 與入口 | 幾何及 layer 狀態可復原 |
| LF-E02 | Extract CP／`extract-cp` | E01 | Extract feature 與入口 | Section 測試案例通過 |
| LF-E03 | Duplicate Layout／`duplicate-layout` | E01、D04 | Layout copy feature 與入口 | 命名、取消與重複執行通過 |
| LF-E04 | Worksession／`worksession` | B02–B03 | event lifecycle、同步 feature 與入口 | register／unregister、重載與錯誤路徑通過 |
| LF-F01 | Cabinet Suite 規格與 fixtures／`cabinet-baseline` | A02–A03 | 延後功能的現況契約與代表案例 | 不先重寫大型 UI／幾何流程 |
| LF-F02 | Cabinet Suite 重建／`cabinet-suite` | F01、核心資料鏈穩定 | Cabinet feature 與入口 | UI、幾何、取消、失敗與來源狀態實機驗證 |
| LF-F03 | 2D Cabinet／Shelf Gap／DW／各自獨立 scope | F02 | 三項功能各自的 feature、入口與測試 | 每項獨立 commit／push，不合成一大包 |
| LF-G01 | Migration 工具／`migration` | canonical contract 與核心功能完成 | scanner、預覽、備份、converter、validator、rollback | 只對測試副本執行，失敗可回復 |
| LF-G02 | Build／Installer 技術選型與建置／`build-release` | 核心功能、資產結構與 migration 完成 | 比較可行封裝技術後，產生完整可安裝套件、LoopFlow 工具列、manifest、checksum 與回復方案 | 正式版不依賴 repo Python 路徑；Rhino Section Macro 可用且不覆蓋 workspace；全新／升級／重複安裝／移除／rollback 通過 |
| LF-G03 | 端到端 RC／`rc-validation` | G01–G02 | 隔離 Rhino 8 的完整 workflow 驗收記錄 | 正常、取消、失敗、中斷、來源零變更與 last good 全部驗證 |

## 建議開發波次

1. **契約波次**：A01–A06。只建立可裁決、可測的資料定義，不搬正式功能。
2. **架構波次**：B01–B03。只建立第一條功能真正需要的最小骨架。
3. **核心資料鏈**：C01–C04。Nexus 優先，但必須先依專用文件再拆分。
4. **可重複功能接入**：D01–E04。每支入口獨立任務，逐項實機驗證。
5. **延後大型功能**：F01–F03。Cabinet／2D 不阻塞前期核心契約。
6. **切換與發布**：G01–G03。完成 migration、build 與 RC 後才合入 `main`。

## 雙機換機檢查點

每次換機前必須達成：工作樹乾淨、任務分支已 push、upstream 差距 `0/0`、`PROGRESS.md` 記錄完成／未完成事項與下一步。另一台電腦先拉 workspace root 與全部子 repo，再從遠端分支續作；不可用雲端同步資料夾或手動複製程式碼取代 Git。
