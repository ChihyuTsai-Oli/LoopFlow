# Rhino MCP 設定交接

| 項目 | 內容 |
|---|---|
| 用途 | **給 AI 代理直接執行**的設定程序。適用於在新電腦上設定 Claude Code／Codex／Cursor，或在既有電腦上補設定其中一家 |
| 建立 | 2026-09-01（**公司電腦**完成設定並實測後撰寫） |
| 補測 | 同日稍後、同一台公司電腦：以 Cursor 連上已安裝的 MCP、開啟測試 `.rws`、啟動 Grasshopper；下午補記 GH headless 載入後 Rhino 當機事件。新增 §7.6～§7.8 |
| 雙機完成 | 2026-09-01 18:26 **家中電腦**依本文件完成設定並端到端驗證通過。§9 改為雙機對照表 |
| 補記 | 2026-09-01 18:40 家中電腦發現 `get_viewport_image` 會回傳全白空圖，且 metadata 毫無異常。新增 §7.9 |
| Config／Registry | 2026-09-02 公司電腦確認測檔已有 `_LoopFlow_Config`，並遷到 2.0.7 的 `loopflow/`；`loopflow_QTY/` 預留為空。見 §10 |
| 實測依據 | [`實測報告.md`](./實測報告.md) |

> **給讀到這份文件的 AI**：使用者是非技術背景，不自行操作指令列。請你直接執行以下步驟，不要把指令貼給使用者叫他自己跑。
>
> **只有下列 Rhino 畫面操作需要請使用者動手**：
>
> 1. 若本次要用測試 worksession：請使用者用 Rhino「開啟檔案」打開 `LoopFlow_R_MCP.rws`（**不要**用 MCP 代開，見 §7.7）
> 2. 在 Rhino 指令列輸入 `MCPStart`，看到 `Port <10500>`（或 `10501`）時按 **Enter**（見 §5.2、§7.6）
> 3. 若要檢查 GH definition：請使用者正常執行 `gh`，在 Grasshopper UI 開啟 `.gh`；**不要**以 `run_python`／`run_csharp` 搭配 `GH_DocumentIO` headless 載入（見 §7.8）
>
> 不要用 `Start-Process`／`/runscript` 代跑 `MCPStart`，不要用 `run_python`、`run_command`、`open_doc` 開啟 `.rws`，也不要在目前工作的 Rhino 行程內 headless 載入 `.gh`。
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

公司電腦當時取得的結果（**僅供對照，新機請重新取得**）：

```
C:\Users\chihyu\AppData\Roaming\McNeel\Rhinoceros\packages\8.0\Rhino-MCP-Platform\0.1.5\router\win-x64\rhino-mcp-router.exe
```

以下步驟中的 `<ROUTER>` 一律代換為此路徑。

> ### ⚠️ 已發生過的事故：把範例路徑抄進設定檔
>
> 2026-09-01 公司電腦上，`~/.cursor/mcp.json` 一度被寫成：
>
> ```
> C:\Users\USER\AppData\Roaming\McNeel\...\rhino-mcp-router.exe
> ```
>
> `USER` 是常見的佔位字串，該路徑在任何機器上都不存在。
>
> **後果是靜默的**——Cursor 不會跳錯誤，那些 `rhino` 工具就只是**不出現**。如果不特地去比對路徑，會誤以為是 MCP 沒裝好或 Rhino 沒開，往完全錯誤的方向查。這與 §7.2 的「空 stdout 當成功」屬同一類失敗模式。
>
> **因此**：
>
> 1. **路徑一律用上面的指令取得**，不要從任何文件、範例或另一台電腦複製
> 2. 寫入後**立即驗證檔案存在**（例如 `Test-Path`），不要只確認 JSON／TOML 格式正確
> 3. 三家設定完成後互相比對，**三者應指向同一支 exe**。相異就是有一份錯了

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

**（使用者操作）** 請使用者開啟 Rhino 8。若本次要測 worksession，先請他用「開啟檔案」打開 `LoopFlow_R_MCP.rws`，再在指令列輸入：

```
MCPStart
```

指令**不會立刻結束**。畫面會停在：

```
Command: MCPStart
MCPStart Port <10500>
```

請使用者按 **Enter** 採用預設埠。成功時才會顯示 `[Rhino MCP] MCP server currently running on http://localhost:10500/`。

若上次的監聽公告檔還在，提示可能是 `<10501>`，同樣按 Enter 即可。

然後由 AI 呼叫 `list_slots`，應回傳類似：

```json
{"payload":[{"slotId":"aardvark","port":10500,"pid":12345,"version":"8","adopted":true,
             "endpoint":"http://localhost:10500"}]}
```

`pid` 應與 Rhino 行程的 PID 一致。埠號是 10500 或 10501 都可以，以這次回傳為準。

若回傳空陣列 `[]`，代表 Rhino 端監聽器沒起來——多半是還沒按 Enter，或 MCP 在換文件時已掛掉（見 §7.7）。可查：

```powershell
Get-ChildItem "$env:LOCALAPPDATA\McNeel\rhino-mcp\listeners"
```

有公告檔＝監聽器已啟動；空的＝沒啟動。空陣列時**不要** `spawn_slot`，請使用者再跑一次 `MCPStart`。

---

## 6　使用時的必要操作

| 事項 | 說明 |
|---|---|
| **每次重開 Rhino 都要跑 `MCPStart`，並在 Port 提示按 Enter** | 監聽器不會隨 Rhino 自動啟動。打完指令後一定還會問埠號，少按 Enter 就等於沒啟動 |
| **測試 `.rws` 由使用者手動開啟** | 開完再 `MCPStart`。不要用 MCP 代開 worksession（見 §7.7） |
| `g1_start` 只開視窗、不建立定義檔 | GH 會停在 `Grasshopper - No document…`，此時所有 `g1_*` 工具回 `Could not get GH document`。需先開啟或新建一份 definition（測試檔是同層的 `LoopFlow_R_MCP.gh`） |
| 一次只用一個 AI 操作 Rhino | 三家各自啟動 router，但 Rhino 只有一條主執行緒。本工作區 `AGENTS.md` 既有的「一次一個 agent」慣例正好避開此問題 |

---

## 7　已知陷阱（動手前必讀）

完整證據見 [`實測報告.md`](./實測報告.md)，以下是操作時最容易踩到的項目。

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

### 7.6 `MCPStart` 會停在 Port 提示，必須按 Enter

公司電腦 2026-09-01 實測：`MCPStart` 不是打完就結束。指令列會停在：

```
Command: MCPStart
MCPStart Port <10500>
```

必須按 **Enter** 採用預設埠，成功時才會出現 `[Rhino MCP] MCP server currently running on http://localhost:10500/`。

若上一次的監聽公告檔還沒清掉，提示可能是 `<10501>`，同樣按 Enter 即可；`list_slots` 的 `pid` 對得上目前 Rhino 就好。

**在 Enter 之前**，指令仍佔著主執行緒：

- `run_python`：`error` 為 `null`、`stdout` 空白（與 §7.2 相同的靜默失效）
- `run_command`：回 `Rhino is already running a command`

**AI 禁止**用 `Start-Process` 搭配 `/runscript="MCPStart"`（或任何腳本）代跑。那會把 Port 提示留在指令列，使用者以為已經連上。請使用者在 Rhino 指令列親手輸入，看到 Port 就按 Enter。

### 7.7 不要用 MCP 開啟 `.rws` worksession

公司電腦 2026-09-01 實測：對已連上 MCP 的空白文件執行

```
-_Worksession _Open "<LOOPFLOW_QTY_MCP_WORKFILES_ROOT>\LoopFlow_R_MCP.rws"
```

實際發生：

1. 檔案有讀進去（2D 成為作用中文件，3D 以 inactive model attach）
2. 指令**沒結束**，停在 `Choose worksession option ( Attach  Detach  Current  Refresh  Open  Save  SaveAs )`，還要再按一次 Enter
3. 換文件時 MCP 伺服器無法正常關閉，指令列出現 `[Rhino MCP] Failed to stop MCP server gracefully. Recommend restarting Rhino.`
4. MCP 工具回 `rhino_closed`、slot 被剪除；Rhino 視窗其實還在
5. `listeners\` 清空，`list_slots` 回 `[]`

`open_doc` 也不適用：那是把檔案**匯入目前文件**，不是開 worksession。

**正確順序**：

1. 請使用者用 Rhino「開啟檔案」打開 `LoopFlow_R_MCP.rws`
2. 若畫面上出現 MCP 建議重開 Rhino 的訊息，請他重開 Rhino 再開 `.rws`
3. 開檔後執行 `MCPStart`，Port 提示按 Enter
4. AI 呼叫 `list_slots` 確認 `pid` 相符，再用 `run_python`（含 `ReferenceObjects = True`）核對 §10 的已知數字
5. **不要** `spawn_slot`

### 7.8 不要用 `GH_DocumentIO` 在使用中的 Rhino headless 載入 `.gh`

公司電腦 2026-09-01 下午實測事故：在已開啟 `LoopFlow_R_MCP.rws`、已連 MCP 的 Rhino 中，透過 `run_python` 載入 Grasshopper assembly、建立 `Grasshopper.Kernel.GH_DocumentIO` 並呼叫 `Open()` 讀取 `LoopFlow_R_MCP.gh`。該工具呼叫逾時；AI 端取消等待後，MCP ping 與其他唯讀腳本一度仍能正常回應，但使用者稍後手動執行 `gh` 時 Rhino 凍結並退出。

事後沒有找到 Windows Application event 或 crash dump，因此「headless 載入留下不完整 GH runtime」是**高度可疑但未證實**的原因。完整時間線見 [`實測報告.md`](./實測報告.md) §4.5、§12.3。

**一律遵守**：

1. 不要在承載 worksession／使用者工作檔的 Rhino 內，以 `run_python` 或 `run_csharp` 建立 `GH_DocumentIO`、headless 開啟 `.gh`
2. AI 端取消工具、逾時返回或後續 ping 成功，**都不能**當成 Rhino runtime 已恢復乾淨
3. 一旦這類 headless GH 呼叫逾時，立即停止所有 Rhino／GH 操作，請使用者重開 Rhino；不要在同一行程手動執行 `gh` 測試
4. 正確檢查方式：使用者正常執行 `gh` → 在 Grasshopper UI 開啟 definition → AI 用 `g1_get_canvas_graph`／`g1_solve_graph` 等正式工具
5. 若需要真正的離線 `.gh` 解析，必須使用與目前 worksession 完全隔離的犧牲環境；目前尚未設計、尚未驗證，不要自行嘗試

**事故後安全恢復順序**：

1. 確認舊 Rhino 行程已結束
2. 開啟全新的 Rhino，手動開啟 `.rws`
3. 若要使用 GH，先正常執行 `gh` 並確認 UI 完整開啟；必要時再開啟 `.gh`
4. 再執行 `MCPStart`，Port 提示按 Enter
5. AI 只先做 `list_slots` 與唯讀模型核對；確認 PID、文件名稱、3116 筆物件均正確後才繼續

### 7.9 `get_viewport_image` 可能回傳全白空圖，而且謊稱成功

家中電腦 2026-09-01 18:40 實測。情境單純：由 LoopFlow 圖框範本開的新檔（未存檔，575 個物件），圖層 `//work` 上有一個 100×100 矩形與一個直徑 80 的圓，兩者都可見。

呼叫 `get_viewport_image`（`view=top`，以 `boxMin`／`boxMax` 框住 85–215 的範圍）**兩次都回傳全白的空圖**：

| 次數 | displayMode | 回傳影像 | metadata |
|---|---|---|---|
| 1 | 未指定（沿用範本的 `2D_Drawing`） | **全白** | `error: null`，相機 `[150,150,13.9]` → target `[150,150,0]`，`visibleObjectCount: 138` |
| 2 | 強制 `Wireframe` | **全白** | `error: null`，相機 `[150,150,7.03]`，`visibleObjectCount: 29` |

**metadata 完全看不出異常**——沒有錯誤、相機正確對準物件中心、螢幕上的物件數也不是 0。

已排除的原因（都以 `run_python` 實際查證，不是推測）：

| 懷疑 | 查證結果 |
|---|---|
| 圖層被關掉或鎖住 | `//work` `IsVisible=True`、`IsLocked=False`、無父圖層 |
| 物件被隱藏 | 兩個物件 `IsHidden=False`、`Attributes.Visible=True` |
| 取景沒框到 | `GetFrustumBoundingBox()` = 39.7–260.3 × 84–216，完整涵蓋 100–200 的幾何 |
| 白線畫在白底 | 圖層色 `(117,203,244)` 淺藍，`DrawColor` 同值，不是白色 |

**一項關鍵線索**：Rhino 該視圖的實際背景是**深色**，但 `get_viewport_image` 回傳的是**白底**。代表它並非照使用者所見的視圖直接擷取，而是走了另一條算繪路徑。根因未確認，**不宣稱已證實**。

**替代做法（實測可用）**：以 `run_python` 呼叫 Rhino 原生的 `CaptureToBitmap()` 存成檔案，再由 AI 讀該檔。

```python
import Rhino, System, os
doc = __rhino_doc__

view = next(v for v in doc.Views if v.ActiveViewport.Name == "Top")
vp = view.ActiveViewport
vp.ZoomBoundingBox(Rhino.Geometry.BoundingBox(
    Rhino.Geometry.Point3d(85, 85, -5),
    Rhino.Geometry.Point3d(215, 215, 5)))
view.Redraw()

bmp = view.CaptureToBitmap(System.Drawing.Size(600, 600))
bmp.Save(r"<暫存資料夾>\check.png")     # 再用 Read 讀這個檔
```

同一情境下這條路徑正確畫出矩形與圓，背景也與螢幕相符（深色）。

**規則**：

1. **不要把 `get_viewport_image` 的結果當作模型狀態的證據。** 空白影像**不代表**模型是空的——這與 §7.1、§7.2 屬同一類「不報錯、只給錯結果」的失敗
2. 需要視覺確認時走 `CaptureToBitmap` 存檔再讀
3. 視覺永遠只是輔助。**數字驗證以 `run_python` 的列舉與量測為準**，不要用截圖判斷物件有無或數量

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

## 9　雙機設定紀錄

兩台都已完成，**同版本、同組態**。差異只有家目錄與 Rhino 9 WIP 的有無。

| 項目 | 公司電腦 | 家中電腦 |
|---|---|---|
| 設定日期 | 2026-09-01 | 2026-09-01（同日 18:10–18:21） |
| 主機名稱 | `TD-ZB-117` | `CHIHYU-202410` |
| 家目錄 | `C:\Users\chihyu\` | `C:\Users\USER\` |
| OS | Windows 11 Pro，`AMD64` | Windows 10 Home，`AMD64` |
| Rhino | Rhino 8，**未裝** Rhino 9 | Rhino 8，**另有 Rhino 9 WIP**（見下方註） |
| 套件版本 | `Rhino-MCP-Platform 0.1.5` | `Rhino-MCP-Platform 0.1.5` |
| router | `%APPDATA%\McNeel\Rhinoceros\packages\8.0\Rhino-MCP-Platform\0.1.5\router\win-x64\rhino-mcp-router.exe` | 同一相對路徑（家目錄不同） |
| 監聽 port | 10500（預設） | 10500（預設） |
| 工具數 | 29（Grasshopper 11 ＋ Rhino 18） | 29，逐一比對與公司電腦**完全相同** |
| Claude Code | `~/.claude.json` → `mcpServers.rhino`，使用者層級 | ✅ 同 |
| Codex | `~/.codex/config.toml` → `[mcp_servers.rhino]`（既有 `node_repl` 未受影響） | ✅ 同（既有 `node_repl`、`cua_repl` 未受影響） |
| Cursor | `~/.cursor/mcp.json`（新建） | ✅ 同 |

> **家中電腦裝有 Rhino 9 WIP，但不影響本設定。** MCP 外掛裝在 `packages\8.0\`，`list_slots` 回傳的 `version` 為 `8`，工具清單仍是 29 個 `g1_*`／Rhino 工具——**沒有因此多出 `g2_` 系列**。若日後要測 Rhino 9 路徑，需另行設定並重新驗證，不可假設沿用。

同日稍後以 Cursor 連線時，沿用上表同一套 0.1.5。新發現的操作陷阱見 §7.6、§7.7。測試 worksession 路徑走 `LOOPFLOW_QTY_MCP_WORKFILES_ROOT`，不要寫死磁碟機。

### 9.1 家中電腦端到端驗證結果（2026-09-01 18:26）

由使用者手動開啟 `LoopFlow_R_MCP.rws` → 執行 `MCPStart` → Port 提示按 Enter，然後由 AI 核對：

| 檢查 | 預期（§10） | 家中電腦實測 |
|---|---|---|
| `list_slots` 的 `pid` | 與 Rhino 行程相符 | ✅ `18172`，且系統只有這一個 Rhino（無 §7.5 的自動多開） |
| 作用中文件 | `LoopFlow_2D_R_MCP.3dm` | ✅ 相符 |
| 模型單位 | Centimeters | ✅ 相符 |
| 完整列舉物件數 | 3116（本機 2972 ＋ 參照 144） | ✅ 3116（2972 ＋ 144） |
| Brep 總數 | 39，全在參照側 | ✅ 39，參照側 39 |
| 帶 `_03_ID編號` 的物件 | 98（本機 61 ＋ 參照 37） | ✅ 98（本機 61 ＋ 參照 37） |
| `doc.Modified` | false | ✅ false（AI 未寫入任何內容） |
| **§7.1 worksession 盲點** | `list_objects` 應看不到參照物件 | ✅ **完全重現**：`geometryType=brep` 回傳 `count: 0`、`truncated: false`、`warning: null`，而 `run_python` 同時讀得到 39 個 |

**結論**：家中電腦行為與公司電腦一致，包含盲點在內。§7 的所有禁令與 §11 的實作建議在兩台機器上同樣適用，不需要分機器版本。

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

**開啟方式**：請使用者在 Rhino 裡打開 `LoopFlow_R_MCP.rws`。若要使用 GH，先正常執行 `gh`、在 UI 開啟 `LoopFlow_R_MCP.gh`；禁止透過 MCP headless 載入（見 §7.8）。接著執行 `MCPStart`。AI 不要用 MCP 代開 `.rws`（見 §7.7）。開成功後用下面的已知數字驗證。

該資料夾內構成一組**依實際作業方式配置**的完整測試環境：

| 檔案 | 用途 |
|---|---|
| `LoopFlow_R_MCP.rws` | worksession：`LoopFlow_3D_R_MCP.3dm` attach 進 `LoopFlow_2D_R_MCP.3dm` |
| `LoopFlow_2D_R_MCP.3dm` | 2D 圖面（作用中文件） |
| `LoopFlow_3D_R_MCP.3dm` | 3D 模型（attach，39 個 Brep 都在這裡） |
| `LoopFlow_Dictionary.xlsx` | Nexus 引用的字典，與 `.3dm` 同層——這是 LoopFlow 的既定結構 |
| `_LoopFlow_Config/loopflow/` | 2.0.7 專案設定與 Registry（`LoopFlow_Project.json`、`M3D/Project_Registry.json` revision 4） |
| `_LoopFlow_Config/loopflow_QTY/` | QTY 預留；目前為空。選取 JSON 日後寫這裡 |
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
| `_LoopFlow_Config/loopflow/` | 2.0.7：`LoopFlow_Project.json`＋`M3D/Project_Registry.json`（revision 4） |
| Registry `objects[]` 與模型 `_07_UUID` | **37 / 37** |
| `_LoopFlow_Config/loopflow_QTY/` | 存在且為空（選取 JSON 日後寫這裡，不寫 AppData） |
