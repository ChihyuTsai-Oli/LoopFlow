# 契約 fixtures

本目錄是 LoopFlow 2.0 可機器驗證的合法／錯誤案例。形狀定義在 `../schema/`，畫面證據在 `../legacy/tag_block_text/`。檢查器：

```text
python wip/tools/check_contract_fixtures.py
```

不依賴 Rhino、pytest 或私人專案檔。第一條規則：`measurement_rule` 與 `estimation_unit` 量綱必須一致。本目錄不含 Dropbox 正式 Dictionary、`.3dm` 或真實專案 Registry。

## 內容

| 路徑 | 覆蓋 |
|---|---|
| `dictionary/columns.json` | 15 欄顯示名、machine key、12 個類別碼 |
| `dictionary/measurement_rules.baseline.json` | 2026-08-14 字典快照 92 列；量綱須 92/92 通過 |
| `dictionary/cases.json` | 合法量綱、空規則警告、錯單位／錯規則、未知欄、14 欄、重複 `type_id`、`_CB.*` |
| `identity/object_id_cases.json` | 新建 UUID、大寫正規化、複製換號、碰撞 mapping、rollback、禁止靜默重建 |
| `space/cases.json` | 多樓層投影重疊可通過、共邊可通過、面積重疊阻擋、EXT 四因；樓層框配對由 unittest 覆蓋 |
| `elevation/cases.json` | `BH`／`TH`／`CH`／`BC`；非 Block 的 `BC` 阻擋；`TH/BH` 只屬 migration |
| `local_frame/cases.json` | Block 插入平面、Extrusion、唯一平面、封閉 Box、沿用、損壞框、禁止 World bbox |
| `drawing/provenance_cases.json` | 零／一／多來源、人工修改不得標 current、過期 revision、索引不完整仍可出圖 |
| `tag/cases.json` | 未知 Block 零寫入、`title_frame` 才寫圖號、`TAG_DW` 全手動、Duplicate 清除／保留、家具 Block 名 |
| `registry/cases.json` | 最小合法、未知版本、未知核心欄、缺 EXT |
| `quantity/cases.json` | COUNT＝1；才＝cm²÷918.09；坪＝m²×0.3025 |

`schema/` 的 `registry.json` 與 `tag_templates.json` 由檢查器一併核對：10 份 manifest、恰好一個 `title_frame`、24 個 legacy key 與畫面擷取一致。

`local_frame/` 與 `quantity/` 是後續 GH 數量計算的材料，2.0 不從模型求值；檢查器仍核對常數與案例，以免契約腐壞。

## 量綱對照

| 規則 | 量綱 | 允許單位 |
|---|---|---|
| `COUNT` | count | 樘、片、組、台、座 |
| `LEN_W`／`LEN_D`／`LEN_H` | length | cm、mm |
| `AREA_WD`／`AREA_WH`／`AREA_DH` | area | 坪、才 |
| `VOL_WDH` | volume | m3 |
| 規則空 | — | 不阻擋量綱，quantity 為空並警告 |

不符列為阻擋。baseline 目前只用到 `COUNT`、`LEN_W`、`AREA_WH`、`AREA_WD`、`VOL_WDH`；其餘 token 仍屬 GH 契約。
