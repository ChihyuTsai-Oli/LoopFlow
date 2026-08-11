# LoopFlow

[繁體中文](./README_zh-TW.md)

> **Embrace the loop. Let it flow.**

LoopFlow is a semi-automated design and documentation toolkit for Rhino 8. It is not another BIM system, and it does not require fixed templates or a parametric workflow. You remain in control of every step while LoopFlow handles data updates, drawing synchronization, and other repetitive work.

The main workflow—from model data to Layout documentation—stays inside Rhino. LoopFlow has been used on multiple real-world design projects. Its goal is to preserve Rhino's design freedom while reducing repetitive cleanup after design changes.

## Core Features

- Manage model data with dictionaries and UserText.
- Maintain relationships between objects and data with UUIDs.
- Regenerate and update related 2D drawings after 3D model changes.
- Create cabinets, Tag Blocks, sheet numbers, elevation and section indexes, and other documentation data.
- Inspect object data and Tag states through visual panels.
- Support multi-user collaboration and data synchronization with Worksession.
- Keep the workflow semi-automated, letting the user decide when to run each update.

For complete command and workflow instructions, see the [LoopFlow User Guide](./docs/USER_GUIDE.md).

## System Requirements

- Rhino 8
- Rhino Section Tools
- Windows 10 or Windows 11
- Python 3.9 or later (included with Rhino 8)

## Quick Start

- [YouTube Tutorial Series](https://www.youtube.com/playlist?list=PLiJmu8T_uzJIjokbOcpvvCoHdQn5SJ2NB): full workflow walkthrough

### Installation

1. Download and extract the latest version from [Releases](https://github.com/ChihyuTsai-Oli/LoopFlow/releases/latest).
2. Run `install_LoopFlow.bat`, or manually copy the `.py` files from `Python/` to `%AppData%\McNeel\Rhinoceros\8.0\scripts\LoopFlow\`.
3. Drag `LoopFlow.rhc` into the Rhino window to load the toolbar.

These steps can be completed while Rhino is open. To remove the toolbar, select LoopFlow in Rhino's Toolbars settings and delete it.

## Basic Workflow

1. Write project dictionary data into the Rhino model.
2. Create cabinets as needed and inspect object information in the data panel.
3. Create sections and elevations with Rhino Section Tools.
4. Create Layout numbers, material Tags, and elevation or section index Tags.
5. Write the latest data into Tag Blocks so the model, drawings, and sheets remain consistent.

Each step can be repeated as the project evolves; the workflow does not need to follow one fixed path.

## Support

- [Discussions](https://github.com/ChihyuTsai-Oli/LoopFlow/discussions): ask questions and share your experience
- [Issues](https://github.com/ChihyuTsai-Oli/LoopFlow/issues): report bugs or suggest improvements
- [Changelog](./CHANGELOG.md): review released changes

LoopFlow is a solo project developed by a designer through real-world practice. Maintenance and response times vary with project workload.

## Related Projects

External rendering synchronization is provided by separate projects and is not included with LoopFlow itself:

- [LoopFlow | Rhino to Blender Sync](https://github.com/ChihyuTsai-Oli/LoopFlow_Rhino-to-Blender-Sync)
- [LoopFlow | Rhino to Octane Sync](https://github.com/ChihyuTsai-Oli/LoopFlow_Rhino-to-Octane-Sync)

## License and Credits

LoopFlow is released under the [MIT License](./LICENSE). See [CREDITS](./CREDITS.md) for the project background and acknowledgments.
