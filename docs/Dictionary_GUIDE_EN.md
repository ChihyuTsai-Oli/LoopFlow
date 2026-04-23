# LoopFlow Dictionary Guide

> Version: v1.0 / Date: 2026-04-23
>
> This guide covers `LoopFlow_Dictionary_EN.xlsx` — format, authoring rules, and usage in Rhino.
>
> Traditional Chinese edition: [`Dictionary_GUIDE_TW.md`](./Dictionary_GUIDE_TW.md)

---

## Table of Contents

1. [What Is the Dictionary](#1-what-is-the-dictionary)
2. [File Format and Location](#2-file-format-and-location)
3. [Column Reference](#3-column-reference)
4. [Layer Naming Convention](#4-layer-naming-convention)
5. [Authoring Rules](#5-authoring-rules)
6. [Using the Dictionary in Rhino](#6-using-the-dictionary-in-rhino)
7. [Affected Files](#7-affected-files)
8. [Full Dictionary Table](#8-full-dictionary-table)
9. [Switching Dictionary Editions Mid-Project](#9-switching-dictionary-editions-mid-project-not-recommended)

---

## 1. What Is the Dictionary

`LoopFlow_Dictionary.xlsx` is the **default attribute definition table** for the LoopFlow system.

Each row defines one Rhino sub-layer and the UserText attribute values its objects should carry — ID number, name, unit, elevation basis, and so on. When `LF_Nexus` runs, it reads this dictionary and writes the defaults to selected objects in one step, keeping attributes consistent across the entire project.

---

## 2. File Format and Location

| Item | Detail |
|---|---|
| Filename | `LoopFlow_Dictionary.xlsx` (configurable in `_LoopFlow_Config.py`) |
| Location | **Same folder as the `.3dm` project file** — LF_Nexus locates it automatically |
| Format | `.xlsx` only; `.csv` and `.xls` are not supported |
| Worksheet | First sheet (any name) |
| Row 1 | Version title row, e.g. `LoopFlow Dictionary v1.0` — skipped by the script |
| Row 2 | **Column header row** — names must match exactly; column order is flexible |
| Row 3+ | One row per Rhino sub-layer |

---

## 3. Column Reference

### Key Column (required)

| Column | Description |
|---|---|
| `__Rhino Layer` | **Primary key.** Full Rhino sub-layer path. See [Section 4](#4-layer-naming-convention). Blank or duplicate rows are ignored. |

### General Attribute Columns

| Column | UserText Key | Description | Values / Format |
|---|---|---|---|
| `_01_Space Name` | `_01_Space Name` | Space that contains the object. Usually left blank; filled automatically by LF_Nexus TagTrigger from space boundaries. | Text, e.g. `Master Bedroom` |
| `_02_Construction Status` | `_02_Construction Status` | Build phase. Structural layers default to `Existing`; all others default to `New`. | `New` / `Existing` / `Demolished` / `Relocated` |
| `_03_ID Number` | `_03_ID Number` | Unique material/work-item code for BOM and drawing index. | `XX-NN`, e.g. `EX-01`, `CL-01` |
| `_04_ID Name` | `_04_ID Name` | Human-readable material label for drawing notes. | Text, e.g. `Tiles` |
| `_05_Width W` | `_05_Width W` | Width preset (optional). | Numeric |
| `_06_Depth D` | `_06_Depth D` | Depth preset (optional). | Numeric |
| `_07_Height H` | `_07_Height H` | Height preset (optional). | Numeric |
| `_08_Unit` | `_08_Unit` | Quantity unit used in BOM reports. | `m2` / `cm` / `mm` / `m3` / `set` / ... |
| `_09_Quantity` | `_09_Quantity` | Actual quantity — usually calculated and filled by LF_Nexus. | Numeric |
| `_10_Elevation Basis` | `_10_Elevation Basis` | Elevation reference plane abbreviation; controls how LF_Nexus measures height. | See table below |
| `_11_Elevation Value` | `_11_Elevation Value` | Computed elevation (written by script; leave blank in dictionary). | Numeric (cm) |
| `_12_UUID` | `_12_UUID` | Object unique identifier (auto-generated; leave blank in dictionary). | Auto |
| `_13_Remarks` | `_13_Remarks` | Free-text notes for special conditions or material specs. | Free text |

#### `_10_Elevation Basis` values

| Code | Full Name | Description |
|---|---|---|
| `BH` | Bottom Height | Measured from the **bottom face** of the object |
| `TH` | Top Height | Measured from the **top face** of the object |
| `CH` | Ceiling Height | Measured from the **underside of the ceiling** (lights, ceiling finishes) |
| `TH/BH` | Top + Bottom | Both top and bottom elevations recorded (e.g. slabs) |

### Cabinet Panel Columns (`_CB.*`)

> ⚠️ **EN edition uses English key names.** These must be paired with `LF_Cabinet_Suite.py` (EN version). Mixing with TW-edition scripts will break CB field synchronisation.

| Column | UserText Key | Description |
|---|---|---|
| `_CB.01_Panel_Type` | `_CB.01_Panel_Type` | Panel classification, e.g. `Side_Panel`, `Door_Leaf`, `Top_Board` |
| `_CB.02_Length_L` | `_CB.02_Length_L` | Longest dimension (cm) |
| `_CB.03_Width_W` | `_CB.03_Width_W` | Second dimension (cm) |
| `_CB.04_Thickness_T` | `_CB.04_Thickness_T` | Thickness (cm) |

---

## 4. Layer Naming Convention

The `__Rhino Layer` value maps to Rhino's layer tree:

```
NN_Category::EnglishType
```

- `NN` — two-digit sort prefix (`00`, `01`, `02`...)
- `Category` — English category name
- `EnglishType` — sub-layer type name

**Example:**

```
02_Wall::Tiles
│        │
│        └─ Sub-layer: material type
└─ Parent: number_category
```

> **Special case:** `20_DW` (Door/Window) is a single-level layer with no `::` sub-layers. Door/window objects live as Blocks on this layer; data is written to the Block, not to sub-layers.

---

## 5. Authoring Rules

### Adding a new row

1. Add a row anywhere in the sheet (order does not matter — LF_Nexus matches by `__Rhino Layer`)
2. `__Rhino Layer` must exactly match the Rhino layer path (case-sensitive)
3. `_02_Construction Status`: structural items → `Existing`; all others → `New`
4. `_03_ID Number`: use the category prefix (CL-XX / WL-XX / FL-XX...)
5. `_08_Unit`: area materials → `m2`; linear → `cm`; volume → `m3`
6. Dimension columns (`_05_` / `_06_` / `_07_`) may be left blank
7. `_CB.*` columns: auto-calculated by the script — leave blank in the dictionary

### Prohibited actions

| Action | Reason |
|---|---|
| Delete or rename Row 1 (title row) | `DICTIONARY_SKIPROWS = 1` always skips Row 1; deleting it shifts the header into the skip zone |
| Rename column headers | LF_Nexus identifies columns by their `_NN_` prefix; renamed headers are silently ignored |
| Duplicate `__Rhino Layer` values | The later row overwrites the earlier one |
| Use `.csv` or `.ods` | Only `.xlsx` is supported |

---

## 6. Using the Dictionary in Rhino

All operations are launched from the **`LF_Nexus`** main interface:

| Operation | What it does |
|---|---|
| **Dict. to Layer** | Reads `__Rhino Layer` and creates all parent/sub-layers in Rhino |
| **Dict. to Object** | After selecting objects, looks up each object's layer in the dictionary and writes the matching UserText values |
| **Rhino to XLSX** | Reads UserText from selected Rhino objects and exports back to the `.xlsx` dictionary |
| **Dictionary Editor** | Auto-locates `LoopFlow_Dictionary.xlsx` in the same folder as the `.3dm` and opens it in Excel |

---

## 7. Affected Files

### Core dependencies

| File | Role |
|---|---|
| `_LoopFlow_Config.py` | Defines dictionary filename, key column name, rows-to-skip count |
| `LF_Nexus.py` | Reads all dictionary columns; runs three-way sync; elevation logic depends on `_10_Elevation Basis` |
| `LF_Dictionary_Editor.py` | Auto-locates and opens the dictionary in Excel |

### Indirect dependencies (read UserText written by the dictionary)

| File | Fields used |
|---|---|
| `LF_TAG-O.py` | `_01_Space Name` |
| `LF_Cabinet_Suite.py` | `_CB.01_Panel_Type`, `_CB.02_Length_L`, `_CB.03_Width_W`, `_CB.04_Thickness_T` |

---

## 8. Dictionary Table Example

> Columns `_05_W` / `_06_D` / `_07_H` / `_09_Quantity` / `_11_Elevation Value` / `_12_UUID` are all blank in this version and are omitted.

### 00 Structure (STR)

| `__Rhino Layer` | `_02_` | `_03_ID` | `_04_ID Name` | `_08_Unit` | `_10_Elev.` | `_13_Remarks` |
|---|---|---|---|---|---|---|
| `00_STR::Beam` | Existing | EX-01 | Beam | m3 | BH | |
| `00_STR::Column` | Existing | EX-02 | Column | m3 | BH | |
| `00_STR::Curb` | Existing | EX-03 | Curb | cm | TH | |
| `00_STR::Slab` | Existing | EX-04 | Slab | m2 | TH/BH | |

### 01 Ceiling

| `__Rhino Layer` | `_02_` | `_03_ID` | `_04_ID Name` | `_08_Unit` | `_10_Elev.` | `_13_Remarks` |
|---|---|---|---|---|---|---|
| `01_Ceiling::Lighting_Box` | New | CL-01 | Lighting_Box | cm | CH | |
| `01_Ceiling::Paint` | New | CL-02 | Paint | m2 | CH | |
| `01_Ceiling::Panel` | New | CL-03 | Panel | m2 | CH | |
| `01_Ceiling::Timber` | New | CL-04 | Timber | m2 | CH | |

### 02 Wall

| `__Rhino Layer` | `_02_` | `_03_ID` | `_04_ID Name` | `_08_Unit` | `_10_Elev.` | `_13_Remarks` |
|---|---|---|---|---|---|---|
| `02_Wall::Tiles` | New | WL-01 | Tiles | m2 | BH | |
| `02_Wall::Timber` | New | WL-02 | Timber | m2 | BH | |
| `02_Wall::Trim` | New | WL-03 | Trim | cm | TH | |
| `02_Wall::Wallpaper` | New | WL-04 | Wallpaper | m2 | BH | |

### 03 Floor

| `__Rhino Layer` | `_02_` | `_03_ID` | `_04_ID Name` | `_08_Unit` | `_10_Elev.` | `_13_Remarks` |
|---|---|---|---|---|---|---|
| `03_Floor::Stone` | New | FL-01 | Stone | m2 | TH | |
| `03_Floor::Threshold` | New | FL-02 | Threshold | cm | TH | |
| `03_Floor::Tiles` | New | FL-03 | Tiles | m2 | TH | |
| `03_Floor::Wood` | New | FL-04 | Wood | m2 | TH | |

### 04 Cabinet (CB)

| `__Rhino Layer` | `_02_` | `_03_ID` | `_04_ID Name` | `_08_Unit` | `_10_Elev.` | `_13_Remarks` |
|---|---|---|---|---|---|---|
| `04_CB::Color` | New | CB-01 | Color | mm | BH | |
| `04_CB::Glass` | New | CB-02 | Glass | m2 | BH | |
| `04_CB::Hardware` | New | CB-03 | Hardware | set | BH | |
| `04_CB::Metal` | New | CB-04 | Metal | mm | BH | |

### 20 Door / Window (DW)

| `__Rhino Layer` | `_02_` | `_03_ID` | `_04_ID Name` | `_08_Unit` | `_10_Elev.` | `_13_Remarks` |
|---|---|---|---|---|---|---|
| `20_DW` | New | DW-01 | DW | — | BH | Place the block on this layer; write data in the block, not in sub-layers |

---

## 9. Switching Dictionary Editions Mid-Project (Not Recommended)

> ⚠️ **Switching dictionary editions during an active project is not recommended.** Once you begin using a dictionary edition, keep it consistent throughout the entire project lifecycle.

The TW and EN dictionaries use different UserText key names (e.g. `_01_空間名稱` vs `_01_Space Name`). If you switch mid-project, old keys on existing objects are **not automatically removed**. Objects end up carrying two conflicting sets of keys, and tools like `LF_TAG-O` that scan all UserText keys by prefix may read the wrong value unpredictably.

**If you must switch, follow these steps in order:**

1. Run LF_Nexus **Dict. to Layer** to create the new-edition layer structure
2. Move all objects to the corresponding new-edition layers
3. **Batch-delete all old-edition UserText keys from every object** (requires a custom Rhino Python script — no built-in tool exists for this step)
4. Run LF_Nexus **Dict. to Object** to write the new-edition default values to all objects
5. Re-run **TagTrigger** so the `_01_` space-name field is recorded under the new key name

> **Note:** Step 3 is not yet available as a built-in LoopFlow tool. You will need to write a short script or handle it manually per object.

---

*Last updated: April 2026*
