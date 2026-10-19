# R2M 圖文教學規劃

> 對象：需要從 Rhino 交付建築殼給 Revit／Archicad，再把 BIM 幾何 IFC 帶回 Rhino 當外參的使用者。現行公開套件為 R2M 1.0.4。依 R2M repo 的 `docs/USER_GUIDE_zh-TW.md`、`docs/COMMANDS_zh-TW.md` 與 `wip/docs/工作流程.md` 製作；本文是教學規劃，不宣稱未實測的 BIM 情境已通過。

## 示範策略

使用[共用示範模型](./README.md#共用示範模型)在 R2M 教學作業資料夾的副本（QTY 規格要求同名空間跨樓層，至少兩層），在副本中補畫各層樓層框，示範「Rhino 出殼 → BIM 畫一面牆 → IFC 回 Rhino → 對照調整 → 再出殼」。主線只選一種 BIM 軟體完整示範；另一種做獨立分支圖文，因為 Archicad 的開啟方式與 Revit 的連結方式不同。正式示範可用已驗證的牆作回程幾何，不把風管／水管的操作寫成已驗證成果。

| 篇 | 作業結果 | 必截畫面 | 展示重點與檢查點 |
|---|---|---|---|
| 01 檔案與座標概念 | 知道哪份是工作檔、IFC、回程外參 | **LoopFlow R2M** 四鈕、資料夾樹、Rhino 模型 Z 與建築 FL 示意 | `RMOpen` 看設定；BIM 端沒有 LoopFlow 外掛。R2M 用 **FL 結構面**，LoopFlow 出圖的 FFL 是不同基準，兩邊不自動讀取。 |
| 02 畫與登記樓層框 | `RMStorey` 得到可檢查的樓層名和 FL | 各層水平閉合框、框比外牆大一圈、WholeBuilding／PartialStoreys 選擇、登記結果 | 整棟要有 1F／RF；部分樓層以實際存在的一層作基準。跨層件涉及的樓層框也要有；不要手改 `R2M_FL`。框與外牆碰邊會擋住，不能沿用 LoopFlow Space 框的共邊規則。 |
| 03 發布建築殼 | `RMModels` 寫出 `R2M.ifc` | 樓層清單、最末端圖層／IFC 類型／幾何類別、Publish 結果與檔案 | 第一次圖層全不勾；天花選 `IfcCovering`，未改類型預設 `IfcPlate`；框外／低於最低層的件數、Proxy 警告要截到。發布不會存來源 `.3dm`。 |
| 04 BIM 收殼：Archicad | 建築殼在正確樓層顯示 | 開啟 IFC 當新檔、樓層／高程、牆與天花位置 | 不用 Merge 或 Update 進範本；非整棟跨層缺框的結果用對照圖說明。 |
| 05 BIM 收殼：Revit | 連結 IFC、建立對應 Level 與 Floor Plan | Link IFC、Level 高度、Floor Plan、連結模型 | Revit 是 Link IFC，需依 IFC 框線高程手動建 Level；顯示單位／進位與 IFC 寫入公分分開解釋。 |
| 06 BIM 幾何回 Rhino | BIM 選取牆匯出 IFC4；空白 Rhino 跑 `RMInbound` | 選取物件匯出、空白 `.3dm`、選 IFC／`config.json`、匯入網面與原模型重疊 | 只出要回傳的 3D 幾何；不要帶整棟與 2D。高度校正值取自**最後一次** `RMModels`；若同資料夾整棟／單層共用設定，Inbound 前先對對應模型跑 Models。 |
| 07 外參與第二輪 | 回程另存 `.3dm`、Worksession 掛載，依外參改 Rhino 後再發布 | 手動另存固定檔名、Attach／Refresh、修改前後、第二次 IFC | `RMInbound` 不代存、不代掛 `.rws`；回程網面只當外參，不當圖紙／Tag 來源。更新同一檔後手動 Refresh。 |

## 每篇文字重點

用三欄「你現在在 Rhino／BIM 哪一端、讀哪份檔、產生哪份檔」標在步驟旁；把 FL、框 Z、`elevation_shift` 用同一組數字貫穿。若碰到失敗，說明停在哪一步及上一份 `R2M.ifc` 是否仍有效。不要把第一版未提供的碰撞檢查或 BIM 外掛畫進教學成果。截圖用 **LoopFlow R2M** 自己的工具列；R2X 合併工具列只在篇末一句帶過。
