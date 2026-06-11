# LF_Geometry_History — 開發備忘錄

> 發想日期：2026-06-11
> 最後更新：2026-06-11
> 狀態：概念確認，待排期開發

---

## 一、背景與動機

現有的 `LF_Push_3D_to_JSON` 已能將 Rhino 物件的屬性（UserText）推送至 `Project_Registry.json`，並以 `_12_UUID` 作為每個物件的唯一識別鍵。

然而目前每次 Push 為**全量覆蓋**，不保留歷史版本。設計過程中若需要找回某個物件的舊版幾何體，只能翻找備份 `.3dm` 檔，流程繁瑣且容易出錯。

本模組目標：在不破壞現有工作流的前提下，為 LoopFlow 加入**單一物件層級的幾何版本歷史**，並支援在 Rhino Viewport 中直接預覽與還原。

---

## 二、核心價值

| 現有備份方式 | 本模組 |
|-------------|--------|
| 以整個 .3dm 檔案為單位 | 以單一物件（UUID）為單位 |
| 需手動打開每個備份檔比對 | 在當前場景直接預覽各版本 |
| 幾何與屬性無法分別追蹤 | 幾何變化與屬性變化分開記錄 |
| 無差異比對 | 自動標示變更類型與幾何差異 |

**關鍵洞察：** `_12_UUID` 機制從設計之初就為版本對應埋好地基，本模組是其自然延伸。

---

## 三、設計原則

1. **完全 opt-in**：不影響現有 LoopFlow 任何腳本，獨立模組、獨立檔案
2. **輕量主檔**：`Project_Registry.json` 保持現況，不因歷史功能而膨脹
3. **幾何資料獨立存放**：歷史幾何體存於獨立檔案，日常存取不受影響
4. **版本上限可設定**：於 `_LoopFlow_Config.py` 統一控制，預設 20 版

---

## 四、檔案架構

```
專案資料夾/
├── Project_Registry.json        ← 現有，保持輕量（屬性 + geom_hash）
├── Project_Registry.lock        ← 現有
├── Project_Geometry_History.db  ← 新增，SQLite，儲存完整幾何體歷史
└── cursor_LF_debug_log.txt      ← 現有
```

### 為何選 SQLite

- Python 內建支援，零額外依賴
- 可精準查詢單一 UUID 的特定版本，不需整檔載入
- 相較於單一肥大 JSON，存取速度穩定

---

## 五、資料結構設計

### Project_Registry.json 微幅擴充

每個 Object 新增 `geom_hash` 欄位作為幾何指紋，用於快速比對是否有幾何變化：

```json
"Objects": {
  "UUID-001": {
    "Layer": "M3D::01_Wall",
    "_03_ID": "W-001",
    "Update_Time": 1745000000,
    "geom_hash": "a3f9c2d1"
  }
}
```

### Project_Geometry_History.db Schema

```sql
CREATE TABLE geometry_versions (
  id            INTEGER PRIMARY KEY AUTOINCREMENT,
  uuid          TEXT    NOT NULL,
  version       INTEGER NOT NULL,
  push_time     REAL    NOT NULL,
  change_type   TEXT,
  geom_hash     TEXT,
  geom_data     TEXT,   -- rhino3dm Encode() 序列化字串
  attr_snapshot TEXT,   -- 該版本屬性的 JSON 快照
  geom_diff     TEXT,   -- 與前一版的幾何差異（JSON）
  attr_diff     TEXT    -- 與前一版的屬性差異（JSON）
);

-- Block 專用表（見第十三節）
CREATE TABLE block_versions (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  block_name  TEXT    NOT NULL,
  version     INTEGER NOT NULL,
  push_time   REAL    NOT NULL,
  geom_hash   TEXT,
  geom_data   TEXT,
  geom_diff   TEXT
);

CREATE INDEX idx_uuid       ON geometry_versions(uuid);
CREATE INDEX idx_block_name ON block_versions(block_name);
```

---

## 六、幾何指紋（geom_hash）計算方式

用於 Check 階段快速判斷幾何是否有變，不需載入完整幾何資料。

**組合輸入（五個特徵值）：**

```
bbox_min + bbox_max + volume + surface_area + face_count
→ MD5 前 8 碼
```

單純 bbox 不足以區分「實心 Box」與「相同外框但中間挖洞的 Box」，加入 volume 與 surface_area 後可有效辨別絕大多數實際場景中的幾何變化。

若 geom_hash 一致 → 幾何未變，跳過幾何資料寫入，節省空間與時間。

---

## 七、變更類型分類

每次 Push 自動判斷並記錄：

| change_type | 說明 |
|-------------|------|
| `created` | 首次出現的物件 |
| `geometry_modified` | 幾何體有變化，屬性未變 |
| `attributes_modified` | 屬性有變化，幾何未變 |
| `geometry_and_attributes_modified` | 兩者皆有變化 |
| `unchanged` | 無任何變化（不寫入 History）|

---

## 八、新增腳本規劃

### `_LF_Geometry_Archive.py`（工具模組，不直接執行）

負責：
- 計算 geom_hash（五特徵值組合）
- 呼叫 rhino3dm Encode 序列化幾何
- 比對新舊版本差異
- 寫入 / 讀取 SQLite（含 Block 專用邏輯）

### `LF_History_Viewer.py`（主執行腳本）

負責：
- 讓使用者選取 Rhino 物件
- 讀取該物件的版本列表，顯示 Eto 選單
- Hover 版次 → 透過 DisplayConduit 在 Viewport 預覽幾何（半透明）
- 確認 → 替換物件幾何，保留現有 UserText；取消 → 清除預覽，不做任何變更

### `LF_Push_3D_to_JSON.py` 修改幅度

**極小。** 只需在現有 push 迴圈結束後，選擇性呼叫 `_LF_Geometry_Archive.push_version()`，以 flag 控制是否啟用歷史記錄功能。

---

## 九、歷史記錄開關設計

兩層控制，互不干擾：

**層一：`_LoopFlow_Config.py` 全域設定**
```python
HISTORY_MAX_VERSIONS  = 20      # 每個物件保留的最大版本數
HISTORY_ENABLED       = True    # 歷史記錄預設開啟
```

**層二：`LF_Push_3D_to_JSON` 指令列選單新增項目**
每次執行時可單次覆蓋全域設定，例如：
```
▶ Push（含幾何歷史）   ← 預設選項
▶ Push（僅屬性，略過幾何歷史）
```

**層三（選配）：Macro 搭配存檔自動執行**
可設定存檔時自動觸發 Push，使用者完全無需手動操作。

---

## 十、還原流程設計

還原時**只置換幾何體，保留現有 UserText**，屬性的更新交回給 LF_Nexus 重新寫入，職責分明：

```
LF_History_Viewer 還原幾何
        ↓
幾何體替換完成，UUID 不變，UserText 維持當前版本
        ↓
視需要執行 LF_Nexus TagTrigger 重新寫入屬性
```

此設計避免「幾何版本與屬性版本錯位」的混亂狀態。

---

## 十一、使用者操作流程

```
平時工作流（不變）
─────────────────────────────────────────────
LF_Nexus TagTrigger → LF_Push_3D_to_JSON
                            ↓（若啟用歷史模組）
                      同時寫入 Geometry_History.db

需要版本回溯時
─────────────────────────────────────────────
1. 選取 Rhino 物件
2. 執行 LF_History_Viewer
3. 彈出版次列表：

   版次  時間               變更類型               幾何變化
   v5   2026-04-20 14:32   屬性修改               —
   v4   2026-04-10 09:15   幾何+屬性修改           體積 +12%
   v3   2026-03-28 11:40   幾何修改               bbox 高度變化
   v2   2026-03-10 16:20   屬性修改               —
   v1   2026-02-15 09:00   初始建立               —

4. Hover 版次 → Viewport 即時預覽（半透明，DisplayConduit）
5. 確認替換 → 幾何置換，UserText 保留
   取消      → 清除預覽，不做任何變更
6. 視需要執行 LF_Nexus TagTrigger 更新屬性
```

---

## 十二、預覽機制技術說明

使用 Rhino 的 **`DisplayConduit`** API，與 Grasshopper 預覽幾何體的底層機制相同：

- 幾何體繪製在 Viewport 中但**不寫入文件**
- 對話框開著時持續顯示，關閉後自動消失
- 可設定半透明、特殊顏色，與場景現有物件明顯區別

操作感類似 GH 在 Bake 前的幾何預覽，對 Rhino 使用者來說是熟悉的互動模式。

---

## 十三、Block 處理方式（待確認）

> 狀態：可行方向已記錄，日後開發時確認細節

### Block 的本質

Rhino Block Instance 的結構：
```
BlockDefinition（定義，存幾何，只有一份）
    ↑
Instance A（UUID-A，位置矩陣）
Instance B（UUID-B，位置矩陣）
Instance C（UUID-C，位置矩陣）
```

Instance 本身不持有幾何，幾何屬於 BlockDefinition。

### 關鍵問題

還原 BlockDefinition 的幾何時，**所有使用該 Block 的 Instance 會同步更新**。這有時是預期行為（例如統一更新某款家具），有時不是（只想還原單一 Instance 的位置）。

### 建議的識別與儲存方式

| 對象 | 識別 key | 儲存內容 |
|------|----------|----------|
| Instance 物件 | `_12_UUID` | 位置矩陣 + BlockDefinition 名稱 |
| BlockDefinition | Block 名稱 | 完整幾何歷史（存於 `block_versions` 表）|

還原時明確區分兩種操作：
- **還原 Instance 位置**：只動位置矩陣，不動幾何定義
- **還原 Block 定義幾何**：更新 BlockDefinition，所有 Instance 同步反映

### 待確認事項
- [ ] 實際專案中 Block 的使用比例與類型
- [ ] 是否需要支援「單一 Instance 例外化」（Explode 後獨立還原）
- [ ] Block 版本歷史是否與 Instance 歷史一併顯示在 LF_History_Viewer

---

## 十四、Cloud Sync（Dropbox）注意事項

專案資料夾存放於 Dropbox，需考慮以下問題：

### `.db` 檔案的同步風險

SQLite 在寫入時會產生 `-wal` 和 `-shm` 暫存檔，Dropbox 可能在寫入過程中同步這些中間狀態，造成資料庫損毀。

**建議對策：**
- 寫入 `.db` 前先在本地暫存，完成後再移至專案資料夾（類似 `_LF_Registry.py` 的 atomic write 機制）
- 或在 Dropbox 設定中將 `Project_Geometry_History.db` 加入**本地排除清單**（不同步至雲端），改以手動備份方式管理

### 檔案大小與同步延遲

`.db` 容量隨版本累積成長，每次 Push 觸發重新上傳可能造成等待。建議：
- 定期執行清理，移除超過上限的舊版本
- 評估是否將 `.db` 排除於 Dropbox 同步範圍之外，僅保留在本機

### `.lock` 檔衝突

`_LF_Registry.py` 已有處理 Dropbox 造成的 stale lock 機制，`.db` 寫入邏輯開發時應沿用相同的防護模式。

---

## 十五、回溯能力的前提條件

### 三層前提

回溯能力需要三個步驟都執行過才成立，缺一不可：

```
LF_Nexus TagTrigger        ← 寫入 _12_UUID（回溯能力的地基）
        ↓
LF_Push_3D_to_JSON         ← 將屬性推送至 Registry.json
        ↓
LF_Geometry_Archive        ← 寫入幾何歷史至 db
```

| 狀態 | 能做什麼 |
|------|---------|
| 只執行過 LF_Nexus | 有 UUID，但無任何歷史記錄 |
| 執行過 Nexus + Push | 有屬性快照，但無幾何歷史 |
| 三個都執行過（至少一次） | 有初始記錄，但尚無可比對版本 |
| 三個都執行過（至少兩次） | 具備完整版本比對與回溯能力 |

### UUID 是整個閉環的核心

沒有 `_12_UUID`，跨版本的物件識別就無法成立——幾何修改後 geom_hash 改變，圖層或名稱異動後其他 key 也會斷鏈，唯有 UUID 能在物件的整個生命週期中保持穩定連結。

**UUID 的連結貫徹整個 LoopFlow 邏輯**，LF_Geometry_History 是這個設計決策在版本追蹤層面的自然延伸。

### `LF_History_Viewer` 前置檢查邏輯

執行時應優先檢查以下條件，不符合則直接提示使用者，而非顯示空選單：

```
選取物件
    ↓
檢查是否有 _12_UUID
    → 無 → 提示「請先執行 LF_Nexus TagTrigger」
    ↓
檢查 db 是否有該 UUID 的記錄
    → 無 → 提示「請先執行 LF_Push_3D_to_JSON（含幾何歷史）」
    ↓
檢查 db 記錄是否 >= 2 筆
    → 只有 1 筆 → 提示「目前只有初始版本，尚無可回溯的版本差異」
    ↓
顯示版次列表
```

---

## 十六、相依關係


```
LF_History_Viewer.py
    ├── _LF_Geometry_Archive.py  （新增）
    ├── _LF_Registry.py          （現有，不修改）
    ├── _LF_Debug.py             （現有，不修改）
    └── _LoopFlow_Config.py      （現有，新增常數）

LF_Push_3D_to_JSON.py
    └── _LF_Geometry_Archive.py  （選擇性呼叫，opt-in）
```

### `_LoopFlow_Config.py` 新增常數

```python
HISTORY_ENABLED       = True
HISTORY_MAX_VERSIONS  = 20
```

---

*本備忘錄由 Claude Sonnet 4.6 協助整理，基於 2026-06-11 發想討論。*
