# LoopFlow Toolkit

與 LoopFlow 2.0、QTY 位於同一 repo，但屬於**不同產品**。Toolkit 收納可獨立使用的建模／圖面小工具，不進 `v2` 套件，也不讓任何單一工具成為其他工具的必要相依。

產品位置已於 2026-09-03 定案（TKO-02）：留在本 repo `toolkit/`，維持獨立 package、tests、Yak 與版本；邊界穩定後仍可整包抽離成獨立 repo。

## 目前階段

**前期評估，尚未建立程式、Yak 或 Rhino 工具列。**

現有 1.x 證據共有三支 `LF_2D_*`：

- `LF_2D_DW_Gen`
- `LF_2D_Shelf_Gap`
- `LF_2D_Cabinet_Gen`

2.0 文件另列 `LF_Cabinet_Suite` 為未納入主產品的第四支工具。使用者原敘述重複提到 `LF_2D_Cabinet_Gen`；因此第四支是否確指 `LF_Cabinet_Suite`，仍列為第一項待決策，不擅自視為定案。

## 工程方向

- 一個 `loopflow-toolkit` 產品與安裝包
- 功能彼此模組化，由 feature catalog 登錄；新增／停用工具不改動其他工具
- 一個穩定的 Toolkit launcher，加上各工具的直接指令
- 正式 Rhino 指令沿用 2.0 慣例：**無底線**（`LFToolkit`、`LFCabinetGroup`），開發期入口才用底線
- 幾何計算、Rhino 文件寫入、UI 三層分離
- 每個功能都有 fixtures、golden geometry 與取消／失敗復原測試
- 1.x 只作行為證據，不整檔搬回
- `LF_Cabinet_Suite` 先拆責任與資料契約，**不阻擋三支 2D 工具先發布**
- Cabinet Group 兩支指令（建立／命名／改名、唯讀檢查）已裁決，排在 Cabinet Suite 之前，**不受其未定案項目阻擋**

## 文件

請依序閱讀：

1. [`docs/前期評估/README.md`](./docs/前期評估/README.md)
2. [`docs/前期評估/程式盤點.md`](./docs/前期評估/程式盤點.md)
3. [`docs/前期評估/架構建議.md`](./docs/前期評估/架構建議.md)
4. [`docs/前期評估/決策紀錄_1.md`](./docs/前期評估/決策紀錄_1.md)
5. [`docs/前期評估/測試計畫.md`](./docs/前期評估/測試計畫.md)
6. [`docs/前期評估/開發順序計畫.md`](./docs/前期評估/開發順序計畫.md)
