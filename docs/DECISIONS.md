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
