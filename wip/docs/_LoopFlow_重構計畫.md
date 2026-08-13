# LoopFlow — 重構計畫

本文件定義 2.0 的完整重構邊界、順序與完成條件。它已整合原先散落於外部分析與舊 memo 的有效內容；後續決策直接更新本文件與 `architecture/PROGRESS.md`。

## 目標

LoopFlow 不再以「每個按鈕一支完整 Python」作為架構邊界。2.0 會先重新定義工作流、Dictionary、命名與資料契約，再讓指令入口只呼叫 command catalog；Tag、Registry、Nexus、Layout、Cabinet 等邏輯依一起變動的功能群管理。

總體資料生態、工作鏈、資料實體、23 支現行程式的保留意圖與可翻案做法，以 `architecture/LOOPFLOW_DATA_ECOSYSTEM.md` 為起點。程式架構服務工作鏈，不反過來限制工作方式。

重構要解決：

- UserText／Dictionary key 有多套版本。
- `setup_environment()`、`get_project_dir()` 等 helper 重複。
- Registry 存在競態、不安全 replace 與 fallback。
- `LF_Nexus.py`、`LF_Cabinet_Suite.py` 同時承擔 UI、規則、I/O 與流程。
- 路徑、相依、RHC、README、安裝器與發行內容不一致。

## 重構模式裁決

本輪採「新版乾淨重建、正式發布時一次切換」：

- `main`、`v1.0.0` 與既有 release payload 凍結為舊版參考與回復點。
- 2.0 在隔離的 `wip/src/`、安裝位置、設定、資料與測試專案建立，不要求開發中的指令可供正式使用。
- 不把舊程式逐支包進新架構，也不以 compatibility wrapper 維持半套新舊系統。
- 開發仍按階段、功能群與 commit 建造；每段都有自動／contract 測試，避免最後才發現底層錯誤。
- 主要工作流全部接通後，再集中進行 Rhino 端到端實機測試與使用者驗收。
- 舊專案若需升級，由獨立 migration 工具一次轉換；新核心不長期雙讀／雙寫舊格式。

## 共同原則

- 採 feature-first package：`entrypoints`、`features`、`platform`、`foundation`。
- 小型 feature 可是一支模組；不強迫 application/domain 多層結構。
- 指令入口最終只呼叫 command catalog，不保存第二份邏輯。
- Dictionary、命名與資料契約先定義，完成前不建立正式 feature。
- P0 安全要求直接納入 2.0 新實作；只有使用者明確要求維護舊版時才另開 1.x hotfix。
- Python-first；只有實際可重現的 host、生命週期、型別或效能問題才評估 C#。
- `main` 維持穩定 1.x；2.0 在隔離分支與安裝環境開發。
- 2.0 不新增功能，不把延後構想偷渡進穩定化工作。

## 目標結構

```text
wip/
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
  fixtures/
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
- 定義 2.0 canonical key、schema version、驗證規則與獨立資料遷移。
- 新核心不散落 legacy aliases；舊名稱只由 migration scanner／converter 辨識。
- 未決定前只能偵測／預覽，不批次改正式專案。

### Tag／圖框 Block 契約

- 以已擷取的 9 份 Tag、1 份圖框、24 個 UserText key 建立 template fixtures，不再只從 Python hard-coded 清單反推 Block。
- Manifest 明列 template ID、family、role、binding mode、欄位 owner、template version、缺值行為與 migration mapping。
- `TAG_DW` 在 2.0 是純手動 Tag，Sync 與 unbound Health 不處理其欄位；1.x 的 DW 名稱解析只供 migration 參考。
- 正式 `lock_state` 使用 typed value；保留「凍結內容與重新綁定」的意圖，但 Health 仍唯讀檢查來源。
- 家具 `FF-01`、圖框 `03-A3 Scale` 與 `title_frame` role 依 ED-14～16 裁決後才固定 canonical schema。

### Project path／環境

- 合併重複的環境與 project path helper。
- path resolver 不顯示 UI；由 command 決定是否詢問使用者。
- 移除 `C:\_RH_Tools` 等個人路徑。

### Data/System layer

- 統一完整 layer path、prefix、大小寫與 2.0 canonical taxonomy。
- Rhino platform 負責查詢／建立；feature 不複製 layer helper。

### Space 判定

- 現況以 bounding-box 中心與第一命中範圍決定單一空間。
- 切割、多值與手動例外尚未裁決；先寫 decision record 與相容規則。
- 不得在搬移 Nexus 時順便改變結果。

### Warning／Rhino 狀態

- 定義 warning color 是否覆蓋使用者顏色及復原時機。
- selection、lock、visibility、object color 必須 snapshot／restore。
- 成功、取消與失敗路徑都需驗證。

## 新版建造順序

### S1：完整工作流與依賴盤點

- 依實際操作順序列出 Dictionary → Nexus／UserText → UUID／Space → Registry → Section／Layout → Tag → Infuser → Cabinet／2D／Worksession。
- 對每一步記錄輸入、輸出、producer、consumer、副作用、失敗條件與現有衝突。
- 既有 1.x 只作觀察與 fixture 來源，不在此階段修改。

### S2：Dictionary、命名與資料契約

- 完成 `_LoopFlow_命名與資料契約.md` 的欄位、layer、UserText、Registry、Tag／圖框 manifest、檔案與設定盤點。
- 由使用者確認工作語彙與顯示名稱；AI 定義 canonical ID、型別、schema version 與 validator。
- 建立合法／錯誤／缺值／舊版 fixtures 與 migration 範圍。
- 契約未定案前不建立正式 feature。

### S3：最小新架構與載入驗證

- 建立全新的 `wip/src/`、bootstrap、command catalog、result／error、logging、version、validator 與測試骨架。
- 驗證 Rhino 8 package import、reload、不同工作目錄與隔離安裝位置。
- 若 module loading 不可靠，使用模組化 source + build-time flatten／bundle。

### S4：依工作流接入核心功能

1. Config、Naming、Result、Logging、Rhino platform。
2. Dictionary 讀取與驗證。
3. Nexus、UserText、UUID、Space、Boundary。
4. Registry 與 Excel；直接實作原子 lock／pending／validate／replace。
5. Section、Layout、Anchor、Extract、Duplicate。
6. Tag、Data Viewer、TAG-O。
7. Infuser All／Part。
8. Cabinet、2D、Worksession。

每一段完成即跑純邏輯、fixture、資料契約與失敗路徑測試；不必等待可供正式使用才測試。

### S5：端到端實機測試

- 主要工作流接通後，以隔離 Rhino 8 與測試 `.3dm` 按真實操作順序執行。
- 驗證正常、取消、失敗、中斷、重複執行、來源文件狀態與 last good output。
- 跨功能錯誤回到契約或所屬 feature 修正，不在測試層加入臨時特例。

### S6：Migration、Build 與一次切換

- 建立獨立舊專案 scanner、預覽、備份、converter、2.0 validator 與 rollback。
- command catalog 產生或驗證 RHC／docs。
- build 產 release payload、ZIP、檔案清單與 hash。
- 重新驗證 RHP，不套用舊攤平腳本假設。
- RC 與實機驗收通過後一次合入 `main`，發布 2.0；不保留施工用相容層。

## Git 與環境隔離

- 2.0 工作由 `codex/v2-<scope>` 合入 `v2-development`。
- `main` 原則上凍結；只有使用者明確要求舊版緊急修補時才從 `main` 開 hotfix。
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

- Registry／installer P0 安全要求已完整實作於 2.0；若另有 1.x hotfix，須獨立記錄。
- Tag、Dictionary、space、Registry、path、version 各有唯一來源。
- 所有指令經 command catalog；舊 `.py` 只剩入口。
- `LF_Nexus.py`、`LF_Cabinet_Suite.py` 不再混合 UI、規則、I/O 與流程。
- Rhino 8 package import 或 build 備案通過實機驗證。
- `main` 與開發環境隔離，`v1.0.0` 可完整回復。
- 延後構想保留於文件，但未混入 2.0 核心範圍。
