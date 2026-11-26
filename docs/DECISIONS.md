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
