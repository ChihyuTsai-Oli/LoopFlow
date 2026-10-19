# R2B 圖文教學規劃

> 對象：要把 Rhino 模型、相機與燈光帶到 Blender 的使用者。現行公開系列為 R2B 3.0；操作事實以 R2B repo 的 `docs/USER_GUIDE_zh-TW.md`、`docs/COMMANDS_zh-TW.md` 與 `wip/docs/工作流程.md` 為準。本文只規劃教學，正式截圖前核對安裝版本與 Blender 畫面。

## 示範策略

使用[共用示範模型](./README.md#共用示範模型)在 R2B 教學作業資料夾的副本（從 3D 檔操作），在副本中補齊：兩種材質、重複的家具 Block、兩台視角、兩種燈具點位。R2B 的輸出資料夾會建在 `.3dm` 同層，所以只在 R2B 的作業資料夾操作。每篇都成對呈現 Rhino 的動作、磁碟輸出及 Blender 的消費結果。把 Work Folder 和 `.3dm` 同層的關係畫成一張固定小圖；不要讓讀者把 `models/` 當 Work Folder。

| 篇 | 作業結果 | 必截畫面 | 展示重點與常見誤解 |
|---|---|---|---|
| 01 安裝與開案 | 兩端能找到同一專案資料夾 | Rhino **LoopFlow R2B** 工具列、Blender N 面板、已存 `.3dm`、Work Folder、兩端 Health | Rhino 產出、Blender 讀取；`RBOpen` 看 last-good。Blender Sync zip 安裝與啟用按公開 README 核對；舊版 add-on 不與 3.0 混用。 |
| 02 主模型第一次同步 | `RBModels` 產 `R2B.3dm`，Blender 建出 `R2B` 集合 | Rhino 選圖層／類別／排除記號；成功檔案；Blender **Sync Models** 前後與材質槽 | 只選需要的圖層；預設 `//` 排除輔助層。示範父子圖層、材質名稱與 Block 重複實例；空範圍不當成功。 |
| 03 日常更新與材質 | 改 Rhino 幾何，Blender 更新但保留已調材質 | 同名材質修改前後、Rhino 更新、**Update Models** 結果，並列 **Sync Models** 用途 | 兩鈕都重建幾何；日常用 Update 保留同名材質節點，需要基本材質時才用 Sync。名稱變動會影響材質對應；不要只說「即時連線」。 |
| 04 選取物件 | 某件家具另匯入 Blender，主集合不變 | Rhino 預選物件、右鍵 **R2B Objects**、時戳 3dm、Blender **Import Objects** | Objects 是無材質、累加的獨立通道；Blender 自選時戳檔。主模型 `R2B.3dm` 和 Objects 檔不能交叉餵給按鈕。 |
| 05 相機 | Rhino 透視視角在 Blender 對齊 | Rhino 視角、左鍵 Camera 開／關、右鍵 Push、Blender Auto／Push 前後 | 已存檔、透視視角；區分自動跟隨與單次 Push，指出 `camera.json` 是中介。只更新相機時不必重跑 Models。 |
| 06 燈點到 Blender 燈具 | Rhino Point 驅動 Blender 模板位置 | `R2B_LT_Points` 子層、`Lighting`／`Lighting Fixtures` 模板、Light Push／Sync、結果集合 | 父層不放 Point；子層末名對模板。同步的是位置，不是 Rhino 燈能量／顏色。沒有符合 Point 時不會清掉 Blender 已有燈。 |
| 07 著色輔助與第二輪 | Box Projection 做材質，再單獨更新變動通道 | Shader Editor 面板、PBR 四槽、World／Object 對照；第二次 Update | Box Projection 是 Blender 著色輔助，不寫 UV、不在同步主鏈。ToolBox 是獨立 add-on，可另寫教學，不混進 R2B 安裝主流程。 |

## 每篇固定檢查點

列出「操作前要存什麼」「按完成功檔名或畫面」「Blender 要按哪一鈕」「取消／失敗後仍保留什麼」。截圖圖說標示左右鍵；指令文字寫 `RBModels`、`RBObjects` 等正式名稱。篇末連到公開指令說明，不重複所有參數。截圖用 **LoopFlow R2B** 自己的工具列；R2X 合併工具列只在篇末一句帶過（按鈕標籤略有不同）。
