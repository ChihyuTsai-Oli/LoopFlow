# LoopFlow — 使用說明

本文件記錄目前 1.x 對使用者可見的行為，也是重構期間不得無意改變的操作契約。完整逐步教學仍以 `USER_GUIDE_TW.md` 與 `Dictionary_GUIDE_TW.md` 為準。

2.0 採乾淨重建；本文件是理解舊工作流與建立測試案例的參考，不要求開發中的半成品持續可供正式使用。命名與操作若經使用者裁決可在 2.0 改變，但必須記錄於 `_LoopFlow_命名與資料契約.md`，並在發布前完成新版使用說明。

## 產品定位

LoopFlow 是 Rhino 8 的半自動化設計與出圖工具。使用者決定何時執行每個步驟；程式負責 Dictionary、UserText、UUID、Registry、Section、Tag、Layout 與 2D 圖說之間的資料整理與同步。

## 使用環境

- Rhino 8（CPython 3.9）
- Rhino Section Tools
- Windows 10／11
- Dictionary 與 Excel 功能使用 `.xlsx`；實際相依套件須以安裝器和執行環境驗證，不可只依 README 推定。

## 安裝與回復

1. 穩定版由 GitHub Release 下載 `LoopFlow_v1.0.0.zip`。
2. 執行 `install_LoopFlow.bat`，或依公開指南手動安裝 Python scripts。
3. 將 `LoopFlow.rhc` 拖入 Rhino 載入工具列。

穩定回復點為 `v1.0.0`。2.0 開發版必須使用獨立 scripts、toolbar、設定、Registry、log 與測試 `.3dm`，不可覆蓋 1.x 正式安裝。

## 主工作流程

1. 以 Dictionary 和 `LF_Nexus` 將資料寫入模型物件。
2. 視需要建立櫃體，並用 `LF_Data_Viewer` 檢查資料。
3. 以 `LF_Push_3D_to_JSON` 發布 Registry 資料。
4. 使用 Rhino Section Tools 產生剖面／立面。
5. 以 `LF_Anchor_Frame`、`LF_Tagger_Layout_ID`、Tagger 指令建立圖面基準與標籤。
6. 使用 `LF_Infuser_Part`／`LF_Infuser_All` 將最新資料寫入 Tag Blocks。

各步驟可以反覆執行，不要求固定成單一路徑；重構不得把半自動流程改成未經確認的全自動流程。

## 指令分組

| 功能群 | 指令 | 目前使用目的 |
|---|---|---|
| 資料與 Dictionary | `LF_Nexus`、`LF_Dictionary_Editor`、`LF_Data_Viewer` | 寫入、編輯與檢視模型資料 |
| Registry | `LF_Push_3D_to_JSON` | 將模型資料發布至 `Project_Registry.json` |
| Tag | `LF_Tagger_Grab`、`LF_Tagger_Laser`、`LF_Tagger_Index`、`LF_Tagger_Layout_ID`、`LF_TAG-O` | 建立、更新與檢查圖面標籤 |
| 圖面同步 | `LF_Infuser_Part`、`LF_Infuser_All` | 更新部分或全部 Tag Blocks |
| Layout / Section | `LF_Anchor_Frame`、`LF_Extract_CP`、`LF_Duplicate_Layout` | 建立基準、擷取剖線與複製 Layout |
| 櫃體與 2D | `LF_Cabinet_Suite`、`LF_2D_Cabinet_Gen`、`LF_2D_Shelf_Gap`、`LF_2D_DW_Gen` | 櫃體及門窗圖面處理 |
| 協作 | `LF_Sync_Worksession` | 監看與更新 Worksession |

## 核心資料規則

- Dictionary 檔名預設為 `LoopFlow_Dictionary.xlsx`，放在 `.3dm` 同一資料夾。
- Dictionary layer 主鍵欄為 `__Rhino Layer`；資料列前跳過 1 列版本標題。
- `_12_UUID` 是物件與 Registry／Tag 關聯的重要識別，不可在未定義遷移規則前改寫。
- `Project_Registry.json` 是發布資料；`Project_Registry.lock` 用於避免同時寫入。
- Dictionary key、legacy alias、完整 layer path 與 space 判定在完成 decision record 前不得偷偷更改結果。

## 使用安全契約

任何指令在成功、取消、失敗或中斷時，都必須符合：

- 不遺失 Rhino 未存修改。
- 不留下非預期 selection、lock、visibility、object color 或暫存 layer 狀態。
- 新輸出驗證成功前保留上一份有效 JSON／XLSX／幾何輸出。
- 不因 Dropbox／OneDrive 延遲或 stale lock 覆蓋其他程序剛寫入的 Registry。
- 錯誤訊息必須能指出失敗階段，不得只顯示成功或靜默忽略。

## Golden workflow

修改功能前，AI 必須用測試資料記錄對應的正常、取消、失敗、重複執行與復原結果。最少涵蓋：

- Tag／Dictionary
- Registry／Nexus
- Layout／Infuser／Worksession
- Cabinet／2D

目前實機驗證狀態以 `architecture/PROGRESS.md` 為準。

## 設定與問題定位

- 可編輯設定目前位於 `_LoopFlow_Config.py`；欄位與預設值見 `_LoopFlow_系統設定.md`。
- Debug log 預設檔名為 `cursor_LF_debug_log.txt`。
- 先保存錯誤畫面、Rhino command line、log、輸入檔與是否有未存修改，再交由 AI 判斷。
- 不要直接刪除 lock、Registry、設定檔或正式專案資料；先讓 AI 檢查狀態與回復方式。

## 文件責任

- `USER_GUIDE_TW.md`：公開逐步操作指南。
- `Dictionary_GUIDE_TW.md`：公開 Dictionary 規格。
- `_LoopFlow_使用說明.md`：重構期間的行為契約。
- `_LoopFlow_系統設定.md`：目前技術設定與檔案責任。
- `_LoopFlow_命名與資料契約.md`：2.0 Dictionary、命名、schema 與 migration 的權威來源。
- `architecture/LOOPFLOW_DATA_ECOSYSTEM.md`：完整工作鏈、資料真相邊界與現行功能的保留意圖。
- `_LoopFlow_重構計畫.md`：目標架構、順序與不做事項。
- `architecture/PROGRESS.md`：當前進度、檢查、限制與下一步。
