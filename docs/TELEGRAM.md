# Telegram 設定(一次,約 5 分鐘)

1. Telegram 找 `@BotFather` → `/newbot` → 取名 → 拿到 token。
2. 傳任意訊息給你的 bot(例如 `hi`)。
3. 瀏覽器開 `https://api.telegram.org/bot<token>/getUpdates`,找 `"chat":{"id":123456789` 的數字。
4. GitHub repo → Settings → Secrets and variables → Actions → New repository secret:
   - `TELEGRAM_BOT_TOKEN` = token
   - `TELEGRAM_CHAT_ID` = 那串數字
5. 測試:Actions → `notify` → Run workflow(不填參數,送出最新一份簡報)。

## 運作方式

- **送出**:每日簡報 `briefs/*.md` 被推上 GitHub → `notify` workflow 送到 Telegram(純文字,超過 4000 字自動分段)。
- **回覆**:直接在 Telegram 回覆(例如「2 沒用」「3 深入」「追蹤 1」)。每次抓資料(約每 6 小時)時順便收進 `memory/inbox.jsonl`,bot 回「收到 N 則」;下次每日簡報時由 AI 判讀成回饋並處理。
- **只認你**:只收 `TELEGRAM_CHAT_ID` 這個聊天的訊息,陌生人傳給 bot 的一律忽略。
- **即時追問**:Telegram 回覆不是即時對話;想立刻深入某則,用 Claude App 打開當天的排程 session 直接問。
- 沒設 secrets 時,所有 Telegram 步驟自動略過,不會報錯。

## 停用

刪掉兩個 secrets 即可。

## 選用:即時推播用 Gemini 潤稿
1. 到 https://aistudio.google.com/apikey 建立 API key(免費層即可)。
2. GitHub repo → Settings → Secrets and variables → Actions → New repository secret,名稱 `GEMINI_API_KEY`,貼上 key。
3. 下次抓取時,即時推播會先經 Gemini 過濾弱優惠並改寫成繁中一句。沒設定也能用,只是文字是原文那一句。
