# Changelog

All notable changes to LoopFlow will be documented here.

---

## [2.0.3] - 2026-08-23

Install this version. Same workflow as 2.0.2.

- Tag and other commands find the installed package after Rhino copies the script to a temp folder
- Do not mix 1.x and 2.0 in the same project. Do not overwrite `v2.0.0`, `v2.0.1`, or `v2.0.2`

---

## [2.0.2] - 2026-08-23

Install this version. Same workflow as 2.0.0 / 2.0.1.

- Include `tag_templates.json` in the yak so Laser, Grab, Index, Infuser, and TAG-O can find Tag templates after a Package Manager install
- Do not mix 1.x and 2.0 in the same project. Do not overwrite `v2.0.0` or `v2.0.1`

---

## [2.0.1] - 2026-08-22

Package Manager listing only. Same product as 2.0.0.

- Package icon and a short purpose description
- Install from Package Manager or the `v2.0.1` yak. Do not mix 1.x and 2.0 in the same project

---

## [2.0.0] - 2026-08-22

Rebuild for Rhino 8. Install with one `.yak`. Do not mix 1.x and 2.0 in the same project.

- Excel Dictionary (Chinese or English headers), Type layers, space frames, write/validate metadata, and a published Registry
- Tags, Layout ID, Catalog, Infuser, TAG-O (marks stale or disconnected tags; no auto-repair)
- Anchor Frame, Extract, Duplicate Layout, Worksession, bilingual UI
- Official `Tag_Blocks.3dm` and Dictionary templates copy to `Documents\LoopFlow` on first command
- Cabinets, 2D tools, and quantity takeoff are not in 2.0

---

## [1.0.0] - 2026-04-23

First public release.

### Commands
- **LF_Nexus** — Data hub: Dict. to Layer, SpaceBoundary, TagTrigger, TagChecker, Layer to Dict.
- **LF_Cabinet_Suite** — Cabinet generator (30 combinations) with BOM dimension data
- **LF_Push_3D_to_JSON** — Push 3D object data to Project_Registry.json
- **LF_Anchor_Frame** — Generate anchor frame for Tagger commands
- **LF_Tagger_Layout_ID** — Auto-number Layout sheets and write to title blocks
- **LF_Tagger_Laser / LF_Tagger_Grab** — Link material/furniture/door Tag Blocks to 2D drawing data
- **LF_Tagger_Index** — Link elevation/section index Tag Blocks to Detail Views
- **LF_Infuser_Part / LF_Infuser_All** — Write data into Tag Blocks
- **LF_2D_DW_Gen** — Generate 2D door/window symbols (8 door + 3 window styles)
- **LF_2D_Cabinet_Gen** — Generate 2D cabinet symbols
- **LF_2D_Shelf_Gap** — Generate equally spaced shelf dividers
- **LF_Sync_Worksession** — Multi-user worksession sync
- **LF_Dictionary_Editor** — Open dictionary Excel directly
- **LF_Data_Viewer** — Inspect UserText data on 3D objects
- **LF_Extract_CP** — Extract Section Tools output by color to new layers
- **LF_Duplicate_Layout** — Duplicate selected Layouts in batch
- **LF_TAG-O** — View all Tag Block states (linked / unlinked / broken)
