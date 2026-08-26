# LoopFlow 2.0 — Excel Dictionary guide

> Format, column meaning, writing rules, and how the Dictionary syncs with the Rhino model. There is one official Chinese template and one English template. The project uses whichever file Nexus selected. Commands: [command reference](./COMMANDS.md). Overall flow: [overview](./USER_GUIDE.md).

## 1　What the Dictionary is

`LoopFlow_Dictionary.xlsx` is LoopFlow’s **finish / work-item default table (Type Catalog)**.

Each row is one finish or work item (a **Type**) and maps to one Rhino sub-layer. When you run [04 Nexus](./COMMANDS.md#04-nexus-project-console) **Sync Type Layers**, LoopFlow builds those layers and applies the defaults. After modelling, put objects on the matching layers; [Write model metadata](./COMMANDS.md#5-write-model-metadata) then writes data from the Type the object actually uses.

The Dictionary stores **what this Type defaults to**, **not** each object’s current state. Objects under the same Type can still differ in construction status, remarks, and so on.

Data flow:

```text
Excel Dictionary          one Type per row: ID, name, layer, defaults, and rules
      │  LFNexus “Sync Type Layers”
      ▼
Rhino Type layers         match the Dictionary by _03_Type ID; keep defaults for new layers
      │  model; put objects on the matching layer
      │  LFNexus “Write model metadata”
      ▼
3D objects                ordinary objects: UUID, space, elevation, construction, remarks, revision (`00_STR` structure layers skipped)
      │  after validation, LFPublishExchange
      ▼
Registry revision         read-only snapshot of model data
      │  LFInfuserPart / LFInfuserAll
      ▼
2D Tag blocks             Type, elevation, drawing number, and other on-drawing fields
```

## 2　File format and location

| Item | Rule |
|---|---|
| Filename | Default `LoopFlow_Dictionary.xlsx`; any other `.xlsx` beside the `.3dm` is allowed |
| Location | The folder of the saved `.3dm` — that folder is the LoopFlow project folder |
| Project settings | `_LoopFlow_Config/loopflow/LoopFlow_Project.json` beside the `.3dm` remembers the Dictionary **filename**, not an absolute path |
| Format | `.xlsx` only; not `.csv` or `.xls` |
| Worksheet | First sheet; current name `LoopFlow_Dictionary` |
| Row 1 | Version title, e.g. `LoopFlow Dictionary v2.0` (skipped) |
| Row 2 | **Header row**: all 15 columns must be the same language (all Chinese or all English; see section 3) |
| Row 3 onward | One Type per row, one Rhino sub-layer |

The first **Sync Type Layers** run asks you to pick a file. After that, the name is stored as `dictionary_filename` in `_LoopFlow_Config/loopflow/LoopFlow_Project.json` and is not asked again. The Dictionary must sit beside the `.3dm`. If the remembered file was renamed or moved, LoopFlow asks you to put it back, then pick again from the `.3dm` folder. Picking a file in another folder is rejected and asked again. **LoopFlow does not scan every Excel in the folder, and it does not store a computer-specific absolute path.**

The `.3dm`, Dictionary, and `_LoopFlow_Config/` are bound by relative location only. Moving the whole project folder to another parent, drive, or computer still works. Copying only the `.3dm` does not take the project name or Dictionary choice with it. Official templates go into `Documents\LoopFlow`, then you copy them beside the `.3dm`.

**Interface language and the Dictionary file are independent.** Switching English / 正體中文 only changes LoopFlow windows and messages. The project Dictionary stays the workbook Nexus selected and remembered. It is not swapped to the tw or en file based on UI language.

### Two official templates

| Template | Contents | Nexus load |
|---|---|---|
| `LoopFlow_Dictionary_tw.xlsx` | Chinese headers, bilingual Rhino Layer, Microsoft JhengHei 10 | **Yes** |
| `LoopFlow_Dictionary_en.xlsx` | English headers and content, English Rhino Layer, Arial 10; count / area use `ea` / `m2` | **Yes** |

Both are complete 92-row official templates. Pick one in Nexus **Sync Type Layers**. Do not mix Chinese and English headers in the same row.

> **Do not pick the wrong file**: a name ending in `_Export.xlsx` is a review sidecar (see section 9). It cannot be opened as the project Dictionary, and it must not be renamed over the official file.

## 3　The 15 columns

The first 9 columns (including the layer path) are the Type basics. The last 6 (`Q_01`–`Q_06`) are reserved for a later Grasshopper quantity workflow. 2.0 does not calculate them and does not write them onto objects. Row 2 must be one dialect for the whole row; after load they map to the same English machine keys. The table below uses English headers; Chinese template names are in parentheses.

| Column | Required | Meaning |
|---|---|---|
| `Rhino Layer` (`__Rhino Layer`) | Required | Full Rhino layer path for this Type (see section 4). This is the **sync** key, not the official Type ID |
| `_01_Space Name` (`_01_空間名稱`) | Leave blank | Computed from the model |
| `_02_Construction` (`_02_建構狀態`) | Optional | Default construction for new layers, e.g. `New` or `Existing`. **Only the initial value on a new layer**; later each object can change, and Dictionary resync does not overwrite it |
| `_03_Type ID` (`_03_ID編號`) | Required | Unique Type ID, `category-serial`, e.g. `EX-01`, `CL-03` (see section 4). **Must not repeat** |
| `_04_Type Name` (`_04_ID名稱`) | Required | Human-readable finish / work-item name shown on tags and notes, e.g. “Aluminium access panel”. You can rename it; the permanent identity is `_03_Type ID` |
| `_05_Elevation Basis` (`_05_高程基準`) | Required | Which basis this Type uses for elevation; one of the four values below |
| `_06_Elevation Value` (`_06_高程計算`) | Leave blank | Computed from the model |
| `_07_UUID` | Leave blank | Object identity, generated by LoopFlow; do not fill |
| `_08_Remarks` (`_08_備註`) | Optional | Default remark hint, usually `(手動輸入備註)`, so users fill the real text on the object |
| `Q_01_Width W` (`Q_01_寬度W`) | Leave blank | Later Grasshopper; 2.0 does not calculate or write this |
| `Q_02_Depth D` (`Q_02_深度D`) | Leave blank | Same |
| `Q_03_Height H` (`Q_03_高度H`) | Leave blank | Same |
| `Q_04_Unit` (`Q_04_單位`) | Required | Estimating unit (not the Rhino document unit). The Chinese template uses `cm`, `mm`, `m3`, `坪`, `才`, `樘`, `片`, `組`, `台`, `座`; the English template uses `ea` for count and `m2` for area (see section 5) |
| `Q_05_Measurement Rule` (`Q_05_計量規則`) | Required | How that unit is measured (see section 5). All 92 current rows are filled |
| `Q_06_Quantity` (`Q_06_實作數量`) | Leave blank | Later Grasshopper; 2.0 does not calculate this |

### Allowed `_05_Elevation Basis` values

| Code | Full name / sample | Meaning |
|---|---|---|
| `BH` | Bottom Height, object bottom | Elevation from the **bottom** face; walls and floor-standing equipment |
| `TH` | Top Height, object top | Elevation from the **top** face; floors and thresholds marked at the top |
| `CH` | Ceiling Height, underside of ceiling objects | Elevation from the **underside of the ceiling**; lights and ceiling finishes |
| `BC` | Block insertion point | Reads the **Block instance insertion point**. **Blocks only** — switches, panels, equipment inserted as blocks. If non-block geometry uses `BC`, write and validate **block**; LoopFlow will not silently switch to another basis |

> The 1.x value `TH/BH` (top and bottom together) is **not** legal in 2.0. It exists only as a migration reference.

## 4　Layer naming

Chinese-template `Rhino Layer` / `__Rhino Layer` format:

```text
top group::EnglishName.ChineseName
```

Example: `01_Ceiling_天花::Access_Panel.檢修口`. The English template drops Chinese from the path, e.g. `00_STR::Beam`. Both path styles load. Do not mix Chinese and English **headers** in the same file.

The Chinese Dictionary has **12 top groups**, each with a fixed category prefix:

| Code | Top group | Example (Type ID / name) | Elevation | Typical `Q_04` / `Q_05` |
|---|---|---|---|---|
| `EX` | `00_STR_結構` | `EX-01` / reinforced concrete (beam) | `BH` / `TH` | `m3` / `VOL_WDH`; `cm` / `LEN_W`; `坪` / `AREA_WD`; `座` / `COUNT` |
| `CL` | `01_Ceiling_天花` | `CL-01` / aluminium access panel | `CH` | `片` / `COUNT`; `坪` / `AREA_WD`; `cm` / `LEN_W` |
| `WL` | `02_Wall_牆面` | `WL-01` / light partition | `BH` | `cm` / `LEN_W` |
| `FL` | `03_Floor_地坪` | `FL-01` / balcony tile floor | `TH` | `坪` / `AREA_WD` |
| `CB` | `04_CB_櫃體` | `CB-01` / millwork cabinet | `BH` | `mm` / `LEN_W` |
| `LS` | `05_LT_燈帶` | `LS-01` / ceiling light strip | `BH` | `cm` / `LEN_W` |
| `EL` | `06_EL_電控系統` | `EL-01` / intercom | `BC` (block) | `組` / `COUNT` |
| `MP` | `07_MEP_空調機電` | `MP-01` / HVAC panel | `BC` (block) | `組` / `COUNT` |
| `SA` | `08_SAN_衛浴設備` | `SA-01` / bathtub | `BC` (block) | `組` / `COUNT` |
| `EQ` | `09_EQP_專用設備` | `EQ-01` / AV equipment | `BH` | `組` / `COUNT` |
| `FP` | `10_FP_消防系統` | `FP-01` / emergency light | `BC` (block) | `組` / `COUNT` |
| `DW` | `20_DW` | `DW-01` / doors and windows | `BH` | `樘` / `COUNT` |

`04_CB_櫃體` is an ordinary finish group. It is not the later cabinet toolkit (outside 2.0).

### `20_DW` (doors and windows) is special

Door/window model data lives on the **block itself** (see [Tag Block reference](./TAG_BLOCKS.md#dw-tag--doors-and-windows)), not on sub-layers. The `20_DW` row note says blocks sit on this layer and data is on the block, not on child layers. Sync treats `20_DW` as one Type and ignores child layers. `TAG_DW` No./W./H. are 2D manual fields; they do not create child Types and they do not write back as 3D object data.

### `00_STR` (structure) does not get object metadata

`00_STR` structure layers and their children **are still** synced as Type layers, including layer `lf_type_id`. 3D objects on those layers **do not** receive object ID, space, or elevation metadata, and they are not Laser / Grab sources. The next Write model metadata run clears leftover object UserText on them. Quantity takeoff is a separate product and does not rely on those object UUIDs.

## 5　Writing rules

- **`_03_Type ID` is always `category-serial`** (e.g. `EX-07`). Load splits and checks it strictly. The category must match the top group of the layer, and it must not duplicate another row.
- **`Q_04_Unit` and `Q_05_Measurement Rule` must share a dimension**, or load is blocked:

  | Rule | Dimension | Allowed `Q_04` units |
  |---|---|---|
  | `COUNT` | count | 樘, 片, 組, 台, 座, ea |
  | `LEN_W` / `LEN_D` / `LEN_H` | length | cm, mm |
  | `AREA_WD` / `AREA_WH` / `AREA_DH` | area | 坪, 才, m2 |
  | `VOL_WDH` | volume | m3 |

  Conversion constants: `坪 = specified area (m²) × 0.3025`; `才 = specified area (cm²) ÷ (30.3 × 30.3)`. These are for later Grasshopper. **2.0 does not evaluate them from model geometry.** `ea` and `m2` are the English template’s count / area units and are registered. Nexus, Infuser, Catalog, and Tagger do not use unit strings for business logic. Units are checked on load and snapshotted into Registry `types[]`.
- `_08_Remarks` should usually be `(手動輸入備註)` so the object field looks empty and user-filled.
- Row 2 must be **all 15 Chinese columns or all 15 English columns**. After load they become internal English keys. Mixing dialects in one row is blocked.
- **Wrong names or column count stop the load.** LoopFlow does not guess columns. Do not rename headers or add columns outside this set.
- Fonts: Chinese template **Microsoft JhengHei 10**; English template **Arial 10**. Export headers and fonts follow the source Dictionary, not the UI language.

### Type rules vs leave-blank columns

The Dictionary stores Type **rules and defaults**, not object instances:

- **Set by the Dictionary**: `Rhino Layer`, `_02_Construction` (initial default), `_03_Type ID`, `_04_Type Name`, `_05_Elevation Basis`, `_08_Remarks` (initial hint), `Q_04_Unit`, `Q_05_Measurement Rule`.
- **Leave blank; model or system fills**: `_01_Space Name`, `_06_Elevation Value`, `_07_UUID`, `Q_01`–`Q_03`, `Q_06`. Filled values are not read and are not copied onto objects.

## 6　Add or change a Type

### Add

1. Insert a row near similar Types, or copy the closest row and edit it.
2. Set `Rhino Layer` to the new full path.
3. Give `_03_Type ID` an **unused** ID, e.g. if `WL-14` exists, use `WL-15`.
4. Fill `_04_Type Name`, confirm `_02_Construction`, pick `_05_Elevation Basis` from the geometry.
5. Fill `Q_04_Unit` and a compatible `Q_05_Measurement Rule`.
6. Keep instance / computed columns blank; save.
7. In Rhino, run [04 Nexus](./COMMANDS.md#04-nexus-project-console) **Sync Type Layers**. Put objects on the layer only after it appears.

### Change an existing Type

**Safe to change**: `_04_Type Name`, `_02_Construction` default, `_08_Remarks` default, `_05_Elevation Basis`, `Q_04` / `Q_05`. Then resync and re-validate.

**Handle with care**: `_03_Type ID`, `Rhino Layer`, category code. These identities are already referenced by objects, the Registry, and tags. Changing the Excel value does not update written objects. Do not just retitle an old ID in Excel and keep working; decide how existing objects will be handled first.

## 7　Dictionary, 3dm, and project settings

LoopFlow does not store the project name or Dictionary filename in the `.3dm`. Those live in `_LoopFlow_Config/loopflow/LoopFlow_Project.json`. Registry and logs are also under `_LoopFlow_Config/loopflow/`. Copying the `.3dm` into a new project therefore does not drag the old paths and settings along.

Merge rules for [04 Nexus](./COMMANDS.md#04-nexus-project-console) **Sync Type Layers**:

- **In Dictionary, missing in Rhino**: create the layer and write `_02_Construction` as the **default for new objects on that layer**, not onto each existing object.
- **Same layer name already in Rhino**: keep existing UserText and construction; display colour is reapplied from the Type category.
- **Object instance values stay on the object**: resync does not overwrite filled object data, and it **does not write object values back into the Dictionary**. The link is one-way (Dictionary → new-layer defaults).
- New Type layers get a `DNA_REF_` point at the origin so Rhino Purge does not delete an empty layer. Resync updates or replaces that point by Type ID; it does not keep adding points.
- Layer display colour follows the category prefix. New material names are the relative path without the project prefix, coloured like the layer. If a same-named material already exists, LoopFlow only attaches it and **does not change colours you already edited**.

In short: **the Dictionary owns Type identity, mapping, defaults, and rules; objects keep their current values.** Sync maintains layer mapping, colour, material attach, and `DNA_REF`. It does not overwrite an object’s construction, remarks, UUID, or elevation.

## 8　Where `Q_01`–`Q_06` stand in 2.0

2.0 does not compute size or quantity, and it does not write Q columns onto objects or the Registry. `Q_04_Unit` and `Q_05_Measurement Rule` still take part in dimension checks. Leave `Q_01`–`Q_03` (W/D/H) and `Q_06` (quantity) blank for a later Grasshopper workflow.

## 9　Review model vs Dictionary differences

The model and Dictionary will drift (for example a temporary layer change while modelling). Review loop:

1. Run [03 Export Dictionary](./COMMANDS.md#03-export-dictionary) to write `{original name}_Export.xlsx`.
2. Run [02 Open exported Dictionary](./COMMANDS.md#02-open-exported-dictionary) and read the `diff_status` colours.
3. Open [01 Open official Dictionary](./COMMANDS.md#01-open-official-dictionary) and **manually** copy needed changes back.

| `diff_status` | Colour | Meaning | What to do |
|---|---|---|---|
| `unchanged` | black | Dictionary and model match | Nothing |
| `modified` | orange | Both exist, contents differ | Compare and pick a side |
| `missing_in_rhino` | red | In Dictionary, not in the model | Resync, or retire the Type |
| `added_in_rhino` | blue | In the model, not in the Dictionary | When merging, assign an **unused** Type ID (`_03_Type ID` on an English source, `_03_ID編號` on a Chinese source) |

The export is **review only**. It never replaces the official Dictionary. LoopFlow does not merge for you. It only lists layer-level defaults, not per-object data. The top red hint, the 15 header names, and the font follow the **source Dictionary** (Chinese: Microsoft JhengHei and `_03_ID編號`; English: Arial and `_03_Type ID`), not the UI language.

## 10　Common problems

| Situation | Typical cause | What to do |
|---|---|---|
| Dictionary will not load | Title, headers, or column count do not match the 15-column definition, or one row mixes Chinese and English headers | Restore the official 15-column structure; keep one dialect for the whole row; do not add, drop, or rename columns |
| Duplicate `_03_Type ID` | A new row reused an old ID | Give it an unused ID |
| Bad elevation basis | A value other than `BH` / `TH` / `CH` / `BC` (e.g. 1.x `TH/BH`) | Use one of the four legal values |
| `BC` fails on write | `BC` used on non-block geometry | Insert as a block, or change that Type to `BH` / `TH` / `CH` |
| Measurement rule error | `Q_04_Unit` and `Q_05_Measurement Rule` disagree on dimension | Fix against the table in section 5 |
| Official Dictionary will not open | File renamed, not beside the `.3dm`, or only the `.3dm` was copied without `_LoopFlow_Config/` | Put the Dictionary back beside the `.3dm`, then re-pick it in [04 Nexus](./COMMANDS.md#04-nexus-project-console) sync |
| Opened `_Export.xlsx` by mistake | Edited the review sidecar as if it were official | Open the official file; sidecar edits are not read |
| Excel changed, Rhino did not | Forgot **Sync Type Layers** | Save, then resync in Rhino |
| Tags still show old data | Write → validate → publish → infuse chain is incomplete | Run the missing steps in order |

## 11　Switching Dictionary files mid-project (not recommended)

`dictionary_filename` remembers a name, not a path. After you switch to another `.xlsx`, Types missing from the new file are no longer recognised by sync. If you must switch, first run the section 9 review and confirm Type IDs and column definitions still match, so existing objects’ `_03_Type ID` still resolve in the new file.
