# 記憶資料說明

| 檔案 | 用途 | 格式 |
|---|---|---|
| profile.md | 長期偏好、目標、工具與訂閱 | 每條標 [確認]/[推測]/[失效] |
| interests.yaml | 預評分主題權重 | topics: 名稱 -> weight, keywords |
| now.md | 短期需求(有到期日) | Markdown |
| tracking.yaml | 長期追蹤項目 | YAML |
| feedback.jsonl | 回饋紀錄(一行一筆) | {"ts","item_id","source_id","topics","verdict","quote","reason"} |
| seen.jsonl | 已推送情報(防重複) | {"id","url","title","source_id","tags","date"} |
| questions.md | 待問使用者的問題 | Markdown |

feedback.jsonl 與 seen.jsonl 初始為空(JSONL 不能有註解)。全部可直接編輯;改動即 git commit。
