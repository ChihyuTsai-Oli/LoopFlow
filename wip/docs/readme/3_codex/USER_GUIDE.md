# LoopFlow 2.0 overview

> A one-minute picture of how LoopFlow works. Command details: [command reference](./COMMANDS.md). Excel Dictionary: [Dictionary guide](./Dictionary_GUIDE.md). On-drawing Tag fields: [Tag Block reference](./TAG_BLOCKS.md).

## Core logic: three stages

**Model freely in 3D, load Type data from the Dictionary, then hand off to 2D.**

1. **Free 3D modelling**: model in Rhino as usual. LoopFlow does not write anything in the background, and it does not restrict how you draw.
2. **Dictionary into the model**: the Excel Dictionary defines defaults for each finish / work item, then syncs them to Rhino layers. After the model is built, put objects on the matching layers and write that data onto each object (ID, finish, elevation, space, and so on).
3. **Publish for 2D**: after validation, publish a read-only **Registry**. That snapshot is how model data moves from 3D to 2D. 2D tags read Type, elevation, and space from a chosen revision.

Model data flows one way: **3D owns object data, the Registry freezes one validated revision, and 2D does not write back 3D Types or objects**. 2D is still active work: sheet numbers / names, tag bindings, detail numbers, remarks, and other manual fields stay on the drawing side. If 3D changes later, return to the affected nodes, rewrite, validate, publish, and infuse again. You do not have to throw away the drawings.

## The project is a folder

The folder of the saved `.3dm` is the LoopFlow project folder. Keep the Dictionary beside the `.3dm`. LoopFlow stores the project name, the chosen Dictionary filename, Registry revisions, and logs under `_LoopFlow_Config/` in that same folder.

When you change computers or drives, move the whole project folder. As long as the `.3dm`, Dictionary, and `_LoopFlow_Config/` stay together, you do not edit absolute paths. Copying only the `.3dm` does not bring the original project settings.

Official Dictionary templates and `Tag_Blocks.3dm` will later ship with the installer: one copy stays in the package folder, and Rhino copies them to `Documents\LoopFlow` on load (existing files are not overwritten). That folder is a convenient source to copy into each project, not the project folder itself. This is not implemented yet.

## Interface language is per computer, not per project

The LoopFlow interface supports **English** and **Traditional Chinese**. The first product command shows a language picker: English on the left, 正體中文 on the right. English is the default; Enter selects English. Esc or closing the window cancels that command, saves nothing, and asks again next time.

The choice is stored in `%APPDATA%\LoopFlow\preferences.json` on this computer, not in the `.3dm` or `_LoopFlow_Config/`. Later, right-click the **Document** toolbar button or run `LFLanguage`. The same project can use different interface languages on different computers. Fixed labels and formula prompts inside `Tag_Blocks.3dm` stay in English.

The project Dictionary is whichever `.xlsx` Nexus remembered after **Sync Type Layers**. Workbooks with Chinese or English header rows both load. Switching the interface language does not switch the Dictionary file.

## The 2D / 3D boundary: Rhino Section

LoopFlow does not ship its own section engine. The 2D geometry flow sits on **Rhino 8 native Section / Clipping Drawing**. That step is the main geometric handoff:

- **Before the line**: the 3D world — free modelling, spaces, data, and publish all happen in the model.
- **After the line**: the 2D world — sheet numbering, tag binding, and display organise data that already exists. They do not rebuild geometry or redefine model data. You still choose which Views to make, how to arrange Layouts, and whether to lock tags. 2D is not a fully automatic dump.

| 3D model | Rhino Section | 2D drawing |
|---|---|---|
| Free modelling and Type Layers | Updatable plans, elevations, or sections | Register Views and the 2D↔3D map |
| Space, elevation, UUID, data revision | Passes geometry; does not redefine model data | Drawings, Layouts, Sheets, and title frames |
| Validate and publish the Registry | Geometry exit | Tag binding, infuse, and manual fields |

In short: **3D produces model data, the Registry is the snapshot, Section is the geometry exit, and 2D is the layout and judgement workspace.**

## The chain can pause and resume

This is a design premise, not an extra rule:

- **Every node is a safe stop.** After Dictionary sync, after writing to the model, after registering a section — save and stop. You do not have to finish the chain in one sitting. A later person or computer can continue without losing completed work.
- **Nothing runs itself.** Each step is user-started. Actions with a wide effect (publish, write) show what will change before they change it.
- **A mistake stays local.** If a source is edited or deleted, LoopFlow marks that node. It does not auto-repair, and it does not break unrelated finished work. Go back to that node and redo it.
- **1.x and 2.0 are different architectures.** Do not mix their files or toolbar buttons.

## Five names to learn first

| Term | Meaning |
|---|---|
| **Project Folder** | The folder of the saved `.3dm`. Dictionary and `_LoopFlow_Config/` are rooted here. |
| **Dictionary** | Type Catalog. Stable Type IDs, layers, display names, initial defaults, and rules. It does not store each 3D object's current values. |
| **Registry** | A read-only snapshot published from 3D so 2D knows which revision it is reading. Not a hand-edited database. |
| **Sheet** | The real source of drawing number, name, and revision. The Layout page name is a display result, not the identity. |
| **Health** | Whether a tag is live, stale, or disconnected. Colour is a recoverable hint; infuse or rebind to restore. |

## How to operate

This page is logic only. For clicks, the six Nexus items, Excel columns, and who writes each Tag field, see the [command reference](./COMMANDS.md), [Dictionary guide](./Dictionary_GUIDE.md), and [Tag Block reference](./TAG_BLOCKS.md).
