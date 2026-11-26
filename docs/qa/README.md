# 測試與驗收紀錄

這裡收錄每一輪修改的驗收證據（說明、測試紀錄、截圖與 JSON 結果）。

- **只想看結論**：讀[候選、接守與排序研究](replay-evidence-20261116/README.md)、[網站與本機 API 收尾](../project-closeout-20261116.md)及[2026 球季資料與守位](data-2026-20261114/README.md)。
- **想核對某項功能**：依下方分類找對應日期的紀錄。
- 舊紀錄保留作歷史追溯，數字與畫面以當時版本為準；現行說明見 [README](../../README.md) 與 [技術細節](../技術細節.md)。

## 最新

以下依日期列出目前分支的最新證據；不等於全部已合併或部署。10/23 及更早資料保留作歷史對照。

| 日期 | 紀錄 | 重點 |
|---|---|---|
| 11-21 | [網站視覺精修與專案整理](visual-refresh-20261121/README.md) | 深藍頁首、卡片與按鈕層次；線上站不再多一次 API 404；移出 15 支停用腳本；11/25 再移除未使用的 CSS 並更新首圖；11/26 共用配球計數規則並移除重複程式；不改模型與數值 |
| 11-16 | [候選名單、實際接守與進件演練](replay-evidence-20261116/README.md) | 360 場候選覆蓋、561 次代打接守、八日排序敏感度及增量進件 |
| 11-16 | [專案收尾與發布驗收](../project-closeout-20261116.md) | GitHub Pages 版本核對、回放連結故障可重試、本機回放 API、模型結果與交接 |
| 11-15 | [多日期回放與疲勞研究](website-roadmap-20261115/README.md) | 8 日／24 場回放、手機候選快比、牛棚 A／B、三棒疲勞與勝率校準 |
| 11-15 | [2026 換投時機回測](timing-2026/README.md) | 360 場、八個月初模型、12,075 個決策點，並與 10/04 回放標記交叉核對 |
| 11-15 | [季中迭代：每週前推檢驗近期加權](season-iteration-2026/README.md) | 2026 24 週、88,179 球；近期加權沒有更準，網站維持不加權 |
| 11-14 | [前端改用 2026 球季資料](data-2026-20261114/README.md) | 三季進件、2026 守位、2024–2026 重訓批次、2026 背號與預設先發、Python／JS 54 情境一致 |
| 11-13 | [2024–2026 投打模型實驗](model-horizons-20261113/README.md) | 逐月重訓、RE24 混合模型、三棒失分同樣本比較與採用決定 |
| 11-06 | [發布驗收與程式碼審查](release-foundation-20261106/README.md) | 分支整合、牛棚雙方案、使用者驗收、跨年進件與全季近況回測 |

## 功能驗收

各項功能上線時的操作與回歸測試。

| 日期 | 紀錄 | 重點 |
|---|---|---|
| 10-18 | [regression-20261018.md](regression-20261018.md) | 網站內容優化後的完整回歸測試 |
| 10-15 | [full-audit-20261015.md](full-audit-20261015.md) | 主分支網站完整驗收與改善紀錄 |
| 10-13 | [audience-history-20261013.md](audience-history-20261013.md) | 新增一般／球隊兩種使用模式與 2025/09/20 單日分析；102 項前端測試與桌機、手機實測 |
| 10-13 | [season-context.md](season-context.md) | 單日分析的賽前狀態（連續出賽、休息天數、近期負荷）驗收 |
| 10-07 | [own-lineup-test.md](own-lineup-test.md) | 我方場上名單（選隊、配置球員／守位／棒次、套用）驗收 |
| 10-07 | [lineup-swap-test.md](lineup-swap-test.md) | 場上名單的守位與棒次互換測試 |
| 10-06 | [number-search-2025.md](number-search-2025.md) | 2025 背號搜尋功能與資料來源驗證 |
| 10-06 | [number-search-full-audit.md](number-search-full-audit.md) | 背號資料對回 360 場比賽紀錄全面複查，11,296 筆一致 |

## 整合與發布驗收

分支整合與推送前的驗收。

| 日期 | 紀錄 | 重點 |
|---|---|---|
| 10-18 | [sync-20261018.md](sync-20261018.md) | 主分支整合與推送前驗收：123 項前端、60 項 Python 測試與實際操作 |
| 10-18 | [release-20261018.md](release-20261018.md) | 比賽展示與靜態發布驗收 |

## 介面

2026-10-04 起各輪前端呈現調整，僅改畫面，不改模型或分數。

| 日期 | 紀錄 | 重點 |
|---|---|---|
| 10-18 | [content-20261018.md](content-20261018.md) | 說明文字與候選比較的可讀性優化 |
| 10-18 | [light-ux-20261018.md](light-ux-20261018.md) | 預設改為淺色主題，並修正實際使用時遇到的問題 |
| 10-05 | [baseball-guidance-update.md](baseball-guidance-update.md) | 補強守位檢查、接守人選與上場資格提醒等棒球情境說明 |
| 10-05 | [readability-update-20261005.md](readability-update-20261005.md) | 文字與操作介面可讀性檢查 |
| 10-04 | [availability-baseline-update.md](availability-baseline-update.md) | 顯示今日可用名單、逐棒圖加入現任基準、四人比較卡片收合細節 |
| 10-04 | [benefit-difference-update.md](benefit-difference-update.md) | 差距圖改為以現任為 0，向右綠色較有利、向左紅色較不利 |
| 10-04 | [paired-comparison-update.md](paired-comparison-update.md) | 代打與換投候選卡共用同一張「與現任比較」圖表 |
| 10-04 | [offense-defense-alignment.md](offense-defense-alignment.md) | 代打與換投兩種評估的介面對齊 |
| 10-04 | [hitter-chart-copy-update.md](hitter-chart-copy-update.md) | 換打「優勢來源」差值圖與文字精簡 |
| 10-04 | [clarity-rules-update.md](clarity-rules-update.md) | 圖示、評估閱讀方式與棒球情境規則檢查 |
| 10-04 | [colors-availability-update.md](colors-availability-update.md) | 比較圖配色、對決字級與板凳名單檢查 |
| 10-04 | [compact-workflow-update.md](compact-workflow-update.md) | 名單摘要、手機版評估與四人比較的版面精簡 |
| 10-04 | [short-method-update.md](short-method-update.md) | 方法說明分層，預設只顯示重點、細節收合 |
| 10-04 | [user-journey-update.md](user-journey-update.md) | 從設定到比較結果實際走一遍使用流程，修正兩個問題 |
| 10-04 | [interaction-update.md](interaction-update.md) | 前端操作更新與使用流程測試 |
| 10-04 | [frontend-refinement.md](frontend-refinement.md) | 前端修改與驗證紀錄 |
| 10-04 | [typography-motion-polish.md](typography-motion-polish.md) | 字級、對齊與動態統一 |
| 10-04 | [motion-update.md](motion-update.md) | 按鍵與切換動態更新 |
| 10-04 | [rounded-surfaces-update.md](rounded-surfaces-update.md) | 卡片、按鈕與輸入框的圓角樣式統一 |
| 10-04 | [minor-polish-update.md](minor-polish-update.md) | 手機表單字級等兩處小幅一致性修正 |
