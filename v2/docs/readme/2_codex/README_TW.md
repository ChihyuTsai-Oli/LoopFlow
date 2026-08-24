# LoopFlow 2.0 使用說明總覽

> 一分鐘理解 LoopFlow 的資料流、3D／2D 分界與工作方式。操作細節請查 [Commands](./COMMANDS_TW.md)，Excel 欄位請查 [Dictionary](./DICTIONARY_TW.md)，圖面標註請查 [Tag Blocks](./TAG_BLOCKS_TW.md)。

## 一分鐘理解 LoopFlow

> **雙語 SVG 流程圖將放在這裡。** 本頁是 SVG 的文字延伸：比圖更完整，但只解釋工作鏈邏輯，不重複逐步操作。

LoopFlow 的核心可以濃縮成三段：

1. **3D 自由建模**  
   使用者照原本方式在 Rhino 建模。LoopFlow 不限制幾何必須由特定工具產生，也不在背景自動往下執行。

2. **Dictionary 賦予資料**  
   Excel Dictionary 定義 Type、Layer、高程基準與其他規則。模型物件放入對應 Type Layer 後，Nexus 才依使用者指示寫入 UUID、Type、空間、高程與資料版次，檢核通過再發布 Registry。

3. **2D 使用已發布的資料**  
   Rhino Section 把 3D 幾何帶到 2D；View、Drawing、Sheet 與 Tag 再組織圖面。模型資料由 3D 往 2D 流動，2D 不反向改寫 3D Type 或物件資料；但 Sheet、Tag 綁定與人工欄位仍由 2D 端自己維護。

簡單說：

~~~text
3D 是模型與資料的來源
→ Dictionary 讓自由幾何具有可追蹤的意義
→ Registry 固定一次通過檢核的資料版本
→ Rhino Section 是幾何出口
→ 2D 將幾何與資料整理成可人工編輯的圖紙
~~~

## 3D／2D 的分界：Rhino Section

LoopFlow 不取代 Rhino 的剖面工具。Rhino 8 原生 Section／Clipping Drawing 是整條鏈的幾何分界：

| 3D 模型端 | Rhino Section | 2D 圖面端 |
|---|---|---|
| 自由建模 | 產生剖面、立面或平面 | View 與 2D↔3D 對應 |
| Dictionary Type 與 Layer | 保持與 3D 幾何連結 | 同步 Section 圖面 |
| 空間、高程、UUID、版次 | 作為幾何出口 | 可獨立編輯的 Drawing |
| Registry revision | 不重新定義模型資料 | Layout、Sheet、圖框、圖目錄、Tag |

Section 產生的圖面會持續跟隨 3D。若需要人工整理線稿，可以另外擷取成獨立 Drawing；這份 Drawing 可以移動與修改，更新時不會被靜默覆寫。

## 不是一次跑到底，而是可回溯的工作鏈

LoopFlow 把每一個節點都當成安全停點：

- 每一步都由使用者主動執行，系統不會自己往下跑。
- 有副作用的動作先預覽或確認影響。
- 完成一段後可以存檔、換人、換電腦，之後從下一段繼續。
- 取消或失敗不應破壞上一份有效資料或留下半成品。
- 修改上游後，只重跑受影響的節點，不必推翻整份圖面。
- 人工 Drawing、Tag 鎖定欄與其他人工內容有明確保護範圍。

當來源改變時，Health 只標示問題，不替使用者猜答案：

- **過期**：來源仍存在，重新注入最新資料。
- **斷連**：來源或目標消失，重新綁定後再注入。

LoopFlow 2.0 不自動 Repair。使用者決定怎麼修改、採用哪次更新，以及哪些人工成果要保留。

## 四個核心名詞

| 名詞 | 意思 |
|---|---|
| **Dictionary** | Type Catalog。定義每種 Type 的穩定 ID、Layer、顯示名稱與規則，不保存每個 3D instance 的現況。 |
| **Registry** | 3D 模型通過檢核後發布的唯讀資料快照，讓 2D 知道自己讀取哪一次 revision。 |
| **Sheet** | 圖號、圖名與頁面身分的正式資料來源；Layout 頁名是人類可讀的輸出。 |
| **Health** | Tag 的正常、過期或斷連檢查結果；用來帶使用者回到需要調整的節點，不是自動修復。 |

## 深入了解

- [Excel Dictionary](./DICTIONARY_TW.md)：Type、Layer、3dm 物件與 Registry 的關係
- [Rhino 指令](./COMMANDS_TW.md)：主工作鏈編號、Nexus 選單與每支指令
- [Tag Blocks](./TAG_BLOCKS_TW.md)：各圖塊的顯示欄、人工欄、綁定與適用範圍
- [文件入口](./README.md)
