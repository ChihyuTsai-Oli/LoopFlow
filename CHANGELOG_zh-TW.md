# Changelog

LoopFlow 已發布版本的變更記在這裡。

[English Version](./CHANGELOG.md)

---

## [2.2.5] - 2026-11-23

請安裝這版。流程與 2.2.3 相同，另外：

- Anchor Update 放在 Anchor Frame 後面。3D 尺寸改過、並已重出 2D 剖面後，用它更新既有外框，Laser 對位才跟得上
- Extract 會把剖面的 Text Dot 複製到 `LoopFlow_Extract::Text`，供抽出後的圖跑 Anchor Frame
- 不要覆寫 `v2.2.3`。裝完請完全關閉 Rhino 再開

---

## [2.2.3] - 2026-11-17

請安裝這版。流程與 2.2.2 相同，另外：

- Package Manager 的套件縮圖改為淺色稿。工具列圖示與指令不變
- 不要覆寫 `v2.2.2`。裝完請完全關閉 Rhino 再開

---

## [2.2.2] - 2026-11-17

請安裝這版。流程與 2.2.1 相同，另外：

- 只換工具列圖示與 Package Manager 圖示。指令不變
- 不要覆寫 `v2.2.1`。裝完請完全關閉 Rhino 再開

---

## [2.2.1] - 2026-11-17

請安裝這版。流程與 2.2.0 相同，另外：

- 五顆 Rhino 9 剖切圖示已內嵌，Rhino 8 也看得到同一組圖
- Document 按鈕右鍵說明是 `Language`
- Rhino 8 保留 Align clipping drawings 按鈕，只為了工具列版面一致。這個指令在 Rhino 8 不會執行
- 不要覆寫 `v2.2.0`。裝完請完全關閉 Rhino 再開

---

## [2.2.0] - 2026-11-17

請安裝這版。Rhino 8 與 Rhino 9 共用同一份套件。

- Rhino 9 的剖面圖塊可直接登記、擷取，並供 Grab／Laser 使用，不必炸開
- 天花圖登記時，Anchor Frame 會問圖面是手動水平翻轉，或用 Rhino 9 Reflected 投影產生
- Nexus 能確認原物件時，可把 `MatchProperties` 複製走的 UUID 寫回去
- 套件附新版 LoopFlow 工具列
- 不要覆寫 `v2.1.1`。裝完請完全關閉 Rhino 再開

---

## [2.1.1] - 2026-11-10

請安裝這版。流程與 2.1.0 相同，另外：

- 工具列按鈕改為 Rhino 8 淺色／深色主題各自的 SVG
- 不要覆寫 `v2.1.0`。裝完請完全關閉 Rhino 再開

---

## [2.1.0] - 2026-10-12

請安裝這版。流程與 2.0.7 相同，另外：

- 多張平面圖疊在一起時，Laser 點到一個以上的 Anchor Frame，先用 Text Dot 名稱選框，再繼續原來的材料選擇
- 舊框再跑一次 Anchor Frame 才會記下這個名稱。在那之前，清單顯示框的物件名稱。Index 對到一個以上的框仍會停止
- 不要覆寫 `v2.0.0`–`v2.0.7`。裝完請完全關閉 Rhino 再開

---

## [2.0.7] - 2026-08-26

請安裝這版。流程與 2.0.6 相同，另外：

- 專案檔改放在已存檔 `.3dm` 旁邊的 `_LoopFlow_Config/loopflow/`（`LoopFlow_Project.json`、Registry、日誌）
- 開一次 2.0.6 的專案，會把舊的根層設定、Registry 資料夾與日誌搬進 `loopflow/`。更舊的 `exchange/` 不會搬，要再發布一次
- 不要把 1.x 與 2.0 混用。不要覆寫 `v2.0.0`–`v2.0.6`。裝完請完全關閉 Rhino 再開

---

## [2.0.6] - 2026-08-26

請安裝這版。流程與 2.0.5 相同，另外：

- `00_STR` 結構層上的物件不再寫入 2.0 物件資料。下一次寫入模型資料時，會清掉這些物件上殘留的 UserText。Type 圖層與圖層的 `lf_type_id` 仍會建立
- Grab 與 Laser 不把 Tag 綁到結構物件
- Grab 的 `TAG_ITEM` 需要家具圖塊與 Tag 在同一個 `.3dm`。2D／3D 分成 Worksession 時，不能從連結檔挑選家具
- 裝完請完全關閉 Rhino 再開。不要把 1.x 與 2.0 混用。不要覆寫 `v2.0.0`–`v2.0.5`

---

## [2.0.5] - 2026-08-25

請安裝這版。流程與 2.0.4 相同。

- LoopFlow 工具列檔補上可見的群組，Package Manager 安裝後按鈕才會出現
- 若工具列仍是空白，把工具列視窗改回 Default，開啟套件裡的 `LoopFlow.rui`，並勾選 LoopFlow
- 同一專案不要混用 1.x 與 2.0。不要覆寫 `v2.0.0`、`v2.0.1`、`v2.0.2`、`v2.0.3` 或 `v2.0.4`

---

## [2.0.4] - 2026-08-25

請安裝這版。流程與 2.0.3 相同。

- 更新官方 `Tag_Blocks.3dm`
- 版本變更後，下一次產品指令會把「文件\LoopFlow」裡的官方檔換成與安裝套件相同的版本。該資料夾裡多出來的檔不會刪。需要新的 Tag 圖塊時，再複製到各個專案
- 同一專案不要混用 1.x 與 2.0。不要覆寫 `v2.0.0`、`v2.0.1`、`v2.0.2` 或 `v2.0.3`

---

## [2.0.3] - 2026-08-23

請安裝這版。流程與 2.0.2 相同。

- Tag 與其他指令在 Rhino 把腳本拷到暫存資料夾後，仍找得到已安裝的套件
- 同一專案不要混用 1.x 與 2.0。不要覆寫 `v2.0.0`、`v2.0.1` 或 `v2.0.2`

---

## [2.0.2] - 2026-08-23

請安裝這版。流程與 2.0.0／2.0.1 相同。

- yak 內含 `tag_templates.json`，Package Manager 安裝後，Laser、Grab、Index、Infuser 與 TAG-O 才找得到 Tag 範本
- 同一專案不要混用 1.x 與 2.0。不要覆寫 `v2.0.0` 或 `v2.0.1`

---

## [2.0.1] - 2026-08-22

只改 Package Manager 清單。產品內容與 2.0.0 相同。

- 套件圖示與一段簡短說明
- 從 Package Manager 或 `v2.0.1` 的 yak 安裝。同一專案不要混用 1.x 與 2.0

---

## [2.0.0] - 2026-08-22

Rhino 8 的重建版。用一份 `.yak` 安裝。同一專案不要混用 1.x 與 2.0。

- Excel 字典（中文或英文欄名）、Type 圖層、空間框、寫入／檢核資料，以及發布 Registry
- Tag、Layout 圖號、圖目錄、Infuser、TAG-O（標出過期或斷開的 Tag，不自動修）
- Anchor Frame、Extract、複製 Layout、Worksession、雙語介面
- 第一次執行指令時，官方 `Tag_Blocks.3dm` 與 Dictionary 範本會拷到「文件\LoopFlow」
- 櫃體、2D 工具與數量計算不在 2.0

---

## [1.0.0] - 2026-04-23

第一次公開發布。

### 指令
- **LF_Nexus** — 資料中心：字典到圖層、SpaceBoundary、TagTrigger、TagChecker、圖層到字典
- **LF_Cabinet_Suite** — 櫃體產生器（30 種組合），含料單尺寸
- **LF_Push_3D_to_JSON** — 把 3D 物件資料推到 Project_Registry.json
- **LF_Anchor_Frame** — 為 Tagger 指令產生錨定框
- **LF_Tagger_Layout_ID** — 自動編 Layout 圖號並寫入圖框
- **LF_Tagger_Laser / LF_Tagger_Grab** — 把材料／家具／門 Tag Block 連到 2D 圖面
- **LF_Tagger_Index** — 把立面／剖面索引 Tag Block 連到 Detail
- **LF_Infuser_Part / LF_Infuser_All** — 把資料寫進 Tag Block
- **LF_2D_DW_Gen** — 產生 2D 門窗符號（8 種門、3 種窗）
- **LF_2D_Cabinet_Gen** — 產生 2D 櫃體符號
- **LF_2D_Shelf_Gap** — 產生等距層板分隔
- **LF_Sync_Worksession** — 多人 Worksession 同步
- **LF_Dictionary_Editor** — 直接開啟字典 Excel
- **LF_Data_Viewer** — 查看 3D 物件上的 UserText
- **LF_Extract_CP** — 依顏色把 Section Tools 的產出抽到新圖層
- **LF_Duplicate_Layout** — 批次複製選取的 Layout
- **LF_TAG-O** — 查看所有 Tag Block 狀態（已連結／未連結／斷開）
