# R2O 影片規劃：Rhino 到 Octane 的完整交接

> 主片展示一個場景在 Rhino 發布、於 Octane 消費，並完成第二輪更新；選單細節與限制由 [R2O 圖文規劃](../教學圖文版/R2O.md) 解釋。片名寫 R2O 2.0 與拍攝時實際安裝版。

## 主片章節

| 章節 | 連續操作與必須看到的結果 | 對應圖文 |
|---|---|---|
| 00 成果與手動交接 | Rhino 模型與 Octane 最終場景對照；指出模型、相機、點位是三條可分別更新的通道 | 01 |
| 01 開案與 Script directory | 存 `.3dm`、`ROOpen`、Lua 所在資料夾、Octane Script 列表 | 01 |
| 02 主模型初次載入 | `ROModels` 選圖層／類別 → `R2O.usdz` → Octane 載入並接材質接口 | 02 |
| 03 模型變更 | Rhino 改一塊幾何重跑 `ROModels`；Octane 關掉再開，同一場景看到新幾何且接線仍在 | 03 |
| 04 獨立組件 | Rhino 預選 Block 跑 `ROObjects`，Octane 自行載入時戳 USDZ | 04 |
| 05 相機 | Rhino 透視視角 Push，Octane 已 Expand 的 Thin Lens 跑 `R2O_Camera.lua`；換視角再套用一次 | 05 |
| 06 點位 | Rhino `R2O::` 子層 Point／Block → `ROPoint` → `R2O_Point.lua` → 場景根 Scatter 接 Proxy | 06 |
| 07 Authoring 與第二輪 | 只選一個材質示範 PBR 或 UV 輔助；再改一個點位重新發布並套用 | 07 |

## 畫面與口白要求

- 每個通道呈現「Rhino → 專案資料夾檔案 → Octane」；模型與 Objects 都沒有 LiveLink 腳本。相機與點位 Lua 在 Octane 是**套用一次**，片中要真的跑第二次展示。
- 主模型改版保留 Octane 關閉與重開的可辨識畫面，避免剪接成按 Reload mesh。材質接口用 Rhino 材質名稱標示。
- 片尾用一張表回顧：模型＝重新發布並重開 Octane；相機＝重新寫出並跑 Camera Lua；點位＝重新發布並跑 Point Lua。完整操作差異連回圖文。
- 正式錄製先核對 Octane 版本、Thin Lens 條件、腳本熱鍵與目前安裝版；不能用未驗證畫面代替結果。
