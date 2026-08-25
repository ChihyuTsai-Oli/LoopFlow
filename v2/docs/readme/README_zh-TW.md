<!-- 草稿。公開主頁以 repo 根目錄 README_zh-TW.md 為準，改安裝或功能事實時先改公開頁。 -->

# LoopFlow

[English](./README.md)

> **Embrace the loop. Let it flow.**

LoopFlow 2.0 是一套以 Rhino 8 為核心、貫穿 SD（Schematic Design）、DD（Design Development）至 CD（Construction Documentation）的半自動化設計與文件工作流。它不是另一個 BIM 系統，也不要求使用固定範本或參數化流程；你仍然掌控每個步驟，LoopFlow 負責資料更新、圖紙同步與其他重複工作。

主要流程都在 Rhino 中完成，讓模型資料、圖面與 Layout 文件能隨著設計發展持續演進。LoopFlow 已在多個實際設計專案中使用，目標是保留 Rhino 的設計自由，同時減少設計變更後的重複整理。

## 主要功能

- 在 Rhino 裡照個人慣用方式建模；材質與工項用 Excel 字典定義，再寫進模型
- 模型若有更改，重新寫入並檢核後，把通過的那一版交給圖面；3D 不會被圖紙反向改掉
- 用 Rhino 剖面出平面、立面或剖面，再編排圖號、材質標註與剖立面索引
- 圖上資料過期或來源不見時會標出來，由你決定重綁或再更新；系統不會主動更改
- 同資料夾雙機或多人出圖時，可監看 3D 檔更新
- 每一步、每個動作都需要自己執行，隨時可以停下，不是黑盒模式，不會一次自動執行完畢

完整指令與操作方式請參考 [LoopFlow 2.0 使用說明](./3_codex/README.md)。

## 與 1.0 的差異

- 2.0 是重建，不是 1.x 的修補版；同一專案不可混用資料、Tag Block、指令或工具列
- 模型改完不會自動灌進圖面；要先寫入、檢核，再發布一版給圖紙讀取
- 1.0 的櫃體與部分 2D 工具，不併入 2.0；獨立為日後獨立專案
- 2.0 不算尺寸或數量
- 安裝改為一份 `.yak`（Package Manager），不再用 1.x 的解壓與拖工具列
- 介面可選 English / 正體中文；Tag 過期或斷開會標示，但不自動修

## 系統需求

- **Rhino 8**（必要；2D 出圖使用 Rhino 原生 Section / Clipping Drawing）
- Windows 10 或 Windows 11

支援雙語介面：English / 正體中文

## 快速開始

- [教學播放清單](https://www.youtube.com/@Chihyu-Oli/playlists)（尚未全部改為 2.0）

### 安裝

不要使用 1.x 的 ZIP、`install_LoopFlow.bat` 或拖放 `.rhc` 工具列。同一專案不可混用 1.x 與 2.0

1. 開啟 Rhino 8，命令列執行 `PackageManager`，搜尋 `LoopFlow`，安裝 2.0.5
2. **完全關掉 Rhino 再開**

也可從 [Releases](https://github.com/ChihyuTsai-Oli/LoopFlow/releases/latest) 下載 `loopflow-2.0.5-rh8_0-win.yak`，在 Package Manager 選擇從檔案安裝。不要下載 1.x 的 ZIP。

裝完後：

- 第一次執行任一 LoopFlow 指令時，若這台電腦還沒選過語系，會問 English／正體中文
- 官方 `Tag_Blocks.3dm` 與兩本 Dictionary 會拷到「文件\LoopFlow」。裝了新版本後，下一次執行指令會換成與套件相同的官方檔；該資料夾裡多出來的檔不會刪。請把需要的檔再複製到你的 `.3dm` 同一層
- 使用 LoopFlow 2.0 工具列；不要按舊的 1.x 按鈕
- 若工具列是空白：工具列視窗最上面改回 Default，再「檔案 → 開啟」套件裡的 `LoopFlow.rui` 並勾選 LoopFlow

## 基本工作流程

1. 依專案 Dictionary 同步 Type 圖層，並把資料寫入 Rhino 模型
2. 檢核通過後，發布一份 Registry 版次
3. 使用 Rhino Section Tools 建立剖面、立面或平面
4. 建立 Layout 編號、材質 Tag 與剖立面索引 Tag
5. 將已發布的資料注入 Tag Blocks，讓模型、圖面與圖紙資訊對到同一版次

各步驟可依專案狀況暫停、重跑或日後接續，不需要一次做到底

## 支援與回報

- [Discussions](https://github.com/ChihyuTsai-Oli/LoopFlow/discussions)：提問與分享使用經驗
- [Issues](https://github.com/ChihyuTsai-Oli/LoopFlow/issues)：回報錯誤或提出建議
- [Changelog](./CHANGELOG.md)：查看已發布版本內容

LoopFlow 是由建築及室內設計師從實際工作中發展的單人專案。程式開發與文件整理使用 AI 協助；工作流程需求、設計決策與實務驗證仍以作者本人的專業經驗為基礎。

維護與回覆速度會依工作狀況調整。

## 相關專案

外部 Render 同步功能由獨立專案提供，不包含在 LoopFlow 本體中：

- [LoopFlow｜Rhino to Blender Sync](https://github.com/ChihyuTsai-Oli/LoopFlow_Rhino-to-Blender-Sync/blob/main/README_zh-TW.md)
- [LoopFlow｜Rhino to Octane Sync](https://github.com/ChihyuTsai-Oli/LoopFlow_Rhino-to-Octane-Sync/blob/main/README_zh-TW.md)

## 授權與致謝

LoopFlow 採用 [MIT License](./LICENSE) 發布。開發背景與致謝請參考 [CREDITS](./CREDITS.md)
