# LoopFlow

[English](./README.md)

> **Embrace the loop. Let it flow.**

> **開發狀態：** LoopFlow v2 正在開發中。目前公開發布版本仍為 v1；除非另有標示，以下文件皆以穩定版本為準。

LoopFlow 是一套以 Rhino 8 為核心、貫穿 SD（Schematic Design）、DD（Design Development）至 CD（Construction Documentation）的半自動化設計與文件工作流。它不是另一個 BIM 系統，也不要求使用固定範本或參數化流程；你仍然掌控每個步驟，LoopFlow 負責資料更新、圖紙同步與其他重複工作。

主要流程都在 Rhino 中完成，讓模型資料、圖面與 Layout 文件能隨著設計發展持續演進。LoopFlow 已在多個實際設計專案中使用，目標是保留 Rhino 的設計自由，同時減少設計變更後的重複整理。

## 主要功能

- 以 Dictionary 與 UserText 管理模型資料。
- 使用 UUID 維持物件與資料之間的關聯。
- 修改 3D 模型後，重新產生並更新相關 2D 圖說。
- 建立櫃體、Tag Block、圖紙編號、剖立面索引及其他出圖資料。
- 透過視覺化面板檢查物件資料與 Tag 狀態。
- 支援 Worksession 多人協作與資料同步。
- 採半自動化流程，由使用者決定何時執行與更新。

完整指令與操作方式請參考 [LoopFlow 使用說明](./docs/USER_GUIDE_TW.md)。

## 系統需求

- Rhino 8
- Rhino Section Tools
- Windows 10 或 Windows 11
- Python 3.9 以上版本（Rhino 8 已內建）

## 快速開始

- [YouTube 教學系列](https://www.youtube.com/playlist?list=PLiJmu8T_uzJIjokbOcpvvCoHdQn5SJ2NB)：完整工作流程示範

### 安裝

1. 從 [Releases](https://github.com/ChihyuTsai-Oli/LoopFlow/releases/latest) 下載最新版本並解壓縮。
2. 執行 `install_LoopFlow.bat`；或手動將 `Python/` 中的 `.py` 檔案複製到 `%AppData%\McNeel\Rhinoceros\8.0\scripts\LoopFlow\`。
3. 將 `LoopFlow.rhc` 拖曳到 Rhino 視窗中載入工具列。

以上步驟可在 Rhino 開啟時進行。若要移除工具列，請在 Rhino 的 Toolbars 設定中選取 LoopFlow 後刪除。

## 基本工作流程

1. 依專案 Dictionary 將資料寫入 Rhino 模型。
2. 視需要建立櫃體，並使用資料面板檢查物件資訊。
3. 使用 Rhino Section Tools 建立剖面與立面。
4. 建立 Layout 編號、材質 Tag 與剖立面索引 Tag。
5. 將最新資料寫入 Tag Blocks，讓模型、圖面與圖紙資訊保持一致。

各步驟可依專案狀況反覆執行，不需要固定成單一路徑。

## 支援與回報

- [Discussions](https://github.com/ChihyuTsai-Oli/LoopFlow/discussions)：提問與分享使用經驗
- [Issues](https://github.com/ChihyuTsai-Oli/LoopFlow/issues)：回報錯誤或提出建議
- [Changelog](./CHANGELOG.md)：查看已發布版本內容

LoopFlow 是由設計師在實際工作中發展的單人專案，維護與回覆速度會依工作狀況調整。

## 相關專案

外部渲染同步功能由獨立專案提供，不包含在 LoopFlow 本體中：

- [LoopFlow｜Rhino to Blender Sync](https://github.com/ChihyuTsai-Oli/LoopFlow_Rhino-to-Blender-Sync/blob/main/README_zh-TW.md)
- [LoopFlow｜Rhino to Octane Sync](https://github.com/ChihyuTsai-Oli/LoopFlow_Rhino-to-Octane-Sync/blob/main/README_zh-TW.md)

## 授權與致謝

LoopFlow 採用 [MIT License](./LICENSE) 發布。開發背景與致謝請參考 [CREDITS](./CREDITS.md)。
