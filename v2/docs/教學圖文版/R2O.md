# R2O 圖文教學規劃

> 對象：把 Rhino 模型、相機與燈具／家具點位交給 Octane Studio 的使用者。現行公開系列為 R2O 2.0；依 R2O repo 的 `docs/USER_GUIDE_zh-TW.md`、`docs/COMMANDS_zh-TW.md` 和 `wip/docs/工作流程.md` 製作。不要把 R2B 的 Blender 按鈕或自動同步語意套進本系列。

## 示範策略

使用[共用示範模型](./README.md#共用示範模型)在 R2O 教學作業資料夾的副本（從 3D 檔操作），在副本中補齊：兩個同名材質的物件、相機視角、燈點和家具 Block；R2O 輸出會建在 `.3dm` 同層，只在 R2O 的作業資料夾操作。Octane 先有可接 USDZ 的場景與一台符合條件的 Thin Lens。每篇並列 Rhino 輸出與 Octane 讀取結果，明示哪一步需手動套用、哪一步需關閉後重開。

| 篇 | 作業結果 | 必截畫面 | 展示重點與檢查點 |
|---|---|---|---|
| 01 安裝、資料夾與腳本 | Rhino 和 Octane 都知道正確來源 | **LoopFlow R2O** 工具列、已存 `.3dm`、`loopflow_R2O` 資料夾、Octane Script directory、腳本清單 | Octane Lua 是安裝來源，不是每個專案一份；專案資料跟 `.3dm` 走。`ROOpen` 可看 last-good。裝新版後核對腳本版本與熱鍵表。 |
| 02 第一次交付主模型 | `ROModels` 發布 `R2O.usdz`，Octane 接好材質 | Rhino 圖層／幾何類別／排除記號、輸出檔、Octane USDZ 節點與材質接口 | 材質接口依 **Rhino 材質名稱**，不是圖層名；相同名稱共用接口。先接一個可辨識材質，讓後續更新效果清楚。 |
| 03 主模型改版 | Rhino 改幾何，Octane 讀到新版並保留接線 | 修改前後 USDZ、Octane 關閉再開後同一場景 | 此版主模型沒有 Models LiveLink 腳本；更新同一 `R2O.usdz` 後關掉 Octane 再開。不要拍成 Reload mesh／Load new mesh 流程。改材質名會形成新接口。 |
| 04 獨立組件 | `ROObjects` 發布時戳 USDZ，Octane 自行載入 | 先選物件、右鍵 **R2O Objects**、時戳檔、Octane 新組件 | 不是主模型更新；Block 不搬原點。把 `USD::` 資產 Block 與 `R2O::` 點位層分清。 |
| 05 相機 | Rhino 視角寫出，Octane 單次套用 | Rhino 透視視角與 Camera Push、`camera.json`、Thin Lens Expand、`R2O_Camera.lua` 前後 | Rhino 可持續寫出或單次 Push；Octane Lua **每次只套用一次**。Octane 場景須恰好一台已 Expand Thin Lens；換視角後要再跑腳本。 |
| 06 燈與家具點位 | `ROPoint` 發布 Point／Block，Octane 生成 Scatter | `R2O::LT_Points`／`FUR_Points` 子層、`point.json`、`R2O_Point.lua`、場景根 Scatter | 父層不放 Point／Block；套用一次後保留已接 Proxy，刪來源類型再套用會移除受管節點。Block 建立時的原點與朝向要一致。 |
| 07 Authoring 與更新判斷 | 觀眾能補材質並知道改什麼要重跑什麼 | 四個 Authoring 腳本各一張用途圖、模型／相機／點位三種改版分支 | Authoring 是 Octane 端著色輔助，不屬 Rhino 四鈕；模型靠重新發布與重開、相機／點位靠重新發布與單次 Lua。 |

## 撰寫與拍攝提醒

每篇先給「完成狀態」圖，再拆解操作；把 `R2O.usdz`、時戳 USDZ、`camera.json`、`point.json` 的用途用短表列出。文字要說明失敗或取消保留上一份有效輸出。畫面上的 Octane 版本與選單字樣在正式截圖時重新核對，不直接沿用舊規劃。截圖用 **LoopFlow R2O** 自己的工具列；R2X 合併工具列只在篇末一句帶過。
