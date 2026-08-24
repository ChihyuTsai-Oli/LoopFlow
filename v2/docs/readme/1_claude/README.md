# LoopFlow 2.0 使用說明 / Documentation

LoopFlow 是一套在 Rhino 8 中運作的室內設計工作流程工具：從材質字典、3D 建模資料化，到剖面圖、圖紙與 Tag 標註，全程保留在 Rhino 檔案裡並可重複執行、驗證與復原。

LoopFlow is an interior-design workflow toolkit that runs inside Rhino 8 — from the material dictionary and 3D model data, through sections, sheets, and tag annotation. Every step stays inside the Rhino file and can be re-run, verified, and undone.

## 系統需求 / System requirements

| 項目 | 需求 |
|---|---|
| Rhino | **8**（必要，非選配） |
| 作業系統 | Windows |

**為什麼一定要 Rhino 8**：LoopFlow 的 2D 圖面流程直接建立在 Rhino 8 原生的 Section／Clipping Drawing 之上（剖面、立面、平面都由它產生），不是自己另外實作一套剖面工具。沒有 Rhino 8，2D 端的整條鏈都無法運作。

| Item | Requirement |
|---|---|
| Rhino | **8** (required, not optional) |
| OS | Windows |

**Why Rhino 8 specifically**: LoopFlow's 2D drawing pipeline is built directly on Rhino 8's native Section / Clipping Drawing tools — sections, elevations, and plans are all produced by that native feature, not a custom section tool. Without Rhino 8, the entire 2D side of the chain cannot run.

## 選擇語言 / Choose a language

| 繁體中文 | English |
|---|---|
| [使用說明總覽（流程圖）](./USER_GUIDE_TW.md) | User Guide (workflow overview) — *coming soon* |
| [指令逐項說明](./COMMANDS_TW.md) | Command Reference — *coming soon* |
| [Excel 字典使用說明](./Dictionary_GUIDE_TW.md) | Dictionary Guide — *coming soon* |
| [Tag Block 說明](./TAG_BLOCKS_TW.md) | Tag Block Reference — *coming soon* |

英文版將在繁中版定案後翻譯。目前四份文件皆為草稿（v1），內容以已完成並實機驗證的 2.0 功能為準。

The English versions will be translated once the Traditional Chinese versions are finalized. All four documents below are drafts (v1), describing the LoopFlow 2.0 features that are implemented and have passed on-machine verification.

## 從哪裡開始 / Where to start

1. 先花一分鐘看 [使用說明總覽](./USER_GUIDE_TW.md)，理解整條工具鏈的邏輯與 2D／3D 分界在哪裡。
2. 需要某支指令的操作細節時，查 [指令逐項說明](./COMMANDS_TW.md)。
3. 準備或維護材質字典時，查 [Excel 字典使用說明](./Dictionary_GUIDE_TW.md)。
4. 圖面上的 Tag 圖塊欄位看不懂時，查 [Tag Block 說明](./TAG_BLOCKS_TW.md)。

Start with the one-minute [User Guide](./USER_GUIDE_TW.md) overview to understand the overall chain logic and where the 2D/3D boundary sits, then use the Command Reference, Dictionary Guide, and Tag Block Reference as needed.
