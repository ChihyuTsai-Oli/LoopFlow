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

1. `LF_Nexus > Dict. to Layer` 依 Dictionary 建立／更新建模 layers；使用者建立與修改 3D 模型。
2. `LF_Nexus > SpaceBoundary` 由使用者選取 closed curves 建立空間邊界。
3. `LF_Nexus > TagTrigger` 對 M3D 範圍寫入 Dictionary、尺寸、高程、空間與 UUID；接著以 `TagChecker` 檢查，必要時修正後重跑。
4. 視需要使用 `Layer to Dict.` 匯出 layer 現況供人工對照；它不是每次發布的必要步驟，也不應自動覆寫正式 Dictionary。
5. 以 `LF_Push_3D_to_JSON` 發布 Registry 資料。
6. 使用 Rhino 8 內建 Clipping／Section 指令建立剖面、立面或平面。
7. 以 `LF_Anchor_Frame` 建立 Tagger 定位基準；若抽出可編輯線稿則執行 `LF_Extract_CP`，移動線稿時 Anchor 必須一起移動。
8. 使用者先準備 Layout、Detail、圖框與 Tag Blocks，再執行 `LF_Tagger_Layout_ID` 批次編號與寫圖框。
9. 依 Tag 類型使用 Grab、Laser 或 Index 綁定；可逐張、逐批完成，不要求一次處理全部頁面。
10. 使用 `LF_Infuser_Part`／`LF_Infuser_All` 更新 Tag，再依紫／橘／紅回饋及 `LF_TAG-O` 檢查與修復。

各步驟可以反覆執行，不要求固定成單一路徑；重構不得把半自動流程改成未經確認的全自動流程。

Cabinet 與三個 2D Generator 是選用／獨立工具，不是每次主工作鏈的必要節點。

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

## Tag Block 的 1.x 操作事實

- 9 份 Tag 與 1 份圖框的實際文字已由 Rhino Block instance 擷取；欄位細節見 `architecture/LOOPFLOW_WORKFLOW_SIMULATION_v2.md`。
- 正式可鎖 Tag 使用 `attr_Lock_不更新>寫入x或X`。只有單一 `x`／`X`（前後空白可有）會生效；其他符號或文字看似已填，實際仍未鎖且沒有警告。
- 鎖定不只阻擋 Infuser 寫入，也會阻擋 Grab／Laser／Index 重新綁定。Infuser 跳過 locked Tag 時也不重新檢查來源與顏色，所以 locked 不代表來源健康。
- `TAG_DW` 後來改成門窗編號、寬、高全部手動輸入，而且沒有 lock 欄位；但 1.x Infuser 仍把它當資料 Tag。執行 Part／All 時，未綁定的 `TAG_DW` 會被塗橘並把人工 `attr_dw_id` 改成 `?`。這是已知 1.x 衝突；2.0 將它定義為純手動且完全不由 Sync 處理。
- `Sample_Frame` 的 `DWG_NAME`／`DWG_NO` 由 Layout ID 寫入；`03-A3 Scale` 現況由使用者維護。

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
- `architecture/LOOPFLOW_DATA_ECOSYSTEM_DECISIONS.md`：使用者可直接填寫的上位原則與實務待決事項。
- `_LoopFlow_重構計畫.md`：目標架構、順序與不做事項。
- `architecture/PROGRESS.md`：當前進度、檢查、限制與下一步。
