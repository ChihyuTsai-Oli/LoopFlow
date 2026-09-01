# Rhino MCP 設定交接

| 項目 | 內容 |
|---|---|
| 用途 | **給 AI 代理直接執行**的設定程序。適用於在新電腦上設定 Claude Code／Codex／Cursor，或在既有電腦上補設定其中一家 |
| 建立 | 2026-09-01（家用電腦完成設定並實測後撰寫） |
| 實測依據 | [`實測報告.md`](./實測報告.md) |

> **給讀到這份文件的 AI**：使用者是非技術背景，不自行操作指令列。請你直接執行以下步驟，不要把指令貼給使用者叫他自己跑。**只有 §3 標記「使用者操作」的部分**（在 Rhino 裡打指令）需要請使用者動手，因為那是 GUI 操作。
>
> 每一步都附了驗證方式，**請實際驗證再回報成功**，不要只憑指令沒報錯就宣稱完成。

---

## 0　這個 MCP 是什麼

McNeel 官方的 Rhino MCP Platform，讓 AI 能讀寫 Rhino 與 Grasshopper。

- **不是 Claude 限定**。MCP 是開放標準，Claude Code／Codex／Cursor／Copilot／Gemini CLI 都能接
- **Rhino 外掛只裝一次**（機器層級），但**每個 AI 工具要各自註冊一次**
- **設定是本機專屬，不隨 git 同步**。換電腦要重做一次，這份文件就是為此而寫

---

## 1　前提檢查

```powershell
Test-Path "C:\Program Files\Rhino 8\System\Rhino.exe"
```

需要 **Rhino 8**（Rhino 9 WIP 亦可，但本工作區使用者全在 Rhino 8）。

0.1.5 版是純 .NET，**不需要 Python、不需要 uv**。

---

## 2　安裝 Rhino 外掛

### 2.1 先確認是否已安裝

```powershell
& "C:\Program Files\Rhino 8\System\Yak.exe" list
```

輸出中若已有 `Rhino-MCP-Platform` 就跳到 §3。

### 2.2 安裝

**Rhino 必須先關閉**，否則檔案會被佔用。

```powershell
& "C:\Program Files\Rhino 8\System\Yak.exe" install Rhino-MCP-Platform
```

這等同使用者在 Rhino 裡跑 `PackageManager` 搜尋安裝，結果相同。

**驗證**：輸出應包含 `Successfully installed Rhino-MCP-Platform (<版本>)`。

---

## 3　取得 router 執行檔路徑

**路徑含版本號，會隨更新改變，務必用指令取得，不要沿用本文件寫死的範例。**

```powershell
Get-ChildItem "$env:APPDATA\McNeel\Rhinoceros\packages\8.0\Rhino-MCP-Platform" -Recurse -Filter "rhino-mcp-router.exe" |
  Where-Object { $_.FullName -like "*win-x64*" } |
  Sort-Object FullName -Descending |
  Select-Object -First 1 -ExpandProperty FullName
```

> ARM 機器改用 `win-arm64`。以 `$env:PROCESSOR_ARCHITECTURE` 判斷（`AMD64` → x64）。

家用電腦當時取得的結果（**僅供對照，新機請重新取得**）：

```
C:\Users\chihyu\AppData\Roaming\McNeel\Rhinoceros\packages\8.0\Rhino-MCP-Platform\0.1.5\router\win-x64\rhino-mcp-router.exe
```

以下步驟中的 `<ROUTER>` 一律代換為此路徑。

> **不需要在 Rhino 裡執行 `MCPConnect`。** 那支指令的用途只是產生一段設定文字讓使用者貼給 AI，而以下步驟已經直接完成同一件事。

---

## 4　註冊到三個 AI 工具

三家指向**同一支 exe**，只是設定檔格式不同。

**全部寫在使用者家目錄，不要寫進任何 git repo。** 路徑帶版本號又是本機專屬，進了版控會同步到另一台而失效，且錯誤訊息對非技術使用者不友善。

### 4.1 Claude Code — `~/.claude.json`

在最上層加入 `mcpServers.rhino`（使用者層級，所有專案通用）。

**先備份**，再用 Python 修改（JSON 手改容易破壞結構）：

```python
import json, io, os, shutil
p = os.path.join(os.environ["USERPROFILE"], ".claude.json")
shutil.copy2(p, p + ".bak")
exe = r"<ROUTER>"
assert os.path.isfile(exe)
with io.open(p, encoding="utf-8") as f:
    d = json.load(f)
d.setdefault("mcpServers", {})["rhino"] = {"command": exe}
with io.open(p, "w", encoding="utf-8") as f:
    json.dump(d, f, ensure_ascii=False, indent=2)
```

> Claude Code 執行中時會自行改寫 `.claude.json`，有覆蓋風險。寫完立刻驗證，並請使用者重開 Claude Code。

### 4.2 Codex — `~/.codex/config.toml`

附加一個 table（TOML 的 table 順序不拘，接在檔尾也合法；放在既有 `[mcp_servers.*]` 附近較易閱讀）：

```toml
[mcp_servers.rhino]
args = []
command = 'C:\...\rhino-mcp-router.exe'
```

> 用**單引號**（TOML literal string），反斜線才不會被當跳脫字元。
>
> 修改前先備份，並確認 Codex 沒在執行。動完後用 `tomllib` 解析一次，確認既有的 `[mcp_servers.*]`、`[projects.*]`、`[plugins.*]` 等區段都還在。

### 4.3 Cursor — `~/.cursor/mcp.json`

多半不存在，直接新建：

```json
{
  "mcpServers": {
    "rhino": {
      "command": "C:\\...\\rhino-mcp-router.exe",
      "args": []
    }
  }
}
```

> 這裡是 JSON，反斜線要**雙寫**。
>
> Cursor 執行中不會熱載入新建的設定檔，寫完請使用者重開 Cursor。

---

## 5　驗證（請實際做，不要跳過）

### 5.1 各工具是否認得

| 工具 | 驗證方式 | 預期 |
|---|---|---|
| Claude Code | 重開後檢查工具清單 | 出現 `mcp__rhino__*` 系列，共 29 個 |
| Codex | 見下方指令 | `rhino` 一列，狀態 `enabled` |
| Cursor | 重開後查 log：`$env:APPDATA\Cursor\logs\<最新>\mcp-server-user-rhino.log` | `connected=true, statusType=connected` |

Codex 的驗證指令（`&` 不會展開萬用字元，必須先解析路徑再呼叫）：

```powershell
$codex = Get-ChildItem "$env:LOCALAPPDATA\OpenAI\Codex\bin\*\codex.exe" |
         Select-Object -First 1 -ExpandProperty FullName
& $codex mcp list
```

> **不要把 codex.exe 路徑寫死。** 中間那層是版本雜湊，會隨 Codex 更新改變——本文件撰寫當天就從 `d0097be4feba73d0` 變成 `b99306303521e97e`。
>
> Codex 的 `Auth` 欄顯示 `Unsupported` 是正常的，代表此伺服器不走 OAuth，與能否使用無關；既有的 `node_repl` 也是同樣顯示。

行程層面的旁證：三家都啟動後，系統會有多個 `rhino-mcp-router.exe` 行程（每個客戶端各一份）。

```powershell
Get-Process rhino-mcp-router -ErrorAction SilentlyContinue
```

### 5.2 端到端連通

**（使用者操作）** 請使用者開啟 Rhino 8，並在指令列輸入：

```
MCPStart
```

成功時 Rhino 會顯示 `[Rhino MCP] MCP server currently running on http://localhost:10500/`。

然後由 AI 呼叫 `list_slots`，應回傳類似：

```json
{"payload":[{"slotId":"aardvark","port":10500,"pid":12345,"version":"8","adopted":true,
             "endpoint":"http://localhost:10500"}]}
```

`pid` 應與 Rhino 行程的 PID 一致。

若回傳空陣列 `[]`，代表 Rhino 端監聽器沒起來——確認 `MCPStart` 有執行成功。可查：

```powershell
Get-ChildItem "$env:LOCALAPPDATA\McNeel\rhino-mcp\listeners"
```

有公告檔＝監聽器已啟動；空的＝沒啟動。

---

## 6　使用時的必要操作

| 事項 | 說明 |
|---|---|
| **每次重開 Rhino 都要跑 `MCPStart`** | 監聽器不會隨 Rhino 自動啟動。這是最常見的「怎麼連不上」原因 |
| `g1_start` 只開視窗、不建立定義檔 | GH 會停在 `Grasshopper - No document…`，此時所有 `g1_*` 工具回 `Could not get GH document`。需先開啟或新建一份 definition |
| 一次只用一個 AI 操作 Rhino | 三家各自啟動 router，但 Rhino 只有一條主執行緒。本工作區 `AGENTS.md` 既有的「一次一個 agent」慣例正好避開此問題 |

---

## 7　已知陷阱（動手前必讀）

完整證據見 [`實測報告.md`](./實測報告.md)，以下是操作時最容易踩到的四項。

### 7.1 worksession 下 MCP 原生工具看不到 attach 的物件

**這是最重要的一項。** LoopFlow 的實際作業配置是 worksession（3D `.3dm` attach 進 2D `.3dm`），而：

| 工具 | 對 attach 進來的參照物件 |
|---|---|
| `list_objects` | ❌ 看不到，且 `truncated: false`、`warning: null`，毫無提示 |
| `get_selection` | ❌ 看不到，即使物件確實處於選取狀態 |
| `set_selection` | ✅ 選得到 |
| `run_python` | ✅ 看得到（需正確設定列舉器） |

「選得進去、讀不出來」的不對稱最危險。**所有物件掃描一律改走 `run_python`**：

```python
s = Rhino.DocObjects.ObjectEnumeratorSettings()
s.NormalObjects = True
s.LockedObjects = True
s.HiddenObjects = True
s.ReferenceObjects = True      # ← 少了這行就看不到 attach 的物件
s.DeletedObjects = False
objs = doc.Objects.GetObjectList(s)
```

讀取選取狀態要逐一檢查 `o.IsSelected(False) > 0`；`doc.Objects.GetSelectedObjects()` 同樣會漏（MCP 的 `get_selection` 底層就是它）。

### 7.2 LoopFlow 指令沒跑完時，MCP 會「靜默失效」

若 LoopFlow 指令停在半路（模態視窗等待使用者、尚未取消），此時對 MCP 下 `run_python`：

- 腳本**照常執行**
- `error` 為 **`null`**
- `stdout` **空白**
- **不逾時、不報錯**

看起來像成功，其實拿不到任何輸出。

**判讀原則：空 stdout 一律視為異常，不可當作成功。** 遇到時先請使用者確認 Rhino 是否有視窗在等待操作。

（附帶結論：LoopFlow 外掛與 MCP 外掛**本身並無衝突**，兩者可安心並存。以上純粹是指令未完成造成。）

### 7.3 不要用 `run_command` 執行 LoopFlow 產品指令

LoopFlow 幾乎每支指令都會彈出模態視窗等待使用者。MCP 在主執行緒執行並等待回傳，會造成 Rhino 卡住，只能手動關閉視窗才能救回。

### 7.4 `doc.Objects.Count` 不等於物件數

它包含「已刪除但可復原」的記錄。要算實際物件請用列舉器（見 §7.1），不要用 `Count` 判斷增減。

### 7.5 找不到已註冊的 Rhino 時，router 會自己開一個新的

若使用者的 Rhino 沒有執行過 `MCPStart`，此時呼叫任何工具（未指定 `slot`），router **不會回報錯誤，而是自動啟動一個新的空白 Rhino** 來服務請求。回傳中會多一個欄位說明：

```json
"autoSpawnedSlot": {
  "slotId": "aardvark", "version": "8",
  "reason": "Auto-spawned Rhino 8 to serve 'run_python' (no `slot` argument
             was passed and no matching Rhino was already running)."
}
```

**後果**：使用者螢幕上會多出一個 Rhino 視窗，而 AI 操作的是那個**空白文件**，不是使用者眼前開著模型的那一個。若沒注意到 `autoSpawnedSlot` 欄位，會誤以為「模型裡怎麼什麼都沒有」。

**應對**：

1. 動手前先呼叫 `list_slots`。回傳空陣列就是使用者還沒跑 `MCPStart`——請他跑，不要直接下工具讓 router 自作主張
2. 每次工具回傳都檢查有無 `autoSpawnedSlot`。出現就代表接錯對象，應請使用者在正確的 Rhino 跑 `MCPStart`，並關掉多開的那個
3. `list_slots` 回傳的 `pid` 應與使用者那個 Rhino 的行程 PID 相符，可用來確認

---

## 8　移除方式

```powershell
& "C:\Program Files\Rhino 8\System\Yak.exe" uninstall Rhino-MCP-Platform
```

三個設定檔各自移除 `rhino` 條目：

- `~/.claude.json` → `mcpServers.rhino`
- `~/.codex/config.toml` → `[mcp_servers.rhino]`
- `~/.cursor/mcp.json` → 整檔可刪（若只有這一項）

---

## 9　家用電腦設定紀錄（供另一台對照）

| 項目 | 值 |
|---|---|
| 設定日期 | 2026-09-01 |
| OS | Windows 11 Pro，`AMD64` |
| Rhino | Rhino 8（`C:\Program Files\Rhino 8\`），未安裝 Rhino 9 |
| 套件版本 | `Rhino-MCP-Platform 0.1.5` |
| router | `%APPDATA%\McNeel\Rhinoceros\packages\8.0\Rhino-MCP-Platform\0.1.5\router\win-x64\rhino-mcp-router.exe` |
| 監聽 port | 10500（預設） |
| 工具數 | 29（Grasshopper 11 ＋ Rhino 18） |
| Claude Code | `~/.claude.json` → `mcpServers.rhino`，使用者層級 |
| Codex | `~/.codex/config.toml` → `[mcp_servers.rhino]`（既有的 `node_repl` 未受影響） |
| Cursor | `~/.cursor/mcp.json`（新建） |

### 工具清單（供對照，確認新機工具數一致）

**Grasshopper（11）**
`g1_start`、`g1_search_components`、`g1_describe_component`、`g1_place_component`、`g1_place_slider`、`g1_connect`、`g1_connect_many`、`g1_get_canvas_graph`、`g1_apply_graph`、`g1_solve_graph`、`g1_clear_canvas`

**Rhino（18）**
`run_python`、`run_csharp`、`run_command`、`list_objects`、`get_selection`、`set_selection`、`get_viewport_image`、`zoom_to_object`、`zoom_to_layer`、`set_camera`、`set_layer_material`、`open_doc`、`save_doc`、`close_doc`、`get_commands`、`list_slots`、`spawn_slot`、`close_slot`

> 前綴是 `g1_` 不是 `gh1_`，且**不存在 `g2_` 系列**（那需要 Rhino 9）。若查到的舊文件寫 `gh1_`／`gh2_`，以此處為準。

---

## 10　測試環境（在 Dropbox，不在 Git）

**工作檔不進 Git，Git 只留本資料夾的文件。** 測試環境位於：

```
<LOOPFLOW_QTY_MCP_WORKFILES_ROOT>
```

雙機的實際路徑見工作區根目錄的 `工作檔路徑.md`（該表是路徑的唯一來源）。**不要在文件或程式中寫死某台電腦的 Dropbox 絕對路徑。**

取得路徑：

```powershell
$root = [Environment]::GetEnvironmentVariable('LOOPFLOW_QTY_MCP_WORKFILES_ROOT', 'User')
if (-not $root) { Write-Output "環境變數未設定，請依 工作檔路徑.md 設定後再繼續" } else { Get-ChildItem $root }
```

> 換機後若此變數未設定，**停止操作並回報**，不要自行猜測磁碟機——這是 `工作檔路徑.md` 的既定規則。

該資料夾內構成一組**依實際作業方式配置**的完整測試環境：

| 檔案 | 用途 |
|---|---|
| `LoopFlow_R_MCP.rws` | worksession：`LoopFlow_3D_R_MCP.3dm` attach 進 `LoopFlow_2D_R_MCP.3dm` |
| `LoopFlow_2D_R_MCP.3dm` | 2D 圖面（作用中文件） |
| `LoopFlow_3D_R_MCP.3dm` | 3D 模型（attach，39 個 Brep 都在這裡） |
| `LoopFlow_Dictionary.xlsx` | Nexus 引用的字典，與 `.3dm` 同層——這是 LoopFlow 的既定結構 |
| `LoopFlow_R_MCP.gh` | GH 預設檔 |

**驗證用的已知數字**（開啟 `.rws` 後應相符）：

| 檢查 | 預期值 |
|---|---|
| 完整列舉物件數（含隱藏／鎖定／參照） | 3116 |
| 　本機（2D） | 2972 |
| 　參照（3D attach） | 144 |
| `list_objects` 回傳數 | **2972**（少了 144，這是 §7.1 的現象，不是故障） |
| Brep 總數 | 39，全在參照側 |
| 帶 `_03_ID編號` 的物件 | 98（本機 61 ＋ 參照 37） |
| 相異 `type_id` | 26，全部在字典查得到規則 |
| 模型單位 | Centimeters |
