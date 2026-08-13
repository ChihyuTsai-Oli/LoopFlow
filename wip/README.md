# LoopFlow WIP

此資料夾是 LoopFlow 2.0 的 Git 追蹤工作區；穩定 1.x 與 release payload 仍留在原位置。

```text
wip/
  docs/           # 重構 SSOT、資料契約、roadmap、progress
  src/            # 後續建立的 2.0 原始碼
  tests/          # 自動測試
  fixtures/       # 可提交、輕量且不含私人資料的測試資料
```

大型 Rhino 工作檔、人工測試輸出與可由 Dropbox 同步的素材不放進 repo。其本機根目錄由環境變數 `LOOPFLOW_WORKFILES_ROOT` 指定，電腦對照與設定方式見工作區根目錄 `工作檔路徑.md`。

重構採用 `%LOOPFLOW_WORKFILES_ROOT%\LoopFlow_Dictionary.xlsx` 的中文版本；Rhino 與其他程式產生／讀取的即時 JSON 放在同一工作檔根目錄的 `exchange/`，不提交 Git。

總體工作鏈、資料實體與 23 支現行程式的保留意圖，先讀 `docs/architecture/LOOPFLOW_DATA_ECOSYSTEM.md`；依 1.0 實際操作與 Block 參數複核後的現行流程讀 `docs/architecture/LOOPFLOW_WORKFLOW_SIMULATION_v2.md`（HTML 為同名 `_v2.html`）；使用者可直接填寫的待決定事項讀 `docs/architecture/LOOPFLOW_DATA_ECOSYSTEM_DECISIONS.md`；欄位與 Nexus 細項再讀 `docs/architecture/NEXUS_DICTIONARY_DECISION_MENU.md`。

`docs/tag_block_text/` 保存從 Rhino 實際 Block instance 擷取的 9 份 Tag 與 1 份圖框文字，是 migration／template fixture 的來源證據；未加 `_v2` 的 workflow simulation 是已取代的初版提案，只供差異追溯。
