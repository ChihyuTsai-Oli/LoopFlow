# LoopFlow 2.0 command reference

> Each LoopFlow 2.0 Rhino command. Overall flow: [overview](./USER_GUIDE.md). Excel columns: [Dictionary guide](./Dictionary_GUIDE.md). On-drawing Tag fields: [Tag Block reference](./TAG_BLOCKS.md).
>
> Command names are the packaged names typed in the Rhino command line (no underscores).

## Project folder

Save the `.3dm` first. **The folder of that file is the project folder**: the official Dictionary sits beside the `.3dm`; project settings, Registry, and logs go under `_LoopFlow_Config/` in the same folder. Moving the whole pack to another parent, drive, or computer still works. LoopFlow does not depend on a fixed absolute path on one computer. Official Dictionary templates and `Tag_Blocks.3dm` appear in `Documents\LoopFlow` after the first product command, ready to copy into a project.

## Quick index

| Stage | Command | One line |
|---|---|---|
| Dictionary | `LFOpenDictionary` | Open the official Excel Dictionary |
| Dictionary | `LFOpenDictExport` | Open the exported Dictionary for review |
| Dictionary | `LFExportTypeLayers` | Export current Rhino layers as a Dictionary for review |
| Project / model | `LFNexus` | Project console: write Dictionary data into the model (6-step menu) |
| Registry | `LFPublishExchange` | Publish model data as a 2D-readable Registry |
| Section | Rhino Section (native) | Build drawings with Rhino’s built-in section tools |
| View | `LFAnchorFrame` | Register a section as a fixed 2D↔3D map (anchor frame) |
| Drawing | `LFExtractCP` | Copy section linework into an independently editable drawing |
| Sheet | `LFDuplicateLayout` | Duplicate whole Layouts, usually before numbering |
| Sheet | `LFTaggerLayoutID` | Number and name sheets by rule |
| Catalog | `LFCatalog` | Build a drawing list (read-only Sheet data) |
| Tag bind | `LFTaggerLaser` | Find a source object from a click plus a fixed projection |
| Tag bind | `LFTaggerGrab` | Pick the source object or furniture block directly |
| Tag bind | `LFTaggerIndex` | Bind an index tag to a registered Detail |
| Infuse | `LFInfuserPart` | Infuse display fields on tags **on this page** |
| Infuse | `LFInfuserAll` | Infuse display fields on tags **on every page** |
| Health | `LFTagO` | Live / stale / disconnected — colour only, no repair |
| Collaboration | `LFSyncWorksession` | Watch same-folder file changes and Refresh Worksession |
| Inspect | `LFDataViewer` | Click an object and read its current data |
| Docs | `LFDocument` | Open LoopFlow’s public documentation entry |
| UI | `LFLanguage` | Switch English / 正體中文; stored on this computer |

Laser, Grab, and Index are three bind methods. Use one or more as the source requires; you do not need all three. Infuser Part and All are the same action at different scope; pick one.

## Contents

**Main chain**: [01 Open official Dictionary](#01-open-official-dictionary) · [02 Open exported Dictionary](#02-open-exported-dictionary) · [03 Export Dictionary](#03-export-dictionary) · [04 Nexus](#04-nexus-project-console) · [05 Publish](#05-publish-exchange-data) · [Rhino Section](#rhino-section-native) · [06 Register View](#06-register-view-anchor-frame) · [07 Sheet numbering](#07-sheet-numbering) · [08 Drawing list](#08-drawing-list) · [09 Laser](#09-laser-projection) · [10 Grab](#10-direct-grab) · [11 Index](#11-index-to-view) · [12/13 Infuse](#1213-infuse-data) · [14 Health](#14-health-check-tag-o)

**Helpers**: [A1 Worksession](#a1-worksession-sync) · [A2 Data Viewer](#a2-data-viewer) · [A3 Extract](#a3-extract-linework) · [A4 Duplicate Layout](#a4-duplicate-layout) · [A5 Documentation](#a5-documentation) · [A6 Language](#a6-switch-interface-language)

---

## 01　Open official Dictionary

**Command**: `LFOpenDictionary`

Opens this project’s remembered official Dictionary in the system Excel app (default filename `LoopFlow_Dictionary.xlsx`). The name is stored in `_LoopFlow_Config/LoopFlow_Project.json` beside the `.3dm`. The command only opens the file; it does not edit or create it.

- If no official Dictionary has been chosen yet, run [04 Nexus](#04-nexus-project-console) **Sync Type Layers** once to pick a file.
- How to read the columns: [Dictionary guide](./Dictionary_GUIDE.md).

## 02　Open exported Dictionary

**Command**: `LFOpenDictExport`

Opens `{original name}_Export.xlsx` in the same folder, produced by [03 Export Dictionary](#03-export-dictionary). This file is for people to review. **It cannot be used as the official Dictionary and will not overwrite it.**

- If the export does not exist yet, run 03 first.

## 03　Export Dictionary

**Command**: `LFExportTypeLayers`

Exports the current Rhino layer state back to Excel (if the official file is `LoopFlow_Dictionary.xlsx`, you get `LoopFlow_Dictionary_Export.xlsx`) so you can compare the model with the official Dictionary.

**What the export contains**:

- Row 1 is a red hint: this file cannot be opened as the official Dictionary and must not overwrite the official file. Hint language, the 15 column headers, and the font follow the **source Dictionary**, not the UI language. A Chinese source uses `_03_ID編號` and Microsoft JhengHei; an English source uses `_03_Type ID` and Arial.
- The same 15 columns as the official Dictionary, plus `diff_status` coloured by difference:
  - **Red**: in the official Dictionary, missing in the model (`missing_in_rhino`).
  - **Blue**: added in the model, not yet in the Dictionary (`added_in_rhino`). These rows sit at the bottom. When merging back, give each an **unused** Type ID; do not reuse an old number.
  - **Orange**: both exist, contents differ (`modified`).
  - Unchanged stays black (`unchanged`).

Only layer-level defaults are compared, not per-object data. After review, copy needed changes back into the official Dictionary by hand.

### Dictionary review loop

03 → 02 → 01 is one review loop, not three independent tools: 03 exports the model, 02 opens it, and you manually edit 01 (the official Dictionary). Only 01 is read by [04 Nexus](#04-nexus-project-console). 02 and 03 do not feed 04 directly.

---

## 04　Nexus (project console)

**Command**: `LFNexus`

The data hub. The first run does an open check; after it passes, this 6-step menu appears. You can rerun steps; you do not have to finish them in order, but later steps usually need earlier ones:

```text
1  Open check
2  Sync Type Layers from the Dictionary
3  Register level frames (closed curves)
4  Register space frames (closed curves, inside a level frame)
5  Write model metadata
6  Validate model metadata (no write)
```

### 1　Open check

Confirms the `.3dm` is saved, then resolves Dictionary, `_LoopFlow_Config/LoopFlow_Project.json`, `project_id`, schema version, and Rhino document units from that folder.

- If the settings file has no schema yet, LoopFlow writes `loopflow.project` / `1`. You can still enter the menu without a project name; fill it in step 2.
- Unreadable settings or an unknown schema version stop the command. LoopFlow does not guess.
- A non-cm document unit is not blocked, but you get a clear warning to switch to cm.
- A missing Dictionary file does not block the menu; it warns, and you pick the file in step 2.

### 2　Sync Type Layers from the Dictionary

Syncs the official Dictionary onto Rhino layers:

- Every sync asks for a **project name** (layer prefix). The first time is empty; the usual first suggestion is `M3D`. After one confirm, later runs prefill the remembered name and you can still edit it. The project name is also the Registry subfolder name, stored in `LoopFlow_Project.json`.
- The first run opens a file picker. The Dictionary must sit beside the `.3dm`. After that, only the filename is remembered.
- If the remembered file was renamed or moved, LoopFlow asks you to put it back beside the `.3dm`, then pick again from that folder. A file in another folder is rejected and asked again; an external path is not written into the project.
- In Dictionary, missing in Rhino: create the layer and apply defaults.
- Same name already in Rhino: keep existing UserText and construction; display colour is reapplied from the Type category.
- Object instance data is not touched, and object values are not written back to the Dictionary.

### 3　Register level frames (closed curves)

Pick a closed curve as a floor datum. Choose `FFL` (finished floor) or `FL` (structural slab), then type a numeric elevation (e.g. `0`, `320`).

### 4　Register space frames (closed curves, inside a level frame)

Pick one or more closed curves as a space, and type one space name for them. The space elevation must fall within ±20 model units of a level frame, and the whole loop must sit inside that level frame (shared edges are allowed).

- Overlapping areas stop the command and list every conflict. LoopFlow does not pick a winner.
- Rooms on the same floor map to the same level frame; you do not type a floor number.

### 5　Write model metadata

**Prerequisite**: level frames (3) and space frames (4) must already be registered, or the write is blocked.

Writes each object’s ID, Type mapping, space, elevation, and data revision onto the object. If an object sits in two space frames, LoopFlow zooms to it and asks you to pick one space.

### 6　Validate model metadata (no write)

Recomputes in memory “what a write would produce now” and compares it with the object. **Nothing is written.**

- Full match: a popup says it is fine.
- Mismatch: a popup lists differences, reminds you to run step 5, and selects the problem objects.

---

## 05　Publish exchange data

**Command**: `LFPublishExchange`

**Prerequisite**: Nexus step 6 must already pass. A partial object selection cannot publish; only the whole project can.

Packs model data into a new Registry (the read-only snapshot for 2D). The official file is `_LoopFlow_Config/<project name>/Project_Registry.json` beside the `.3dm`:

1. Take an exclusive lock (so two people do not publish at once).
2. Re-read current state and bump the revision.
3. Write a temp file and fully validate it; only then replace the official file (no half-written official file).
4. On success, objects in the official scope get this publish revision in their data-revision field.

On failure, the last good official file stays. The popup lists the same mismatches as step 6 and selects the related objects.

---

## Rhino Section (native)

Not a LoopFlow command. Use Rhino 8 built-in `Section` / `Clipping` commands for plans, elevations, or sections. LoopFlow does not replace this step; the next command registers the result.

---

## 06　Register View (anchor frame)

**Command**: `LFAnchorFrame`

Registers a section as a fixed 2D↔3D map for [09 Laser](#09-laser-projection).

**Where**: **2D model space** (not Layout).

1. Window-select that section’s linework / blocks / hatches, plus **exactly one** Text Dot (the text must match a Clipping Plane name).
2. A popup asks for frame offset (default 50).
3. LoopFlow first looks for a Clipping Plane whose full name matches the Text Dot (case-insensitive). If none, it allows a longer unique name that contains that text. If candidates are not unique, it stops and does not guess.
4. The new frame is drawn on `LoopFlow::Anchor_Frame`. If you selected a 1.x registered frame, that frame is upgraded in place; a second frame is not added.

Register each section once. Later, if you **move the frame with the drawing** (no re-cut, rotate, or mirror), you do not rerun this command. Reflected ceiling plans should be mirrored left-right before you register.

---

## 07　Sheet numbering

**Command**: `LFTaggerLayoutID`

Numbers and names every Layout by rule, and creates Sheet metadata (the real source of drawing number, name, and series). The Layout page name is only the display result.

### Name format

Series starts and manual pages use the same three-column format:

```text
**category__number__title        ← ** prefix: start of an auto-numbered series
//category__number__title        ← // prefix: manual page, not auto-numbered
```

- Keep `**` on the **first page of each series**. Do not delete it after the command runs.
- `//` pages do not consume a number, but they still need all three columns.
- The drawing number only needs a **numeric tail**: `201`, `101.01`, `101.1`, `A01` are all legal. `.01` is not required.

### How auto-numbering works

Pages are scanned top to bottom. A `**` page starts a series at that number. Each following page adds **1 to the numeric tail** until the next `**`. Examples:

| Current | Next page |
|---|---|
| `201` | `202` |
| `101.9` | `101.10` (no leading zero on carry) |
| `A09` | `A10` |

If the file has no `**` and no legal `//`, the command stops and only shows the naming rules. It does not guess.

### How to run

1. Rename the first page of each series to `**category__number__title`. Later pages only need the title (third column) edited. Unnumbered pages use `//category__number__title`.
2. Run the command. If a title-frame list appears, **tick only real title frames** (e.g. `_Frame_A3_shop_drawing`). Do not tick `tag_*` marker blocks — the list defaults to none ticked.
3. A review list appears (original name / new name / status, same order as the Layout list). Confirm to write; cancel writes nothing.
4. What is written: Layout page names as three columns, title frame number and title, `TAG_ELEV_0` current-page number, and Sheet metadata in the document. **Scale (`lf_scale`) is filled by hand; this command does not touch it.**

A page with no title frame, or with two or more, is skipped and listed in the report. Other pages still write. **After inserting pages or reordering, run this again** so numbers follow the new order. Features that read this data (drawing list, and so on) should report stale data if you skip the rerun; they must not quietly show old values.

---

## 08　Drawing list

**Command**: `LFCatalog`

**Prerequisite**: 07 has already created Sheet metadata.

Reads Sheet metadata to place drawing-list text. It does not re-parse page contents. The panel has six actions:

1. **Pick number points**: independent Points for the number column; they turn red and move to `LoopFlow::Drawing_Number`.
2. **Pick name points**: another set for the title column; they turn green and move to `LoopFlow::Drawing_Name`. Together they form the grid.
3. **Select Layouts**: pick pages to include (four columns: order / number / title / page name; Shift range, Ctrl add).
4. **Generate number/title**: preview and update the list. New text is originated at the lower-left of the point, default layer `LoopFlow::Drawing_Text`. Existing text only updates its contents; **it is not pulled back to the point**. Before generate, each cell’s font, height, layer, and colour are remembered on the point, so later mid-list deletes, rebinds, or rebuilds after text deletion still use that cell’s look.
5. **Clear points and restore layers**: drop catalog data, delete generated text, and put points back on their previous layers.
6. **Export TXT**: write the current list text.

Points remember which Sheet a cell belongs to and that cell’s text look. They do not store the actual number or title, and they do not store the page name, so you can have more points than Layouts (e.g. 40 cells for 28 sheets). After generate, clear, or export, the panel closes. After the three pick actions, it stays open. There is **no Refresh and no extra Close button**, so a content-only update cannot accidentally delete cell text for a removed page with no undo.

---

## 09　Laser projection

**Command**: `LFTaggerLaser`

Click on the drawing; LoopFlow shoots along a fixed direction to find the model object on the section and writes the source bind.

1. On **Layout**, pick a Height or Finish Laser tag.
2. Click a location on the section inside the target Detail. **That point must fall inside an [06 Register View](#06-register-view-anchor-frame) frame**, or you are told to run 06 first.
3. The 2D origin is the current section linework centre inside the frame. The ray uses the direction frozen at register time. Each object is counted once. If several objects are hit, a candidate list appears (layer names only, no object IDs) for you to pick.

**No write if**: Esc, click outside the Detail, the tag is locked, the wrong block type (Grab / Index / `TAG_DW` / title frame), 0 or 2+ registered frames at the click, the ray hits nothing, or the source has no usable ID.

Everyday use does not draw a test ray. To check direction, the command line shows `DebugRay` while you pick the tag; set it to `Yes` to draw a magenta debug line (not plotted).

---

## 10　Direct grab

**Command**: `LFTaggerGrab`

No projection. Pick the source object directly — useful when section linework is clear, or when binding a furniture block.

1. On **Layout**, pick a tag.
2. Click into the target Detail to enter model space.
3. Pick the source: a 2D section curve, a 3D object, or a furniture block.

- Height / Finish tags bind the object ID.
- Item (furniture) tags bind the **block name** (e.g. `FF-01__Chair-1`) **and that instance**. Later rename or delete then shows up in [12/13 Infuse](#1213-infuse-data) and [14 Health](#14-health-check-tag-o). The same furniture type can share one block name.

**No write if**: Esc, click outside the Detail, the tag is locked, the wrong block type (Laser / Index / `TAG_DW` / title frame), or the source has no usable ID. Afterward you return to Layout.

---

## 11　Index to View

**Command**: `LFTaggerIndex`

Binds an index tag (section-detail index, elevation-direction index) to a registered View (the section of an 06 anchor frame).

1. On **Layout**, pick `TAG_SECTION_DETAIL` or `TAG_ELEV_1`–`4`.
2. From a searchable list, pick any Detail on any Layout in the file (shown as “page name + Detail name”; picking jumps and zooms).
3. The Detail model-space centre is tested against registered View frames. **Exactly one hit** writes the bind and stores the chosen page name so Infuser can find the drawing number later.

**No write if**: Esc, locked tag, wrong block type, not on a Layout, that page has no Detail, 0 or 2+ Views at the centre, or you cancel the list.

> Note: `TAG_ELEV_0` (six-direction index plaque) is not bound by this command. Direction fields are manual; the current-page number is written by [07 Sheet numbering](#07-sheet-numbering).

---

## 12/13　Infuse data

**Command**: `LFInfuserPart` (this page) / `LFInfuserAll` (every page)

Writes Registry data from 05 and Sheet metadata from 07 into already-bound tag display fields. The two commands share the same rules; only the scope differs:

- **`LFInfuserPart`**: this Layout only (including tags on Details of that page). Use after finishing one page.
- **`LFInfuserAll`**: every Layout in the file; can also run from model space. Use after a large update.

Behaviour:

- Height / Finish material and elevation fields prefer published Registry data; if that misses, they fall back to the object’s current UserText.
- Furniture tags that stored an instance read that instance’s **current** block name — a rename updates the drawing. If the instance was deleted, they show disconnected (`?`, whole tag red).
- Tags already marked disconnected by [14 Health](#14-health-check-tag-o) are **not** filled again. Rebind (09 / 10 / 11) first; the next infuse restores them.
- Locked tags, `TAG_DW`, title frames, `TAG_ELEV_0`, and all manual fields (remarks, Detail number, elevation direction, and so on) are not overwritten.
- Unbound fields show `-` and are not colour-warned.
- A summary popup reports what this run did.

---

## 14　Health check (TAG-O)

**Command**: `LFTagO`

After 12 / 13, checks every bound tag and opens a scrollable dark panel, listed in Layout order (grey lines between pages):

| Status | Colour | Automatic fields | Meaning |
|---|---|---|---|
| Live | green | unchanged | Source still exists; data is current |
| Stale | orange | `!`, whole tag orange | Source still exists, but the drawing is not current — rerun 12 / 13 |
| Disconnected | red | `?`, whole tag red | Source gone, target page deleted, or target Detail deleted — rebind, then 12 / 13 |

- Only **already bound** tags are listed. Unbound tags (`-` on the drawing) are omitted and not colour-warned.
- Click a row to highlight it, jump to that Layout, and zoom (leaving space around the title frame).
- Locked tags still list and are labelled locked, but their text and colour are not changed.
- `TAG_DW` and `TAG_ELEV_0` are out of scope.
- **Check and colour only. Nothing is auto-repaired.** 2.0 has no auto-repair; you decide what to change.

A normal round: **Infuser → TAG-O to see live or disconnected → rebind or just re-infuse.**

---

## A1　Worksession sync

**Command**: `LFSyncWorksession`

For multi-computer work, so the drawing side can see the latest 3D reference.

- The current file must already be saved to disk.
- The first run pops up “watching started” and watches `.3dm` changes in **the same folder** (temp files skipped).
- After a change, when Rhino is idle for 0.5 seconds, one Worksession Refresh runs.
- **Refresh only.** It does not Attach or Detach references, and it does not edit the `.rws` file.
- A failed Refresh retries after a delay and **does not tear down the last good reference**.
- Run again to stop watching. If the file was Save As’d to another folder, running again watches the new location.

## A2　Data Viewer

**Command**: `LFDataViewer`

Click any object to read its current canonical fields (ID, space, elevation, remarks, revision, …) without writing.

- Never writes, never changes the object name.
- Missing values show as missing. Values recovered from old fields are labelled so you can tell an unmigrated object.
- Esc or Enter to finish.

## A3　Extract linework

**Command**: `LFExtractCP`

Copies Rhino Section linework kept as a live source (drawing A) into an independently editable drawing (drawing B).

**Where**: **2D model space**.

1. Tick section root layers (the ones with Visible / Hatch / Curve children).
2. Copy under `LoopFlow_Extract` and strip 3D / drawing-A data fields, leaving drawing identity only.
3. If it maps to a registered View, source and publish revision are stored for later stale checks.
4. If that section was extracted before, you are asked to **replace**, **add**, or **skip** — a drawing you already edited by hand is not overwritten on replace unless you choose it.

Extracted drawings can move with the 06 anchor frame so they sit apart from the original. Later [09 Laser](#09-laser-projection) can use the same frame on both drawings.

## A4　Duplicate Layout

**Command**: `LFDuplicateLayout`

Duplicates whole Layouts (Details, title frames, tags), usually **before** 07 numbering.

1. Multi-select source Layouts in a taller scrollable list (Ctrl / Shift).
2. A popup asks how many copies (1–100), applied to every selected page.
3. Pages are copied through the Rhino API. **The system clipboard is not used.**

After copy:

- Except `TAG_DW`, **all tag source binds are cleared** and the tag is marked disconnected (`?`, red) so you rebind.
- **Lock state is not changed.**
- `TAG_DW` number, width, and height are kept in full.
- Built-in title frames and project frames previously registered by 07 get a new Sheet identity. Number and title are cleared until 07 runs again; scale (`lf_scale`) is kept.
- Drawing-list points get a new catalog identity. If they were bound to the source Sheet, the copy binds the new Sheet so two pages do not share one catalog record.
- New page names keep three columns and add `_CopyN`, without automatic `**` / `//`, so they are not mistaken for a new numbered series.

Cancel, a source with no objects, or a failed run leaves no half-copied pages. Before a copy enters 08, rerun 07 numbering.

## A5　Documentation

**Command**: `LFDocument`

Opens LoopFlow’s public documentation entry (not the project homepage). It does not change the model and does not guess Rhino / Windows UI language. If the page cannot open, it only explains why.

## A6　Switch interface language

**Command**: `LFLanguage` (**Document** toolbar button, right-click)

The interface is wired to English / 正體中文 strings. The first product command shows two buttons: English on the left, 正體中文 on the right. English is the default; Enter selects English. Esc or closing the window cancels that command, saves nothing, and asks again next time.

Later, right-click **Document** or type `LFLanguage` to open the same picker. The preference is stored in `%APPDATA%\LoopFlow\preferences.json` on this computer, not in the `.3dm` or `_LoopFlow_Config/`. The confirmation message uses the new language.

Fixed `Grab`, `Laser`, `W.`, `H.`, and formula prompts inside `Tag_Blocks.3dm` are block content. They stay in English and do not follow `LFLanguage`.
