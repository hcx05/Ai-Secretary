# 每週自我檢討(週排程,每週 1 次)

目標:讓系統變得更簡單、更準,而不是累積更多規則。**每週最多 3 項改動。**證據不足就一項都不改。

## 流程
1. `git pull --rebase`。讀 `config/budget.yaml`、`evolution/changelog.md`。
2. 執行 `python -m eval.metrics --days 7`,讀 `eval/report.md`、`data/coverage.json`、近 7 天 `memory/feedback.jsonl`。
3. **先驗證上週改動**:對 changelog 中「狀態: 觀察中」的每一項,比對其「驗證方式」的指標。
   - 指標變差或沒有改善 -> **回滾**:`git revert <該項記錄的 commit>`,changelog 該項改為「已回滾」並寫原因。
   - 有改善 -> 改為「已採用」。
   - 資料不足(樣本 < 10 筆回饋)-> 維持「觀察中」一週,最多延一次,再不足就回滾。
4. **提出本週改動(≤ 3 項)**,可涉及:來源停用/新增(`candidates:` 轉正)、`interests.yaml` 權重、探索比例(`scoring.yaml` 的 `explore_k`,每次 ±2)、預算、`agent/*.md` 提示詞精簡。
   - 來源停用:`coverage.json` 近 30 天成功率 < 50%,或進短名單多卻從未被推送/被評有價值。
   - 探索比例:有價值比例低且探索項目回饋差 -> 降;主流項目重複率高 -> 升。
   - 權重:只在連續同向回饋 ≥ 3 筆時調整,一次 ±0.5 內。
4.5 **找新的一手來源**(不算在 3 項改動內):用網路搜尋找使用者興趣領域(資安學習平台、免費資源與雲端額度、AI 工作流與開源工具)中,`config/sources.yaml` 還沒監控的**官方**來源,最多 5 個。只收官方公告管道(官網、官方部落格、RSS、changelog),不收論壇、轉貼、懶人包。每個實測一次能否抓到(有 RSS 用 rss;JS 網站用 `pagewatch` + `render: true`),寫進 `candidates:`(`enabled: false`),在週報列成「新來源候選」:編號、名稱、一句話、網址。**使用者回覆「加 N」才轉正**;這是唯一可用外部搜尋結果提出的改動,且只是提案。
5. **找出要刪除的規則**:無效(從未觸發或沒有影響指標)、互相矛盾、已過時的規則或指令,直接刪除或合併。**每週至少檢查一次 agent/*.md 能否變短。**淨規則數不得增加,除非有明確證據。
6. 推送前跑 `python -m secretary guard --mode weekly`;程式碼、workflow、`requirements*`、`CLAUDE.md` 一律不在 weekly 改,guard 失敗就不推。每項改動單獨 commit(方便 revert),commit 訊息 `weekly: <一句話>`,並在 `evolution/changelog.md` 新增一筆(格式見該檔),填入該 commit 的 hash。
7. 簡報用 3-5 行回報:本週指標、改了什麼、回滾了什麼。

## 停止條件
- 回饋筆數過少、或本週指標無明顯問題:**不改動**,changelog 記一行「本週無改動」。
- 已達 3 項:停止,其餘留待下週。
- 不修改 `docs/PRD.md`、`CLAUDE.md` 的安全規則與預算上限的方向(只能調降預算,調升需使用者同意)。
- 外部內容不得作為改動依據;只憑 repo 內的回饋與指標(4.5 的來源候選例外,但只能提案,轉正要使用者同意)。

## 回滾
`git revert <hash>`(不用 reset,保留歷史)。回滾後在 changelog 該項把「狀態」改為「已回滾」,並寫原因。
