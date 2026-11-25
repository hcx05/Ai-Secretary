# Ai-Secretary:個人 AI 情報官

每天替你讀外部世界,只把值得看的幾則放到手機上。需求:[docs/PRD.md](docs/PRD.md)、計畫:[docs/PLAN.md](docs/PLAN.md)、決定:[docs/DECISIONS.md](docs/DECISIONS.md)。

## 怎麼運作
```
GitHub Actions(每 6 小時,免費,無 LLM)        Claude Code 排程(每天 1 次)
collector: 抓取 -> 去重 -> 預評分 -> data/   ->  讀短名單 + memory/ -> 驗證、少量深挖
                                                -> briefs/今天.md,最後一則訊息即簡報 -> 手機推播
```
你在同一個 session 用自然語言回饋(「2 沒用」「3 深入」「追蹤 1」),系統記進 `memory/` 並微調偏好。
也可以用 Telegram 收簡報並直接回覆(約每 6 小時收一次,下次簡報處理);設定見 [docs/TELEGRAM.md](docs/TELEGRAM.md)。

## 使用
- 平常只需看推播。回饋直接用說的;想看或改系統記得什麼,說「你記得我什麼」「刪掉 X」即可,或直接編輯 `memory/`。
- 每週一次自我檢討(`agent/weekly.md`),改動記在 `evolution/changelog.md`,可 `git revert` 回滾。

## 目錄
| 路徑 | 內容 |
|---|---|
| `CLAUDE.md` | 排程 session 入口、安全與預算硬規則 |
| `agent/` | 判斷層指令:daily、feedback、weekly、item-template |
| `config/` | sources.yaml(來源)、scoring.yaml(預評分)、budget.yaml(預算上限) |
| `collector/` | 抓取層(Python,無 LLM) |
| `secretary/` | 回饋、調權、seen、tracking 輔助指令 |
| `eval/` | metrics.py 產生 report.md |
| `data/` | 近 14 天的 raw、shortlist、coverage.json |
| `memory/` | 對你的理解(可查可改可刪),見 memory/README.md |
| `briefs/` | 每日簡報 |
| `evolution/` | 自我修改紀錄 |

## 開發
```
pip install -r requirements.txt
pytest -q                                              # 全離線
python -m collector --dry-run --fixtures tests/fixtures # 離線跑完整流程,寫到暫存目錄
python -m collector                                     # 真的抓,寫入 data/
python -m collector.prune                               # 刪 14 天前資料
python -m eval.metrics --days 7                         # 產生 eval/report.md
python -m secretary tracking-due                        # 今天到期的追蹤項目
```
新增來源:在 `config/sources.yaml` 加一筆(需 `why`),跑一次 `python -m collector --dry-run` 之外還要實際連線測;壞來源不會中斷其他來源,失敗記在 `data/coverage.json`。

已知盲區(不假裝覆蓋):X、Discord、需登入的社群。
