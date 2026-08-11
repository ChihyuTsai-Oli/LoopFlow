# LoopFlow 2.0 重構進度

- 建立日期：2026-08-12
- 目標版本：`v2.0.0`
- 整合分支：`v2-development`
- 建立基準：`main` / `b09d650d5ba1a618c0ce8de154af2b961292e066`
- 穩定回復點：`v1.0.0` / `1479ba5f57d79f4048dd858f8afb0ff439c9fe66`
- 狀態：隔離整合線與繁中維護文件 SSOT 已建立；尚未修改產品程式碼

## AI 接手入口

本 repo 已建立自足的繁中維護文件。AI 開始前依序讀取根目錄 `AGENTS.md`、`docs/_LoopFlow_使用說明.md`、`docs/_LoopFlow_系統設定.md`、`docs/_LoopFlow_重構計畫.md`，最後讀本文件確認即時進度。外部分析檔不再是必要輸入。

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
- 1.x 的 P0 修復從 `main` 開獨立 hotfix 分支，發布後再同步至 `v2-development`。
- `v2.0.0` 只在 RC 與實機驗收完成、合回 `main` 後建立。

## Golden workflow 基準

開始修改對應功能前，使用隔離的 Rhino 8、測試 `.3dm` 與測試資料，記錄以下現行輸入、輸出與畫面結果：

- Tag：Grab、Index、Layout ID、Laser、TAG-O、Data Viewer。
- Dictionary：讀取、編輯、缺檔與錯誤資料。
- Registry：正常 push、取消、壞 JSON、lock、replace 失敗與最後有效資料。
- Nexus：UUID、boundary、dimensions、elevation、space、XLSX 與 JSON。
- Layout / Infuser / Worksession：完整與部分同步、warning、重複執行與復原。
- Cabinet / 2D：Suite、Cabinet、Shelf Gap、DW 的代表性輸入與輸出。

實機結果與 fixture 路徑必須在相關批次開始前補入本文件；未驗證項目不得標記為通過。

## 第一階段順序

1. Registry P0：原子 lock、鎖內重讀、安全 replace、保留最後有效 JSON。
2. Installer P0：升級保留 config / log，失敗可回復。
3. Rhino import / reload spike。
4. bootstrap、command catalog、foundation 最小骨架。
5. `LF_Tagger_Grab` 第一條垂直切片。

## 驗證紀錄

| 日期 | 分支 / commit | 檢查 | 結果 | 限制 |
|---|---|---|---|---|
| 2026-08-12 | `v2-development` 建立基準 | Git 同步、Release ZIP 完整性與 SHA-256、23 支 Python 靜態語法、RHC XML | 通過 | Rhino 8 實機流程由後續批次逐項驗證 |
| 2026-08-12 | 文件 SSOT 建置 | 建立繁中使用說明、系統設定、重構計畫與 repo AI 規則；Markdown 本機連結檢查 | 通過 | 既有大型程式標頭與英文註解依 feature 批次遷移，不做一次性翻譯 |

## 下一步

從風險順序開始時，先建立短期工作分支與對應測試資料；不要在本整合分支直接進行未分批的大型改寫。
