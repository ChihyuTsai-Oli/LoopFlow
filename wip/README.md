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
