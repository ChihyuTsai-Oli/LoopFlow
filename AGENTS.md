# LoopFlow Repository Instructions

範圍：本 repo。另須遵守上一層 `E:\_GitHub\AGENTS.md`。

## 開始作業前必讀

AI 必須依序完整讀取：

1. `wip/docs/_LoopFlow_使用說明.md`
2. `wip/docs/_LoopFlow_系統設定.md`
3. `wip/docs/_LoopFlow_命名與資料契約.md`
4. `wip/docs/architecture/LOOPFLOW_DATA_ECOSYSTEM.md`
5. `wip/docs/architecture/LOOPFLOW_DATA_ECOSYSTEM_DECISIONS.md`
6. `wip/docs/architecture/LOOPFLOW_WORKFLOW_SIMULATION_v2.md`
7. `wip/docs/architecture/NEXUS_DICTIONARY_DECISION_MENU.md`
8. `wip/docs/_LoopFlow_重構計畫.md`
9. `wip/docs/architecture/DEVELOPMENT_ROADMAP.md`
10. `wip/docs/architecture/PROGRESS.md`

公開的 `README.md`、`README_zh-TW.md`、`docs/USER_GUIDE*.md` 與 `docs/Dictionary_GUIDE*.md` 是使用者文件，不是重構指令的權威來源；改變使用行為時仍須同步更新。重構中的文件、原始碼、fixtures 與測試統一放在 `wip/`；Dropbox 工作檔路徑依上一層 `工作檔路徑.md` 解析，不得寫死單一電腦的絕對路徑。

## 分支與版本

- `main` 在 2.0 正式發布前維持穩定 1.x。
- `v2-development` 是 2.0 整合分支，不直接承接未分批的大型修改。
- 每項工作從 `v2-development` 建立 `codex/v2-<scope>` 短期分支。
- `main` 原則上凍結；僅在使用者明確要求維護 1.x 時，才建立獨立 hotfix，發布後再同步必要修正至 `v2-development`。
- `v1.0.0` tag 與 Release 永不移動或覆寫。

## 重構模式

- 2.0 採「新版乾淨重建、正式發布時一次切換」，不要求開發中的新舊指令互相相容。
- `main` 與既有 release payload 作為唯讀舊版參考；新程式在隔離的 `wip/src/`、安裝位置與測試資料建立。
- 先完成整體工作流、Dictionary、命名與資料契約，再建立程式架構與接入功能。
- 新核心不長期保留 legacy alias、雙寫或 compatibility wrapper；舊專案轉換集中於獨立 migration 工具。
- 建造過程仍分批提交並做自動測試；Rhino 端到端實機測試在主要工作流串接完成後集中進行。

## 文件與語言

- 維護、架構、設定、重構與進度文件一律使用繁體中文。
- 對外英文 README／使用指南是發布翻譯，可保留英文；若功能事實改變，必須與繁中版本同步。
- 模組的完整責任、流程、資料契約與副作用寫入 `docs/`，不在程式檔頂端重複長篇說明。
- 新增或修改的 docstring、區塊註解與行內註解使用繁體中文；API 名稱、識別字、指令與第三方授權文字維持原文。
- 不為翻譯而一次改動所有程式。每次重構某個功能時，先確認其說明已進入 docs，再以同一批或緊接的獨立提交精簡標頭與翻譯必要註解。

## AI 作業流程

1. 確認 repo、branch、origin、upstream 與乾淨工作樹；只用 fast-forward pull。
2. 讀取上述文件，從 `PROGRESS.md` 找到目前階段、限制與下一步。
3. 建立短期工作分支，只處理一個 P0 或一條 feature。
4. 命名契約尚未定案前，不建立正式 feature；先完成依賴盤點、schema 與 fixtures。
5. 每段完成後執行自動測試與契約檢查；主要工作流串接後再以測試專案做 Rhino 端到端實機驗證。
6. 同步更新使用說明、系統設定與 `PROGRESS.md`；記錄 commit、檢查、限制和下一步。
7. 檢查 diff 後提交、推送短期分支，再依使用者授權合入整合分支。

使用者不負責操作 Git 或自行推導技術步驟；AI 應直接完成安全、可逆的操作，並以簡短繁體中文回報結果。
