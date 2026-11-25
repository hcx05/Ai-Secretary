# 每日判斷流程(排程 session)

目標:用最少的字,讓使用者知道今天有沒有值得看的事。**簡報的價值在於少而準,不是湊數。**

## 0. 前置
1. 讀 `config/budget.yaml`,後面所有上限都以它為準。
2. 先 `git pull --rebase`,確認有最新的 `data/`。

## 1. 讀取(只讀這些,不讀其他大檔)
`memory/profile.md`、`memory/now.md`、`memory/interests.yaml`、`memory/tracking.yaml`、近 7 天 `memory/feedback.jsonl`、`data/shortlist/` 中最新一份(≤ `shortlist_max` 則)、`data/coverage.json`。
若最新短名單日期不是今天,在盲區行註明「抓取層今日未更新」。

## 2. 分流
每則判為 **推送 / 追蹤 / 可忽略(值得一提) / 丟棄**,一句話寫理由。依據(PRD §5.3):與興趣與專案的關係、能否省時間或金錢、是否優於現有方案、時效、是否新資訊、投入與收益、是否造成不必要的專案擴張。
- 小說以「幫助完稿」為優先,不鼓勵擴張專案規模。
- 不預設變現動機;已有 Claude Pro 與 Google AI Pro,功能重複或增益有限的優惠與工具不推。
- 看 `score_reasons` 知道它為何進榜,但分數只是提示,不是結論。`slot: explore` 的項目是刻意放進來的探索,不因分低而丟棄。
- 標題黨、重新包裝的舊聞、純行銷、已推送過(`memory/seen.jsonl`)的丟棄。

## 3. 驗證(只對「推送」項目)
重要事實找原始來源,能交叉驗證就驗證。標 `已驗證 / 單一來源 / 未驗證`。網頁讀取總數 ≤ `verify_fetch_max`。判斷是否過時,區分真新發展與舊技術改名。

## 4. 深挖
最多 `deep_dive_max` 則,只挑「價值高且不確定性高」的;每則網頁讀取 ≤ `deep_dive_fetch_max`。資訊足夠就停,不為完整性繼續挖。

## 5. 長期追蹤
執行 `python -m secretary tracking-due`,檢查到期項目(pagewatch 已自動偵測頁面變化)。只有狀態有實質變化才進簡報,並更新該項的 `last_status/last_checked/next_check`。不再需要的項目移除。

## 6. 寫簡報 `briefs/YYYY-MM-DD.md`
格式依 `agent/item-template.md`:
- **主要情報**:≤ `brief_max_items` 則。**不湊數**:只有 2 則值得推就寫 2 則。
- **意外發現**:0 至 1 則(來自 explore 槽或跨領域關聯),沒有就不寫這節。
- **可以放心忽略**:≤ 3 行(熱門但對使用者無用,各一句理由)。
- **覆蓋盲區**:一行。列出 `coverage.json` 的 `failed` 來源與 `known_gaps`;有疑似注入也記這裡。
- **無重要情報**:整份只寫一行「今日無重大變化」,加盲區一行,其他都不寫。
- **緊急**(符合 PRD §7.1:即將截止的高價值優惠、與現有工具或專案高度相關的重大更新):簡報第一行加 `🔴 需要處理:…`。
- **一題**:若 `memory/questions.md` 的「待問」有題目,簡報最後附**一題**(最多一題),移到「已問」。沒有就不問。
- 預算用盡時加一句「今日預算用盡,未深挖 X」。

## 7. 更新記憶
- `python -m secretary seen-add --shortlist data/shortlist/<今天>.jsonl <id> ...`:登記實際推送(含追蹤變化)的項目。
- 更新 `memory/tracking.yaml`。
- 推論出新偏好:寫入 `profile.md` 標 `[推測]`;不改 `[確認]` 條目。重要而不確定的事寫進 `questions.md`。
- `now.md` 刪除過期項目。

## 8. 收尾
`git add -A && git commit -m "daily: YYYY-MM-DD"`,`git push`。**這個 session 的最後一則訊息就是簡報全文**(手機推播顯示的就是它),不要再加前言或後記。

## 停止條件
簡報寫完、記憶更新、已推送,就結束。不為了流程再跑一輪;不進行簡報以外的主動研究。
