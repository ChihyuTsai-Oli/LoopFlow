# R2B 影片規劃：Rhino 專案進 Blender，再更新一次

> 一支主片展示可連續操作的案例；選項、安裝與排錯詳見 [R2B 圖文規劃](../教學圖文版/R2B.md)。正式拍攝以 R2B repo 的公開指令說明核對目前畫面，片名寫明 R2B 3.0 與實際安裝版。

## 主片章節

| 章節 | 連續操作與必須看到的結果 | 對應圖文 | 初估 |
|---|---|---|---|
| 00 成果與檔案關係 | Rhino 房間與 Blender 完成場景並排；指出 `.3dm` 同層是 Work Folder | 01 | 1 分 |
| 01 兩端開案 | 存 Rhino，`RBOpen`，設定 Blender Work Folder 與 Open / Health | 01 | 2 分 |
| 02 主模型第一次同步 | `RBModels` 選圖層與類別 → `R2B.3dm` → Blender **Sync Models**；顯示 `R2B` 集合及材質名 | 02 | 4 分 |
| 03 調材質、改幾何、再同步 | 在 Blender 調一個同名材質 → Rhino 改幾何重跑 Models → Blender **Update Models**，展示幾何變、材質留 | 03 | 3 分 |
| 04 選取物件 | Rhino 預選家具跑 `RBObjects` → Blender Import Objects 選時戳 3dm；顯示新增到場景根 | 04 | 2 分 |
| 05 相機與燈 | Rhino Camera Push／Auto、Blender 套用；建立 LightLayer 子層 Point 與 Blender 模板，再 Push／Sync | 05、06 | 5 分 |
| 06 最終更新 | 只改視角與燈點，分別更新 Camera／Light；最後顯示 Box Projection 的 World／Object 對照 | 07 | 3 分 |
| | **合計** | | **約 20 分** |

## 剪輯與資訊配置

- 每個通道保留「Rhino 動作 → 產出檔或時間 → Blender 按鈕 → 場景結果」四格視覺節奏。字幕寫正式指令名與 Blender 按鈕原文。
- 模型的 **Sync Models** 與 **Update Models** 用同一鏡位前後比較，避免口頭抽象描述。Objects 通道保留選檔視窗，以證明它是另選時戳檔。
- 完整錄一次燈光模板如何命名；其他燈具可加速。不要把 ToolBox 拍成 R2B Sync 安裝必需品。
- 片尾卡連到圖文 01～07，描述欄放章節時間碼、示範版本及同案例圖文入口。
