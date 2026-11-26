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
