# LoopFlow 2.0 — English UI Copy

English copy for review. The `id` values are unchanged from `wip/docs/介面語系.md`; `%s` placeholders must remain unchanged when these strings are wired into the application.

## Language

| id | English |
|---|---|
| `locale.title` | LoopFlow |
| `locale.choose` | Choose interface language / 選擇介面語言 |
| `locale.zh` | Traditional Chinese |
| `locale.en` | English |
| `locale.hint` | You can change this later by right-clicking the Document button (LFLanguage). / 之後可用 Document 按鈕右鍵切換（指令 LFLanguage）。 |
| `locale.saved.zh` | Interface language set to Traditional Chinese. |
| `locale.saved.en` | Interface language set to English. |
| `locale.cancelled.first` | Language selection canceled. Nothing was saved, so you will be asked again next time. |
| `locale.cancelled.switch` | Language change canceled. |

## Dictionary column labels

| id | English |
|---|---|
| `dict.col.layer` | Rhino Layer |
| `dict.col.space` | _01_Space Name |
| `dict.col.construction` | _02_Construction |
| `dict.col.type_id` | _03_Type ID |
| `dict.col.type_name` | _04_Type Name |
| `dict.col.elev_basis` | _05_Elevation Basis |
| `dict.col.elev_calc` | _06_Elevation Value |
| `dict.col.uuid` | _07_UUID |
| `dict.col.remarks` | _08_Remarks |
| `dict.col.w` | Q_01_Width W |
| `dict.col.d` | Q_02_Depth D |
| `dict.col.h` | Q_03_Height H |
| `dict.col.unit` | Q_04_Unit |
| `dict.col.rule` | Q_05_Measurement Rule |
| `dict.col.qty` | Q_06_Quantity |

## Command dispatch

| id | English |
|---|---|
| `dispatch.001` | Warning: %s |
| `dispatch.002` | Unknown command: %s |

## Catalog

| id | English |
|---|---|
| `catalog.001` | Catalog anchor points are persistent controls. Do not delete them after creating the drawing index, and move them together with the index. |
| `catalog.002` | Drawing name, Drawing number |
| `catalog.003` | Anchor points loaded. |
| `catalog.004` | Anchor points paired. |
| `catalog.005` | Drawing-index TXT exported. |
| `catalog.006` | Export drawing-index TXT |
| `catalog.007` | Drawing-index panel closed. |
| `catalog.008` | This document has no schema. Operation stopped; no changes were made. |
| `catalog.009` | Tag templates loaded. |
| `catalog.010` | No matching drawing-number and drawing-name anchors were found. Operation stopped; no changes were made. |
| `catalog.011` | The anchor points belong to multiple drawing indexes. Operation stopped; no changes were made. |
| `catalog.012` | The drawing-index ID is not a valid UUID. Operation stopped; no changes were made. |
| `catalog.013` | Anchor selection canceled. No changes were made. |
| `catalog.014` | There are no drawing-index anchors to clear. |
| `catalog.015` | Clear operation canceled. No changes were made. |
| `catalog.016` | The drawing-number and drawing-name anchor counts do not match on every page. Operation stopped; no changes were made. |
| `catalog.017` | A drawing-name anchor is not on the same row as its drawing-number anchor. Operation stopped; no changes were made. |
| `catalog.018` | Drawing index created with %s text items. |
| `catalog.019` | Updated %s drawing-index text items. |
| `catalog.020` | The drawing-number and drawing-name anchor bindings do not match. Export stopped. |
| `catalog.021` | Sheet metadata is out of date. Run Layout ID first. Export stopped. |
| `catalog.022` | This Rhino file has not been saved. Choose where to save the drawing-index TXT file. |
| `catalog.023` | Drawing-index review list |
| `catalog.024` | There are no Layouts to include in the drawing index. Run Layout ID first. |
| `catalog.025` | LF_Catalog drawing index |
| `catalog.026` | (empty) |
| `catalog.027` | Drawing-number anchors must be standalone Points on a Layout. Operation stopped; no changes were made. |
| `catalog.028` | Drawing-name anchors must be standalone Points on a Layout. Operation stopped; no changes were made. |
| `catalog.029` | Unknown catalog field: %s. |
| `catalog.030` | The selected anchors belong to different drawing indexes. Operation stopped; no changes were made. |
| `catalog.031` | Restored %s %s anchors to their original positions. |
| `catalog.032` | This will clear all data from the drawing-index anchors, return the points to their original layers, and delete the index text. Continue? |
| `catalog.033` | Clear anchors |
| `catalog.034` | Restored %s anchors and deleted %s drawing-index text items. |
| `catalog.035` | The anchors could not be paired. Operation stopped; no changes were made. |
| `catalog.036` | No Sheets are selected. Operation stopped; no changes were made. |
| `catalog.037` | More Sheets are selected than there are available anchors. Operation stopped; no changes were made. |
| `catalog.038` | Sheet metadata is out of date. Run Layout ID first. Operation stopped; no changes were made. |
| `catalog.039` | Drawing-index update canceled. |
| `catalog.040` | Skipped %s rows. |
| `catalog.041` | The drawing-number and drawing-name anchor bindings do not match. Operation stopped; no changes were made. |
| `catalog.042` | Eto UI is unavailable, so the drawing-index panel cannot be opened. |
| `catalog.043` | Drawing-number anchors: %s　Drawing-name anchors: %s　Selected Layouts: %s |
| `catalog.044` | Select drawing-number anchors (standalone Points; Esc to cancel) |
| `catalog.045` | Select drawing-name anchors (standalone Points; Esc to cancel) |
| `catalog.046` | A Block or Block sub-object was selected. Operation stopped; no changes were made. Anchors must be standalone Points. |
| `catalog.047` | The selection is not a standalone Point. Operation stopped; no changes were made. |
| `catalog.048` | Could not bind the Sheet. Operation stopped; no changes were made. |
| `catalog.049` | Select drawing-number anchors |
| `catalog.050` | Select drawing-name anchors |
| `catalog.051` | Select Layouts |
| `catalog.052` | Generate drawing numbers and names |
| `catalog.053` | Clear anchors and restore layers |
| `catalog.054` | Export TXT |
| `catalog.055` | Drawing no. |
| `catalog.056` | Drawing name |

## Dictionary

| id | English |
|---|---|
| `dictionary.001` | The Dictionary contains prohibited `_CB.*` columns. Operation stopped. |
| `dictionary.002` | The Dictionary columns do not match schema 1. Operation stopped; column prefixes will not be used to guess the schema. |
| `dictionary.003` | Dictionary loaded with %s Types. |
| `dictionary.004` | The Dictionary must have 15 columns; %s were found. Operation stopped. |
| `dictionary.005` | Unknown Dictionary version header: %s. Operation stopped; the format will not be guessed. |
| `dictionary.006` | Dictionary validation failed with %s issues. Operation stopped. |
| `dictionary.007` | Dictionary loaded with %s Types and %s warnings. |
| `dictionary.008` | Dictionary file %s was not found. Put it back in the same folder as the .3dm file, or choose another .xlsx file in that folder. No file was created. |
| `dictionary.009` | (blank) |
| `dictionary.010` | The measurement rule is not defined on row %s. Quantity will be left blank. |
| `dictionary.011` | On row %s, calculation field %s should be blank and was ignored. |
| `dictionary.012` | Row %s is missing `layer_path`. |
| `dictionary.013` | Row %s: %s |
| `dictionary.014` | The `type_id` on row %s duplicates row %s: %s |
| `dictionary.015` | The `layer_path` on row %s duplicates row %s. |
| `dictionary.016` | Invalid elevation basis on row %s: %s |
| `dictionary.017` | The unit and measurement rule on row %s have incompatible or unknown dimensions: %s / %s |
| `dictionary.018` | Row %s is missing `type_display_name`. |
| `dictionary.019` | No Dictionary has been assigned to this file. Save the file first, then use Nexus menu 2 to choose an .xlsx file from the same folder as the .3dm file. |
| `dictionary.020` | Dictionary file %s was not found. Put it back in the same folder as the .3dm file, or use Nexus menu 2 to choose another .xlsx file from that folder. |
| `dictionary.021` | Export file %s was not found. Run LF_Export_Type_Layers first. |
| `dictionary.022` | Found %s. |
| `dictionary.023` | Opened exported Dictionary %s. |
| `dictionary.024` | Opened source Dictionary %s. |
| `dictionary.025` | Unknown Dictionary file type: %s |
| `dictionary.026` | Could not open %s: %s |
| `dictionary.027` | Missing `type_id`. |
| `dictionary.028` | Unknown `type_category`; cannot split `type_id`: %s |
| `dictionary.029` | `type_id` split successfully. |
| `dictionary.030` | `type_id` is missing a sequence number: %s |
| `dictionary.031` | This file is for review only. It cannot be opened as the project Dictionary or overwrite %s. When merging blue `added_in_rhino` entries, assign each one a new `_03_Type ID`; do not reuse an old layer number. |
| `dictionary.032` | Layers are in sync and the file can be saved. Scan, Apply, and Publish are not implemented yet. |
| `dictionary.033` | Type Layer sync completed (%s): %s created, %s retained. |
| `dictionary.034` | Dictionary %s was not found. Put it back in the same folder as the .3dm file (the Dictionary may be renamed), then choose the .xlsx file for this project in the window that opens. |
| `dictionary.035` | Layer differences exported. The project Dictionary was not changed. |
| `dictionary.036` | Type Layer sync canceled. |
| `dictionary.037` | A reverse export cannot overwrite the project Dictionary. |
| `dictionary.038` | The export folder does not exist and will not be created. |
| `dictionary.039` | Exported %s to the same folder as the .3dm file. The project Dictionary was not changed. |
| `dictionary.040` | Type Layer sync failed. Layers and reference lines created during this run were removed. |
| `dictionary.041` | Excluded %s sublayers under `20_DW`; no Types were created for them. |
| `dictionary.042` | The project name cannot be blank or contain `: \ / * ? " < > \|`. |
| `dictionary.043` | Export Type Layers cannot overwrite the project Dictionary. |
| `dictionary.044` | Project-name entry canceled. |
| `dictionary.045` | Dictionary selection canceled. |

## Document

| id | English |
|---|---|
| `document.001` | Traditional Chinese |
| `document.002` | Interface language set to Traditional Chinese. |
| `document.003` | Interface language set to English. |
| `document.004` | Language selection canceled. Nothing was saved, so you will be asked again next time. |
| `document.005` | Language change canceled. |
| `document.006` | The language menu is unavailable. |
| `document.007` | Opened the LoopFlow documentation. |
| `document.008` | Could not open the LoopFlow documentation page. / %s |

## Extract CP

| id | English |
|---|---|
| `extract_cp.001` | No matching View was found. |
| `extract_cp.002` | Select the section layers to extract (multiple selection allowed): |
| `extract_cp.003` | Extract editable linework |
| `extract_cp.004` | Previous output detected |
| `extract_cp.005` | Editable linework extracted. |
| `extract_cp.006` | Missing root layer name. |
| `extract_cp.007` | Matching View found. |
| `extract_cp.008` | Extracted “%s”: %s objects. |
| `extract_cp.009` | Extraction complete: %s objects copied. |
| `extract_cp.010` | A previous extraction exists for “%s.” Choose Replace, Add New, or Skip. |
| `extract_cp.011` | Copied %s objects to %s. |
| `extract_cp.012` | Source index: %s unique, %s unidentified, %s with multiple sources. |
| `extract_cp.013` | Output was created despite an incomplete index. |
| `extract_cp.014` | No Rhino session is available. |
| `extract_cp.015` | Section layer “%s” matches more than one View and was skipped. No match was guessed. |
| `extract_cp.016` | Skipped %s sections with existing output. |
| `extract_cp.017` | Run Extract in 2D model space, not on a Layout page. |
| `extract_cp.018` | No Visible, Hatch, or Curve layers were found for the Clipping Drawing. |
| `extract_cp.019` | Extraction canceled. |
| `extract_cp.020` | No section layers are selected. |
| `extract_cp.021` | Skipped the previous output for “%s.” |
| `extract_cp.022` | Unknown rerun option. |
| `extract_cp.023` | This Rhino session cannot copy objects. |
| `extract_cp.024` | The Drawing for “%s” was edited manually and will not be overwritten. Choose Add New to create another version. |
| `extract_cp.025` | Replace previous output |
| `extract_cp.026` | Add new version (keep existing) |
| `extract_cp.027` | Skip |

## TAG-O

| id | English |
|---|---|
| `tag_o.001` | (no page) |
| `tag_o.002` | OK |
| `tag_o.003` | Source missing |
| `tag_o.004` | Unlinked |
| `tag_o.005` | Out of date |
| `tag_o.006` | Not checked |
| `tag_o.007` | (unsaved) |
| `tag_o.008` | Out-of-date Tags show `!` in auto-filled fields and are highlighted orange. Unlinked Tags show `?` and are highlighted red. Repair is not implemented yet. |
| `tag_o.009` | No space boundaries; overlap check skipped |
| `tag_o.010` | Out-of-date Tags show `!` in orange; unlinked Tags show `?` in red. Unbound Tags are not listed. Repair is not implemented yet. |
| `tag_o.011` | Checked %s Tags. |
| `tag_o.012` | Active: %s. |
| `tag_o.013` | Out of date and not synced |
| `tag_o.014` | Out of date / ambiguous |
| `tag_o.015` | This file has no Layout pages. Operation stopped; no changes were made. |
| `tag_o.016` | File: %s |
| `tag_o.017` | Scan: %s |
| `tag_o.018` | Scanned %s Tags |
| `tag_o.019` | ── Tag binding status (%s items) ── |
| `tag_o.020` | (locked) |
| `tag_o.021` | Select an item to jump to its Tag (the view zooms out slightly to show the title block) |
| `tag_o.022` | ── Spaces without a Finish Tag ── |
| `tag_o.023` | Every space has a Finish Tag |
| `tag_o.024` | Unlinked: %s. |
| `tag_o.025` | Locked but still unlinked: %s. |
| `tag_o.026` | Not checked (unknown Block): %s. These do not count as passing. |
| `tag_o.027` | Title blocks: %s |
| `tag_o.028` | Doors/windows: %s |
| `tag_o.029` | Covered but not counted as unbound: %s. |
| `tag_o.030` | No Tags were found that can be checked |
| `tag_o.031` | No bound Tags were found |
| `tag_o.032` | (unnamed page) |
| `tag_o.033` | ── Spaces without a Finish Tag (%s) ── |
| `tag_o.034` | [Details] %s |
| `tag_o.035` | No Registry is available, so out-of-date status cannot be determined. Source availability will still be checked. |
| `tag_o.036` | The current Registry is unavailable. Using last-good instead. |
| `tag_o.037` | The project name has not been set, so the Registry cannot be read. Run Nexus menu 2 first. |

## Infuser

| id | English |
|---|---|
| `infuser.001` | Entire file |
| `infuser.002` | Some Height and Finish values were read from the current model and are not yet in the Registry. |
| `infuser.003` | Not yet in Registry |
| `infuser.004` | Processed %s Layout pages. |
| `infuser.005` | Matched the target View to a Sheet. |
| `infuser.006` | Furniture name resolved. |
| `infuser.007` | The target View's page has no Sheet metadata. Run Layout ID first. |
| `infuser.008` | The target View matches more than one Sheet. No match was guessed. |
| `infuser.009` | The target Sheet has no drawing number. |
| `infuser.010` | The Index Tag has no target View. |
| `infuser.011` | The bound target Detail no longer exists. |
| `infuser.012` | The furniture Tag has no source Block name. |
| `infuser.013` | Processed Layout page “%s.” |
| `infuser.014` | Updated %s Tags. |
| `infuser.015` | Locked |
| `infuser.016` | Door/window or manual |
| `infuser.017` | Title block |
| `infuser.018` | Unknown Block |
| `infuser.019` | Object not found in Registry |
| `infuser.020` | No Registry (publish first) |
| `infuser.021` | Ambiguous source |
| `infuser.022` | Furniture name mismatch |
| `infuser.023` | Target drawing number missing |
| `infuser.024` | Target missing |
| `infuser.025` | Unlinked; values not updated |
| `infuser.026` | Run Infuser Part on a Layout page. Operation stopped; no changes were made. |
| `infuser.027` | The current Layout page could not be identified. Operation stopped; no changes were made. |
| `infuser.028` | Drawing number read from the target page name. |
| `infuser.029` | The bound target Layout no longer exists. |
| `infuser.030` | Target Sheet used. |
| `infuser.031` | Furniture Block name “%s” does not match the expected format `FF-01__Chair-1`. |
| `infuser.032` | Skipped: %s. |
| `infuser.033` | Warning: %s. |
| `infuser.034` | …and %s more. |
| `infuser.035` | No Registry was found. Only Tags that do not require the Registry will be updated. |
| `infuser.036` | Registry revision %s loaded. |
| `infuser.037` | The project name has not been set, so the Registry cannot be read. Run Nexus menu 2 to sync Type Layers from the Dictionary first. |
| `infuser.038` | Could not read the Registry: %s |
| `infuser.039` | The Registry is invalid. Operation stopped; no Tags were updated. %s |
| `infuser.040` | The current Registry is unavailable. Using last-good revision %s. |

## Nexus — Write and verify metadata

| id | English |
|---|---|
| `nexus_metadata.001` | Identity verification passed. Space and elevation data are not ready, so publishing is unavailable. |
| `nexus_metadata.002` | Using the injected Type Catalog. |
| `nexus_metadata.003` | Applied ID and Type data to %s objects. Space and elevation data were not written. Publishing is unavailable. |
| `nexus_metadata.004` | Scan canceled. |
| `nexus_metadata.005` | Partial scan completed for %s objects. This does not confirm that the full project is ready to publish. |
| `nexus_metadata.006` | Full scan completed for %s objects. No data has been written, so publishing is unavailable. |
| `nexus_metadata.007` | Apply canceled. |
| `nexus_metadata.008` | Verification still has %s unresolved issues. Publishing is unavailable. |
| `nexus_metadata.009` | Rollback canceled. |
| `nexus_metadata.010` | There is no ID mapping to restore. |
| `nexus_metadata.011` | Restored %s `object_id` values. |
| `nexus_metadata.012` | New IDs in the mapping must be lowercase UUID v4 values. |
| `nexus_metadata.013` | Applying this mapping would still create duplicate `object_id` values. Operation stopped; IDs were not changed automatically. |
| `nexus_metadata.014` | There are no objects ready to update. The remaining %s items need an ID mapping or Type correction. |
| `nexus_metadata.015` | %s items remaining. |
| `nexus_metadata.016` | This object is in more than one space. Choose the space it belongs to: |
| `nexus_metadata.017` | Space and elevation data applied. Publishing is unavailable. |
| `nexus_metadata.018` | Space/elevation scan completed: %s objects and %s EXT objects. Publishing is unavailable. |
| `nexus_metadata.019` | Space/elevation scan canceled. |
| `nexus_metadata.020` | Applying Space/elevation data was canceled. |
| `nexus_metadata.021` | There is no Space/elevation data to write. |
| `nexus_metadata.022` | Registered %s Space Boundaries. Model object Space fields were not changed. |
| `nexus_metadata.023` | Level-boundary selection canceled. |
| `nexus_metadata.024` | Choose FFL or FL for the level boundary. |
| `nexus_metadata.025` | Elevation must be a number, such as 0 or 320. |
| `nexus_metadata.026` | No level boundaries are selected. Select closed curves, then press Enter. |
| `nexus_metadata.027` | Registered %s %s level boundaries at elevation %s. |
| `nexus_metadata.028` | Space Boundary registration canceled. |
| `nexus_metadata.029` | No Space Boundaries are selected. Select closed curves, then run the command again. |
| `nexus_metadata.030` | The same `space_id` appears on multiple boundaries. Operation stopped; IDs were not changed automatically. |
| `nexus_metadata.031` | Plan overlap on different levels is allowed: %s. Boundaries on the same level must match the same level boundary. |
| `nexus_metadata.032` | %s curves are invalid because they are open or have too few control points. |
| `nexus_metadata.033` | Level boundary type |
| `nexus_metadata.034` | Choose a level boundary type |
| `nexus_metadata.035` | Level boundary type selection canceled. |
| `nexus_metadata.036` | Level-boundary selection canceled. |
| `nexus_metadata.037` | Elevation (for example, 0 or 320) |
| `nexus_metadata.038` | Elevation entry canceled. |
| `nexus_metadata.039` | Space-boundary selection canceled. |
| `nexus_metadata.040` | Space name |
| `nexus_metadata.041` | Space-name entry canceled. |
| `nexus_metadata.042` | %s curves are invalid because they are open, have too few control points, or are missing a name or level. |
| `nexus_metadata.043` | %s spaces match multiple level boundaries at the same elevation. Operation stopped. |
| `nexus_metadata.044` | %s spaces do not match a level boundary. A space boundary must be within ±%s elevation of a level boundary and entirely inside it. |
| `nexus_metadata.045` | Spaces overlap on the same level. Operation stopped. Conflicts: %s |
| `nexus_metadata.046` | Run Nexus 5 — Write Model Metadata to write the correct data back to the model. |
| `nexus_metadata.047` | Type ID |
| `nexus_metadata.048` | Type category |
| `nexus_metadata.049` | Type sequence |
| `nexus_metadata.050` | Construction status |
| `nexus_metadata.051` | Remarks |
| `nexus_metadata.052` | Data revision |
| `nexus_metadata.053` | Space ID |
| `nexus_metadata.054` | Elevation basis |
| `nexus_metadata.055` | Elevation value |
| `nexus_metadata.056` | Display elevation |
| `nexus_metadata.057` | UUID not assigned |
| `nexus_metadata.058` | Invalid UUID format |
| `nexus_metadata.059` | Duplicate UUID |
| `nexus_metadata.060` | Unknown Type |
| `nexus_metadata.061` | Layer not mapped in Dictionary |
| `nexus_metadata.062` | Ambiguous space match |
| `nexus_metadata.063` | Elevation basis is BC, but the object is not a Block |
| `nexus_metadata.064` | Invalid elevation basis |
| `nexus_metadata.065` | Bounding box unavailable |
| `nexus_metadata.066` | Obsolete size/quantity fields |
| `nexus_metadata.067` | Verification found %s noncompliant objects. |
| `nexus_metadata.068` | The noncompliant objects are selected: |
| `nexus_metadata.069` | Verification passed. Data for %s objects matches the written values. |
| `nexus_metadata.070` | Verification has not passed. Publishing is unavailable. |
| `nexus_metadata.071` | …and %s more. |
| `nexus_metadata.072` | Verification canceled. |
| `nexus_metadata.073` | %s has not been written (expected %s) |
| `nexus_metadata.074` | %s currently contains “%s” but should not exist |
| `nexus_metadata.075` | %s is “%s”; expected “%s” |
| `nexus_metadata.076` | (empty) |

## Nexus

| id | English |
|---|---|
| `nexus.001` | Open-project check complete. You can now run Type Layers, register level and space boundaries, and write or verify metadata. Use the separate commands to export the Dictionary or publish. |
| `nexus.002` | Open-project check |
| `nexus.003` | Sync Type Layers from Dictionary |
| `nexus.004` | Register level boundaries (closed curves) |
| `nexus.005` | Register space boundaries (closed curves inside a level boundary) |
| `nexus.006` | Write/verify model metadata |
| `nexus.007` | There are no fields to write. |
| `nexus.008` | Publishing is unavailable. |
| `nexus.009` | Scan completed for %s objects. No data has been written. Spaces: %s EXT. Publishing is unavailable. |
| `nexus.010` | Space/elevation |
| `nexus.011` | Updated %s objects with %s. |
| `nexus.012` | Open-project check canceled. |
| `nexus.013` | Rhino is not available, so the project name and document units cannot be read. No files were changed. |
| `nexus.014` | The project name has not been set. Use menu 2 to sync Type Layers from the Dictionary. |
| `nexus.015` | Dictionary file %s was not found. Put it back in the same folder as the .3dm file, or use menu 2 to choose it again. |
| `nexus.016` | The document unit is %s, not cm. You can continue, but dimension handling is not yet guaranteed to be safe. Switching to cm is recommended. |
| `nexus.017` | Console step not implemented: %s |
| `nexus.018` | Unknown `schema_version`: %s. Operation stopped; the format will not be guessed. |
| `nexus.019` | Unknown Identity action: %s |
| `nexus.020` | Register level boundaries (3) and space boundaries (4) first. |
| `nexus.021` | 1  Open-project check |
| `nexus.022` | 2  Sync Type Layers from Dictionary |
| `nexus.023` | 3  Register level boundaries (closed curves) |
| `nexus.024` | 4  Register space boundaries (closed curves inside a level boundary) |
| `nexus.025` | 5  Write model metadata |
| `nexus.026` | 6  Verify model metadata (no changes) |
| `nexus.027` | Open-project check complete. Choose a step, or press Esc to cancel. |
| `nexus.028` | Cancel |
| `nexus.029` | Open-project check complete. The remaining steps were canceled. |
| `nexus.030` | Enter the project name (layer prefix) |
| `nexus.031` | Choose this project's Dictionary Excel file (must be in the same folder as the .3dm file) |
| `nexus.032` | Dictionary filename (.xlsx in the same folder as the .3dm file) |

## Publish Registry

| id | English |
|---|---|
| `registry.001` | Publishing canceled. |
| `registry.002` | A partial selection cannot be published. Run Nexus menu 6 and pass verification before publishing. |
| `registry.003` | The project name has not been set. Run Nexus menu 2 to sync Type Layers from the Dictionary first. |
| `registry.004` | The Registry is locked by another process and will not be overwritten. |
| `registry.005` | Registry lock released. |
| `registry.006` | Registry lock acquired. |
| `registry.007` | There is no lock to release. |
| `registry.008` | The lock is now owned by another process and will not be deleted. |
| `registry.009` | Could not remove the stale lock: %s |
| `registry.010` | Could not release the lock: %s |
| `registry.011` | Could not create the lock: %s |
| `registry.012` | The current Registry file is in use, usually because cloud sync is still writing it. Wait for syncing to finish, then reopen Rhino and publish again. Do not delete `Project_Registry.json`. |
| `registry.013` | The Registry payload must be an object. |
| `registry.014` | `project_id` must be a valid project name matching the layer prefix. Run Nexus menu 2 first. |
| `registry.015` | Published Registry revision %s. |
| `registry.016` | Could not create the Registry folder: %s |
| `registry.017` | The current Registry's `project_id` does not match this publication. |
| `registry.018` | Could not read the pending file after writing it: %s |
| `registry.019` | Publishing interrupted: %s |
| `registry.020` | The current Registry could not be read. Operation stopped; it was not overwritten. %s |
| `registry.021` | Could not update last-good. Operation stopped; the current Registry was not overwritten. %s |
| `registry.022` | The new data was written to last-good. Publish again after syncing finishes. |
| `registry.023` | Atomic replace failed. The current file was not deleted. %s |
| `registry.024` | Published Registry revision %s, but last-good could not be written. |
| `registry.025` | Registry payload passed validation. |
| `registry.026` | `schema_version` must be an integer. |
| `registry.027` | `project_id` must be a valid project name matching the layer prefix and cannot contain path characters. |
| `registry.028` | `registry_revision` must be a positive integer starting at 1. |
| `registry.029` | Missing `published_at`. |
| `registry.030` | Missing `model_unit`. |
| `registry.031` | `extension` must be an object. |
| `registry.032` | `types` must be an array. |
| `registry.033` | `spaces` must be an array. |
| `registry.034` | `objects` must be an array. |
| `registry.035` | `spaces[]` must include the reserved EXT entry. |
| `registry.036` | `%s[%s]` must be an object. |
| `registry.037` | `%s[%s]` contains unknown core fields: %s. |
| `registry.038` | `%s[%s]` is missing core fields: %s. |
| `registry.039` | The Registry contains unknown core fields: %s. Store non-core data under `extension` only. |
| `registry.040` | The Registry is missing core fields: %s. |
| `registry.041` | `types[%s]` is missing `type_id`. |
| `registry.042` | EXT `level_id` must be null. |
| `registry.043` | EXT `space_display` must be `EXT`. |
| `registry.044` | `objects[%s]` must be an object. |
| `registry.045` | `objects[%s]` cannot contain size or quantity fields: %s. |
| `registry.046` | `object_id` in `objects[%s]` must be a lowercase UUID v4. |
| `registry.047` | `type_id` in `objects[%s]` does not exist in `types[]` for this revision. |
| `registry.048` | `space_id` in `objects[%s]` must be a UUID or `EXT`. |
| `registry.049` | `space_id` in `spaces[%s]` must be a UUID or `EXT`. |

## Duplicate Layout

| id | English |
|---|---|
| `duplicate_layout.001` | How many copies? |
| `duplicate_layout.002` | Rebind the Tags on the new pages, then run Layout ID if needed. |
| `duplicate_layout.003` | Created %s Layout copies. |
| `duplicate_layout.004` | The source Layout contains no objects. |
| `duplicate_layout.005` | This Rhino session cannot duplicate Layout pages. |
| `duplicate_layout.006` | Source: %s |
| `duplicate_layout.007` | Layout “%s” was not found. |
| `duplicate_layout.008` | This document has no Layouts. Create at least one page first. |
| `duplicate_layout.009` | Duplicate Layout canceled. |
| `duplicate_layout.010` | Source Layout %s contains no objects. No copies were created. |
| `duplicate_layout.011` | The number of copies must be between %s and %s. |
| `duplicate_layout.012` | Could not create Layout “%s.” |
| `duplicate_layout.013` | Could not copy objects from “%s.” |
| `duplicate_layout.014` | Undefined Sheet field: %s |
| `duplicate_layout.015` | Drawing number cannot be incremented: %s |

## Grab

| id | English |
|---|---|
| `grab.001` | “%s” is not supported by Grab. Operation stopped; no changes were made. |
| `grab.002` | Select a Tag to bind (Esc to cancel) |
| `grab.003` | Select the source model object (Esc to cancel) |
| `grab.004` | Select the source furniture Block (Esc to cancel) |
| `grab.005` | “%s” is a manual-only Tag and cannot be bound with Grab. |
| `grab.006` | Use Laser to bind “%s.” Grab made no changes. |
| `grab.007` | Use Index to bind “%s.” Grab made no changes. |
| `grab.008` | “%s” does not bind to a model source. Grab made no changes. |
| `grab.009` | Select a Tag Block. Operation stopped; no changes were made. |
| `grab.010` | This Tag is locked. Unlock it before binding. |
| `grab.011` | Source UUID bound. |
| `grab.012` | Furniture Block name bound. |
| `grab.013` | Unknown Block “%s.” Operation stopped; no changes were made. |
| `grab.014` | The source matches more than one 3D object. Operation stopped; no match was guessed. |
| `grab.015` | The source object does not have a UUID. Run Nexus — Write Model Metadata first. |
| `grab.016` | For a furniture Tag, select a furniture Block as the source. Operation stopped; no changes were made. |
| `grab.017` | Grab canceled. |
| `grab.018` | The selected Tag was not found. |
| `grab.019` | (unnamed) |
| `grab.020` | Invalid furniture Block name: %s. Expected format: `FF-01__Chair-1`. |

## Index

| id | English |
|---|---|
| `index.001` | Use Layout ID to write the current page's drawing number to `TAG_ELEV_0`. Index made no changes. |
| `index.002` | Use Grab to bind furniture Tags. Index made no changes. |
| `index.003` | “%s” is not supported by Index. Operation stopped; no changes were made. |
| `index.004` | (unnamed View) |
| `index.005` | (unnamed Detail) |
| `index.006` | Target View found. |
| `index.007` | Select an Index Tag to bind (Esc to cancel) |
| `index.008` | Target View bound. |
| `index.009` | Use Laser to bind “%s.” Index made no changes. |
| `index.010` | Use Grab to bind “%s.” Index made no changes. |
| `index.011` | “%s” is a manual-only Tag and cannot be bound with Index. |
| `index.012` | “%s” does not bind to a target drawing. Index made no changes. |
| `index.013` | This Detail does not match a registered View. Run Anchor Frame first. |
| `index.014` | This Detail matches more than one registered View. Operation stopped; no match was guessed. |
| `index.015` | The target View does not have a valid `lf_view_id`. Run Anchor Frame first. |
| `index.016` | Run Index on a Layout. |
| `index.017` | Index canceled. |
| `index.018` | There are no Detail Views to bind. |

## Other

| id | English |
|---|---|
| `other.001` | attr_Lock_No Update > enter x or X |
| `other.002` | x = Do not update |
| `other.003` | Do not update |
| `other.004` | Loaded %s Tag templates. |
| `other.005` | Tag template manifest not found: %s |
| `other.006` | Unknown `schema_id`: %s. Expected %s. Operation stopped; the format will not be guessed. |
| `other.007` | Microsoft JhengHei |
| `other.008` | Worksheet loaded. |
| `other.009` | Worksheet saved. |
| `other.010` | The xlsx file contains no worksheets. |
| `other.011` | The first worksheet path was not found. |
| `other.012` | The xlsx file is missing a title row or column-name row. |
| `other.013` | General |
| `other.014` | The output folder does not exist and will not be created. |
| `other.015` | Dictionary file %s was not found. No file was created. |
| `other.016` | Could not read the xlsx file: %s |
| `other.017` | Could not write the xlsx file: %s |

## Laser

| id | English |
|---|---|
| `laser.001` | Use Grab to bind furniture Tags. Laser made no changes. |
| `laser.002` | “%s” is not supported by Laser. Operation stopped; no changes were made. |
| `laser.003` | Select a Laser Tag to bind (Esc to cancel) |
| `laser.004` | (no layer) |
| `laser.005` | Multiple objects overlap here. Choose the source to tag. |
| `laser.006` | Use Grab to bind “%s.” Laser made no changes. |
| `laser.007` | “%s” is a manual-only Tag and cannot be bound with Laser. |
| `laser.008` | Use Index to bind “%s.” Laser made no changes. |
| `laser.009` | “%s” does not bind to a model source. Laser made no changes. |
| `laser.010` | Laser canceled. |
| `laser.011` | This point is not inside any registered View frame. Run Anchor Frame first. |
| `laser.012` | The View frame does not have a valid fixed transform. Run Anchor Frame again. |
| `laser.013` | The ray did not hit a 3D object with a UUID. |
| `laser.014` | The object hit by the ray has no object ID. Operation stopped; no changes were made. |
| `laser.015` | This point is inside %s overlapping View frames. Operation stopped; no View was guessed. |
| `laser.016` | The ray was drawn but did not hit a 3D object with a UUID. Check it in the 3D viewport. |

## Layout ID

| id | English |
|---|---|
| `layout_id.001` | Title blocks are ready, but no series starting page has been defined, so nothing was processed. / Name the first page of each series as follows: / **DrawingType__DrawingNumber__DrawingName / **IN__101.01__First Floor Plan / **A__101__First Floor Plan /  / --- / 1. Keep the ** prefix; it marks the start of an auto-numbered series. / 2. Pages between ** starting pages belong to the same series. / 3. For Layouts outside a ** series, enter only the drawing name. / 4. Pages prefixed with // are not auto-numbered, but must follow the same naming format. / 5. Drawing numbers and names can be edited in the Layout list. /    Auto-numbering writes them to the title block; do not edit the title block directly. / --- /  / Example / **IN__101.01__First Floor Plan / Second Floor Plan / Third Floor Plan / **IN__201.01__Elevation 1 / Elevation 2 / //S__901__Structural Plan /  / Result after automatic numbering / **IN__101.01__First Floor Plan / IN__101.02__Second Floor Plan / IN__101.03__Third Floor Plan / **IN__201.01__Elevation 1 / IN__201.02__Elevation 2 / //S__901__Structural Plan |
| `layout_id.002` | Original name |
| `layout_id.003` | New name |
| `layout_id.004` | Status |
| `layout_id.005` | Title block locked |
| `layout_id.006` | No title block on this page |
| `layout_id.007` | This page has %s title blocks, so its identity cannot be determined |
| `layout_id.008` | There are no Layout pages ready to update. Make sure each page has exactly one registered title block. |
| `layout_id.009` | There are no Layout pages ready to update. |
| `layout_id.010` | This file has no Layout pages that can be numbered. |
| `layout_id.011` | Series start |
| `layout_id.012` | Manual page; not numbered |
| `layout_id.013` | Duplicate series start; continuing the current series |
| `layout_id.014` | Layout ID review list |
| `layout_id.015` | Wrote drawing numbers to %s pages; created %s Sheet IDs and renamed %s pages. |
| `layout_id.016` | No registered title block (unregistered Blocks: %s) |
| `layout_id.017` | …and %s more pages. |
| `layout_id.018` | No series start appears before this page, so it was not numbered |
| `layout_id.019` | Drawing number: %s → %s |
| `layout_id.020` | Drawing name: %s → %s |
| `layout_id.021` | Skipped: %s |
| `layout_id.022` | This file has no Layout tabs. Operation stopped; no changes were made. |
| `layout_id.023` | Layout ID canceled. No changes were made. |
| `layout_id.024` | Skipped %s pages. See the report for details. |
| `layout_id.025` | Page name is blank |
| `layout_id.026` | Invalid manual-page format. Use `//DrawingType__DrawingNumber__DrawingName`. |

## Anchor Frame

| id | English |
|---|---|
| `anchor_frame.001` | Ceiling |
| `anchor_frame.002` | View registered. |
| `anchor_frame.003` | Enter frame offset distance |
| `anchor_frame.004` | Select exactly one Text Dot as the section-name label. Operation stopped; no changes were made. |
| `anchor_frame.005` | The Text Dot is blank. Operation stopped; no changes were made. |
| `anchor_frame.006` | More than one existing View frame was selected. Operation stopped; no frame was chosen automatically. |
| `anchor_frame.007` | No usable section geometry was found. Operation stopped; no changes were made. |
| `anchor_frame.008` | The section bounds could not be calculated. Operation stopped; no changes were made. |
| `anchor_frame.009` | No 3D model geometry intersects the Clipping Plane, so the fixed transform could not be written. |
| `anchor_frame.010` | The calculated View transform is invalid. Operation stopped; no changes were made. |
| `anchor_frame.011` | No Clipping Plane with a name containing “%s” was found. Operation stopped; no changes were made. |
| `anchor_frame.012` | The name filter “%s” matches %s Clipping Planes. Operation stopped; no match was guessed. |
| `anchor_frame.013` | View registration canceled. |

## Data Viewer

| id | English |
|---|---|
| `data_viewer.001` | Object not found. |
| `data_viewer.002` | Viewer closed. |
| `data_viewer.003` | Viewed %s objects. |
| `data_viewer.004` | (missing) |
| `data_viewer.005` | The project schema has not been written yet, but object fields can still be viewed. |
| `data_viewer.006` | This object has no UserText. |
| `data_viewer.007` | Layer: %s |
| `data_viewer.008` | Name: %s |
| `data_viewer.009` | Project: %s |
| `data_viewer.010` | The project schema is incomplete: `schema_id=%s`, `schema_version=%s`. Operation stopped; the format will not be guessed. |
| `data_viewer.011` | Unknown `schema_id`: %s. Expected %s in the project settings. Operation stopped; the format will not be guessed. |
| `data_viewer.012` | Block: %s |
| `data_viewer.013` | Document schema: %s %s |
| `data_viewer.014` | Document schema: %s |
| `data_viewer.015` | Dictionary name: %s |
| `data_viewer.016` | Missing values: %s |
| `data_viewer.017` | Legacy fields (not part of 2.0): %s |
| `data_viewer.018` | Unknown `schema_version` %s for %s. Operation stopped; the format will not be guessed. |
| `data_viewer.019` | Source: object name (legacy-file compatibility) |
| `data_viewer.020` | Override (Dictionary default: %s) |
| `data_viewer.021` | Type %s was not found in the Dictionary. |
| `data_viewer.022` | Source: legacy key %s |

## Sync Worksession

| id | English |
|---|---|
| `sync_worksession.001` | Worksession monitoring stopped. |
| `sync_worksession.002` | The Worksession could not be updated. Try again later. The previous reference was left unchanged. |
| `sync_worksession.003` | Save the file to disk before monitoring other .3dm files in the same folder. |
| `sync_worksession.004` | File change detected: %s |
| `sync_worksession.005` | Worksession reference updated. |
| `sync_worksession.006` | Monitoring started: %s (%s-second delay) |
| `sync_worksession.007` | Could not monitor folder “%s.” / %s |
| `sync_worksession.008` | Monitoring folder changed to: %s (%s-second delay) |

## Foundation

| id | English |
|---|---|
| `foundation.001` | JSON loaded. |
| `foundation.002` | The output folder does not exist, so the final file was not created. |
| `foundation.003` | Wrote %s. |
| `foundation.004` | The JSON root must be an object. |
| `foundation.005` | The file to copy was not found. |
| `foundation.006` | JSON file not found: %s |
| `foundation.007` | Could not write the file: %s |
| `foundation.008` | Could not read the JSON file: %s |
| `foundation.009` | Could not read the source: %s |
| `foundation.010` | Using built-in advanced settings. |
| `foundation.011` | Unknown language: %s |
| `foundation.012` | Using the log path from the project-settings folder. |
| `foundation.013` | Log written. |
| `foundation.014` | Using the specified log path. |
| `foundation.015` | Could not write the log: %s |
| `foundation.016` | Unknown result status: %s |
| `foundation.017` | Unknown `schema_id`: %s. Operation stopped; the format will not be guessed. |
| `foundation.018` | Unknown `schema_version` %s for %s (current: %s). Operation stopped; the format will not be guessed. |

## Paths and working folder

| id | English |
|---|---|
| `paths.001` | Rhino is not available, so the .3dm location cannot be determined. No files were changed. |
| `paths.002` | Save this file as a .3dm first. The working folder is the folder containing the .3dm file; without it, settings, the Dictionary location, and %s cannot be created. |
| `paths.003` | Dictionary filename confirmed. |
| `paths.004` | File folder confirmed. |
| `paths.005` | .3dm working folder resolved. |
| `paths.006` | Registry path resolved. |
| `paths.007` | The Dictionary filename cannot be blank. |
| `paths.008` | The Dictionary filename cannot contain `\ / : * ? " < > \|`. |
| `paths.009` | An export file cannot be used as the project Dictionary. |
| `paths.010` | %s folder resolved. |
| `paths.011` | Project name is missing, so the Registry cannot be resolved. Run Nexus menu 2 and enter the project name first. |
| `paths.012` | The project name cannot contain `\ / : * ? " < > \|` or be a folder path. |
| `paths.013` | Enter a filename only. The full path cannot be resolved until the .3dm folder is known. |
| `paths.014` | The Dictionary must be beside the .3dm file, not in a subfolder. |
| `paths.015` | Enter a filename only, without a folder path. |
| `paths.016` | The Dictionary must be an .xlsx file. |
| `paths.017` | The Dictionary must be in the same folder as the .3dm file. / Selected: %s / Required folder: %s |

## Project settings

| id | English |
|---|---|
| `project_config.001` | Project settings loaded. |
| `project_config.002` | Project settings updated. |
| `project_config.003` | No project settings file exists yet. |
| `project_config.004` | %s does not contain a settings object. Operation stopped; the contents will not be guessed. |
| `project_config.005` | Could not parse %s: %s. Operation stopped; the contents will not be guessed. |
| `project_config.006` | Could not write %s: %s |

## Rhino platform messages

| id | English |
|---|---|
| `rhino.001` | Connected to the Rhino document. The live adapter has not yet been tested in Rhino. |
| `rhino.002` | No active Rhino document. |
| `rhino.003` | Connected to the Rhino document. |
| `rhino.004` | Could not load Rhino. |
| `rhino.005` | Could not create drawing-index text. |
| `rhino.006` | A closed boundary requires at least 3 points. |
| `rhino.007` | Rhino is not available: %s |
| `rhino.008` | Unknown layer: %s |
| `rhino.009` | Unknown object: %s |
| `rhino.010` | Rhino view state restored. |
| `rhino.011` | The command returned no Result. Rhino state was restored. |
| `rhino.012` | %s objects from the snapshot could not be found during restore. All other state was restored. |
| `rhino.013` | An exception occurred while creating the snapshot. / %s |
| `rhino.014` | An exception occurred during the operation. Rhino state was restored. / %s |

## Shared prompts and buttons

| id | English |
|---|---|
| `prompts.001` | Choose interface language / 選擇介面語言 |
| `prompts.002` | You can change this later by right-clicking the Document button (LFLanguage). |
| `prompts.003` | Duplicate Layout |
| `prompts.004` | Index Binding |
| `prompts.005` | Select objects to inspect (Enter or Esc to finish) |
| `prompts.006` | Select a Block (Esc to cancel) |
| `prompts.007` | Click inside the target Detail (Esc to cancel) |
| `prompts.008` | Select the section objects and matching Text Dot (Esc to cancel) |
| `prompts.009` | Select a drawing-index anchor (standalone Point; Esc to cancel) |
| `prompts.010` | Select closed curves, then press Enter |
| `prompts.011` | Hold Ctrl or Shift to select multiple pages. Selected rows are highlighted. |
| `prompts.012` | Search by drawing name or number |
| `prompts.013` | These Blocks are not registered as title blocks. Select the actual title blocks. Unselected Blocks will be skipped and will not receive drawing numbers. |
| `prompts.014` | Use Shift to select a range, or Ctrl to add or remove items. Selected rows are highlighted. Unselected pages are excluded, and new pages are not added to an existing drawing index automatically. |
| `prompts.015` | Select All |
| `prompts.016` | Clear Selection |
| `prompts.017` | Run Grab on a Layout. |
| `prompts.018` | The clicked point is not inside a Detail. |
| `prompts.019` | Run Laser on a Layout. |
| `prompts.020` | Close |
| `prompts.021` | Distance cannot be less than %s. |
| `prompts.022` | Select a Detail first. |
| `prompts.023` | Order |
| `prompts.024` | Page name |

## Not implemented

| id | English |
|---|---|
| `runners.001` | This is the LoopFlow 2.0 test entry point for “%s.” The feature is not implemented yet (%s). |
| `runners.002` | To be scheduled |
