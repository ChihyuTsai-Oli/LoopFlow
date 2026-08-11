# LoopFlow — 命名與資料契約

本文件是 2.0 命名、Dictionary 與跨指令資料契約的權威來源。正式寫程式前先完成盤點與裁決；未定案欄位不得由 AI 自行猜測。

## 狀態

- 階段：準備盤點
- 套用版本：LoopFlow `v2.0.0`
- 舊版參考：`v1.0.0`
- 原則：新版乾淨定義；舊版資料不在開發中零散改寫

## 核心裁決

- Dictionary、UserText、layer、Registry、Tag 與指令名稱是一條完整資料鏈，必須整體定義。
- 新版核心只使用一套 canonical contract，不在各 feature 散落舊名稱 alias 或雙寫邏輯。
- 舊專案若需要升級，由獨立 migration scanner／converter 處理，不把相容程式混入日常 command。
- `main`、`v1.0.0` 與 Release ZIP 保留舊規則；2.0 在隔離安裝與測試資料上使用新規則。
- 名稱的語意由使用者確認；AI 負責盤點依賴、提出衝突與可理解選項。

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

## Dictionary 定義工作

1. 盤點 `LoopFlow_Dictionary.xlsx` 的所有欄、版本列、型別與允許值。
2. 對照 `Dictionary_GUIDE_TW.md`、Nexus、Tagger、Registry、Cabinet 與 2D consumer。
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
