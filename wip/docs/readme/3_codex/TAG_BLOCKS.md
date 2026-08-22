# LoopFlow 2.0 Tag Block reference

> What each Tag / title-frame block in `Tag_Blocks.3dm` shows, who writes each field, and what you may edit by hand. Commands: [command reference](./COMMANDS.md). Overall flow: [overview](./USER_GUIDE.md).
>
> 2.0 keeps **one** `wip/docs/Tag_Blocks_3dm/Tag_Blocks.3dm`. The file has Chinese and English notes together; there are not two 3dm files. Fixed labels on the block (`Grab`, `Laser`, `W.`, `H.`) are drawn text, not data fields. Formula default prompts stay in English and do not follow `LFLanguage`. The installer copies this library to `Documents\LoopFlow`.
>
> Names follow the contract: `TAG_HEIGHT_GRAB`, `TAG_HEIGHT_LASER`, `TAG_FINISH_GRAB`, `TAG_FINISH_LASER`, `TAG_ITEM`, `TAG_DW`, `TAG_SECTION_DETAIL`, `TAG_ELEV_1`, `TAG_ELEV_2`, `TAG_ELEV_3`, `TAG_ELEV_4`, `TAG_ELEV_0`, `Sample_Frame`. Existing Rhino definitions such as `Tag_Height_Grab` still match case-insensitively.

## Pick the right Tag

| What you want to mark | Block | Command |
|---|---|---|
| Object elevation and finish; you can pick the source | `TAG_HEIGHT_GRAB` | [10 Direct grab](./COMMANDS.md#10-direct-grab) |
| Object elevation and finish; you only have a section location | `TAG_HEIGHT_LASER` | [09 Laser projection](./COMMANDS.md#09-laser-projection) |
| Finish / Type, no elevation; you can pick the source | `TAG_FINISH_GRAB` | [10 Direct grab](./COMMANDS.md#10-direct-grab) |
| Finish / Type, no elevation; section location only | `TAG_FINISH_LASER` | [09 Laser projection](./COMMANDS.md#09-laser-projection) |
| Furniture or other shared blocks | `TAG_ITEM` | [10 Direct grab](./COMMANDS.md#10-direct-grab) |
| Door/window number, width, height | `TAG_DW` | Fully manual; no bind command |
| Section-detail index | `TAG_SECTION_DETAIL` | [11 Index to View](./COMMANDS.md#11-index-to-view) |
| Elevation-direction index (four directions) | `TAG_ELEV_1`–`TAG_ELEV_4` | [11 Index to View](./COMMANDS.md#11-index-to-view) |
| Six-direction elevation index plaque on this page | `TAG_ELEV_0` | [07 Sheet numbering](./COMMANDS.md#07-sheet-numbering) (writes this-page number only; directions are manual) |
| Title frame (number / title / scale) | Project frame (e.g. `Sample_Frame`) | [07 Sheet numbering](./COMMANDS.md#07-sheet-numbering) |

## Four shared ideas

### 1　Automatic vs manual fields

Each tag field is one of:

- **Automatic**: written by [12/13 Infuse](./COMMANDS.md#1213-infuse-data) or [07 Sheet numbering](./COMMANDS.md#07-sheet-numbering). Do not edit by hand — the next infuse / numbering overwrites it.
- **Manual**: you type it. Commands do not overwrite it (Duplicate Layout is the exception; see “After Duplicate Layout” below).

Every field table below marks automatic or manual.

### 2　What `-` / `!` / `?` mean on the drawing

Shared by [14 Health](./COMMANDS.md#14-health-check-tag-o) and 12/13 infuse. They appear only on **automatic** fields:

| Symbol | Colour | Meaning |
|---|---|---|
| `-` | no tint | This tag is not bound yet |
| `!` | whole tag orange | Stale: source still exists, drawing is not current — re-infuse |
| `?` | whole tag red | Disconnected: source is gone — rebind, then re-infuse |

### 3　How lock works

Most tags have a lock field in the upper left. Typing `x` or `X` locks it (key `lf_00_lock_state`; the `00` only sorts it to the top of Rhino’s attribute list).

- When locked: **binding is frozen**. [09 Laser](./COMMANDS.md#09-laser-projection) / [10 Grab](./COMMANDS.md#10-direct-grab) / [11 Index](./COMMANDS.md#11-index-to-view) and 12/13 infuse do not change this tag.
- [14 Health](./COMMANDS.md#14-health-check-tag-o) still lists locked tags and labels them locked, but does not change their text or colour.
- Blank, or the on-drawing hint (`x to lock`), is not a lock.
- `TAG_DW` (doors/windows) and title frames **have no** lock field.

### 4　System fields you must not edit by hand

Besides fields marked manual, tags also carry hidden identity fields: tag id, bind mode, source object ID, target View / Sheet, sync revision, health. **Do not edit those.** If the bind is wrong, Grab / Laser / Index again. Hand-editing hidden fields makes LoopFlow lose the correct source or target.

---

## Height Tag

**Blocks**: `TAG_HEIGHT_GRAB`, `TAG_HEIGHT_LASER`　**Bind**: [10 Direct grab](./COMMANDS.md#10-direct-grab) or [09 Laser projection](./COMMANDS.md#09-laser-projection)

Marks object elevation (sill, ceiling height, and so on).

| On-drawing field | Who writes | Notes |
|---|---|---|
| Lock | Manual | `x` / `X` |
| Elevation basis | Automatic | Source measure basis: `BH` (bottom) / `TH` (top) / `CH` (ceiling underside) / `BC` (block insertion point, blocks only) |
| Elevation value | Automatic | Display string; may include `+`, `±0`, etc. Not a raw number for calculation |
| Finish category | Automatic | Source Type category, e.g. `WL` |
| Finish serial | Automatic | Source Type serial, e.g. `00` |
| Finish name | Automatic | Type display name from the Dictionary |
| Remarks | Manual | Default hint “Enter”; you type the real text |

## Finish Tag

**Blocks**: `TAG_FINISH_GRAB`, `TAG_FINISH_LASER`　**Bind**: [10 Direct grab](./COMMANDS.md#10-direct-grab) or [09 Laser projection](./COMMANDS.md#09-laser-projection)

Marks surface finish; no elevation fields.

| On-drawing field | Who writes | Notes |
|---|---|---|
| Lock | Manual | `x` / `X` |
| Finish category | Automatic | Source Type category, e.g. `FL` |
| Finish serial | Automatic | Source Type serial |
| Finish name | Automatic | Type display name from the Dictionary |
| Remarks | Manual | Default hint “Enter” |

## Item Tag — furniture / equipment

**Block**: `TAG_ITEM`　**Bind**: [10 Direct grab](./COMMANDS.md#10-direct-grab) (pick a furniture block)

| On-drawing field | Who writes | Notes |
|---|---|---|
| Lock | Manual | `x` / `X` |
| Furniture category | Automatic | Front of the block name, e.g. `FF` from `FF-01__Chair-1` |
| Number | Automatic | Middle of the block name, e.g. `01` |
| Name | Automatic | Tail of the block name, e.g. `Chair-1` |
| Remarks | Manual | Default hint “Enter” |

The same furniture type can share one block name (a set of chairs all named `FF-01__Chair-1`). Grab also stores **this instance**, so a later rename updates the drawing; deleting the instance shows disconnected (`?`). A bad name format is blocked with a warning; LoopFlow does not guess how to split it.

## DW Tag — doors and windows

**Block**: `TAG_DW`　**Bind**: fully manual; no Tagger command

| On-drawing field | Who writes | Notes |
|---|---|---|
| Number | Manual | Door/window number |
| Width | Manual | The number after the `W.` label; do not change the label |
| Height | Manual | The number after the `H.` label; do not change the label |

`TAG_DW` has **no lock field** because everything is hand-filled. 12/13 infuse never touches it. [14 Health](./COMMANDS.md#14-health-check-tag-o) does not treat it as unbound. [Duplicate Layout](./COMMANDS.md#a4-duplicate-layout) keeps its contents in full.

## Index Tag — detail / elevation index

**Blocks**: `TAG_SECTION_DETAIL`, `TAG_ELEV_1`–`TAG_ELEV_4`　**Bind**: [11 Index to View](./COMMANDS.md#11-index-to-view)

Points at a registered View (section / elevation) so you know which page holds that detail or elevation. The four elevation blocks look different (direction or layout) but share field rules.

| On-drawing field | Who writes | Notes |
|---|---|---|
| Lock | Manual | `x` / `X` |
| Drawing number | Automatic | Target page number (12/13 from target Sheet metadata) |
| Ref | Automatic | Target page reference code |
| Detail number | Manual | e.g. `A`, `B`, `1` when one page has several Details; infuse does not write this |

After you renumber (for example after inserting a page), you usually only rerun 12/13 infuse. You do not need to rerun 11 — the bind is the View, not the drawing number itself.

## Elev 0 — six-direction elevation plaque

**Block**: `TAG_ELEV_0`　**Bind**: not bound to the model by Tagger, but **this-page drawing number** is written by [07 Sheet numbering](./COMMANDS.md#07-sheet-numbering)

A plaque on the plan showing which elevation drawings sit at four directions plus up and down. It is **not** a normal Index tag and does not accept 11 Index binds.

| On-drawing field | Who writes | Notes |
|---|---|---|
| Lock | Manual | `x` / `X`; when locked, 07 also does not overwrite “this-page number” |
| This-page number | Automatic | Written by 07; the drawing number of the page **this plaque sits on** |
| Number | Manual | Plaque serial |
| Elevation | Manual | Elevation direction |
| Up / left / down / right | Manual | Drawing numbers for the four directions |

[14 Health](./COMMANDS.md#14-health-check-tag-o) does not check this block. After [Duplicate Layout](./COMMANDS.md#a4-duplicate-layout), direction fields are cleared so you fill them on the new page.

## Title Frame

**Block**: the project title frame, e.g. `Sample_Frame`　**Bind**: [07 Sheet numbering](./COMMANDS.md#07-sheet-numbering) writes number and title

Title frames have no lock. Write is controlled only by the 07 review list.

| On-drawing field | Who writes | Notes |
|---|---|---|
| Drawing number | Automatic | 07 from series and numeric tail |
| Drawing title | Automatic | 07 from Layout page-name column 3 |
| Scale | Manual | Each sheet is filled by hand; 07 does not touch this. A missing field shows `####` (Rhino cannot find the field — the command is not broken) |

**Only registered title frames are processed.** If 07 meets an unknown block, it lists names and asks you to tick “this is a real title frame”, default none ticked. A project-custom frame (not built-in `Sample_Frame`) must be ticked once in that list before 07 keeps processing it. A page should have exactly one registered frame; none or two-or-more skips that page.

---

## After Duplicate Layout

After [A4 Duplicate Layout](./COMMANDS.md#a4-duplicate-layout):

- Except `TAG_DW`, all tag binds are cleared and the tag is marked disconnected (`?`, red) so you rebind.
- Manual fields (remarks, Detail number, elevation direction, and so on) are written as a blank character so the field itself remains and the drawing does not show `####`. That is not “has content”.
- **Lock state is not changed.** An on-drawing `x` stays.
- `TAG_DW` number, width, and height stay in full.
- Built-in frames and project frames previously registered by 07 get a new Sheet identity. Number and title clear until 07 runs again; scale is kept.
- Drawing-list points get a new catalog identity. Points that bound the source Sheet bind the new Sheet on the copy, so the original and the copy do not overwrite each other.

Before a copy enters the drawing list, rerun 07 so number, title, and Sheet metadata are complete.

## Unknown blocks

LoopFlow only handles blocks listed in the `Tag_Blocks.3dm` contract (the kinds in this file, plus project-registered title frames). Commands that must read a Tag contract stay at zero write and report or skip per that command:

- **No data is written.** If the flow has a report, names are listed for you to judge.
- Similar names are not guessed as a known Tag.
- Ordinary blocks are not auto-registered as title frames. A frame must be ticked by hand in the [07 Sheet numbering](./COMMANDS.md#07-sheet-numbering) list.
