# LoopFlow 2.0 使用說明 / Documentation

LoopFlow 2.0 是 Rhino 8 的室內設計資料與出圖工作鏈：自由建立 3D 模型，再由 Excel Dictionary 賦予可追蹤的資料；幾何經 Rhino Section、已發布資料經 Registry，在 2D Drawing、Sheet 與 Tag 重新整合。

LoopFlow 2.0 is a data and documentation workflow for interior design in Rhino 8: model freely in 3D and apply traceable data from an Excel Dictionary. Geometry travels through Rhino Section, while published data travels through the Registry; both meet again in 2D drawings, sheets, and tags.

## 系統需求 / System Requirements

| 項目 | 需求 |
|---|---|
| Rhino | **Rhino 8，必要** |
| 作業系統 | Windows |
| 版本 | LoopFlow 2.0；不可與 1.x 混用 |

| Item | Requirement |
|---|---|
| Rhino | **Rhino 8, required** |
| Operating system | Windows |
| Version | LoopFlow 2.0; do not mix with 1.x |

**為什麼必須使用 Rhino 8？** LoopFlow 的 3D／2D 幾何交接直接建立在 Rhino 8 原生 Section／Clipping Drawing 上，不另外實作一套剖面引擎。沒有 Rhino 8，2D 端的主工作鏈無法成立。

**Why Rhino 8?** LoopFlow's 3D-to-2D geometry handoff is built directly on Rhino 8's native Section / Clipping Drawing tools rather than a separate section engine. Without Rhino 8, the main 2D workflow cannot run.

> LoopFlow 1.x 與 2.0 是不同架構。請勿在同一份 3dm、同一套工具列或同一次工作流程中混用。
>
> LoopFlow 1.x and 2.0 use different architectures. Do not mix them in the same 3dm file, toolbar, or workflow.

## 選擇語言 / Choose a Language

| 文件 / Document | 繁體中文 | English |
|---|---|---|
| 一分鐘總覽 / One-minute overview | [使用說明](./README_TW.md) | Coming soon |
| Excel Dictionary | [Dictionary](./DICTIONARY_TW.md) | Coming soon |
| Rhino 指令 / Commands | [Commands](./COMMANDS_TW.md) | Coming soon |
| Tag Blocks | [Tag Blocks](./TAG_BLOCKS_TW.md) | Coming soon |

英文版會在繁中版定案後依相同結構翻譯。

The English edition will follow the same structure after the Traditional Chinese edition is approved.

## 從哪裡開始 / Where to Start

1. 先閱讀[一分鐘總覽](./README_TW.md)，理解資料流、3D／2D 分界與可回溯工作方式。
2. 要編輯 Type Catalog，查 [Dictionary](./DICTIONARY_TW.md)。
3. 要操作某支工具，查 [Commands](./COMMANDS_TW.md)。
4. 要選 Tag 或確認欄位，查 [Tag Blocks](./TAG_BLOCKS_TW.md)。

本頁是 Rhino 指令 **LFDocument** 開啟的文件入口，不是專案首頁。

This page is the documentation entry opened by the Rhino command **LFDocument**. It is not the project homepage.
