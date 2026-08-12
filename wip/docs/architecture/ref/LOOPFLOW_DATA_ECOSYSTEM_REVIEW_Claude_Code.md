# LoopFlow 2.0 — 資料生態藍圖：複核、校正與補充

本文件是對 `LOOPFLOW_DATA_ECOSYSTEM.md`（以下稱「藍圖」）的獨立複核。它不取代藍圖，也不改寫藍圖的上位原則；目的是把「程式實際做了什麼」與「藍圖描述的意圖」逐項對齊，指出藍圖的事實錯誤、補上會改變裁決結果的遺漏，並提出對架構本身的意見。

藍圖與 `NEXUS_DICTIONARY_DECISION_MENU.md` 仍是討論主文件。本文件的每一條結論都附程式位置或資料證據，使用者裁決後應把採納的部分回寫到藍圖與 `_LoopFlow_命名與資料契約.md`，本文件即可退為過程紀錄。

## 複核基準

- 日期：2026-08-12
- 複核者：Claude Opus 5（獨立於藍圖作者）
- 程式基準：`codex/v2-dev-entrypoints` / `31d15b6`，`releases/LoopFlow/Python/` 全部 23 支、5,839 行，逐檔完整閱讀
- Dictionary 基準：`%LOOPFLOW_WORKFILES_ROOT%\LoopFlow_Dictionary.xlsx`，以 openpyxl 實際解析欄位、型別、值域與分布
- 交叉比對：`docs/Dictionary_GUIDE_TW.md`、`docs/USER_GUIDE_TW.md`、`_LoopFlow_Config.py`
- 方法：靜態閱讀、全 repo 符號搜尋（確認 producer／consumer 是否真的存在）、Dictionary 統計
- 未執行：Rhino 8 實機操作、舊專案資料抽樣、雙機並行寫入測試。本文件所有「行為」敘述都是讀碼推論，標示為需實機確認者已個別註明
- 未修改任何產品程式碼、Dictionary 或工作檔

## 一、藍圖判斷正確、複核後確認的部分

先確立共識，避免後面的校正被誤讀為否定藍圖：

- 「Dictionary 定義類型、模型保存實例、Registry 發布快照」的分層，與程式實際資料流一致。
- ECO-01～ECO-08 八條原則，複核後**全部同意**，且每一條都能在現行程式找到對應的具體痛點。
- 「保留意圖、翻案做法」的分類方式正確。特別是「Grab／Laser／Index 三種綁定意圖都要保留」這個判斷，從程式看確實是三種不同的使用情境，不能合併。
- 「顏色只作提示、狀態要用正式欄位」（ECO-07）是目前最急迫的一條，複核發現的實證比藍圖描述的更強（見 S-10）。
- 23 支程式的 2.0 責任建議，方向上沒有需要推翻的項目。

## 二、校正：藍圖與程式不符之處

### C-1　`Target_CP` / `Role` 是死資料，Laser 從未讀取

藍圖「Section、Layout 與可編輯圖面」表格描述 `LF_Anchor_Frame.py`：

> 由 Section 幾何與 Text Dot 建 bbox frame，寫 `Target_CP`／`Role`，供 Laser 做 2D→3D 對位

實際上 `LF_Anchor_Frame.py:123-124` 寫入這兩個 key 之後，**全 repo 沒有任何讀取者**。`LF_Tagger_Laser.get_cp_ray_origin()` 找 anchor frame 的方式是（`LF_Tagger_Laser.py:103`）：

```python
container_obj = next((obj for obj in all_objs
    if rs.ObjectName(obj.Id)
    and sec_name in rs.ObjectName(obj.Id).upper()
    and rs.IsCurveClosed(obj.Id)), None)
```

也就是「**ObjectName 字串包含 Clipping Plane 名稱**，且是封閉曲線」。`Target_CP` 完全沒有參與。

影響裁決：藍圖據此認為「已有 CP 對應欄位、只是精度不足」，因而把 View Registration 的工作量估得偏低。實際狀況是**關聯機制目前只有名稱包含比對**，`view_id` 要從零建立；同時任何一條剛好同名的封閉曲線都會被誤認為 anchor frame。

### C-2　Registry 三個區段中，兩個是死的

`_LF_Registry.py:46-54` 建立三個區段，實際使用狀況：

| 區段 | Producer | Consumer | 狀態 |
|---|---|---|---|
| `Objects` | `LF_Push_3D_to_JSON.py:155` | `LF_Infuser_Part.py:258`、`LF_TAG-O.py:161` | 活的 |
| `Layout_Map` | `LF_Tagger_Layout_ID.py:243` | **無** | 只寫不讀 |
| `Tag_Links` | `_LF_Registry.py:199` 定義 `push_tag_links()` | **無呼叫者** | 完全死碼 |

Infuser 要顯示剖面索引的圖號時，不是查 `Layout_Map`，而是在執行當下遍歷 `page_views_all` 找到 `.Target_DV_ID` 所屬頁面，再從 `PageName` 字串現場解析（`LF_Infuser_Part.py:132-152`）。所以 `Layout_Map` 產生後沒有任何用途。

影響裁決：藍圖的 Registry payload 建議（`types / objects / spaces / views / sheets`）方向正確，但沒指出現況已經有兩個空轉區段。2.0 若照現有結構「補齊 schema」，等於把死結構制度化。建議明確記載：**新 Registry 的每個區段都必須有已知 consumer，否則不建立**。

### C-3　`Dict to Layer` 的副作用遠多於「建立圖層」

藍圖描述 `LF_Nexus.py` 的 Dict to Layer 為「讀取 LoopFlow_Dictionary.xlsx 並建立 M3D layer 結構」。實際 `func_dict_to_layer()` 每次執行還會：

1. **為每個 layer 建立同名 Rhino Material**（PhysicallyBased），並設 `RenderMaterialIndex`（`LF_Nexus.py:779-791`）。以目前 92 列計，會產生 92 個材質。
2. **為每一列在原點附近畫一條參考線**：`rs.AddLine([0, y, 0], [-25, y, 0])`，命名為 `DNA_REF_<_04值>`，並把整列 Dictionary 值寫成該線的 UserText（`LF_Nexus.py:794-805`）。
3. 把每一列的值寫成 **layer 的 UserString**（`LF_Nexus.py:775-777`）——這是 `Layer to Dict` 反向匯出的唯一來源。
4. 執行 `rs.ZoomExtents`（`LF_Nexus.py:807`），改變使用者視圖。

第 2 點沒有去重：圖層存在時不會重建，但**參考線每次執行都會新增一批**。連跑三次就有 276 條線疊在原點旁。這些線是 Curve（type 4），不在 `VALID_GEOM_TYPES` 內，所以不會被 TagTrigger 或 Push 收錄，屬於純視覺殘留——但它們帶著完整的 Dictionary UserText，容易被誤認為資料物件。

影響裁決：藍圖把 Dict-to-Layer 歸為「Type Catalog → 模型 layer」的單純動作。實際上它同時是**材質產生器**、**參考幾何產生器**與**layer UserString 寫入器**。2.0 必須逐項裁決去留，特別是 `DNA_REF_` 線的用途（推測是給使用者目視對照與取樣，需向使用者確認）。

### C-4　藍圖與決策菜單內部的欄名不一致

`NEXUS_DICTIONARY_DECISION_MENU.md` 的「實際 Dictionary 快照」正確指出欄名為中文（`_01_空間名稱`），但同一份文件的「18 欄的現行所有權」表卻使用英文欄名（`_01_Space Name`、`_03_ID Number`）。實際 Dropbox 檔案的 18 個欄名全部是中文：

```
__Rhino Layer   _01_空間名稱   _02_建構狀態   _03_ID編號     _04_ID名稱
_05_寬度W       _06_深度D      _07_高度H      _08_單位       _09_實作數量
_10_高程基準    _11_高程計算   _12_UUID       _13_備註
_CB.01_板材類型 _CB.02_長度L   _CB.03_寬度W   _CB.04_厚度T
```

值得注意的是 `_LoopFlow_Config.py:73` 的 `WHITE_LIST` 已經是中文 key（`_02_建構狀態`、`_09_實作數量`、`_13_備註`），但 repo release 內附的 Dictionary 是英文版。也就是**現行 config 與現行 release Dictionary 本身就不匹配**，程式之所以還能運作，只是因為所有比對都退化成前四碼 prefix（`wl[:4]`，`LF_Nexus.py:419`）。這正是 CF-02 的根因，也解釋了為什麼 prefix 掃描無法輕易移除。

## 三、補充：藍圖未涵蓋、且會改變裁決的事實

### S-1　`_08_單位` 不是模型單位，是估算單位——ND-04 的題目要拆開

實測 `_08_單位` 的完整值域（92 列）：

| 值 | 筆數 | 量綱 |
|---|---|---|
| `組` | 34 | 計數 |
| `坪` | 21 | 面積 |
| `cm` | 17 | 長度 |
| `才` | 8 | 面積（台制） |
| `台` | 4 | 計數 |
| `mm` | 3 | 長度 |
| `m3` | 2 | 體積 |
| `座` / `片` / `樘` | 各 1 | 計數 |

`docs/Dictionary_GUIDE_TW.md:66` 明確定義：「數量計算單位，影響工程估算報表」。它與 `_09_實作數量` 是一組 BOM 欄位，**與 Rhino 文件單位是兩件完全不同的事**。

決策菜單的 ND-04「模型單位：A. 所有 LoopFlow 專案固定 cm」把兩者混為一談。建議拆成兩題：

- **ND-04a｜模型文件單位**：實測為 cm（見 S-2）。要決定的是「是否強制、非 cm 時擋下或換算」。
- **ND-04b｜`_08` 估算單位**：要決定的是允許值清單、每個值的量綱分類，以及 `_09` 的數量由誰計算、依據哪個幾何量（長度取哪一邊？面積取哪一面？）。這是 `_09` 至今沒有 producer 的真正原因——**沒有單位到幾何的映射規則，就寫不出計算式**。

### S-2　模型單位實測為 cm，但程式從不驗證

證據鏈（全部來自使用者可見的提示字串與預設值，不是推測）：

| 位置 | 內容 |
|---|---|
| `LF_2D_DW_Gen.py:488` | `"Total length {:.1f} cm. Enter number of splits"` |
| `LF_2D_DW_Gen.py:451` | 牆厚預設 `12.0`（12 cm） |
| `LF_2D_DW_Gen.py:454,459` | 門扇 `90.0`、淋浴門 `65.0` |
| `LF_2D_Shelf_Gap.py:28,31` | `"board thickness (cm)"` 預設 `1.8`；`"target spacing (cm)"` 預設 `30.0` |
| `LF_Cabinet_Suite.py:317` | 側板 `1.8`、上帽 `6.0`、踢腳 `12.0`、背板 `3.0` |
| `LF_Cabinet_Suite.py:464,466` | 同樣標示 `(cm)` |

**單位是 cm 可以視為確立**。但全 repo 只有一處讀取 `sc.doc.ModelAbsoluteTolerance`（`LF_Tagger_Laser.py:112`），**沒有任何一處讀取 `ModelUnitSystem`**。所有帶量綱常數都是裸浮點數。

在 cm 前提下重新解讀幾個關鍵常數，會發現它們的實際行為與直覺不同：

| 常數 | 位置 | cm 下的實際意義 | 評估 |
|---|---|---|---|
| `+200.0` 候選聚類 | `LF_Tagger_Laser.py:243` | **2 公尺**內的命中都列為候選 | 過寬。射線穿過整個房間深度的物件都會進候選清單 |
| `2000.0` boundary 搜尋 | `LF_Nexus.py:211` | **20 公尺** | 等同不限制，實質上「取全案最近的樓層線」 |
| `50.0` 同距容差 | `LF_Nexus.py:219` | 50 公分 | 合理 |
| `200.0` slab 判定 | `LF_Nexus.py:226` | 2 公尺 | 樓層線往上 2m 內視為同層，一般樓高下合理 |
| `OFFSET_VAL` 預設 `50.0` | `LF_Anchor_Frame.py:59` | 50 公分外擴 | 合理 |
| `±1.0` 各處容差 | `LF_Nexus.py:227-231` | 1 公分 | 對 cm 模型偏緊，樓板厚度誤差易失敗 |

建議：**ECO 層級新增「量綱」原則**（見 V-1），並在 2.0 啟動時驗證文件單位，把上述常數改為具名、標註單位、可調的規則參數。

### S-3　`_03_ID編號` 已經是「類別碼-序號」複合鍵，ND-19 的答案在資料裡

實測 92 列 `_03` **全部**符合 `^[A-Za-z]+-\d+$`，無例外。12 個前綴與 12 個 layer 頂層群組**完全一一對應**：

| Layer 頂層 | `_03` 前綴 | 列數 |
|---|---|---|
| `00_STR_結構` | `EX` | 7 |
| `01_Ceiling_天花` | `CL` | 7 |
| `02_Wall_牆面` | `WL` | 17 |
| `03_Floor_地坪` | `FL` | 10 |
| `04_CB_櫃體` | `CB` | 7 |
| `05_LT_燈帶` | `LS` | 3 |
| `06_EL_電控系統` | `EL` | 7 |
| `07_MEP_空調機電` | `MP` | 7 |
| `08_SAN_衛浴設備` | `SA` | 11 |
| `09_EQP_專用設備` | `EQ` | 9 |
| `10_FP_消防系統` | `FP` | 6 |
| `20_DW` | `DW` | 1 |

而 `LF_Infuser_Part.py:196` 正是以第一個 `-` 拆兩段：

```python
mat_key, mat_val = raw_id.split("-", 1) if "-" in raw_id else (raw_id, "")
```

分別寫進 Tag 的 `attr_mat_key` 與 `attr_mat_val`。所以 Tag 上顯示的兩段文字就是「**類別碼**」與「**序號**」。

因此 ND-19 不需要再問「目前 Tag 上兩段文字各代表什麼」——資料與程式已經一致回答了。建議直接裁決為：2.0 定義 `type_category`（列舉，12 個值）與 `type_sequence`（整數）兩個獨立欄位，`_03` 的組合字串降為顯示格式。這同時解決 CF-22（ID 內含連字號會被誤拆），因為不再需要在執行期拆字串。

**連帶發現的命名空間衝突**：`MP` 同時是 `07_MEP` 的類別碼，與 2D 圖層前綴（`MP_5_DW`、`MP_6_DW`、`MP_7_ORBIT_DW`、`MP_4_FURN`、`MP_Defpoints`，`_LoopFlow_Config.py:54-67`）。2.0 的命名契約必須把「類型類別碼」與「2D 圖層前綴」列為不同命名空間，否則未來自動化容易互相誤判。

### S-4　`_10_高程基準` 同時是「幾何規則」與「顯示標籤」，兩者要分開定義

實測分布與 layer 群組高度相關，不是隨意填的：

| basis | 筆數 | 主要出現位置 |
|---|---|---|
| `BH` | 50 | 02_Wall（15）、04_CB（7）、09_EQP（8）等 |
| `TH` | 17 | 03_Floor **全部 10 列**、08_SAN（4） |
| `BC` | 16 | 06_EL **全部 7 列**、08_SAN（4）、10_FP（3）、07_MEP（2） |
| `CH` | 8 | 01_Ceiling **全部 7 列** + 02_Wall 扶手 1 列 |
| `TH/BH` | 1 | 00_STR 樓板 |

程式（`LF_Nexus.py:244-247`）只有三種幾何規則：

```python
calc_z = obj_bh                                    # 預設：bbox 底
if basis == "TH": calc_z = obj_th                  # bbox 頂
elif basis == "BC" and rs.IsBlockInstance(obj_id):
    calc_z = rs.BlockInstanceInsertPoint(obj_id).Z # block 插入點
```

而 `LF_Infuser_Part.py:203` 把 basis 原字串直接寫進 Tag 的 `attr_ch_key`：

```python
rs.SetUserText(obj_id, "attr_ch_key", h_basis)
```

所以更精確的描述是：**basis 同時承擔幾何取值規則與 Tag 上的顯示標籤**。據此重新理解決策菜單的 CF-06：

- **`CH` 的幾何等同 `BH`，但顯示為 `CH`。**對天花板而言，使用者要標的天花高度本來就是天花物件的**底面**高度。所以這**可能是刻意的標籤差異，不是未實作的演算法**。`01_Ceiling` 7 列全用 CH 這件事支持這個解讀。需向使用者確認，但不應預設為 bug。
- **`BC` 只在 block instance 成立**，靠「這些設備圖層都放 block」的未強制約定。實測 `06_EL`（開關、插座、感應器）全用 BC——這些確實在實務上以 block 建模，且標註高度習慣量到面板中心。但若使用者用非 block 幾何建了一個插座，程式會**靜默退回 BH**，Tag 仍顯示 `BC`，數值卻是底面高度。這是**顯示與實際不一致**的靜默錯誤。

建議 ND-11 改成裁決一張表，每個 basis 明確定義三件事：

```
basis_id      顯示標籤    幾何規則              前置條件（可驗證）
BH            BH          bbox 最低點 Z         無
TH            TH          bbox 最高點 Z         無
CH            CH          bbox 最低點 Z         物件屬天花類型
BC            BC          block 插入點 Z        物件必須是 block instance ← 目前未檢查
TH/BH         TH / BH     取絕對值較小者顯示    無
```

前置條件不成立時應**明確報錯**，而不是退回預設。

### S-5　TagTrigger 的 UUID 重建會切斷既有 Tag，且無法回溯

這是複核中發現**最容易造成不可逆資料損失**的路徑。

`check_global_uuids()`（`LF_Nexus.py:293-311`）掃描 `rs.AllObjects(True, True)`——**全模型，包含非 M3D 物件**。發現重複時：

```python
if u_clean in used_uuids:
    duplicate_objs.add(o)                    # 後發現的
    duplicate_objs.add(used_uuids[u_clean])  # 先發現的，也一起加入
```

**兩個物件都進入 `duplicate_objs`。**接著 TagTrigger（`LF_Nexus.py:376-382`）：

```python
needs_new_uuid = (not current_uuid or not current_uuid.strip()
                  or guid in duplicate_objs
                  or guid in invalid_uuid_objs)
if needs_new_uuid:
    rs.SetUserText(guid, "_12_UUID", str(uuid.uuid4()).upper())
```

實際後果：

1. 使用者複製一個已經被 Tag 標註的物件（Rhino 複製會連 UserText 一起複製）。
2. 下次跑 TagTrigger，原件與複本**兩者的 UUID 都被換成新的**。
3. 原本正確綁定的 Tag，其 `Source_UUID` 在 Registry 裡再也找不到 → Infuser 標紅為 broken。
4. 完成訊息只顯示「新產生／修復 N 個 UUID」（`LF_Nexus.py:429`），**不列出是哪些物件、原 UUID 是什麼**，沒有任何回溯資訊。

此外 scope 不一致（CF-12 的具體形式）：偵測掃全模型，寫入只處理 M3D。一個 M2D 或未分類物件若持有與 M3D 物件相同的 UUID（例如從 3D 複製貼到 2D 參考），會導致該 M3D 物件的 UUID 被重建。

建議：把「重複 UUID 處理」提升為與 Registry P0 同級的安全項目。最低要求是——先產生報告、保留其中一個、列出將被影響的 Tag、由使用者確認後才執行，並保留新舊 UUID 對照供 Tag 重新指向。

### S-6　Infuser／TAG-O 會在 2D 文件旁自建空 Registry，並把全部 Tag 標紅

`RegistryCenter.__init__` 呼叫 `_ensure_registry_exists()`（`_LF_Registry.py:42-55`），檔案不存在就**直接寫入空骨架**。這是 constructor 產生寫入副作用的具體案例。

而所有取得專案目錄的函式都是取「**當前作用中文件**」的資料夾：

```python
def get_project_dir():
    doc = Rhino.RhinoDoc.ActiveDoc
    return os.path.dirname(doc.Path)
```

（`LF_Infuser_Part.py:72-75`、`LF_Infuser_All.py:39-44`、`LF_Push_3D_to_JSON.py:60-65`、`LF_TAG-O.py:316`）

組合後的失敗情境：**若 2D.3dm 與 3D.3dm 不在同一個資料夾**（或使用者把 2D 另存到別處），在 2D 執行 Infuser 會：

1. 在 2D 旁邊建立一份**空的** `Project_Registry.json`
2. `db = json_data.get("Objects", {})` 得到空字典
3. 每個 Tag 都走 broken 分支：塗紅、欄位寫成 `?`（`LF_Infuser_Part.py:219-230`）
4. 訊息只說「source lost or JSON not re-pushed」

使用者看到的是「全部圖說壞掉」，實際原因是路徑。而且原本的 Tag 顯示值已經被 `?` 覆蓋，重跑正確的 Infuser 才能救回。

**重要推論：「3D 與 2D 必須同資料夾」是整套系統的隱性硬需求**，目前只靠 Dropbox 工作資料夾的擺放慣例維持（實測工作檔目錄確實是 `LoopFlow_3D.3dm`、`LoopFlow_2D.3dm`、`LoopFlow.rws` 同層）。

這一點對 2.0 是好消息：`LOOPFLOW_WORKFILES_ROOT` + `exchange/` 的設計正好可以把這個隱性需求變成**明確契約**——Registry 位置由專案根目錄決定，不再由「當前開啟的是哪個檔案」決定。建議把這條寫進藍圖的資料實體表（Project 的 `project_id` 對應工作檔根目錄，而非資料夾名稱猜測）。

### S-7　Laser 的 2D→3D 對位基準會隨使用者正常編輯而漂移

藍圖說 Laser 用「bbox 猜測」，精度不足。複核後認為問題比這更嚴重：**對位基準不是固定的，它每次執行都重新計算，而且會被使用者的正常編輯改變**。

`get_cp_ray_origin()`（`LF_Tagger_Laser.py:110-140`）的實際做法：

1. **3D 側基準**：把當下**所有可見 brep** 與 clipping plane 求交（`Intersection.BrepPlane`），把所有交線轉到 CP 平面座標，取聯集 bbox 的中心（`:113-136`）。
2. **2D 側基準**：取 anchor frame 範圍內**所有非 reference 的 curve / hatch**，取聯集 bbox 中心；有 hatch 就只用 hatch，沒有才用 curve（`:126-135`）。
3. 計算滑鼠點相對 2D 中心的位移，加到 3D 中心上，得到射線起點（`:138-140`）。

因此：

- 在剖面圖上**新增一條線、刪一個 hatch、把某條線拉長** → 2D bbox 中心移動 → 之後所有 Laser 綁定的落點偏移。
- **3D 模型任何改動**（新增一道牆、隱藏一個圖層）→ 3D 交線 bbox 中心移動 → 同樣偏移。
- 偏移量沒有任何紀錄，使用者只會發現「Laser 抓錯物件」，無從判斷偏移多少。

另外這也是效能問題：每次綁定都要對**全模型**做一次 brep–plane 交集。

這是 ECO-03／ECO-04 需要「正式 view transform」的最強論證，建議直接寫進藍圖的論證段落——Clipping Plane 本身已經帶有 `Plane`，Detail View 也有 `PageToWorldTransform`（`LF_Tagger_Laser.py:227` 已經在用）。所需資訊都存在，缺的是**把它固化成 View Recipe 保存下來**，而不是每次重算。

### S-8　Extract 不具冪等性，且會改動圖層鎖定狀態

`LF_Extract_CP.run_kali_distiller()` 每次執行都 `rs.CopyObject()` 一份到 `Extract::*`（`:124,131,150`），**不記錄來源、不比對、不去重**。連續執行兩次就得到兩份完全重疊的線，之後無法分辨哪一份是哪次產生的，也無法只刪除其中一份。

附帶問題：

- `ensure_layer()`（`:47-52`）對目標圖層執行 `rs.LayerLocked(full_path, False)` **解鎖且不還原**。使用者刻意鎖定的 Extract 圖層會被靜默解鎖。
- `Extract` 根圖層**不在 `M2D::` 之下**（`_LoopFlow_Config.py:43`），與 `M2D::Anchor_Frame`（`:48`）的命名規則不一致。同一個 2D 文件出現兩套根命名。
- Curve 依顏色 hex 自動分層（`Extract::Curve_#RRGGBB`，`:143`），圖層數量隨來源顏色種類無上限增長。

建議：Drawing lifecycle 的**第一個可測需求**應該是「重跑時能辨識前次產出，並讓使用者選擇取代、新增或略過」，而不是先做 `generated / modified / stale` 六種狀態。狀態機沒有冪等性作基礎會無法實作。

### S-9　Duplicate Layout 會複製「身分」，且產生靜默錯誤

`duplicate_layout()`（`LF_Duplicate_Layout.py:100-161`）用**系統剪貼簿**整頁複製：

```python
Rhino.RhinoApp.RunScript("_-CopyToClipboard 0,0,0", True)   # :127
...
Rhino.RhinoApp.RunScript("_-Paste 0,0,0", True)             # :146
```

三個後果：

1. **覆蓋使用者的剪貼簿內容**，且不還原。
2. 複製後的 Tag 保留原 `Source_UUID` → 指向同一個 3D 物件。這通常是合理的（同一個物件在不同圖上標註）。
3. 複製後的 **Index Tag 保留原 `.Target_DV_ID`** → 指向**來源頁**的 Detail View。新頁上的剖面索引會顯示來源頁的圖號，而 Infuser 會判定它「綁定正常」（找得到該 DV）→ **不會標紅**。

第 3 點是**靜默錯誤**：圖面看起來完全正常，索引卻指向錯誤的頁。這比 broken 更難發現，因為現有的健康檢查機制設計上抓不到它。

藍圖建議「複製時建立新 `sheet_id`／`tag_id`」方向正確；補充的是——**Index Tag 的 `.Target_DV_ID` 在複製時必須失效或重新指向**，不能沿用，且複製動作本身需要一個「這些綁定需要重新確認」的產出清單。

### S-10　TAG-O 的判定完全建立在物件顏色上，且 Infuser 會破壞使用者顏色

藍圖 ECO-07 說「顏色只作視覺提示」。複核發現現況比這更極端：**顏色是 TAG-O 的唯一真相來源**。

`check_tag_status()`（`LF_TAG-O.py:112-122`）：

```python
if (obj.Attributes.ColorSource != Rhino.DocObjects.ObjectColorSource.ColorFromObject):
    continue                                    # 非物件色 → 直接跳過，視為正常
c = obj.Attributes.ObjectColor
if _rgb_match(c, WARNING_COLOR):   results.append((u"Unbound", ...))
elif _rgb_match(c, BROKEN_COLOR):  results.append((u"Broken",  ...))
```

它完全不讀 `Source_UUID`、不查 Registry，只比對 RGB。因此：

- 使用者若曾手動把某個 Tag 設成 `(255,130,46)` → **誤報為 Unbound**。
- 使用者若把一個真正 broken 的 Tag 改成自訂顏色 → **漏報**。
- 必須先跑 `Infuser_All` 才有意義（檔頭已註明），形成「**先改資料才能檢查資料**」的倒置順序——檢查工具無法在不修改文件的前提下執行。

而 `_clear_warning_color()`（`LF_Infuser_Part.py:87-91`）：

```python
rh_obj.Attributes.ColorSource = Rhino.DocObjects.ObjectColorSource.ColorFromLayer
```

把 ColorSource 設回 ByLayer，**清掉使用者原本設定的物件顏色且不還原**。使用者對 Tag 的任何顏色自訂，在下次 Infuser 後消失。

**空間覆蓋檢查的另一個問題**：`check_space_coverage()` 是把 boundary 曲線的 `Space_Name` UserText（`LF_TAG-O.py:142`）與 Registry 內物件的 `_01_` 值（`:197`）**做字串值比對**。兩邊任一改名、或改名後未重跑 TagTrigger，覆蓋率就靜默失準。這是 CF-08「兩套 key」的具體後果——不只是命名不一致，而是**跨文件的關聯建立在可變字串上**。

### S-11　Cabinet 的圖層依賴與方向語意

三個獨立問題：

**(a) 產出圖層與判定圖層不一致。**`run_cabinet_gen()` 明確在**當前圖層**產生幾何（`LF_Cabinet_Suite.py:439` 的完成訊息即為 "Objects generated in the current layer"），但：

- `run_bom_updater()` 只處理 `04_CB` 圖層上的物件（`:528`、`:579`）
- Nexus TagTrigger 對非 `04_CB` 圖層**一律把 `_CB.*` 寫成 `-`**（`LF_Nexus.py:417`）

所以在錯誤圖層產生的櫃體，`_CB` 資料會先被 Nexus 清空，全程無警告。

**(b) 方向語意被排序丟棄。**`write_cabinet_tags()`（`:78`）：

```python
dims = sorted([abs(d) for d in dims])
T, W, L = dims[0], dims[1], dims[2]
```

但呼叫端 `make_part()`（`:299-315`）其實**已經知道真實方向**——它有 `true_w` / `true_h` / `true_d` 三個具名參數。資訊在傳入 `write_cabinet_tags()` 的瞬間被 `sorted()` 抹平。

這對 ND-24 是好消息：建議 A（依 panel local frame）**不需要重新推導方向**，現有程式已經持有這些資訊，只要不排序即可。

**(c) BOM Updater 會覆蓋使用者更正過的板件名稱。**`:642`：

```python
if (not part_name) or (part_name in standard_names):
    part_name = guessed_name
```

只要既有名稱屬於 `standard_names`（14 個標準名），就會被幾何猜測值覆蓋。使用者若把系統誤判的 `Shelf` 手動改成正確的 `Top_Board`，下次跑 BOM Update 又會被改回猜測結果。只有取非標準名稱（如自訂字串）才能保住。

猜測本身依賴一串量綱常數：`2.0`（同高判定）、`25.0`（矮板件）、`1.2`（薄板）、`10.0`（玻璃鄰近）、`0.75`（體積比）、`0.05`（尺寸容差）、`+0.2`（render gap 補正，`:645-666`）。這些在 cm 下大致合理，但沒有任何一個有名字或說明。

### S-12　設定來源不只一個，且 fallback 值互相衝突

除 `_LoopFlow_Config.py` 外，還有專案目錄下的 **`NamingRules_Config.json`**（`_LF_NamingRules.py:36`），控制 `separator`、`baseline_mark`、`dwg_no_format`、`ref_id_format`、`prefix_pattern` 五項。2.0 的「設定唯一來源」原則必須涵蓋這第二個檔案，不能只盤點 `config.py`。

另外 `_LF_Registry.py:22-27` 的 import fallback：

```python
except Exception:
    LOCK_TIMEOUT       = 8.0     # config 是 20.0
    STALE_LOCK_SECONDS = 120.0   # config 是 30.0
```

fallback 與 config 不一致，且 fallback 只在 import 失敗時生效。**實際生效值不可預測**，取決於 `sys.path` 狀態與各腳本的 reload 時機（部分腳本用 `importlib.reload(_CFG)`，部分只 `from ... import`）。這使得「調整 timeout」這個動作無法驗證是否生效。

### S-13　死設定與死欄位清單

盤點時應直接移除，不要當成需要保留的契約：

| 項目 | 位置 | 狀態 |
|---|---|---|
| `CEILING_KEYWORDS` | `_LoopFlow_Config.py:134` | 註解說給 `LF_2D_DW_Gen` 用，**無任何 import 或使用** |
| `LAYER_CABINET_NAME` | `_LoopFlow_Config.py:38` | 只被 `LF_Cabinet_Suite.py:25` import，函式本體未使用 |
| `Role` / `Target_CP` | `LF_Anchor_Frame.py:123-124` | 只寫不讀（見 C-1） |
| `Tag_Links` + `push_tag_links()` | `_LF_Registry.py:53,199` | 無呼叫者（見 C-2） |
| `Layout_Map` | `_LF_Registry.py:52`、`LF_Tagger_Layout_ID.py:243` | 只寫不讀（見 C-2） |
| `WHITE_LIST` 的 `_12_UUID` | `_LoopFlow_Config.py:73` | 冗餘——`_12_` 在迴圈更早處已 `continue`（`LF_Nexus.py:402`） |
| 硬編碼 debug 路徑 | `LF_Cabinet_Suite.py:703` | `C:\_RH_Tools\cursor_LF_debug_log.txt`，與實際 log 位置不符 |

## 四、18 欄的 Producer／Consumer 實測對照

此表可直接併入 `_LoopFlow_命名與資料契約.md` 的依賴盤點，回答 ND-03（欄位所有權）。「Consumer」欄只列**真正讀取該值並產生行為**的程式，不含「被寫進 Registry」這種純儲存。

| 欄位 | Producer | 寫入時機與規則 | 實際 Consumer | 備註 |
|---|---|---|---|---|
| `__Rhino Layer` | Dictionary（人工） | — | Nexus 建層／比對、Layer-to-Dict | 相對路徑，程式補 `M3D::` |
| `_01_空間名稱` | Nexus `get_space_name_at_object()` | TagTrigger 每次覆寫 | **TAG-O 空間覆蓋** | bbox 底面中心，**第一個**命中 boundary；無命中為 `EXT` |
| `_02_建構狀態` | Dictionary 預設 | 僅當物件值為空／`-` | 無 | WHITE_LIST 保護；7 列 Existing 全在 `00_STR` |
| `_03_ID編號` | Dictionary | TagTrigger 每次覆寫 | **Infuser**（拆兩段）、Laser 顯示、Push 過濾 | 值為 `-` 時 Push 略過該物件 |
| `_04_ID名稱` | Dictionary | TagTrigger 每次覆寫 | **Infuser** → `attr_note`、Laser 候選清單 | 92 列中 85 個相異，**非唯一** |
| `_05_寬度W` | Nexus `get_dimensions()` | TagTrigger 每次覆寫 | **無** | 一般物件用 World bbox 對角距；block 用 definition bbox × xform 向量長 |
| `_06_深度D` | 同上 | 同上 | **無** | 同上 |
| `_07_高度H` | 同上 | 同上 | **無** | 同上 |
| `_08_單位` | Dictionary | TagTrigger 每次覆寫 | **無** | 估算單位，非模型單位（S-1） |
| `_09_實作數量` | **無 producer** | 僅當物件值為空／`-` 時寫 `-` | **無** | 指南稱由 Nexus 計算，程式不存在（CF-04） |
| `_10_高程基準` | Dictionary | TagTrigger 每次覆寫 | **Nexus 計算 `_11`**、**Infuser** → `attr_ch_key` | 規則＋標籤雙重責任（S-4） |
| `_11_高程計算` | Nexus `get_elevation_value()` | TagTrigger 每次覆寫 | **Infuser** → `attr_ch_val` | 顯示字串（`+120.0` / `±0` / `+10.0 / -`），非數值 |
| `_12_UUID` | Nexus | 空值／重複／格式錯誤時重建 | **Push / Grab / Laser / Infuser / TAG-O** | 重建會切斷 Tag（S-5） |
| `_13_備註` | Dictionary 預設 | 僅當物件值為空／`-` | 無 | 91 列為 `我是備註，UCCU`；1 列為 `20_DW` 操作說明 |
| `_CB.01_板材類型` | Cabinet_Suite | 產生時／BOM Update | 無 | 非 `04_CB` 圖層被 Nexus 清為 `-` |
| `_CB.02_長度L` | 同上 | 同上 | 無 | 由三邊 `sorted()` 取最大（S-11b） |
| `_CB.03_寬度W` | 同上 | 同上 | 無 | 取中間值 |
| `_CB.04_厚度T` | 同上 | 同上 | 無 | 取最小值 |

**關鍵觀察：18 欄中有 8 欄（`_02`、`_05`、`_06`、`_07`、`_08`、`_09`、`_13`、`_CB.*`）目前沒有任何下游消費者**，只是被 Push 原樣寫進 Registry。這是 ND-18 選 A（版本化 typed schema ＋ 明確 extension 區）的直接證據：現行 Registry 已經把大量無人消費的欄位變成事實上的公開 API。

### 非 Dictionary 的持久化 key

| key | 寫在哪 | Producer | Consumer |
|---|---|---|---|
| `Space_Name` | boundary 封閉曲線 | Nexus Boundary Setter | Nexus 空間判定、**TAG-O 覆蓋檢查**、`_check_level_boundaries` |
| `Source_UUID` | Tag Block | Grab / Laser | **Infuser**、TAG-O |
| `NAME_PARSED`（哨兵值） | Tag Block 的 `Source_UUID` | Grab | Infuser（走 `.Auto_*` 分支） |
| `.Auto_DW_ID` / `.Auto_Item_Key` / `.Auto_Item_Val` / `.Auto_Item_Note` | Tag Block | Grab（解析 block 名稱） | Infuser |
| `.Target_DV_ID` | Index Tag | Tagger_Index | **Infuser**（遍歷所有頁找 DV） |
| `Category` / `REF_ID` | Tag Block | Index、Infuser、Layout_ID | Tag 顯示 |
| `DWG_NO` / `DWG_NAME` | 圖框 Block | Layout_ID | 圖框顯示 |
| `attr_ch_key` / `attr_ch_val` / `attr_mat_key` / `attr_mat_val` / `attr_note` / `attr_dw_id` / `attr_item_*` | Tag Block | Infuser | Tag 內部文字欄位 |
| `Role` / `Target_CP` | Anchor Frame | Anchor_Frame | **無**（C-1） |
| 鎖定 key（含 `LOCK` / `不更新` / `NoUpdate`） | Tag Block | 人工 | Infuser、Grab、Laser、Index |

鎖定 key 的辨識規則三支程式不一致：`LF_Infuser_Part.py:112` 與 `LF_Tagger_Grab.py:49`、`LF_Tagger_Index.py:156` 用 `"LOCK" in k.upper() or "不更新" in k`；`LF_Tagger_Laser.py:202` 用 `"LOCK" in k.upper() or "NoUpdate" in k`（大小寫敏感，且不認「不更新」）。**同一個 Tag 在 Laser 眼中可能沒鎖，在 Infuser 眼中卻是鎖的。**這是 ND-20 選 A 的直接證據。

## 五、對藍圖本身的觀點

### V-1　ECO 原則建議補三條

現有 ECO-01～08 我全部同意。建議補上三條，都是複核中反覆出現的根因：

| ID | 原則 | 理由 |
|---|---|---|
| **ECO-09** | 量綱明確：模型文件單位是啟動驗證項；所有帶量綱常數必須具名並標註單位；估算單位（`_08`）與模型單位是不同概念，不得互相推導 | S-1、S-2；目前十餘個裸浮點數常數決定了空間、高程、候選判定的結果 |
| **ECO-10** | 冪等性：每個會產生幾何或改寫資料的指令，都必須定義「重跑會發生什麼」，且能辨識前次產出 | S-8（Extract 重複複製）、C-3（DNA_REF 線累積）、S-9（Duplicate 複製身分）目前三者皆無 |
| **ECO-11** | 識別碼的產生與變更必須可追溯：任何自動重新產生 ID（尤其 UUID）都要先報告、可預覽、可回復 | S-5；這是目前唯一會造成不可逆資料損失的路徑 |

### V-2　工作鏈少了一個實際存在的階段

藍圖的 W1–W10 中，W5（建立 View）到 W6（圖面化）之間，實際還有一個必要動作：**Anchor／對位註冊**（`LF_Anchor_Frame`）。

它目前是**唯一**把 2D 圖面座標與 3D View 關聯起來的機制，也是 Laser 綁定的硬前置條件——沒有 anchor frame，`get_cp_ray_origin()` 直接回傳 `None`，Laser 顯示「無法定位」。

藍圖把它歸入 View Registration 是正確的，但工作鏈表格沒有對應階段，容易讓人以為「Section 生成後就能直接 Laser」。建議在 W5 的「前進條件」明列：**View 必須註冊可用且穩定的座標轉換**（而非每次重算，見 S-7）。

### V-3　Health Engine 的十種狀態，目前只有四種能可靠判定

藍圖列出 10 種 health state。以現有資料鏈能**可靠判定**的只有 4 種：

| 可判定 | 依據 |
|---|---|
| `unbound` | `Source_UUID` 為空 |
| `orphaned` | `Source_UUID` 不在 Registry `Objects` |
| `manual_locked` | 鎖定 key（需先統一，見 ND-20） |
| `stale_data` | 需要 revision——**目前不存在**，但只要 Registry 加上 revision 即可 |

其餘 6 種都需要現在不存在的欄位：`ambiguous` 需要候選集合的持久化、`view_missing` 需要 `view_id`、`drawing_stale` 需要 `drawing_id` + 來源 revision、`template_outdated` 需要 `template_version`、`schema_mismatch` 需要 `schema_version`、`healthy` 的嚴格定義需要以上全部。

建議在藍圖的 Health 表格加一欄「**前置資料需求**」，並標明哪些屬於 2.0 第一階段、哪些延後。否則 2.0 一開始就承諾了無法判定的狀態，實作時只能用顏色或猜測補——正好回到現在的問題。

### V-4　建議把「23 支程式」表格改成以資料所有權分層

現行分組（Foundation／Dictionary／Section／Tag／Cabinet）是按檔案來源分的，這對「理解現況」很好，但無法直接導出契約。

建議在藍圖保留現有表格的同時，補上以「**誰是某個欄位的唯一 producer**」為軸的視角——也就是本文件第四節那張表。它可以直接回答 ND-03，並讓「哪些欄位其實沒有 producer」（`_09`）與「哪些欄位沒有 consumer」（8 欄）一眼可見。

### V-5　關於「乾淨重建」的一點提醒

複核後我支持「乾淨重建、一次切換」的裁決。但有一個現實風險值得先寫下來：

現行 23 支程式裡，**真正承載不可替代知識的是那些「看起來很醜」的部分**——高程判定的樓板搜尋、Laser 的鏡射與 Y 軸反轉、Cabinet 的板件猜測與 render gap 補正、DW 的 11 種門窗幾何。這些都是從實際專案長出來的，且大多沒有文件。

乾淨重建若只帶走「架構」而不帶走這些規則，2.0 會在實機測試階段一次性遇到大量「以前可以、現在不行」的回歸，而那時已經沒有舊程式可對照（因為新舊不相容）。

建議：在 S2（契約）階段就把這些**幾何與判定規則**單獨抽成一份「現行規則清單」，逐條記錄「規則、常數、單位、來源推測、是否保留」。這份清單不需要使用者裁決語意，但需要在對應 feature 重建前完成，並作為 fixture 的來源。這比「等到 S5 端到端測試才發現」便宜得多。

## 六、建議的裁決順序調整

決策菜單目前分三輪。根據複核結果，建議調整優先序：

**先處理（不需使用者裁決，屬安全問題）**

1. **UUID 重建的資料損失路徑**（S-5）——與 Registry P0 同級。
2. Registry 的 constructor 副作用與專案目錄解析（S-6）——`LOOPFLOW_WORKFILES_ROOT` 已經定案，可直接落實。
3. 死設定與死欄位清除（S-13）。

**第一輪可以立即定案的（資料已給出答案）**

- **ND-19**（`_03` 語意）→ 建議直接定為兩欄位（S-3）。
- **ND-20**（Tag 鎖定）→ 三支程式規則不一致已是明確 bug，選 A。
- **ND-24**（Cabinet 方向）→ 現有程式已持有 local frame 資訊，選 A 成本比預期低（S-11b）。
- **ND-04** → 拆成 04a（模型單位＝cm）與 04b（估算單位規則）（S-1）。

**需要使用者實際回答語意的（AI 無法代答）**

- **ND-11**：`CH` 是刻意的顯示標籤還是未實作？`BC` 是否等同「量到 block 插入點」？（S-4）
- **ND-10**：boundary 實際會不會重疊？是否有多樓層？
- **ND-13**：不同物件類型的「寬、深、高」在實務上如何定義？
- **ND-16**：`_09_實作數量` 要不要做？若要，每個 `_08` 單位對應哪個幾何量？
- **ND-17**：`我是備註，UCCU` 是測試字串還是有意義的預設？
- **C-3 延伸**：`DNA_REF_` 參考線的實際用途是什麼？2.0 要不要保留？

## 七、本文件的限制

- 全部結論來自靜態閱讀與資料統計，**未經 Rhino 8 實機驗證**。標示為「靜默失敗」「會漂移」的行為，都是從程式邏輯推論，實機表現可能因 Rhino API 細節而不同。
- Dictionary 只解析了公司電腦的 Dropbox 版本一份，未抽樣任何實際專案的 `.3dm` 或 `Project_Registry.json`（工作檔目錄的 `exchange/` 目前為空）。因此「使用者實際怎麼用」仍有推測成分，特別是 S-4 對 `CH`／`BC` 的解讀。
- 未檢查 `LoopFlow.rhc` 工具列與 `Tag_Blocks.3dm` 的 Block 定義。Tag 的 `attr_*` 欄位是否與 Block 內部欄位完全對應，尚未驗證。
- 本次未修改任何產品程式碼、Dictionary 或工作檔。
