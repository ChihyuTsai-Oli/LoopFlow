# LoopFlow 數量計算（qty）

同 LoopFlow repo、**不同產品**。不是出圖 2.0 的模組，也不進 Package Manager `loopflow`。

## 邊界

| 做 | 不做 |
|---|---|
| 單向讀 2.0 已發布的 Registry／物件資料 | 寫回物件 UserText、Registry、Nexus |
| 輸出獨立 Excel 估價單（與明細） | 打進 2.0 `.yak` 或工具列 |
| 依 Dictionary 的 `Q_01`～`Q_06` 規則求值 | 把「一式」寫進字典 |

2.0 算出圖；數量計算讀它留下的資料，自己產出 xlsx。契約語意以 `../v2/docs/資料契約.md` 為準。

## 現況

目前只有說明與評估筆記，還沒有計算程式。

- `docs/MCP評估/初步評估報告.md`：Rhino MCP／Grasshopper 可行性
- `docs/MCP評估/數量計算需求筆記.md`：估價領域需求

下一步才寫程式；不要把計算邏輯塞進 `v2/src/loopflow`。
