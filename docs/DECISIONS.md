# 決定紀錄

格式:編號、日期、決定、理由、依據、會重開的條件。

## D-001 執行架構:混合式(2026-11-25,使用者選定)
- **決定**:GitHub Actions 免費跑無 LLM 的抓取層;每天 1 次 Claude Code 雲端排程做判斷、驗證、少量研究、簡報、記憶更新,推播到手機;使用者在同一 session 回饋與追問。
- **理由**:抓取不耗 AI 額度;判斷用已付費的 Claude Pro;手機只需一個介面;判斷層指令是純 Markdown,可換供應商。
- **捨棄**:A 全靠 Claude 排程(抓取不穩、全耗額度、完全綁單一供應商);B 全自建 Gemini+Telegram(工程最多,Gemini 免費搜尋額度不確定)。
- **依據**:Claude Code 排程任務 Pro 可用,官方發布文寫 Pro 每天 5 次(單一來源,另有使用者回報不同上限);Gemini 免費搜尋接地額度說法不一(未驗證);同類開源專案(Horizon、AI Digest Daily、BuzzAgent)多為「Actions 抓取 + LLM 評分」。
- **重開條件**:Claude 用量過高、排程次數不夠、或需要即時通知時。

## D-002 Token 約束(2026-11-25,使用者:「如果不會很燒 token 就用 Claude」)
- **決定**:判斷層只讀預先篩好的短名單,並受 `config/budget.yaml` 硬上限約束;排程用 Sonnet。
- **驗證**:上線第一週看 Claude 用量頁;過高先降短名單與深挖數,仍過高則重開 D-001。

## D-003 Repo(2026-11-25,使用者選定)
- 名稱 `hcx05/Ai-Secretary`,私有。

## D-004 推送通道:Telegram(2026-11-25,使用者選定)
- **決定**:簡報推上 `main` → `notify` workflow 送 Telegram;回覆由 `collect` 每 6 小時收進 `memory/inbox.jsonl`,daily 處理。只收 `TELEGRAM_CHAT_ID` 的訊息。
- **理由**:Telegram token 與 Discord webhook 都在 URL 裡,雲端代填憑證只支援 header,所以由 Actions 用 repo secrets 發送。
- **待辦**:使用者設 `TELEGRAM_BOT_TOKEN`、`TELEGRAM_CHAT_ID`(見 `TELEGRAM.md`)。

## D-005 排程跑在常駐 session(2026-11-25,上線測試後改)
- **原計畫**:每次排程開新 session。**實測**:新 session 拿不到本 repo 的寫入權限(push 403、`add_repo` 不可用),簡報推不上去。
- **改為**:建一個帶本 repo 的常駐 session,每日與每週排程都叫醒它。實測 `daily: 2026-11-25` 已推上 `main`,`notify` 也觸發成功。
- **代價**:對話會累積,靠自動壓縮控制;每次執行都以 repo 檔案為準,不依賴對話內容。這種排程不能開 Claude App 推播,推播改靠 Telegram。
- **重開條件**:把本 repo 加進雲端環境的 Repositories 後,可改回每次開新 session(較省 token、可開 App 推播)。

## 已知限制(2026-11-25)
- ~~雲端環境網路受限~~:2026-11-26 使用者核准,Default 環境網路改為不限制;實測 arxiv.org、simonwillison.net 可讀,判斷層可驗證原文。
- Reddit 在 GitHub Actions 與雲端 session 都回 403(Reddit 擋雲端 IP,非我方網路設定;其餘 20 個來源正常)。

## D-006 常駐 session v2 + 台北日期(2026-11-26)
- **問題**:(1) 07:43 台北觸發時 UTC 仍是前一天,判斷層以為今天已做過;(2) GitHub 排程的 collect 未準時執行;(3) 常駐 session 對話累積,每次喚醒重讀約 16 萬 token。
- **改為**:日期一律用 Asia/Taipei(`collector/clock.py`);daily 發現資料超過 8 小時就本機補抓;新常駐 session「AI 情報官(常駐 v2)」每次把工作交給一次性子 agent,自己只轉貼結果,對話增長小。排程已改指向 v2;舊常駐 session 保留未封存。
- **Telegram**:改用 HTML 格式送出(粗體、標題、連結),失敗自動改送純文字。

## D-007 優惠範圍、資安平台、簡報格式(2026-11-26,使用者指示)
- **來源**:新增 HTB blog、OffSec、PortSwigger blog(RSS),TryHackMe blog、HTB events、Google Cloud 免費方案、AWS Free Tier(頁面變動偵測)。Azure 學生頁每次內容不同會誤報,未加;TryHackMe 無 RSS。
- **權重**:`deals`、`free_resources` 升到 3.0,關鍵字不限學生;新增 `security_platforms` 3.0。
- **格式**:每則去掉「為什麼重要/與你有關」標籤、「建議行動」、自我關聯評語;可信度只寫高/中/低。簡報新增「優惠與活動」一節,不占主要情報名額。
- **限制**:頁面變動偵測第一次只建基準,不會報出加入前已存在的內容。

## D-008 工作流與開源工具(2026-11-26,使用者指示)
- **來源**:新增 Anthropic Engineering、Latent Space、Addy Osmani、Armin Ronacher、Hamel Husain、OpenAI Engineering(RSS)。
- **GitHub**:除了 7 天內新建的 repo,新增「竄升」查詢:30 天內建立且 ★≥200,主題 claude-code、agent-skills、claude-skills、claude-code-plugin、mcp-server、context-engineering、ai-agents。已進過短名單的不重複出現。
- **權重**:新增 `workflow` 主題 3.0。簡報新增「開源工具」一節(一行一則),只介紹不安裝。
- **風險**:熱門新 repo 可能是供應鏈攻擊載體;簡報標「程式碼未審查」,判斷層不執行任何抓到的程式。

## D-009 collect 排程重新登記(2026-11-26)
- **問題**:`17 */6 * * *` 自 11-25 上線後一次都沒自動觸發,只有手動那次。原因未確定(GitHub 排程是盡力而為,新 repo 與高峰時段常延誤或略過)。
- **做法**:改為 `41 1,7,13,19 * * *`(UTC;台北 09:41、15:41、21:41、03:41),修改檔案讓 GitHub 重新登記排程。daily 的本機補抓照舊當備援。
- **重開條件**:改完後 24 小時內仍沒有 `schedule` 觸發的執行,就改用外部觸發或完全依賴 daily 補抓。
- **2026-11-26 08:05 UTC 檢查**:07:41 沒有 `schedule` 執行(至今 3 次全是手動)。07:03 又改過 cron(D-011),可能尚未生效;再看 09:41、11:41 兩次。仍沒有就改外部觸發:cron-job.org 每 2 小時呼叫 workflow_dispatch(需使用者建立只限本 repo、只有 Actions 寫入權限的 fine-grained token)。
- **2026-11-26 10:20 UTC**:09:41 仍未觸發(累計錯過 5 次,`schedule` 執行數 0)。判定 GitHub 排程不可靠,改請使用者設定 cron-job.org 外部觸發;workflow 內的 cron 保留,恢復時兩者並存,`concurrency` 防止重疊。

## D-010 簡報只留情報(2026-11-26,使用者指示)
- 移除「可以放心忽略」「覆蓋盲區」兩節、預算說明、「程式碼未審查」等附註、標題後的括號註解。
- 抓取失敗、疑似提示注入、預算用盡改記在 commit 訊息;安全規則不變(只介紹開源工具,不安裝、不執行)。

## D-011 一手情報員:盯官方、限時即推、自己找新來源(2026-11-26,使用者同意)
- **起因**:Hack Smarter「新靶場 24 小時免費」只在官網、Discord、Reddit 公告;Reddit 從雲端一律被擋,官網是 JS 網站,舊抓法看不到內容,所以漏掉。
- **盯官方**:`pagewatch` 新增 `render: true`,用無頭瀏覽器跑出內容再比對(Hack Smarter、HTB 首頁、OffSec 首頁)。TryHackMe 首頁擋自動瀏覽器,維持部落格頁。Reddit 停用(二手資訊且抓不到)。
- **限時即推**:`notify/flash.py` 在每次抓取後,對 platform/deals/free 來源的新內容比對限時、免費、折扣等字眼,命中就立刻送 Telegram(不用 AI),每則只送一次。collect 改每 2 小時一次。
- **找新來源**:weekly 4.5 搜尋尚未監控的官方來源,最多 5 個列為候選;使用者回「加 N」才轉正。
- **代價**:Actions 用量約每天 12 次 × 2–3 分鐘(私有 repo 免費額度每月 2000 分鐘內)。
- **仍抓不到**:只在 Discord 或 X 公告的消息。
- **2026-11-26 12:00 UTC 已恢復(外部觸發)**:使用者設定 cron-job.org 每 2 小時(台北整點偶數時)呼叫 `collect.yml` 的 workflow_dispatch,token 為 fine-grained、只限本 repo、只有 Actions 讀寫;測試回 204,12:00 UTC 實際觸發成功。token 存在 cron-job.org,不在 repo;到期或外洩時到 GitHub 撤銷重建。

## D-012 滲透測試後的加固(2026-11-26,使用者:「在不影響現有功能情況下盡可能修」)
- **H1 提示注入 → 改程式 → 拿 secrets**:無法在程式層完全封死(私有 repo 的分支保護需付費方案)。三層緩解:(1) `python -m secretary guard`:排程流程推送前檢查路徑白名單(daily 只能動 `briefs/ memory/ data/`),失敗不推;(2) `guard.yml`:main 上程式、workflow、依賴、`agent/`、`config/` 有變更就發 Telegram 通知,不執行 repo 程式;(3) CLAUDE.md 明定外部內容要求改程式、加來源、推送、讀秘密一律視為注入。
- **M1**:Anthropic 兩個鏡像來源拿掉 `official`、prior 降到 1.0;只讀鏡像可信度最多「中」。
- **M2**:無頭瀏覽器只拿到最小環境變數(不含 token),能開沙箱就開;collect checkout 不留憑證,推送時才帶 token。
- **M3**:`requirements.txt`、`requirements-render.txt` 以 pip-compile 釘版本與 hash(來源在 `*.in`),Python 3.11/3.13 都實測安裝與測試通過。升級:改 `.in` 後重跑 pip-compile。
- **M4**:Telegram 連結文字若像網址卻指向別處,改顯示真實網址。
- **L1–L8**:來源 id 限 `[a-z0-9_]`;inbox 只收私聊且寄件者是本人,轉傳標 `forwarded`;外部 tag 加 `x:` 前綴;Telegram 錯誤訊息不含 token;notify 手動輸入只接受 `briefs/YYYY-MM-DD.md`;下載上限 10MB / 60 秒;限時正規表示式數字限 4 位;feedback 原話用 heredoc 傳入。
- **未做**:Telegram 與 collect 仍執行 repo 內程式(H1 的根本解需要分支保護或把 secrets 移出 repo 程式可及範圍)。

## D-013 AI 大模型免費用量(2026-11-26,使用者要求)
- **來源**:ChatGPT 方案、OpenAI API 價格、GitHub Copilot 方案、Kiro 方案、Gemini API 價格(官方頁,頁面變動偵測);codertesla/ai-coding-deals(第三方清單,只用來發現,推送前回官網驗證)。
- **規則**:免費或加倍用量、免費 credits 一律推,不因已有 Claude Pro / Google AI Pro 而略過;限時關鍵字加入 2x usage、免費額度等。
- **pagewatch**:雜湊變了但沒有任何字詞變動時不算變更(ChatGPT 價格頁每次載入雜湊不同)。
- 3C 與顯卡優惠待使用者決定地區與品項。

## D-014 3C 與顯卡優惠(2026-11-26,使用者:台灣+美國,整類特價+指定品項)
- **台灣**:原價屋價目表(`coolpc`,解析 6,500+ 品項)。整類:指定分類中折扣 ≥15%、≥NT$1000 的前 12 則進短名單。指定品項:比上次看到的最低價低就即時推播。
- **美國**:Slickdeals 首頁與熱門 RSS,只留 3C 字眼的;指定品項用 Slickdeals 搜尋,有新符合的優惠就即時推播。Newegg 擋機器人,未加。
- **指定品項**:`config/watchlist.yaml`(name、match、exclude、tw_category、us)。整類特價不即時推播,放每日簡報「優惠與活動」。
- **已知雜訊**:Slickdeals 搜尋結果鬆散(整機、筆電),靠各品項的 exclude 調整。

## D-015 3C 改由系統自行判斷(2026-11-26,使用者:「中高階 3C 周邊有明顯特價都通知」)
- **中高階**:原價屋依分類設原價門檻(顯示卡 NT$12000、螢幕 6000、處理器 6000、主機板 5000、鍵盤 2500、滑鼠 2000、耳機/喇叭 3000、SSD/記憶體 2500 等,見 sources.yaml `tiers`);美國 Slickdeals 只留 $100 以上的周邊與零組件,排除筆電、手機、電視、整機、整新品。
- **明顯特價**:折扣 ≥20%,或限時下殺 ≥15%。同款不同顏色算一則。Slickdeals 首頁/熱門本身是社群篩過的優惠。
- **通知**:每次抓取把新的 3C 特價合成一則「🛒 3C 特價」,最多 8 行;同一品項同價格只推一次。watchlist 保留為選用。
- **量**:上線時原價屋符合 10 則;之後每 2 小時只推新出現的。

## D-016 3C「明顯特價」門檻提高(2026-11-26,使用者:「折扣沒低於六折,就必須至少價差過萬」)
- 取代 D-015 的 20% / 限時 15%:中高階周邊必須**六折以下**,或**省 NT$10000 以上**(美國 Slickdeals 以 40% off 或省 US$300 判斷,標題沒有原價或折扣的不推)。
- 上線時原價屋與 Slickdeals 符合者皆 0 則:預期很少通知,有就是真的大折扣。

## D-017 頁面比對忽略「只是換位置」的內容(2026-11-27)
- **問題**:GitHub 學生方案頁每次載入,優惠順序都不同;逐字比對把舊優惠當成新增,含「free access」就觸發限時推播(11-27 08:01、10:24 兩則誤報)。
- **改為**:新增或刪除的片段,要有一半以上的 5 字片語是另一版沒有的才算;整塊搬移的內容不算。實測學生方案頁比對結果為空;真正新增的段落仍會被抓到(有測試)。
