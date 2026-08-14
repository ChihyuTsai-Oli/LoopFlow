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

## 文件導覽與責任

| 文件 | 唯一責任 |
|---|---|
| `docs/_LoopFlow_使用說明.md` | 1.x 可觀察操作事實、使用者安全與公開文件入口 |
| `docs/_LoopFlow_系統設定.md` | repo、runtime、路徑、entrypoint、build／installer 等技術設定 |
| `docs/_LoopFlow_命名與資料契約.md` | 已確認的 2.0 canonical schema、命名與 migration 契約 |
| `docs/資料生態藍圖.md` | 資料實體、真相邊界、producer／consumer 與架構原則 |
| `docs/資料生態決策表.md` | 所有待決與已裁決事項的唯一使用者編輯區；保留雙 AI 建議與比較 |
| `docs/工作流程模擬.md` | 2.0 暫定操作流程；若其他規畫文件描述衝突，先以本檔為操作基準並把疑義寫回決策表 |
| `docs/Nexus與字典盤點.md` | 1.x Nexus／Dictionary 靜態證據、欄位、設定、衝突與風險；不保存第二份答案 |
| `docs/_LoopFlow_重構計畫.md` | 重構策略、範圍、目標結構、品質門檻與完成條件 |
| `docs/開發任務與路徑.md` | 任務 ID、相依順序、工作波次與雙機安全停點 |
| `docs/重構進度.md` | 已完成工作、驗證結果、限制與唯一下一步 |

`docs/工作流程模擬.html` 與 `docs/資料生態決策表.html` 都是對應 Markdown 的衍生閱讀版，分別由 `wip/tools/build_workflow_html.py`、`wip/tools/build_decision_table_html.py` 產生，不是另一份規格，不手動編輯；兩者都可用 `--check` 驗證是否過期。已整合且過時的原始評閱副本已刪除；採納內容與雙 AI 比較保留在現行文件及 Git 歷史中。

`docs/tag_block_text/` 保存從 Rhino 實際 Block instance 擷取的 9 份 Tag 與 1 份圖框文字，是 migration／template fixture 的來源證據。已過時的 workflow simulation 初版提案已刪除，不再作為追溯來源。

`docs/loopflow_1.0_workflow_YT.txt` 是 1.0 的逐步操作說明，作為**操作邏輯參考**：它說明使用者實際怎麼用、在哪些點介入，但 1.0 的步驟順序不是 2.0 的流程契約，2.0 可依新架構重新安排。
