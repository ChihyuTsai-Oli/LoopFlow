# LoopFlow

> **Embrace the loop. Let it flow.**
>
> - LoopFlow is not another BIM system.
> - It's semi-automated. You're in control at every step. You participate, you decide, you earn your afternoon tea.

## Sound Familiar?

You love Rhino's design freedom. But every time you modify a design, you have to manually update dozens of drawings. Maybe you've looked for other solutions, only to lose that freedom — trapped in templates and rigid rules.

## What I'm Trying to Do

Everything from modeling to layout, all inside Rhino. (Of couse, not including rendering.)

Under your control, LoopFlow handles the tedious work — data updates, drawing sync, all the repetitive stuff — so your time stays where it belongs: your design. Or a cup of coffee.

**What can LoopFlow do?**

- **Design Freedom**: Model your way — no templates, no constraints (well, a tiny bit, but really just a tiny bit)
- **Efficiency Boost**: Stop meaningless repetitive work
- **Complete Control**: You decide what gets automated and what stays manual
- **Update Drawings** — one click to update object data, one click to update 2D drawings
- **Battle-tested**: Stable through multiple real production design projects
- **External High-Quality Render Support**: Simple as Enscape — sync external render engines to produce high-quality images

## Key Features

- Automatic 2D/3D Synchronization: Modify your 3D model, all 2D drawings update instantly
- UUID Tracking: Unique identifier, serving as the data chain path
- Flexible Automation: You decide what's automatic and what's manual
- No Design Restrictions: Model however you want — no parametric constraints, no templates
- (Separate release) External Render Engine Integration: Sync Points, Blocks, and Cameras; auto-align lights and furniture via Proxy and Scatter; preserve edited materials while swapping models
- Compatible software: OctaneRender Standalone / Blender. The sync logic for Points and Blocks is consistent with LoopFlow's drawing logic — the same data drives both 2D drawings and 3D rendering

## System Requirements

- Rhino: 8.0 (Section Tools required)
- Operating System: Windows 10/11
- Python: 3.9+ (included with Rhino 8)
- Optional: OctaneRender Standalone 2025.6+ / Blender 4.5+ (for rendering features)

## Quick Start

Prefer to watch rather than read?
→ [Meet the Monkey](https://chihyutsai-oli.github.io/LoopFlow/slideshow.html) — visual intro
→ [Tutorial Series on YouTube](https://www.youtube.com/playlist?list=PLiJmu8T_uzJIjokbOcpvvCoHdQn5SJ2NB) — full workflow walkthrough

### Installation

1. Download the latest release from [Releases](https://github.com/ChihyuTsai-Oli/LoopFlow/releases/latest)
2. Extract the ZIP, then install the scripts (choose one):
  - **2a.** Run `install_LoopFlow.bat` — copies `.py` files to the scripts folder automatically
  - **2b.** Manually copy all `.py` files from `Data/` to `%AppData%\McNeel\Rhinoceros\8.0\scripts\LoopFlow\`
3. Drag `LoopFlow.rhc` into the Rhino viewport — toolbar appears
4. All of the above can be done while Rhino is open
5. To uninstall: Options > Toolbars > select LoopFlow > Edit dropdown > Delete

### How Does It Work?

1. Worksession mode — multi-user collaboration and automatic updates
2. Based on dictionary definitions, auto-write data to the model — no manual keying
3. One-click cabinet generation — auto-determine panel positions and dimensions
4. Visual UI panel — quickly review object data
5. Create sections using Rhino Sections
6. Auto-number Layout sheets and write to title blocks simultaneously
7. Create material Tag Blocks — penetrate Detail View to extract section object data
8. Create section index Tag Blocks — bind Tag to Detail View
9. One click to inject data into all Tag Blocks
10. Data flows through all drawings, sheets, drawing numbers, indexes, numbers, elevations, dimensions, and more

From this point on, every design change syncs automatically.
All steps can be revisited in any order, at any time.

Command Reference [USER_GUIDE](./docs/USER_GUIDE.md)

## Development Roadmap

Some ideas and features are in active development:

**Planned Features (Planned)**

- Grasshopper form builder with quantity calculations
- Extended tag types for custom metadata
- Expanded drawing number naming rules
- Cabinet component identification system (BOM)
- Drawing index link system

**Experimental (Technical challenges, not guaranteed)**

- Window/door and equipment 2D/3D block management system (technical research phase)

## About Reliability

Built from real design challenges, refined through actual use. It's not perfect yet, but it's already saved my life.

- Internal stable version running: 6 months
- Real-world track record: Multiple production design projects completed
- Current maturity: Ready for design teams

## Support & Community

- [Discussions](https://github.com/ChihyuTsai-Oli/LoopFlow/discussions) — Ask questions, share ideas
- [Report Issues](https://github.com/ChihyuTsai-Oli/LoopFlow/issues) — Found a bug? Let us know
- Contributing — Want to help? Open an issue and let's talk

## About the Creator

- I'm an architect and interior designer with 20 years of experience spanning the entire building industry: design firms, interior design, construction management, site supervision, and real estate development — familiar with the challenges at every stage
- I have no programming background, and English isn't my first language. None of this would have been possible without AI assistance
- If anyone benefits from LoopFlow, that would be my honor

## One Person's Project

LoopFlow is a solo project. I maintain it, respond to issues, and fix bugs myself.

What this means:

- You get a tool verified by a real designer in actual work
- Response time is human speed (within a week typically)
- I can't promise when a feature will be complete
- During busy design projects, things will be slower

## License

LoopFlow is released under the MIT License. See [LICENSE](./LICENSE) for details.

## You Might Also Like

- [LoopFlow_Rhino-to-Octane-Sync](https://github.com/ChihyuTsai-Oli/LoopFlow_Rhino-to-Octane-Sync)
- [LoopFlow_Rhino-to-Blender-Sync](https://github.com/ChihyuTsai-Oli/LoopFlow_Rhino-to-Blender-Sync)

## Special Thanks

My wife, who tolerates me glued to the computer staring at AI at all hours.

---

*Last updated: April 2026*