# LoopFlow — 命名與資料契約

本文件是 2.0 命名、Dictionary 與跨指令資料契約的權威來源。正式寫程式前先完成盤點與裁決；未定案欄位不得由 AI 自行猜測。

## 狀態

- 階段：1.0 靜態盤點、實際操作流程與 Tag／圖框欄位盤點完成，等待使用者依決策表與 `architecture/NEXUS_DICTIONARY_DECISION_MENU.md` 裁決
- 套用版本：LoopFlow `v2.0.0`
- 舊版參考：`v1.0.0`
- 原則：新版乾淨定義；舊版資料不在開發中零散改寫
- Dictionary 盤點來源：`%LOOPFLOW_WORKFILES_ROOT%\LoopFlow_Dictionary.xlsx` 中文版本；repo release 的英文版本只作舊版比較

## 核心裁決

- Dictionary、UserText、layer、Registry、Tag 與指令名稱是一條完整資料鏈，必須整體定義。
- 新版核心只使用一套 canonical contract，不在各 feature 散落舊名稱 alias 或雙寫邏輯。
- 舊專案若需要升級，由獨立 migration scanner／converter 處理，不把相容程式混入日常 command。
- `main`、`v1.0.0` 與 Release ZIP 保留舊規則；2.0 在隔離安裝與測試資料上使用新規則。
- 名稱的語意由使用者確認；AI 負責盤點依賴、提出衝突與可理解選項。
- 整條工作鏈、資料實體與真相邊界以 `architecture/LOOPFLOW_DATA_ECOSYSTEM.md` 為上位藍圖；本文件負責把已確認原則落成可驗證 schema。
- 尚待使用者確認的上位原則與實務問題只維護於 `architecture/LOOPFLOW_DATA_ECOSYSTEM_DECISIONS.md`；確認後才回寫本契約。

## 必須盤點的命名層級

| 層級 | 例子 | 必須回答 |
|---|---|---|
| 工作流程語彙 | Dictionary、Nexus、Registry、Tag、Infuser | 這個詞代表什麼，與其他詞的邊界在哪裡 |
| Rhino 指令 | `LF_Nexus`、`LF_Tagger_Grab` | 對使用者顯示名稱、command ID、入口與功能責任 |
| Layer taxonomy | `M3D`、`04_CB`、`_Data` | 完整 path、類別、大小寫、層級與用途 |
| Dictionary 欄位 | `__Rhino Layer`、各資料欄 | 欄位意義、型別、必填、預設、版本與驗證 |
| UserText key | `_12_UUID` 等 | 寫入者、讀取者、唯一性、可否由使用者修改 |
| Registry schema | project／object／geometry／metadata | 欄位、型別、ID、版本與成功條件 |
| Block／Tag | Block 名稱與欄位 | 定義檔、插入者、更新者、顯示文字與缺值行為 |
| 檔案／資料夾 | Dictionary、Registry、log、output | 所屬位置、生命週期、備份與是否使用者可見 |
| Config | layer prefix、顏色、timeout | 真正可調設定與不可調內部契約的分界 |
| 程式識別字 | module、class、function、constant | 英文命名規則、縮寫與所屬 feature |

## 依賴盤點格式

每個持久化名稱都要建立一列：

| 現行名稱 | 意義 | Producer | Consumer | 儲存位置 | 衝突／問題 | 2.0 canonical 名稱 | 遷移方式 | 狀態 |
|---|---|---|---|---|---|---|---|---|
| 待盤點 |  |  |  |  |  |  |  | 未定案 |

只有完成 Producer／Consumer 追蹤後才能改名，不能只因名稱看起來不清楚就直接替換。

1.0 的實際欄位、producer／consumer、指南衝突與使用者選項已整理於 `architecture/NEXUS_DICTIONARY_DECISION_MENU.md`。該文件是討論輸入；使用者的裁決應回寫本文件，成為 2.0 正式契約。

使用者已指定採用中文 Dictionary 作為內容與 layer taxonomy 的重構來源；是否直接使用完整中文欄名作為 machine key，仍須與多語顯示方式一起裁決，不能只由檔案版本反推。

## Tag／圖框現況契約（1.x 觀察基準）

以下是 migration 與 2.0 schema 必須能辨識的 1.x 事實，不代表沿用同一批 canonical key。證據來自 `wip/docs/tag_block_text/` 的 10 份 Rhino Block instance 擷取文字（9 Tag、1 圖框，共 24 個唯一 UserText key）、`Tag_Blocks.3dm` 畫面與現行 Tagger／Infuser／Layout ID 程式。

| Family | 現行 binding | 自動顯示欄位 | 人工欄位／特殊規則 |
|---|---|---|---|
| Height Grab／Laser | `Source_UUID` | `attr_ch_key`、`attr_ch_val`、`attr_mat_key`、`attr_mat_val`、`attr_note` | `attr_manual_補充說明`、lock |
| Finish Grab／Laser | `Source_UUID` | `attr_mat_key`、`attr_mat_val`、`attr_note` | `attr_manual_補充說明`、lock |
| Item | `Source_UUID`；Block 名稱解析時另用 `.Auto_Item_*` | `attr_item_key`、`attr_item_val`、`attr_note` | `attr_manual_補充說明`、lock；`FF-01__Chair-1` 與 Dictionary `_03_ID編號` 是兩套來源 |
| Section Detail／Elev 1～4 | `.Target_DV_ID` | `Category`、`REF_ID` | `Detail_NO`、lock |
| Elev 0 | 無 binding | Layout ID 寫目前頁 `Category` | 六個方向／編號欄人工維護；不參加 Infuser／TAG-O |
| `TAG_DW` | **無；使用者已確認為純手動** | 無 2.0 自動欄位 | `attr_dw_id`、門窗寬、門窗高全部人工；沒有 lock。1.x Infuser 仍會把編號覆寫為 `?`，屬既成衝突 |
| `Sample_Frame` | 無 binding | Layout ID 寫 `DWG_NAME`、`DWG_NO` | `03-A3 Scale` 人工；固定文字不是 UserText |

正式 8 種可鎖 Tag 都使用 `attr_Lock_不更新>寫入x或X`。現行 Grab／Laser／Index／Infuser 都能找到這個 key，但只有值在 `strip().upper()` 後恰為單一 `X` 才鎖定；鎖定同時阻擋資料寫入與重新綁定。2.0 的 canonical `lock_state` 必須是 typed boolean／enum，由 UI 切換；其他既有值交給 migration 列為待確認，不推測含義。

2.0 Block manifest 至少需要：穩定 template ID、family、role、允許的 binding mode、欄位 owner、缺值顯示、template version 與 migration mapping。`TAG_DW` 使用 `binding_mode: manual`；是否以 `role: title_frame` 限定 Layout ID 寫入見 ED-16。`03-A3 Scale` 不能直接沿用為 canonical ID，因它把面板排序、圖幅與欄位語意混在名稱中；是否繼續人工或改為自動值見 ED-15。家具 `FF-01` 的資料身分見 ED-14。

## Dictionary 定義工作

1. 盤點 `LoopFlow_Dictionary.xlsx` 的所有欄、版本列、型別與允許值。
2. 對照 `Dictionary_GUIDE_TW.md`、Nexus、Tagger、Registry 與 2D consumer。Cabinet／BOM 已排除在主工作流程外，`_CB.*` 四欄不納入 2.0 主鏈 schema，改由 Cabinet 工作軌自行定義。
3. 找出同義欄位、中英文混用、prefix 推導、空值與預設值衝突。
4. 定義 2.0 schema：欄位名稱、顯示名稱、程式 key、型別、必填、驗證與版本。
5. 建立最小與完整 fixtures，包含合法、缺值、重複、未知欄位與舊版資料。
6. 使用者確認詞義與工作方式後才鎖定 schema。

## Layer／空間與物件識別

- Layer 名稱同時可能承擔分類、顯示與資料 key，2.0 必須拆清楚其責任。
- 完整 layer path 與 terminal name 不可混用。
- Space 判定規則需和 `_01_空間名稱`、boundary、Registry 與數量構想一致，不在搬程式時順便改。
- UUID 的產生、唯一性、複製、Block instance 與遺失處理必須明確定義。
- 顏色與 layer 名稱不可作唯一資料識別，除非契約明確規定並有測試。

## 新版資料版本

Dictionary、Registry 與需要跨程序保存的資料都必須有明確 `schema_version`。程式啟動時先驗證版本：

- 相符：正常執行。
- 未知／較新：停止並說明，不猜測解析。
- 舊版：交由獨立 migration 工具預覽與轉換。

## 舊專案遷移邊界

Migration 工具獨立於新核心：

```text
掃描舊專案
→ 產生差異與衝突報告
→ 使用者確認
→ 建立完整備份
→ 一次轉換 Dictionary／UserText／layer／Registry／Tag
→ 以 2.0 validator 驗證
→ 失敗時回復備份
```

禁止在一般指令執行時偷偷改名，也不長期雙寫新舊欄位。

## 定案門檻

- 目前工作流與所有名稱依賴已列出。
- 每個持久化名稱都有 producer、consumer 與儲存位置。
- 使用者已確認工作語彙與顯示名稱。
- canonical schema、版本與驗證規則完成。
- fixtures 與 migration 範圍完成。
- `_LoopFlow_系統設定.md` 與 `_LoopFlow_重構計畫.md` 已同步。

完成上述門檻後，才建立 2.0 command catalog 與 feature 程式骨架。
