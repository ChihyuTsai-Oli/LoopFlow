# R2M 影片規劃：Rhino → BIM → Rhino 一輪往返

> 主片用已驗證的「牆」呈現 IFC 往返；樓層、類型、高度校正與不同 BIM 端操作詳見 [R2M 圖文規劃](../教學圖文版/R2M.md)。片名與描述寫明 R2M 1.0 系列及拍攝時安裝版，不以牆的結果宣稱風管／水管也實測完成。

## 主片：選一種 BIM 軟體跑完

建議先以可穩定錄製的一端拍完整循環；另一端另拍短片，避免在一支片中交錯兩套 BIM 軟體的收檔方式。鏡頭上固定標示目前軟體與檔名。

| 章節 | 連續操作與必須看到的結果 | 對應圖文 |
|---|---|---|
| 00 成果與三份檔 | Rhino 原模型、`R2M.ifc`、回程外參 `.3dm`；外參與原模型重疊 | 01 |
| 01 樓層 | 畫比建築大一圈的高程框，跑 `RMStorey`；顯示框 Z 與 FL | 02 |
| 02 出建築殼 | `RMModels` 選圖層、IFC 類型及類別 → Publish → `R2M.ifc` 與件數摘要 | 03 |
| 03 BIM 收檔與畫牆 | Archicad 開 IFC 當新檔，或 Revit Link IFC、建 Level／Floor Plan；新增一面可定位的牆 | 04 或 05 |
| 04 BIM 回程 | 選牆匯出 IFC4；空白 Rhino 跑 `RMInbound`、選對應 `config.json`，展示高度校正後重疊 | 06 |
| 05 外參與再發布 | 手動另存回程 `.3dm`、Worksession Attach；對照牆修改 Rhino 建築模型，再跑 Models | 07 |

## 配片與驗收鏡頭

- **另一 BIM 軟體收檔短片**：只補它的 IFC 收檔、樓層準備與牆回程差異。Archicad 用「開啟當新檔」；Revit 用「連結 IFC」並自建 Level／Floor Plan。
- **部分樓層短片**：用 PartialStoreys 示範跨層物件為何需要相鄰樓層框，對應圖文 02～03；若示範檔條件不完整，先不錄此片。
- 高度校正必須用同一組數字與畫面說明「BIM 的 FL」和「Rhino 框 Z」的差；同資料夾整棟與單層共用 `elevation_shift`，拍 Inbound 前要確認最後發布的是對應那份模型。
- 不剪掉 `RMInbound` 之後的手動另存與 Worksession Attach，因為這是實際流程的一部分。描述欄放章節時間碼及對應圖文，不把外參當圖紙或 Tag 來源。
