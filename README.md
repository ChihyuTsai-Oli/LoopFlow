[繁體中文版](./README_zh-TW.md)

An open-source workflow automation tool developed by **蔡智聿 (Chihyu Tsai)**. [https://intro.chihyu-tsai.com](https://intro.chihyu-tsai.com)

---

# LoopFlow

> **Embrace the loop. Let it flow.**

LoopFlow 2 is a Rhino 8/9-based, semi-automated design and documentation workflow built to carry a project from schematic design (SD), through design development (DD), to construction documentation (CD). It is not another BIM system, and it does not require fixed templates or a parametric workflow. You remain in control of every step while LoopFlow handles data updates, drawing synchronization, and other repetitive work.

The main workflow stays inside Rhino, allowing model data, drawings, and Layout documentation to evolve continuously with the design. LoopFlow has been used on multiple real-world design projects. Its goal is to preserve Rhino's design freedom while reducing repetitive cleanup after design changes.

## Features

- Model in Rhino the way you already work. Define finishes and work items in an Excel Dictionary, then write that data into the model.
- After the model changes, write and validate again, then hand the passed revision to the drawings. 3D is not rewritten from the sheets.
- Cut plans, elevations, or sections with Rhino Section, then arrange sheet numbers, material tags, and elevation or section indexes.
- Stale or missing sources are marked on the drawing. You decide whether to rebind or update. LoopFlow does not change things on its own.
- When two computers or several people draw from the same folder, LoopFlow can watch the 3D files for updates.
- Every step and every action is started by you. You can stop at any time. It is not a black box and will not run the whole chain by itself.

For complete command and workflow instructions, see the [LoopFlow 2 documentation](./docs/README.md).

## Quick start

- [Tutorial playlists](https://www.youtube.com/@Chihyu-Oli/playlists) (not all videos have been updated for LoopFlow 2 yet)

### Installation

1. Open Rhino 8 or 9, run `PackageManager`, search for `LoopFlow`, and install 2.2.5.
2. **Quit Rhino completely and reopen it.**

You can also download `loopflow-2.2.5-rh8_0-win.yak` from [Releases](https://github.com/ChihyuTsai-Oli/LoopFlow/releases/latest) and install from file.

After install:

- The first LoopFlow command asks English / 正體中文 if this computer has not chosen a language yet.
- Official `Tag_Blocks.3dm` and both Dictionary workbooks copy to `Documents\LoopFlow`. If that default folder is missing (for example you moved it), any formal command copies it again. After you install a new version, the next command replaces those official files so they match the package. Extra files in that folder are left alone. Copy what you need beside your saved `.3dm`.
- If the toolbar does not appear after restart: **Tools → Options → Plug-ins**, enable **LoopFlow**. If it still does not show, type `LFDocument` once.
- If the toolbar is blank, in Toolbars change the file back to Default, then File > Open the package `LoopFlow.rui` and check LoopFlow.

## Basic workflow

1. Sync Type layers from the project Dictionary and write data into the Rhino model.
2. After validation passes, publish a Registry revision.
3. Create sections, elevations, or plans with Rhino Section Tools.
4. Create Layout numbers, material tags, and elevation or section index tags.
5. Infuse the published data into Tag Blocks so the model, drawings, and sheets point at the same revision.

Each step can pause, rerun, or continue later. You do not have to finish the chain in one sitting.

## System requirements

- **Rhino 8 or Rhino 9** (2D drawings use native Section / Clipping Drawing)
- Windows 10 or Windows 11

Bilingual interface: English / Traditional Chinese

## What changed from 1.0

LoopFlow 2 is a rebuild. Commands, Tag Blocks, and the rest cannot be shared with 1.0.

## Support

- [Discussions](https://github.com/ChihyuTsai-Oli/LoopFlow/discussions): ask questions and share your experience
- [Issues](https://github.com/ChihyuTsai-Oli/LoopFlow/issues): report bugs or suggest improvements
- [Changelog](./CHANGELOG.md): review released changes

LoopFlow is a solo project designed and developed by an architect and interior designer through real-world practice. AI assists with coding and documentation, while workflow requirements, design decisions, and production validation remain grounded in the author's own professional experience.

Maintenance and response times vary with project workload.

## Related projects

These are separate projects and are not included with LoopFlow itself:

- [LoopFlow | Rhino to Blender Sync](https://github.com/ChihyuTsai-Oli/LoopFlow_Rhino-to-Blender-Sync)
- [LoopFlow | Rhino to Octane Sync](https://github.com/ChihyuTsai-Oli/LoopFlow_Rhino-to-Octane-Sync)
- [LoopFlow | Rhino to MEP Sync](https://github.com/ChihyuTsai-Oli/LoopFlow_Rhino-to-MEP-Sync)
- [LoopFlow | R2X Toolbar](https://github.com/ChihyuTsai-Oli/LoopFlow_R2X)

## License and credits

LoopFlow is released under the [MIT License](./LICENSE). See [CREDITS](./CREDITS.md) for the project background and acknowledgments.
