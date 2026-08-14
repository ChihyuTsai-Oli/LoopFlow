# LoopFlow WIP

此資料夾是 LoopFlow 2.0 的 Git 追蹤工作區；穩定 1.x 與 release payload 留在原位置。

```text
wip/
  docs/             # 實作階段的有效規格與進度
  src/              # 2.0 原始碼
  tests/            # 自動測試
  fixtures/         # 可提交、不含私人資料的測試資料與 legacy 證據
  tools/            # 文件產生器與開發輔助工具
```

大型 Rhino 工作檔、人工測試輸出與 Dropbox 素材不放進 repo。本機根目錄由 `LOOPFLOW_WORKFILES_ROOT` 指定，雙機對照與設定方式見工作區根目錄 `工作檔路徑.md`。

## 實作文件

AI 或開發者依序閱讀：

1. `docs/實作總覽.md`
2. `docs/資料契約.md`
3. `docs/工作流程.md`
4. `docs/開發任務與路徑.md`
5. `docs/系統設定.md`
6. `docs/重構進度.md`

| 文件 | 唯一責任 |
|---|---|
| `docs/實作總覽.md` | 2.0 範圍、架構邊界、安全原則與完成關卡 |
| `docs/資料契約.md` | Dictionary、模型、Registry、View、Drawing、Sheet、Tag 與 Health 正式契約 |
| `docs/工作流程.md` | 使用者操作順序、介入點、安全停點、重跑與失敗行為 |
| `docs/開發任務與路徑.md` | 任務 ID、依賴、工作波次與驗收條件 |
| `docs/系統設定.md` | repo、runtime、路徑、entrypoint、build／installer 等技術設定 |
| `docs/重構進度.md` | 已完成工作、驗證、限制與唯一下一步 |

`docs/工作流程.html` 是由 `docs/工作流程.md` 產生的閱讀版，不是第二份規格；修改 Markdown 後執行 `wip/tools/build_workflow_html.py` 更新。

## 前期規劃與測試證據

`docs/前期規劃/` 保存決策過程、雙 AI 比較、1.x 盤點與原始流程模擬。它只供歷史追溯，不作為 2.0 實作規格；與根目錄文件不同時，以根目錄文件為準。

Rhino Block 文字擷取結果位於 `fixtures/legacy/tag_block_text/`。A04 的 Registry／Tag manifest 位於 `fixtures/schema/`。這些是契約與 migration 的來源，不是實作說明。
