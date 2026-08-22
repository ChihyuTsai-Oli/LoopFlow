# LoopFlow 2.0

LoopFlow 讓 Rhino 裡自由建立的 3D 模型，經由 Dictionary 取得可追蹤的資料，再透過 Rhino Section 銜接到 2D 圖面、Sheet 與 Tag。它不是一次跑到底的自動化，而是一條能停下、確認、回頭修改，再繼續往下走的工作鏈。

## 一分鐘理解 LoopFlow

![LoopFlow 2.0 主工作鏈 / Main Workflow](./assets/loopflow-workflow-bilingual.svg)

整條工具鏈可概括為：

~~~text
自由建立 3D 模型
→ Dictionary 賦予 Type 與規則
→ 寫入、檢核並發布模型資料
→ Rhino Section 將 3D 幾何轉為 2D 圖面
→ 建立 Sheet、圖框與 Tag
→ 把 3D／Sheet 資料注入 2D 標籤
→ 檢查過期與斷連，再回到需要調整的節點
~~~

## 1. 自由建模，Dictionary 賦予資料

LoopFlow 不規定 3D 幾何必須由特定建模工具建立。使用者照原本方式在 Rhino 建模，再把物件放入對應的 Type Layer。

Excel Dictionary 是 Type Catalog，定義每種 Type 的穩定 ID、顯示名稱、Layer、高程基準與其他規則。Nexus 依 Dictionary 對 3D 物件寫入 Type、空間、高程、UUID 與資料版次，使自由建立的幾何成為能被後續圖面辨認的模型資料。

Dictionary 管理 Type；每個 3D 物件則保留自己的 instance 現值。重新同步 Dictionary 不會把物件的人工內容當成 Type 預設覆寫。

## 2. Registry 是 3D 與 2D 的資料交接

模型資料完成寫入與檢核後，LoopFlow 才發布新的 Registry revision。

Registry 是經驗證的唯讀快照，不是另一份人工維護的資料庫。它把某個時間點的 3D 模型狀態固定下來，讓 2D Tag 可以知道自己讀到哪一版資料，也讓後續變更能被辨認為正常、過期或斷連。

若模型改變，使用者可以回到 3D 更新資料、重新檢核，再發布下一個 revision；不必推翻已完成的整條工作鏈。

## 3. Rhino Section 是 3D／2D 的分界

LoopFlow 以 Rhino 8 原生 Section Tools 作為幾何交接點，不另外重做一套剖面引擎。

Section 之前屬於 **3D 模型端**：

- 自由建立與修改幾何
- Dictionary Type 與 Layer
- 空間、高程與物件 Metadata
- Registry revision

Section 之後屬於 **2D 圖面端**：

- View 與固定的 2D↔3D 對應
- 可持續跟隨 3D 的 Section 圖面
- 可選擇擷取成獨立編輯的 Drawing
- Layout、Sheet、圖框、圖目錄與 Tag

Rhino Section 產生的同步圖面仍跟隨 3D。需要人工整理線稿時，可以另外擷取成離線 Drawing；這份 2D 成果可以移動與修改，LoopFlow 不會在更新時靜默覆寫已辨認為人工編輯的內容。

## 4. 2D 使用 3D 資料，但保留人工出圖空間

進入 2D 後，LoopFlow 不把圖面變成全自動生成物。使用者仍決定：

- 哪些 View 與 Drawing 要建立
- Layout 如何安排與編號
- Tag 要綁定哪一個物件或 Detail
- 更新目前頁或全案
- 哪些欄位鎖定，保留人工內容

Tag 的綁定只建立穩定關係；Infuser 再依 Registry 與 Sheet metadata 更新顯示內容。人工備註、Detail 編號、比例與純手動 Tag 仍由使用者控制。

## 5. 每個節點都能停下，也能回頭

LoopFlow 的工作鏈不是單向流水線。每一階段都可以：

- 預覽影響後再執行
- 完成後停下、存檔或換機
- 取消而不留下半成品
- 修改上游資料後重新執行
- 保留人工成果，選擇新增、取代或略過

當 3D 物件、Sheet 或 Detail 改變時，TAG-O 會把 Tag 標示為過期或斷連。使用者可以依問題回到對應節點：

- **過期**：來源仍在，重新注入最新資料
- **斷連**：來源或目標已消失，重新綁定後再注入

LoopFlow 只報告狀態與影響，不替使用者猜測新的來源，也不自動修復。

## 深入了解

- [Excel Dictionary](./DICTIONARY_TW.md)：Dictionary 的使用方式，以及它與 3dm、Layer、物件、Registry 的關係
- [Rhino 指令](./COMMANDS_TW.md)：完整工具鏈與每支指令的操作方式
- [Tag Blocks](./TAG_BLOCKS_TW.md)：各種 Tag Block 的內容、綁定方式與適用範圍
- [文件入口](./README.md)
