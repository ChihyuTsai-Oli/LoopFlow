# LoopFlow Repository Instructions

範圍：本 repo。另須遵守上一層 `E:\_GitHub\AGENTS.md`。

## 開始作業前必讀

AI 必須依序完整讀取：

1. `docs/_LoopFlow_使用說明.md`
2. `docs/_LoopFlow_系統設定.md`
3. `docs/_LoopFlow_重構計畫.md`
4. `docs/architecture/PROGRESS.md`

公開的 `README.md`、`README_zh-TW.md`、`docs/USER_GUIDE*.md` 與 `docs/Dictionary_GUIDE*.md` 是使用者文件，不是重構指令的權威來源；改變使用行為時仍須同步更新。

## 分支與版本

- `main` 在 2.0 正式發布前維持穩定 1.x。
- `v2-development` 是 2.0 整合分支，不直接承接未分批的大型修改。
- 每項工作從 `v2-development` 建立 `codex/v2-<scope>` 短期分支。
- 1.x P0 修復從 `main` 建立獨立 hotfix，發布後再同步至 `v2-development`。
- `v1.0.0` tag 與 Release 永不移動或覆寫。

## 文件與語言

- 維護、架構、設定、重構與進度文件一律使用繁體中文。
- 對外英文 README／使用指南是發布翻譯，可保留英文；若功能事實改變，必須與繁中版本同步。
- 模組的完整責任、流程、資料契約與副作用寫入 `docs/`，不在程式檔頂端重複長篇說明。
- 新增或修改的 docstring、區塊註解與行內註解使用繁體中文；API 名稱、識別字、指令與第三方授權文字維持原文。
- 不為翻譯而一次改動所有程式。每次重構某個功能時，先確認其說明已進入 docs，再以同一批或緊接的獨立提交精簡標頭與翻譯必要註解。

## AI 作業流程

1. 確認 repo、branch、origin、upstream 與乾淨工作樹；只用 fast-forward pull。
2. 讀取上述四份文件，從 `PROGRESS.md` 找到目前階段、限制與下一步。
3. 建立短期工作分支，只處理一個 P0 或一條 feature。
4. 修改前保存該功能的 golden workflow／fixture；不得以正式專案資料作測試。
5. 完成後執行可用的靜態檢查與實機驗證，不得將未執行項目寫成通過。
6. 同步更新使用說明、系統設定與 `PROGRESS.md`；記錄 commit、檢查、限制和下一步。
7. 檢查 diff 後提交、推送短期分支，再依使用者授權合入整合分支。

使用者不負責操作 Git 或自行推導技術步驟；AI 應直接完成安全、可逆的操作，並以簡短繁體中文回報結果。
