### 安裝方式

1. 從 [Releases](https://github.com/ChihyuTsai-Oli/LoopFlow/releases/latest) 下載最新版本的 ZIP
2. 解壓縮後，選擇其中一種安裝方式：
   - **2a.** 執行 `install_LoopFlow.bat`，自動將腳本複製至正確位置
   - **2b.** 手動將 `Python/` 資料夾內所有檔案複製至 `%AppData%\McNeel\Rhinoceros\8.0\scripts\LoopFlow\`
3. 將 `LoopFlow.rhc` 拖曳至 Rhino 視窗，工具列即出現
4. 可在 Rhino 開啟狀態下執行上述步驟

### 包含檔案

| 檔案 / 資料夾 | 說明 |
|---|---|
| `Python/` | 所有 LoopFlow `.py` 腳本 |
| `install_LoopFlow.bat` | 自動安裝程式，將腳本複製至正確的 Rhino 路徑 |
| `LoopFlow.rhc` | Rhino 工具列定義檔 |
| `LoopFlow_Dictionary.xlsx` | 預設屬性字典 |
| `Tag_Blocks.3dm` | 預設 Tag Block 庫，**打包 ZIP 時必須包含** |

### 資料夾結構

```
LoopFlow/
  Python/                    ← 所有 .py 腳本
  install_LoopFlow.bat
  LoopFlow.rhc
  LoopFlow_Dictionary.xlsx
  README.md
  Tag_Blocks.3dm
```
