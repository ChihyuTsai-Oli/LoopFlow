# LoopFlow 2.0 — 資料生態決策表

這是 `LOOPFLOW_DATA_ECOSYSTEM.md` 的使用者編輯區。藍圖保存現況、工作鏈與架構說明；所有尚未定案、需要使用者確認或補充實務語意的事項集中在本文件。

## 使用方式

- 可以直接修改表格中的「你的決定／說明」，不需要使用固定回覆格式。
- 可以把 `待決定` 改成「採用」、「不採用」，或直接寫自己的規則。
- 可以改寫建議內容；若選項不符合實務，直接刪掉重寫也可以。
- 請保留 `ECO-*`／`ED-*` 編號，方便後續追蹤與回寫。
- AI 讀取你的修改後，先整理歧義與影響，再同步回寫藍圖、命名與資料契約、Nexus／Dictionary 細項及進度紀錄。
- 在回寫完成前，本文件是尚待確認事項的唯一來源；不要同時在藍圖與本文件維護兩份答案。

### AI 建議強度

| 強度       | 意義                                                      |
| -------- | ------------------------------------------------------- |
| **強烈建議** | 最好照做；這通常關係到資料不斷鏈、可復原、避免靜默錯誤或能否長期擴充。若不採用，需要先設計同等安全的替代方案。 |
| **一般建議** | 可以改，但會增加相應的規則、操作或維護成本；決定時需明確接受代價。                       |
| **輕鬆建議** | 原則上不影響核心資料鏈，可依實際習慣、時程或介面偏好調整。                           |

## A. 上位生態原則

兩次獨立複核都支持以下方向，但仍由使用者決定是否採用或修改。

| ID | 建議原則 | CodeX 建議（強度） | Claude 建議（強度） | 你的決定／說明 |
| --- | --- | --- | --- | --- |
| ECO-01 | Dictionary 是 Type Catalog；3D Object 是 Instance truth | **強烈建議**：採用。避免 Type 預設與 Object 現值互相覆寫、形成兩份真相。 | **強烈建議**：採用。這是「恢復 Dictionary 預設」能成立的前提。現況 `_02`／`_13` 靠「值為空才寫入」模擬繼承，使用者無法分辨某個值是預設還是自己改過的。 | 待決定 |
| ECO-02 | Layer 是人類分類入口，不是永久資料 ID | **強烈建議**：採用。Layer 改名或重組時，不應讓既有 Tag 與資料關聯一起斷線。 | **強烈建議**：採用。Dictionary 已有 92 個 Type、12 個群組且持續成長，重新分類是遲早的事；現況 layer path 就是主鍵，一改就全斷。 | 待決定 |
| ECO-03 | Section 圖面可獨立編輯；更新不得靜默覆寫人工成果 | **強烈建議**：採用。這是保護出圖人工成果的核心安全線。 | **強烈建議**：採用。人工描圖是整條鏈上**唯一無法自動重建**的成果，其他階段都能從模型重跑。 | 待決定 |
| ECO-04 | Tag 綁定穩定 Object／View／Sheet ID；圖面位置只協助定位 | **強烈建議**：採用。否則名稱、位置或圖面調整都可能造成無法察覺的錯綁。 | **強烈建議**：採用。這就是產品的核心承諾本身，不是實作細節；若不成立，其餘功能都只是畫圖工具。 | 待決定 |
| ECO-05 | Sheet metadata 是圖框與命名真相；Layout 名稱是輸出 | **強烈建議**：採用。日後插頁、改圖號格式或多種交付格式才不需拆字串回推。 | **一般建議**：方向同意，但這是 A 表唯一**失敗可回復**的一條——現況圖號在 render 當下重新解析，弄亂了重跑 Layout_ID 就會修好，不會遺失資料。建議採用但分階段：先讓 metadata 成為產生 Layout 名稱的來源，完整 Sheet 管理介面延後。代價是初期 metadata 仍需人工維護。 | 待決定 |
| ECO-06 | Registry 是版本化唯讀發布快照，不是另一份人工資料庫 | **強烈建議**：採用。避免 3D 模型與 JSON 可各自編輯後產生衝突。 | **強烈建議**：採用。兩份可各自編輯的同源資料是最典型的不可回復衝突；一旦分岔就無法判斷哪邊才對。 | 待決定 |
| ECO-07 | 狀態、revision 與問題是正式資料；顏色只作可還原提示 | **強烈建議**：採用。顏色不能可靠判斷真實狀態，也不能破壞使用者原色。 | **強烈建議**：採用。現況 TAG-O 完全以 RGB 判定，且 Infuser 清除提示時把 ColorSource 設回 ByLayer——這已經是實際的資料破壞，不只是判斷不準。 | 待決定 |
| ECO-08 | 每階段可單獨執行、驗證、重跑與復原 | **強烈建議**：採用。符合雙機、分時工作與小批次測試，也降低一次大操作的風險。 | **強烈建議**：採用。這一條是其他十條**能被測試**的前提；沒有它，任何驗證都得靠整案重跑，實機測試成本會失控。 | 待決定 |
| ECO-09 | 模型單位先驗證；工程估算單位分離；所有量綱常數具名並標註單位 | **強烈建議**：採用。單位混用會直接產生錯誤尺寸、搜尋距離與數量。 | **強烈建議**：採用，但關鍵在時機。乾淨重建時替常數命名、標單位幾乎零成本；等功能寫完再回頭補，就得重新驗證每一個幾何行為。這是「現在做免費、以後做很貴」的典型。 | 待決定 |
| ECO-10 | 每個產生幾何或改寫資料的指令都定義冪等重跑政策，並能辨識前次產出 | **強烈建議**：採用。避免 Extract、參考線或 Sheet 重跑後無限累積與複製身分。 | **強烈建議**：採用。這是使用者**每天會遇到**的問題（Extract 重跑疊圖、Dict-to-Layer 累積參考線），不是理論風險。 | 待決定 |
| ECO-11 | ID 的產生與變更可追溯；自動換 ID 前先報告、預覽、建立 mapping 並可回復 | **強烈建議**：採用。這直接防止 UUID 重建造成既有 Tag 不可逆斷鏈。 | **強烈建議**：採用，且建議列為**全部項目中的第一優先**。這是整份複核中唯一會造成不可回復損失的路徑：複製一個已標註物件後跑 TagTrigger，原件與複本的 UUID 會**同時**被換掉，且只回報數量、不留舊值。 | 待決定 |

## B. 證據已足、建議優先確認

這些已有明確程式或 Dictionary 證據；仍保留使用者翻案空間。

| ID | 現況與建議 | CodeX 建議（強度） | Claude 建議（強度） | 你的決定／說明 |
| --- | --- | --- | --- | --- |
| ED-01 | `_03_ID編號` 的 92 筆現值都是「類別碼-序號」；建議 2.0 拆成 `type_category` 與 `type_sequence`，組合字串只作顯示 | **強烈建議**：照此拆分。資料已證明兩段語意不同，可移除執行期拆字串的歧義。 | **強烈建議**：照此拆分，且成本接近零。Excel 仍可維持單欄、使用者維護方式不變，只在載入時解析。額外好處：92 列的類別碼與 12 個 layer 頂層群組完全 1:1，拆開後就多一條可自動驗證的規則（category 必須與所屬 layer 群組相符），能抓出放錯層的 Type。 | 待決定 |
| ED-02 | 現行 Tag lock 同時辨識 `LOCK`、`不更新`、`NoUpdate` 且各指令規則不一；建議統一為單一正式 `lock_state` | **強烈建議**：統一。否則同一 Tag 在不同指令中可能同時被視為鎖定與未鎖定。 | **強烈建議**：統一。這已經是現行 bug 而非設計選擇：Laser 認 `NoUpdate`（大小寫敏感）但不認「不更新」，Infuser／Grab／Index 則相反。所以一個用「不更新」鎖住的 Tag，Infuser 會尊重、Laser 卻允許重新綁定。 | 待決定 |
| ED-03 | Cabinet 現有程式已持有 panel 的 true W／H／D，卻在寫入前排序抹除方向；建議 L／W／T 依 panel local frame | **強烈建議**：採 local frame。資訊已存在，不需要再靠三邊大小猜方向。 | **一般建議**：技術結論同意，但優先序不同。`_CB.*` 四欄目前**沒有任何 consumer**，方向錯了今天也不會有人看到。真正該固定的要求是「Cabinet 重建時不要再 `sorted()`」，而不是現在就得動工；驗收條件等 BOM 消費端定義後再補。 | 待決定 |
| ED-04 | Rhino 模型文件單位與 Dictionary `_08_單位` 是兩件事；建議拆成模型單位契約與工程估算單位契約 | **強烈建議**：拆分。兩者用途與量綱完全不同，合併只會製造錯誤推導。 | **強烈建議**：拆分。這是定義層面的修正，成本為零，卻能擋掉一整類錯誤推導——例如把 `坪`、`組`、`樘` 當成模型單位去做換算。公開指南本身已定義 `_08` 為「數量計算單位，影響工程估算報表」。 | 待決定 |
| ED-05 | Drawing lifecycle 先完成「重跑時辨識前次產出，讓使用者選擇取代／新增／略過」，再建立完整狀態機 | **強烈建議**：先完成這個最小安全基礎。沒有冪等性，後續狀態機無法可靠運作。 | **強烈建議**：同意。補充：這與其說是功能，不如說是**順序**。先做冪等再做狀態機，成本幾乎為零；反過來做，六種狀態全都得重寫，因為狀態機的每個判斷都預設「能認出前次產出」。 | 待決定 |

## C. 需要實務語意的問題

這些無法只靠讀碼正確決定，可以直接在最右側「你的決定／說明」欄自由描述實際工作方式。

| ID | 需要確認 | 目前觀察／可參考方向 | CodeX 建議（強度） | Claude 建議（強度） | 你的決定／說明 |
| --- | --- | --- | --- | --- | --- |
| ED-06 | 高程 `CH`／`BC` 的正式語意 | `CH` 現況顯示 CH、幾何取物件底面；`BC` 對 Block 取插入點，非 Block 卻靜默退回底面 | **一般建議**：保留 CH＝天花物件底面、BC＝Block 插入點，但把規則、顯示標籤與前置條件分開；非 Block 使用 BC 時直接報錯。代價是部分舊模型需修正。 | **強烈建議**（提高）：請把這題拆兩半看。「CH／BC 各代表什麼」只需你確認一句話，屬輕鬆；但「BC 前置條件不成立時必須報錯」我認為屬強烈。Dictionary 有 16 列使用 BC，若物件不是 block instance，Tag 會**顯示 BC 卻計算 BH**，等於印出錯誤的施工高度且全程無提示——這是會流到現場的錯誤，不只是資料不整潔。 | 待決定 |
| ED-07 | Space boundary 是否會重疊、是否同時有多樓層 | 現況取 bbox 底面中心命中的第一條 boundary；需要定 priority／level／衝突行為 | **一般建議**：Space 使用穩定 ID、level 與 priority；多重命中時停止並列出衝突。代價是 boundary 需要多幾個正式欄位。 | **一般建議**：同意，但建議先做一個更便宜的中間步驟。現況「沒命中任何 boundary」一律回 `EXT`，所以**「這東西在室外」與「這東西沒被任何空間涵蓋」無法區分**，而 TAG-O 的空間覆蓋檢查正好依賴這個值。先把「未命中」與「室外」分成兩種結果，比完整的 priority／level 便宜很多，卻立刻讓覆蓋檢查可信。 | 待決定 |
| ED-08 | 不同 Type 的寬、深、高如何定義 | 現況一般物件偏 world bbox；建議依 Type 與 local frame 定義 | **一般建議**：以 local frame 為預設，再允許各 Type 指定尺寸規則。代價是前期要為主要 Type 建立規則與 fixtures。 | **輕鬆建議**（降低）：`_05`／`_06`／`_07` 目前**沒有任何 consumer**，所以現在定義了也無從驗證對錯，很容易訂完又改。建議把順序反過來：先確定「誰要用這三個欄位」（BOM？估算表？外部工具？），再依那個 consumer 的實際需求定義方向規則。在那之前保留欄位並明確標為「未定義」即可。 | 待決定 |
| ED-09 | `_09_實作數量` 是否要實作 | 目前沒有 producer；若要實作，需定義每種 `_08_單位` 對應的長度／面積／體積／計數規則 | **輕鬆建議**：2.0 第一階段保留 schema，但先設為人工／外部值；等估算需求明確再逐種單位實作。主要代價只是暫時沒有自動數量。 | **輕鬆建議**：同意設為人工／外部值。但建議同時修掉 `docs/Dictionary_GUIDE_TW.md` 第 67 行「通常由 LF_Nexus 計算後填入」那句敘述——這個計算從未存在過，文件不改的話會一直讓人等一個不會來的功能。 | 待決定 |
| ED-10 | `_13_備註` 的預設與 `20_DW` 操作說明 | `我是備註，UCCU` 看似測試字串；`20_DW` 說明可移至獨立 instruction | **輕鬆建議**：備註預設空白，`20_DW` 操作說明移到 instruction。這主要影響資料整潔，不影響核心鏈。 | **輕鬆建議**：同意。補充兩點：`我是備註，UCCU` 會經 TagTrigger 寫進 91 個 layer 底下的**所有物件**並進 Registry，所以它是「散佈在正式資料裡的測試字串」，不只是 Dictionary 裡的一格；另外 `20_DW` 那列是真正的操作說明（「Block放在此圖層，資料寫在Block，不寫在子圖層」），必須有 instruction 欄位承接，不能一併清空。 | 待決定 |
| ED-11 | `DNA_REF_` 參考線是否仍需要 | Dict-to-Layer 每次建立帶完整 Dictionary UserText 的參考線且會累積；需確認原本用途 | **輕鬆建議**：日常 Dict-to-Layer 不再建立；若仍需要目視樣本，另做可重建、可清除的 Type Sample 指令。 | **一般建議**（提高）：不是因為風險高，而是因為這是整份清單裡**唯一「我們不知道它為什麼存在」**的項目。其他每一項都有明確的現況與後果，這一項只有觀察。建議移除前先請你說明原本用途，不要因為它看起來像殘留就砍掉。累積問題可以先用「重跑時先清除前次 `DNA_REF_`」單獨解決，去留可以晚點再決定。 | 待決定 |
| ED-12 | Rhino 文件不是 cm 時如何處理 | A. 直接阻擋；B. 明確換算並顯示；目前工具與常數全部按 cm 設計 | **強烈建議**：2.0 初版直接阻擋並清楚說明；待全部量綱規則有測試後再考慮換算。這會限制非 cm 專案，但安全且可預測。 | **一般建議**（降低）：建議拆成兩件事。「啟動時偵測並明確顯示文件單位」是強烈建議且幾乎零成本；「非 cm 時直接阻擋」則只是目前最安全的**預設策略**，不是必要條件。實務上你所有專案都是 cm（每支工具的預設值都是 cm），阻擋的實際價值有限，卻會讓一個合法的 mm 專案完全打不開。先做偵測＋明確警告，阻擋與否日後可隨時調整。 | 待決定 |
| ED-13 | 複製 Sheet 時一般 Tag 是否保留原模型來源 | 同一模型物件可能合理地出現在多張圖；但新 `sheet_id`／`drawing_id`／`tag_id` 必須建立，Index Tag 目標必須重審 | **一般建議**：一般 Tag 保留 `source_object_id`，但建立新 Tag／Sheet／Drawing ID；Index Tag 清除或重新指定目標。代價是複製完成後需處理待確認清單。 | **強烈建議**（提高，僅限 Index Tag）：一般 Tag 保留來源屬一般建議，同意 CodeX。但 Index Tag 的處理屬強烈：現況複製 Layout 後 Index Tag 沿用來源頁的 `.Target_DV_ID`，Infuser 判定「找得到目標、綁定正常」而**不標紅**，於是新頁的剖面索引安靜地指向來源頁圖號。這是複核中唯一**現有任何檢查都抓不到**的錯誤，必須在複製當下就處理，不能留給事後 Health。 | 待決定 |

## D. 已確認、不需在本表重複決定

- 2.0 正式版以完整安裝檔／可安裝套件交付；開發期才使用逐支 entrypoint 測試按鈕。
- 工具列保留 Rhino Section 快捷入口；Macro 直接呼叫 Rhino 8 內建指令，不建立 Python entrypoint、不封裝 Rhino Section 功能本體。
- 正式安裝不覆蓋使用者完整 Rhino workspace。
- 實際封裝技術、工具列格式與圖示來源延後至發佈階段評估。
- Dictionary 與即時交換 JSON 使用 Dropbox 工作檔根目錄，實體路徑由每台電腦的環境設定解析。

## AI 回寫檢查

使用者修改本文件後，AI 必須：

1. 逐項區分「已明確決定」、「仍待決定」與「答案會影響其他項目」。
2. 不擅自補完使用者沒有回答的語意。
3. 將已決定內容回寫 `LOOPFLOW_DATA_ECOSYSTEM.md` 與 `_LoopFlow_命名與資料契約.md`。
4. 對應重排 `NEXUS_DICTIONARY_DECISION_MENU.md`，避免同一問題出現兩套答案。
5. 更新 `DEVELOPMENT_ROADMAP.md`、`PROGRESS.md`、fixtures 與 migration 影響。
6. 回寫完成後保留本文件的決策結果與日期，作為可追溯紀錄。

## E. 依目前 AI 建議推導的完整工作流程

本節先把上述建議轉成一條可實際理解的操作鏈，協助判斷這些原則是否符合工作習慣。`LF_*` 名稱是 **2.0 概念指令名稱，不是已完成的按鈕或最終命名**；`! _Clipping*` 則是 Rhino 8 內建指令。

---

# CodeX 模擬執行流程

### 第一次建立模型到完成圖面

| 步驟                 | 使用的指令／動作                                    | 做了什麼                                                                                     | 產生的結果與下一步                                                                                           |
| ------------------ | ------------------------------------------- | ---------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------- |
| 1. 開啟專案            | `LF_Project_Open`／啟動檢查                      | 解析這台電腦的 `%LOOPFLOW_WORKFILES_ROOT%`，找到 Dictionary、`exchange/`、3D／2D 工作檔；驗證 Rhino 文件單位與版本 | 若不是 cm，依 ED-12 建議先阻擋並說明，不讓錯誤單位進入資料鏈；通過後建立 `project_id` context                                      |
| 2. 驗證 Dictionary   | `LF_Dictionary_Validate`                    | 讀取中文 Dictionary，檢查 schema、18 欄、Type ID、重複值、估算單位與必要欄位                                     | 產生只讀 Validation Report；錯誤先修正，通過後得到版本化 Type Catalog                                                  |
| 3. 同步 Type 與 Layer | `LF_Type_Sync`                              | 依 Type Catalog 建立或更新人類可讀的中英雙語 Rhino layers；Type ID 與 layer path 分開保存                     | 使用者得到建模 layer；不自動建立會累積的 `DNA_REF_` 線，也不因 layer 改名改變 Type ID                                         |
| 4. 建立 3D 模型        | Rhino 一般建模／Cabinet 等 LoopFlow 工具            | 使用者在對應 layer 建立、修改 Block 或幾何；Cabinet 依 local frame 保存板件方向                                | 此時幾何是設計成果，但尚未直接假設所有資料都正確；下一步先掃描預覽                                                                   |
| 5. 掃描資料影響          | `LF_Nexus_Scan`                             | 根據 Type、幾何、Space、Elevation 與既有 metadata，找出缺 ID、重複 ID、未知 Type、尺寸與前置條件問題                   | 只產生 Impact Report，不修改模型；重複 UUID 會列出原件、複本與受影響 Tag，不立即換號                                              |
| 6. 套用模型資料          | `LF_Nexus_Apply`                            | 使用者確認報告後，才建立／修復 Object ID，寫入 Type reference、Space ID、高程、尺寸及允許的 Instance override         | 形成可驗證的 Model Objects；任何 ID 變更同時保存 old→new mapping，失敗可回復                                             |
| 7. 發布 Registry     | `LF_Publish_Registry`                       | 將已通過驗證的 Type／Object／Space 資料寫入 pending，驗證完成後 atomic replace 為 current revision           | 例如產生 Registry revision `42`；2D 文件只讀這個快照，不直接修改 Registry，也不在找不到檔案時自建空檔                                |
| 8. 建立剖面／平面         | `! _ClippingSections`                       | 從 LoopFlow 工具列直接呼叫 Rhino 8 內建 Section 指令，建立 Clipping Plane／Section                       | Rhino 產生剖面定義；LoopFlow 不複製 Rhino 功能本體，也不為此建立 Python entrypoint                                       |
| 9. 建立連動圖面          | `! _ClippingDrawings`                       | Rhino 依 Clipping Plane 產生 linked Generated Drawing                                       | 得到可由 Rhino 更新的原始 Section 成果；它仍不是供長期人工修改的 Editable Drawing                                           |
| 10. 註冊 View        | `LF_View_Register`                          | 綁定 Clipping Plane、Generated Drawing 與 Detail，保存 `view_id`、方向、比例及穩定 2D↔3D transform       | 之後 Laser 由正式 transform 定位，不再用名稱包含與可變 bbox 中心猜測                                                      |
| 11. 產生可編輯圖面        | `LF_Drawing_Materialize`                    | 檢查是否已有同一 `view_id` 的前次產出，讓使用者選擇「新增、取代、略過」；複製成 Editable Drawing                           | 產生 `drawing_id`、來源 Registry／View revision 與 `generated` 狀態；不改變使用者原有 layer lock、visibility、selection |
| 12. 人工整理圖面         | Rhino 一般 2D 編輯                              | 使用者修改線稿、補線、刪除不需要內容或調整圖層                                                                  | Drawing 轉為 `modified`；LoopFlow 記得來源但不會靜默覆寫人工成果                                                      |
| 13. 建立 Sheet       | `LF_Sheet_Create` 或 `LF_Sheet_Duplicate`    | 建立 Layout、Detail、圖框與 Sheet metadata；複製時產生新 `sheet_id`／`drawing_id`／`tag_id`              | 圖號與 Layout 名稱由 metadata 算出；一般 Tag 可依 ED-13 保留模型來源，Index Tag 目標必須重審                                  |
| 14. 建立 Tag 綁定      | `LF_Tag_Grab`／`LF_Tag_Laser`／`LF_Tag_Index` | Grab 直接選模型來源；Laser 由圖面點位經 View transform 找候選；Index 選目標 View／Sheet                        | Tag 保存 `source_object_id`、`view_id`、`drawing_id`、`sheet_id` 與 template version；位置只協助定位，不作資料真相       |
| 15. 顯示最新資料         | `LF_Sync_Current_Sheet` 或 `LF_Sync_All`     | 從 Registry revision `42` 依 Tag Template 產生高程、材料、圖號、圖名等顯示值                                | Tag 記錄 `last_synced_revision=42`；`lock_state` 的人工鎖定值不被覆寫                                            |
| 16. 交付前檢查          | `LF_Health_Check`                           | 唯讀檢查 unbound、orphaned、stale、view missing、template outdated、schema mismatch 等狀態           | 產生 Issue Report；不必先由 Infuser 塗色，也不修改使用者物件色                                                          |
| 17. 選擇性修復          | `LF_Repair_Preview` → `LF_Repair_Apply`     | 先顯示問題原因、會改哪些 ID／Tag／Drawing，再由使用者選擇重新綁定、同步、保留、脫離或略過                                      | 每項修復保存結果與復原資訊；完成後重新跑 Health，直到交付範圍內問題關閉                                                             |

### 模型修改後，資料如何延續到最末端

以下用一個具體例子串起變更循環：

1. 使用者把 3D 磁磚牆高度由 240 cm 改成 260 cm。
2. 執行 `LF_Nexus_Scan`，系統辨認同一個 `object_id` 的幾何與高程資料改變，只顯示影響，不建立新 ID。
3. 使用者確認後執行 `LF_Nexus_Apply`，模型物件更新為新資料；接著 `LF_Publish_Registry` 發布 revision `43`。
4. 既有 Tag 的 `last_synced_revision` 仍是 `42`，Health 因此判定 `stale_data`；既有 Editable Drawing 的 source revision 也是 `42`，判定 `drawing_stale`。
5. 使用者先用 Rhino 內建 `! _UpdateClippingDrawings` 更新 linked Generated Drawing。這一步只更新 Rhino 的原始 Section 成果，不直接覆寫已人工修改的 Editable Drawing。
6. 執行 `LF_Drawing_Materialize`，系統找到既有 `modified` Drawing，要求選擇：
   - 保留舊圖並另建 revision `43` 的 Drawing；
   - 預覽後明確取代；
   - 保留現況並標成 detached；
   - 這次略過，繼續保持 stale。
7. 使用者選擇後，執行 `LF_Sync_Current_Sheet`；未鎖定的 Tag 從 revision `43` 更新高度，人工鎖定欄位維持原值。
8. 再執行 `LF_Health_Check`，已同步的 Tag 回到 healthy；若 Drawing 刻意保留舊版，報告會保留其 stale／detached 狀態與理由，不假裝問題不存在。

因此完整資料鏈是：

```text
Dictionary Type
→ Rhino Layer／3D Object
→ Nexus Scan／Apply
→ Registry Revision
→ Rhino Clipping Section／Generated Drawing
→ View Registration
→ Editable Drawing
→ Sheet Metadata
→ Tag Binding／Template Render
→ Health Report
→ Previewed Repair
```

這條鏈的核心效果是：3D 資料可以一路傳到圖框與 Tag，但每個階段都有明確 ID、revision、預覽與人工停點；任何更新都不以「方便」為理由靜默換 ID、重綁來源或覆蓋人工圖面。

---

# Claude Code 模擬執行流程

這一版走同一條資料鏈，但在三件事上刻意寫得比較細：**每一步在哪個 Rhino 文件執行**、**失敗或取消時會停在哪裡**、以及**哪些是第一階段就必須有、哪些可以晚點補**。指令名稱同樣是 2.0 概念名稱，不是最終命名。

全文用同一個案子當例子：一間住宅，主臥室有一面磁磚牆（Type `WL-14`，`02_Wall_牆面::Tiles.磁磚`，高 240 cm）和一個開關面板（Type `EL-05`，`06_EL_電控系統::Switch.開關面板`，Block instance，高程基準 `BC`）。

## 前提：這條流程同時跑在兩個文件上

CodeX 版流程沒有明講這一點，但它決定了很多步驟為什麼要那樣設計。

| 角色 | 檔案 | 負責 |
| --- | --- | --- |
| 3D 文件 | `LoopFlow_3D.3dm` | 建模、資料化、剖面定義、發布 Registry |
| 2D 文件 | `LoopFlow_2D.3dm` | 圖面整理、Layout、圖框、Tag、出圖 |
| 交換層 | `%LOOPFLOW_WORKFILES_ROOT%\exchange\` | Registry 快照，兩個文件之間唯一的資料通道 |
| Worksession | `LoopFlow.rws` | 讓 2D 文件看得到 3D 幾何（給對照與定位用） |

現行 1.x 的隱性要求是「3D、2D、Registry 必須同資料夾」，因為程式從目前作用中的 `.3dm` 推導路徑。2.0 改成由 `%LOOPFLOW_WORKFILES_ROOT%` 解析，這個限制才會消失——但**兩個文件的分工本身要保留**，因為使用者實際就是這樣工作的。

---

## 階段 1｜開案與環境檢查（3D 文件）

**指令 `LF_Project_Open`** → 解析本機環境變數、確認工作檔根目錄存在、載入 Dictionary 與 `exchange/` 位置、讀取 `doc.ModelUnitSystem` → 建立本次工作階段的 `project_id` context，並在命令列印出**實際生效的設定值**（Dictionary 路徑、Registry 路徑、文件單位、規則來源）。

這一步刻意做兩件現況沒有的事：

- **印出實際生效值**。現況 config 有 import fallback（`_LF_Registry` 的 8.0／120.0 vs config 的 20.0／30.0），加上各腳本 reload 時機不一，使用者無法確認「我改的設定到底有沒有生效」。
- **偵測文件單位**。依 ED-12 我的建議，這裡**一定要偵測並顯示**；至於非 cm 時是擋下還是只警告，屬於可調策略。

失敗行為：環境變數缺失或目錄不存在 → 顯示變數名稱與設定方式後**停止**，不猜測磁碟機、不建立任何檔案。

## 階段 2｜Type Catalog 與 Layer（3D 文件）

**指令 `LF_Dictionary_Validate`** → 讀取中文 Dictionary，檢查 `schema_version`、欄位完整性、Type ID 唯一性、`type_category` 與 layer 群組是否相符、估算單位是否在允許清單內 → 產生**唯讀** Validation Report。

依 ED-01，`_03_ID編號` 在載入時就拆成 `type_category` + `type_sequence`（Excel 仍維持單欄，使用者維護方式不變）。於是這裡多出一條免費的檢查：`WL-14` 必須位於 `02_Wall_牆面` 底下；如果有人把它放進 `03_Floor_地坪`，這一步就會擋下來。現況沒有任何機制會發現這件事。

**指令 `LF_Type_Sync`** → 依 Type Catalog 建立或更新 Rhino layer，並把 `type_id` 寫成 layer 的正式屬性 → 使用者得到可建模的 layer 樹。

與現況 Dict-to-Layer 的差別（依 ECO-10 與 ED-11）：

- 不再每次新增 92 條 `DNA_REF_` 參考線。若你確認這些線有用途，改由獨立的 `LF_Type_Sample` 產生，且重跑時**先清除前次產物**再重建。
- 材質建立與 layer 建立分開成兩個明確動作，不是一個指令的隱藏副作用。
- 不執行 `ZoomExtents`——不改變使用者的視圖。

## 階段 3｜建模（3D 文件）

使用者用 Rhino 一般工具或 `LF_Cabinet_Suite` 在對應 layer 建立幾何。這階段 LoopFlow 不介入，只有一個約束（依 S-11a）：**Cabinet 產生前先確認目標 layer**，避免現況「在當前 layer 產生櫃體 → Nexus 把 `_CB.*` 全部清成 `-`」的靜默清空。

## 階段 4｜資料化：先掃描，後套用（3D 文件）

這是整條流程中我認為最需要改變操作習慣的一段。現況 `TagTrigger` 是「一鍵掃描全模型並直接寫入」；2.0 拆成兩個指令。

**指令 `LF_Nexus_Scan`** → 依 Type、幾何、Space、Elevation 前置條件掃描全部 M3D 物件，但**不寫入任何東西** → 產生 Impact Report，例如：

```text
待建立 Object ID：18 個
重複 Object ID：2 組（4 個物件）
  · 主臥磁磚牆 (WL-14)  ← 原件，已被 3 個 Tag 引用
  · 主臥磁磚牆 (WL-14)  ← 2026-08-10 複製產生，無 Tag 引用
未知 Type：1 個（layer 不在 Dictionary 內）
前置條件不成立：1 個
  · 開關面板 (EL-05) 高程基準為 BC，但此物件不是 Block instance
空間未命中：3 個（區分「室外」與「未涵蓋」）
```

**指令 `LF_Nexus_Apply`** → 使用者在報告上逐項決定後才執行寫入 → 產生帶穩定 ID 的 Model Objects，並保存 `old_id → new_id` mapping。

這樣做直接解掉三個現況問題：

| 現況 | 2.0 行為 | 對應建議 |
| --- | --- | --- |
| 重複 UUID 時原件與複本**都**被換新號，既有 Tag 一起斷，只回報數量 | 報告列出雙方、標示哪一個有 Tag 引用；預設保留有引用的一方，另一方發新號 | ECO-11 |
| `BC` 用在非 Block 物件上時靜默退回 BH，Tag 仍顯示 BC | 前置條件不成立**直接列為錯誤**，不寫入該物件的高程 | ED-06 |
| 空間未命中一律寫 `EXT`，之後無法分辨「室外」與「漏掉」 | 兩者分成不同結果，TAG-O 的覆蓋檢查才可信 | ED-07 |

`_05`／`_06`／`_07` 依 ED-08 的建議，這階段先**寫入但標為「規則未定義」**，等確定有 consumer 後再回頭定方向規則。

失敗行為：Apply 過程中斷 → 已寫入部分保留、mapping 已落地，重跑 Scan 會顯示剩餘項目，不需要從頭來。

## 階段 5｜發布 Registry（3D 文件 → `exchange/`）

**指令 `LF_Publish_Registry`** → 把已驗證的 Type／Object／Space 寫入 `registry.pending.json`，驗證通過後 atomic replace 成 `registry.current.json`，前一版保留為 `registry.previous.json` → 得到 revision `42`。

三個與現況的差異：

- **只發布有 consumer 的欄位**。現況 18 欄裡有 11 欄沒有任何行為 consumer，卻全部被寫進 Registry 變成事實上的公開 API。2.0 把它們放進明確的 extension 區，或先不發布。
- **不建立沒有 consumer 的區段**。現況的 `Layout_Map` 只寫不讀、`Tag_Links` 連呼叫者都沒有。
- **Reader 永不寫入**。這是 ECO-06 的實作重點，下一階段就會用到。

## 階段 6｜剖面與 View 註冊（3D 文件）

**Rhino 內建 `! _ClippingSections`** → 建立 Clipping Plane → Rhino 產生剖面定義。
**Rhino 內建 `! _ClippingDrawings`** → 產生 linked Generated Drawing → 得到可由 Rhino 自行更新的原始剖面成果。

**指令 `LF_View_Register`** → 把 Clipping Plane、Generated Drawing、目標 Detail 綁在一起，保存 `view_id`、視線方向、比例與**固定的 2D↔3D 轉換矩陣** → 之後所有定位都用這個矩陣。

這一步是我在複核裡認為最值得投資的地方（S-7）。現況 Laser 的對位基準是**每次執行時重算**的兩個 bbox 中心：3D 側把所有可見 brep 與剖面求交、2D 側取 anchor frame 內所有 curve/hatch。結果是——你在剖面圖上多畫一條線，之後所有 Laser 綁定的落點就偏移，而且沒有任何紀錄能看出偏移了多少。

需要的資訊 Rhino 都已經提供（Clipping Plane 自帶 `Plane`，Detail 自帶 `PageToWorldTransform`，現行程式也已經在用）。缺的只是**把它固化下來**，而不是每次重猜。

## 階段 7｜圖面化（2D 文件）

**指令 `LF_Drawing_Materialize`** → 先查詢同一個 `view_id` 是否已有前次產出 → 若有，讓使用者選「新增版本 / 取代 / 略過」；若無，直接建立 → 產生 `drawing_id`、記錄來源 `view_id` 與 Registry revision `42`、狀態設為 `generated`。

依 ED-05，這個「先辨識前次產出」是 Drawing lifecycle 的第一個功能，先於任何狀態機。現況 Extract 每次無條件複製，跑兩次就是兩份完全重疊的線，且無法分辨。同時要修掉一個現況副作用：`ensure_layer()` 會把目標 layer 解鎖且不還原。

### 一個順帶解決 Laser 的提案

既然 Materialize 這一刻同時握有「3D 物件」與「剛生成的 2D 線」，建議在這裡**一次算出每條線的來源 `object_id`，存成 drawing 的來源索引**。

這樣 Laser 就從「每次對全模型求交後射線判斷」變成「點選最近的已標記線，讀出它的 `object_id`」：

| | 現況 Laser | 改用來源索引 |
| --- | --- | --- |
| 每次綁定的計算量 | 全模型 brep × 剖面求交 | 查表 |
| 對位是否會漂移 | 會（見階段 6） | 不會，關聯在生成當下就固定 |
| 多候選如何處理 | 依距離聚類，容差 200 cm（=2 公尺，過寬） | 該點附近有幾條不同來源的線，直接列出 |
| 是否需要 Worksession 附掛 3D | 必須 | 不必（但仍建議附掛以便對照） |

計算量其實沒有增加——只是把現在每次綁定都做一遍的事，改成生成時做一次。

**但這一項需要 Rhino 實機 spike 驗證**：要確認 Rhino 的 Clipping Drawing 輸出能不能穩定對應回來源物件，或者退而由 LoopFlow 自行以剖面交線做鄰近比對。在 spike 通過前，先按階段 6 的固定 transform 做即可，兩者不衝突。

**使用者接著做人工整理** → 補線、刪除不需要的內容、調整圖層 → Drawing 狀態轉為 `modified`，LoopFlow 從此不會靜默取代它。

## 階段 8｜Sheet 與圖框（2D 文件）

**指令 `LF_Sheet_Create`** → 建立 Layout、Detail、圖框，寫入 Sheet metadata（discipline / level / series / sequence / title …）→ Layout 名稱 `IN 101.01__一樓平面配置圖` 由 metadata **算出來**，不是資料本身。

依我對 ECO-05 的評估（一般建議、可分階段），第一階段只要做到「metadata 是產生名稱的來源」就夠了，完整的 Sheet 管理介面可以晚一點；因為這條的失敗是可回復的——名稱弄亂了，重跑一次就會修好。

**指令 `LF_Sheet_Duplicate`** → 複製版面 → **建立全新的 `sheet_id`／`drawing_id`／`tag_id`**，並產出一份待確認清單。

依 ED-13，這裡有一個必須當場處理、不能留給事後 Health 的項目：**Index Tag 的目標必須清除或重新指定**。現況複製後 Index Tag 沿用來源頁的 `.Target_DV_ID`，Infuser 認為「目標找得到、綁定正常」而不標紅，於是新頁的剖面索引安靜地指向來源頁的圖號。這是整份複核裡唯一連 Health 檢查都抓不到的錯誤。

另外不使用系統剪貼簿複製（現況 `_-CopyToClipboard` 會覆蓋使用者剪貼簿內容且不還原）。

## 階段 9｜Tag 綁定（2D 文件）

三種綁定意圖都保留，因為它們對應三種不同的使用情境：

| 指令 | 使用者做的動作 | 結果 |
| --- | --- | --- |
| `LF_Tag_Grab` | 直接點選要標的模型物件 | Tag 存下 `source_object_id`，來源明確無歧義 |
| `LF_Tag_Laser` | 在剖面圖上點位置 | 經固定 transform（或來源索引）找到候選；多候選時列出讓使用者選定，並記錄這是 `ambiguous` 解法 |
| `LF_Tag_Index` | 選另一張圖 / 另一個 View | Tag 存下 `target_view_id`／`target_sheet_id`，顯示的圖號由 Sheet metadata 產生 |

每個 Tag 一律保存：`tag_id`、`source_object_id`、`view_id`、`drawing_id`、`sheet_id`、`template_version`、`lock_state`。

依 ED-02，鎖定改成單一 `lock_state`。現況三支程式規則不一致——Laser 只認 `NoUpdate`、Infuser／Grab／Index 只認「不更新」——所以一個用「不更新」鎖住的 Tag，Infuser 會尊重，Laser 卻允許你重新綁定。

門窗與家具 Tag 不再使用 `NAME_PARSED` 這個哨兵值假裝有來源，改為正式的 source type。

## 階段 10｜同步顯示值（2D 文件）

**指令 `LF_Sync_Current_Sheet`（或 `LF_Sync_All`）** → 讀 Registry revision `42`，依 Tag Template 把欄位對應成顯示值 → Tag 記錄 `last_synced_revision = 42`。

以磁磚牆的高度 Tag 為例，Template 宣告的對應是：

```text
TAG_HEIGHT
  attr_ch_key  <- elevation.basis.label     → "BH"
  attr_ch_val  <- elevation.display         → "+240"
  attr_mat_key <- type.category             → "WL"
  attr_mat_val <- type.sequence             → "14"
  attr_note    <- type.display_name         → "磁磚牆面"
```

`type.category` / `type.sequence` 直接來自階段 2 拆好的欄位，不需要在這裡對 `_03` 字串做 `split("-", 1)`——這也順帶解掉「ID 本身含連字號會被誤拆」的問題。

`lock_state` 為鎖定的 Tag 完全跳過，人工填的值原樣保留。

## 階段 11｜健康檢查與修復（2D 文件）

**指令 `LF_Health_Check`** → **完全唯讀**掃描，依 metadata 判定狀態 → 產生 Issue Report。

這一步與現況 TAG-O 有本質差異。現況 TAG-O 只比對物件的 RGB 顏色，因此：必須先跑 Infuser 塗色才能檢查（先改資料才能檢查資料）、使用者自訂過顏色的 Tag 會誤判、而 Infuser 清除提示時會把 ColorSource 設回 ByLayer，**破壞使用者原本的物件顏色**。

第一階段能可靠判定的狀態只有這幾種，建議先只做這些：

| 狀態 | 判定依據 | 第一階段可做 |
| --- | --- | --- |
| `unbound` | 沒有 `source_object_id` | ✅ |
| `orphaned` | `source_object_id` 不在 Registry | ✅ |
| `manual_locked` | `lock_state` | ✅ |
| `stale_data` | Tag revision < Registry revision | ✅ |
| `drawing_stale` | Drawing source revision < 目前 revision | ✅ |
| `ambiguous` / `view_missing` / `template_outdated` / `schema_mismatch` | 需要候選集合、`view_id`、`template_version`、`schema_version` | 待對應契約完成 |

**指令 `LF_Repair_Preview` → `LF_Repair_Apply`** → 先顯示「會改哪些 ID／Tag／Drawing、原值是什麼」，使用者逐項選擇重新綁定 / 同步 / 保留 / 脫離 / 略過 → 每項修復保存結果與復原資訊。

---

## 完整變更循環：把磁磚牆從 240 改成 260

這是實務上最常發生的事，也是檢驗整條鏈是否成立的標準案例。

| # | 在哪 | 指令／動作 | 發生什麼 | 結果 |
| --- | --- | --- | --- | --- |
| 1 | 3D | Rhino 一般編輯 | 使用者把牆拉高 20 cm | 幾何改變，`object_id` 不變 |
| 2 | 3D | `LF_Nexus_Scan` | 比對後發現此物件的高程與尺寸已變 | 報告顯示「1 個物件資料需更新」，**不建立新 ID、不寫入** |
| 3 | 3D | `LF_Nexus_Apply` | 使用者確認後寫入新高程 | Model Object 更新，ID 與既有 Tag 關聯完全不動 |
| 4 | 3D | `LF_Publish_Registry` | pending → validate → replace | 產生 revision `43`，`previous` 保留 `42` |
| 5 | 2D | `LF_Health_Check` | Tag 的 `last_synced_revision=42` < `43`；Drawing source revision 也是 `42` | 報告：3 個 Tag `stale_data`、1 張圖 `drawing_stale`。**此時什麼都還沒被改** |
| 6 | 2D | `! _UpdateClippingDrawings` | Rhino 更新 linked Generated Drawing | 原始剖面成果變新，**已人工修改的 Editable Drawing 不受影響** |
| 7 | 2D | `LF_Drawing_Materialize` | 偵測到既有 Drawing 狀態是 `modified` | 要求選擇：另建 revision `43` 版本 / 預覽後取代 / 標為 detached / 這次略過 |
| 8 | 2D | `LF_Sync_Current_Sheet` | 未鎖定的 Tag 從 revision `43` 取值 | 高度 Tag 從 `+240` 變成 `+260`；鎖定的 Tag 原值不動 |
| 9 | 2D | `LF_Health_Check` | 重新判定 | 已同步的 Tag 回到 healthy；若第 7 步選了「略過」，報告會**繼續保留** `drawing_stale` 與原因，不假裝問題消失 |

關鍵在第 5 步和第 7 步：**檢查不修改任何東西**，而**任何可能覆蓋人工成果的動作都要先問**。現況這兩點都不成立——TAG-O 要先靠 Infuser 塗色才能檢查，Extract 則是直接再複製一份。

---

## 中斷、取消與失敗時停在哪裡

這是 ECO-08 的實際意義，也是現況最薄弱的地方。每個階段都要能明確回答「我按了 Esc 之後現在是什麼狀態」。

| 階段 | 中途取消 | 執行失敗 |
| --- | --- | --- |
| 開案 | 無副作用 | 顯示缺少的設定，不建立任何檔案 |
| Dictionary 驗證 | 無副作用（唯讀） | 列出全部錯誤列，不部分套用 |
| Type Sync | 已建立的 layer 保留，重跑補齊 | 報告哪些 layer 失敗，不留半套 |
| Nexus Scan | 無副作用（唯讀） | 同上 |
| Nexus Apply | 已寫入部分保留、mapping 已落地，重跑 Scan 顯示剩餘 | 同左，並標明中斷點 |
| Publish | `current` 不變，`pending` 留著供檢查 | `current` 與 `previous` 都完好 |
| Materialize | 不留半份圖 | 已建立的部分可用同一 `drawing_id` 辨識並清除 |
| Sheet 複製 | 不留半頁 | 待確認清單仍產出 |
| Tag 綁定 | Tag 維持原綁定 | 同左 |
| 同步 | 已同步的 Tag 保留其 revision，未處理的維持舊值 | 同左，報告列出未完成範圍 |
| Health | 無副作用（唯讀） | 部分結果仍可顯示，標明未檢查範圍 |
| Repair | 未套用的項目不變 | 已套用項目可依復原資訊回退 |

另外三個現況會「順手改掉使用者東西」的行為，在 2.0 都要還原：selection、layer lock／visibility、物件顏色。

---

## 第一階段最小可用範圍

這條鏈不需要全部做完才能開始用。若要讓「模型 → 圖面 → Tag」跑通一次，最少需要：

**必須有**（缺一條鏈就斷）

1. `LF_Project_Open`：路徑解析 + 單位偵測
2. `LF_Dictionary_Validate` + `LF_Type_Sync`：Type Catalog 與 layer
3. `LF_Nexus_Scan` / `LF_Nexus_Apply`：Object ID 與資料（含 ID 變更預覽）
4. `LF_Publish_Registry`：安全發布 + revision
5. `LF_View_Register`：固定 transform
6. `LF_Drawing_Materialize`：冪等的可編輯圖面
7. `LF_Tag_Grab` + `LF_Sync_*`：最簡單的綁定與同步
8. `LF_Health_Check`：前述五種可靠狀態

**可以晚一輪**

- `LF_Tag_Laser`（有 Grab 就能出圖，Laser 是效率工具）
- `LF_Sheet_Duplicate`（可以先手動建頁）
- 完整 Drawing 狀態機（先有冪等就夠）
- Cabinet／2D 工具重建（現有 1.x 版本可以繼續用到最後）
- `_09_實作數量`、`_05`/`_06`/`_07` 的方向規則（都還沒有 consumer）

**建議最先動工的一項**：階段 4 的 Scan／Apply 拆分。它同時解掉 UUID 不可逆損失（ECO-11）、BC 靜默錯誤（ED-06）與空間未命中歧義（ED-07），而且不依賴其他任何新契約。

---

## 與 CodeX 流程的主要差異

兩版的資料鏈結論一致，差異在細節與優先序：

| 項目 | CodeX 版 | 本版 |
| --- | --- | --- |
| 文件分工 | 未區分 3D／2D | 每步標明執行文件，並說明 Worksession 角色 |
| Nexus | Scan → Apply 兩步 | 相同，但明列 Impact Report 實際內容與三個現況問題的對應 |
| Laser | 用固定 View transform 定位 | 相同，另提議在 Materialize 時建立來源索引，讓 Laser 退化成查表（需 spike 驗證）|
| Sheet metadata | 強烈建議、一次到位 | 一般建議、可分階段（失敗可回復）|
| 非 cm 專案 | 直接阻擋 | 偵測與顯示是必須；阻擋只是可調的預設策略 |
| Health 狀態 | 列出十種 | 第一階段只做五種可靠判定的，其餘標註前置需求 |
| 失敗行為 | 未展開 | 每階段列出取消與失敗時的狀態 |
| 施工順序 | 未排 | 給出最小可用範圍與建議最先動工項目 |

兩版都指向同一個核心：**每個階段都有明確 ID、revision、預覽與人工停點，任何更新都不以「方便」為理由靜默換 ID、重綁來源或覆蓋人工成果。**
