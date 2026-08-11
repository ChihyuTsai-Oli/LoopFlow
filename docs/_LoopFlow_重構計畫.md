# LoopFlow — 重構計畫

本文件定義 2.0 的完整重構邊界、順序與完成條件。它已整合原先散落於外部分析與舊 memo 的有效內容；後續決策直接更新本文件與 `architecture/PROGRESS.md`。

## 目標

LoopFlow 不再以「每個按鈕一支完整 Python」作為架構邊界。使用者仍看到原指令，但入口只呼叫 command catalog；Tag、Dictionary、Registry、Nexus、Layout、Cabinet 等邏輯依一起變動的功能群管理。

重構要解決：

- UserText／Dictionary key 有多套版本。
- `setup_environment()`、`get_project_dir()` 等 helper 重複。
- Registry 存在競態、不安全 replace 與 fallback。
- `LF_Nexus.py`、`LF_Cabinet_Suite.py` 同時承擔 UI、規則、I/O 與流程。
- 路徑、相依、RHC、README、安裝器與發行內容不一致。

## 共同原則

- 採 feature-first package：`entrypoints`、`features`、`platform`、`foundation`。
- 小型 feature 可是一支模組；不強迫 application/domain 多層結構。
- 指令入口最終只呼叫 command catalog，不保存第二份邏輯。
- P0 安全修復先在現有架構完成，不等待 package。
- Python-first；只有實際可重現的 host、生命週期、型別或效能問題才評估 C#。
- `main` 維持穩定 1.x；2.0 在隔離分支與安裝環境開發。
- 2.0 不新增功能，不把延後構想偷渡進穩定化工作。

## 目標結構

```text
src/
  loopflow/
    bootstrap.py
    command_catalog.py
    features/
      tagging/
      nexus/
      layout/
      cabinet/
      drawing2d/
    platform/
      rhino/
      registry.py
      dictionary_files.py
      excel.py
    foundation/
      config.py
      paths.py
      logging.py
      results.py
      atomic_io.py
      dependencies.py
      version.py
  entrypoints/
tests/
docs/
tools/
```

## Track 0：先處理安全問題

### Registry P0

- 使用真正的 exclusive lock，記錄 PID、主機與時間並處理 stale lock。
- 取得 lock 後重新讀取資料，避免先讀後鎖覆蓋別人更新。
- 先完整寫入 pending、flush／驗證後再 replace；正式檔不先刪除。
- 驗證雙程序、程序中斷、壞 JSON、replace 失敗與雲端同步延遲。
- 無論成功或失敗，都保留最後有效 JSON 與可理解的錯誤階段。

### Installer P0

- 不再整包刪除安裝根目錄。
- 保存使用者 `_LoopFlow_Config.py` 與 debug log；長期移至穩定 user-data 位置。
- 驗證全新安裝、升級、重複安裝與 rollback。

### 低風險一致性

- 核對 README／User Guide 的 `Data/`、`Python/` 與實際 ZIP／安裝器。
- 移除 Cabinet 的個人 debug 路徑。
- 明確宣告 `pandas`、`openpyxl`；缺少時提供可理解處理方式。
- RHC 中 R2B、R2O 或舊路徑另批清理並做 Rhino 實機驗證。

## SSOT 與未決策項目

### UserText／Dictionary

- 盤點 `LF_TAG-*`、中英文 key、prefix 掃描與所有 consumer。
- 定義 canonical key、legacy aliases、讀取優先序與資料遷移。
- 未決定前只能偵測／預覽，不批次改正式專案。

### Project path／環境

- 合併重複的環境與 project path helper。
- path resolver 不顯示 UI；由 command 決定是否詢問使用者。
- 移除 `C:\_RH_Tools` 等個人路徑。

### Data/System layer

- 統一完整 layer path、prefix、大小寫與 legacy alias。
- Rhino platform 負責查詢／建立；feature 不複製 layer helper。

### Space 判定

- 現況以 bounding-box 中心與第一命中範圍決定單一空間。
- 切割、多值與手動例外尚未裁決；先寫 decision record 與相容規則。
- 不得在搬移 Nexus 時順便改變結果。

### Warning／Rhino 狀態

- 定義 warning color 是否覆蓋使用者顏色及復原時機。
- selection、lock、visibility、object color 必須 snapshot／restore。
- 成功、取消與失敗路徑都需驗證。

## 遷移順序

### L1：回復點與 import spike

- 保持 `main` 可發布，使用 `v2-development` 整合。
- 保存 Tag、Registry、Dictionary、Nexus、Layout、Cabinet golden fixtures。
- 驗證 Rhino 8 entrypoint → package import、reload、不同工作目錄與安裝路徑。
- 若 package loading 不可靠，改用模組化 source + build-time flatten／bundle。

### L2：最小骨架

- 建立 bootstrap、command catalog、result/error、logging、version。
- catalog 記錄 handler、相關檔案、docs、selection、undo 與副作用。

### L3：Tag 垂直切片

- 先以 `LF_Tagger_Grab` 驗證 entrypoint → feature → Rhino platform。
- 操作結果不變，舊入口只剩薄 wrapper。
- 若人或 AI 無法由 catalog 一次找到完整脈絡，合併過度分散的模組。

### L4：Tag／Dictionary 全群

- 遷移 Grab、Index、Layout ID、Laser、TAG-O、Data Viewer。
- 每組 key／prefix 衝突先寫 decision record。
- 完成後舊入口不得保留 UserText key 與讀寫邏輯副本。

### L5：Registry／Nexus

- Dictionary loading → file platform。
- dimensions／elevation／space → feature rules + Rhino geometry platform。
- UUID／boundary validation → Nexus feature。
- JSON push → registry service；XLSX → Excel platform；dialog → Rhino UI platform。
- 先讓舊 UI 呼叫新 feature，最後才移出大型檔案。

### L6：Layout／Infuser／Worksession

- 合併 Infuser All／Part 的資料查找、warning 與 layout 寫入。
- Duplicate Layout、Anchor Frame、Extract CP 改走 Rhino platform。
- watcher 只管理 event lifecycle，實際同步交給 feature。

### L7：Cabinet／2D

- 先拆 UI 與 handler，再比較 Suite、2D Cabinet、Shelf Gap、DW 規則。
- 幾何純計算留在 feature；Rhino bake 放 platform。
- 本階段不改 UI 或輸出幾何。

### L8：Build／RHP

- 核心入口穩定後才讓 `src/` 成為唯一可編輯來源。
- command catalog 產生或驗證 RHC／docs。
- build 產 release payload、ZIP、檔案清單與 hash。
- 依新 package 重新驗證 RHP，不套用舊「24 個攤平腳本」假設。

## Git 與環境隔離

- 2.0 工作由 `codex/v2-<scope>` 合入 `v2-development`。
- P0 若需先發布 1.x，從 `main` 開 hotfix，驗證／發布後再同步整合線。
- RC 通過才合入 `main` 並建立 `v2.0.0`。
- Dev scripts、toolbar、config、Registry、log 與 `.3dm` 必須與 1.x 分離。
- 升級測試只對 1.x 資料副本執行。

## C# Gate

導入 C# 前必須全部成立：

1. Python 有可重現、可量測的實際問題。
2. 問題屬 Rhino host、生命週期、型別或效能，不是架構混亂。
3. 規則與介面已穩定。
4. C# 能完整負責該邊界，不只是啟動 Python。
5. DLL、build、.NET／Rhino 版本與部署可驗證、可回復。
6. 導入後總維護成本更低。

## 延後範圍

### Geometry History

2.0 不實作物件級幾何歷史。未來可能以 `_12_UUID`、獨立 SQLite／snapshot 保存版本，但必須先解決 hash、容差、Block definition、容量、Dropbox WAL／衝突與跨電腦策略。不可直接在 Dropbox 中開啟共享 SQLite。

### GH Quantity

2.0 不實作 Grasshopper 工程數量。未來規格需重新確認 Rhino document units、坪／才／長度／體積換算、跨空間物件、Excel 表單版本、重複引用與人工例外；資料來源是 Rhino 場景，不經 Registry。

### RHP

RHP 是 L8 包裝工作，不是當前功能。需重新驗證 Rhino Script Project、shebang、`.rhproj`、rhinocode CLI、RUI/RHC 與 shared resources。

## 每批完成門檻

- 一批只處理一個安全問題或一條 feature，不混入新功能。
- golden workflow、取消、失敗、中斷與資料復原通過。
- 來源 Rhino 文件沒有非預期變更，上一份有效輸出仍存在。
- 新規則只有一個權威來源，舊入口不保留副本。
- catalog、使用說明、系統設定、進度與測試結果同步。
- diff 排除秘密、快取、產物與無關修改。
- commit、push、回復點與實機限制有紀錄。

## 2.0 完成條件

- Registry／installer P0 可先安全供 1.x 使用。
- Tag、Dictionary、space、Registry、path、version 各有唯一來源。
- 所有指令經 command catalog；舊 `.py` 只剩入口。
- `LF_Nexus.py`、`LF_Cabinet_Suite.py` 不再混合 UI、規則、I/O 與流程。
- Rhino 8 package import 或 build 備案通過實機驗證。
- `main` 與開發環境隔離，`v1.0.0` 可完整回復。
- 延後構想保留於文件，但未混入 2.0 核心範圍。
