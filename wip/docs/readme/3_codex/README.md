# LoopFlow 2.0 Documentation

LoopFlow 2.0 is a data and documentation workflow for interior design in Rhino 8. Model freely in 3D, apply traceable Type data from an Excel Dictionary, then bring geometry and published data together again in 2D drawings, sheets, and tags.

Geometry moves from 3D to 2D through Rhino Section. Validated model data moves through a versioned Registry. The workflow remains user-directed: every stage can be reviewed, stopped, repeated, or resumed without forcing the entire chain to run at once.

## System requirements

| Item | Requirement |
|---|---|
| Rhino | **Rhino 8, required** |
| Operating system | Windows |
| Project version | LoopFlow 2.0 only |

### Why Rhino 8 is required

LoopFlow uses Rhino 8's native Section and Clipping Drawing tools as the geometry handoff between 3D and 2D. It does not ship a separate section engine. Without Rhino 8, the main 2D workflow cannot run.

> LoopFlow 1.x and 2.0 use different architectures. Do not mix their data, commands, toolbars, or workflow steps in the same project.

## Project folder

The folder containing the saved `.3dm` is the LoopFlow project folder. Keep the selected Dictionary beside the `.3dm`; LoopFlow stores project settings, Registry revisions, and logs under `_LoopFlow_Config/` in that same folder.

```text
<project folder>/
  Project.3dm
  LoopFlow_Dictionary.xlsx
  _LoopFlow_Config/
    LoopFlow_Project.json
    <project name>/
      Project_Registry.json
```

`LoopFlow_Project.json` remembers the project name and Dictionary filename. Moving the whole folder to another parent folder, drive, or computer preserves these relative links. Copying only the `.3dm` does not carry the project settings with it. Starter copies of the Dictionary and `Tag_Blocks.3dm` will later be placed in `Documents\LoopFlow` after install (not implemented yet).

## Documentation

The Traditional Chinese edition is the current working edition. English documents will follow the same structure after the Traditional Chinese text is approved.

| Document | Traditional Chinese | English |
|---|---|---|
| One-minute overview | [Open](./USER_GUIDE_TW.md) | Coming soon |
| Excel Dictionary | [Open](./Dictionary_GUIDE_TW.md) | Coming soon |
| Rhino commands | [Open](./COMMANDS_TW.md) | Coming soon |
| Tag Blocks | [Open](./TAG_BLOCKS_TW.md) | Coming soon |

## Where to start

1. Read the [one-minute overview](./USER_GUIDE_TW.md) to understand the toolchain and the 3D/2D boundary.
2. Use the [Dictionary guide](./Dictionary_GUIDE_TW.md) when defining or maintaining Types.
3. Use the [command reference](./COMMANDS_TW.md) for individual tools and the six Nexus menu items.
4. Use the [Tag Block reference](./TAG_BLOCKS_TW.md) to choose a block and identify automatic, manual, and system-owned fields.

This directory is the 2.0 documentation draft prepared for the entry opened by **LFDocument**. Until the G03 public-documentation pass is complete, the command still opens the public `docs/README.md` entry whose linked guides remain 1.x. It is not the project homepage.

---

# LoopFlow 2.0 使用說明

LoopFlow 2.0 是一套在 Rhino 8 中運作的室內設計資料與出圖工作鏈。使用者可以自由建立 3D 模型，再由 Excel Dictionary 賦予可追蹤的 Type 資料，最後在 2D Drawing、Sheet 與 Tag 中重新整合幾何與已發布資料。

3D 幾何透過 Rhino Section 進入 2D；通過檢核的模型資料則透過有版次的 Registry 交接。整條流程由使用者主導，每個階段都能檢查、暫停、重跑或日後接續，不必一次執行到底。

## 系統需求

| 項目 | 需求 |
|---|---|
| Rhino | **Rhino 8，必要** |
| 作業系統 | Windows |
| 專案版本 | 僅限 LoopFlow 2.0 |

### 為什麼必須使用 Rhino 8

LoopFlow 以 Rhino 8 原生的 Section／Clipping Drawing 作為 3D 與 2D 之間的幾何交接，不另外提供一套剖面引擎。沒有 Rhino 8，2D 端的主要工作鏈無法運作。

> LoopFlow 1.x 與 2.0 是不同架構。請勿在同一專案中混用兩者的資料、指令、工具列或操作流程。

## 專案資料夾

已存檔的 `.3dm` 所在資料夾，就是 LoopFlow 的專案工作資料夾。採用的 Dictionary 放在 `.3dm` 同一層；專案設定、Registry 版次與 log 則放在同一層的 `_LoopFlow_Config/`。

```text
<專案資料夾>/
  Project.3dm
  LoopFlow_Dictionary.xlsx
  _LoopFlow_Config/
    LoopFlow_Project.json
    <專案名稱>/
      Project_Registry.json
```

`LoopFlow_Project.json` 會記住專案名稱與 Dictionary 檔名。整個資料夾搬到其他上層目錄、磁碟或電腦時，相對關係仍然有效；若只複製 `.3dm`，則不會連同專案設定一起帶走。官方 Dictionary 範本與 `Tag_Blocks.3dm` 日後會放到「文件\LoopFlow」，再複製到各專案使用（尚未實作）。

## 說明文件

目前先以繁中版定案；英文版將依相同結構翻譯。

| 文件 | 繁體中文 | 英文 |
|---|---|---|
| 一分鐘總覽 | [開啟](./USER_GUIDE_TW.md) | 待翻譯 |
| Excel Dictionary | [開啟](./Dictionary_GUIDE_TW.md) | 待翻譯 |
| Rhino 指令 | [開啟](./COMMANDS_TW.md) | 待翻譯 |
| Tag Blocks | [開啟](./TAG_BLOCKS_TW.md) | 待翻譯 |

## 從哪裡開始

1. 先閱讀[一分鐘總覽](./USER_GUIDE_TW.md)，理解整條工具鏈與 3D／2D 分界。
2. 定義或維護 Type 時，查 [Dictionary 使用說明](./Dictionary_GUIDE_TW.md)。
3. 操作個別工具或 Nexus 六個選單時，查 [指令逐項說明](./COMMANDS_TW.md)。
4. 選擇 Tag、確認自動欄與人工欄時，查 [Tag Block 說明](./TAG_BLOCKS_TW.md)。

本資料夾是準備給 **LFDocument** 文件入口使用的 2.0 說明草稿。G03 公開文件尚未完成前，指令仍會開啟公開的 `docs/README.md` 入口，該頁連結的指南目前仍是 1.x；文件入口不是專案首頁。
