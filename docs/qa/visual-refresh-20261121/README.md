# 11/21 網站視覺精修與專案整理

**範圍**：只改外觀與載入流程，不改模型、權重、正式數值或網站資料（`docs/data/` 未變動）。

## 網站外觀（`docs/style.css` 末端「11/21 視覺精修」一層）

- **頁首**：改成深藍漸層底與白字，底部加紅土色線，和比分板同一套配色；標誌改白底深藍線，深色主題維持原本的面板色。
- **主要入口**：一般使用者／球隊／單日分析改成白底膠囊分段，選中時帶各入口的識別色淡底與底線。
- **按鈕**：功能切換、評估、套用配置與記錄換人改用藍色漸層與柔和陰影；示範按鈕圓角一致。
- **卡片**：圓角 16px、暖灰邊線、分層陰影；卡片標題前加紅土色短線；空狀態卡改虛線框。
- **表單與表格**：輸入框圓角 10px、聚焦時有柔和外框；表頭淡底、列邊線改暖灰，滑過時淡藍底。
- 深色主題另外定義同名變數：不加陰影與光暈，頁首用面板色。
- `index.html` 的 `style.css`、`app.js` 版本參數改為 `visual-refresh-20261121`，讓瀏覽器重新抓取。

## 載入流程

- 網站在 `*.github.io` 上直接進入靜態模式，不再先請求 `api/meta`。原本每次開啟線上站都會多一次 404 往返並在主控台留下錯誤（已以 `curl` 確認線上 `api/meta` 回 404）。本機 `server.py` 與其他主機仍照舊先探測 API。

## 前端細修（行為不變）

- **初次載入**：背號、官方球員名單、預設先發三份小檔改成同時抓（`Promise.allSettled`），少兩次往返；任一份失敗仍各自略過，批次不一致照舊中止。
- **無障礙**：
  - 局數、壘上跑者、板凳野手、本場角色、對手接下來 3 棒、牛棚投手六組控制項加上 `role="group"`，並用原本的標題命名。
  - 局數數字加 `aria-live`，按 ± 時讀出新值。
  - 評估方向、上下半局、單日分析內容、場上名單操作四組分段按鈕加 `role="group"`。
  - 接下來三棒的下拉選單改用畫面上的「第 1 棒」標籤，不再另外覆蓋名稱。
  - 「清除選取」的名稱改為包含畫面文字。
  - 表單內按鈕補上 `type="button"`。
- **價值分數圖例**：色塊原本寫死色碼，和分數徽章不同色（「佳」用的是深色主題的色）。現在改用和徽章同一組顏色，含深色主題，淡色色塊加外框。
- **死碼**：自訂情境的「預設」按鈕綁定一定會被單日分析的版本覆蓋，移除這三行和沒有其他呼叫的 `clearSituation`。
- 換行格式：`index.html`、`check_repository.py` 維持原本的 CRLF，`style.css` 新增段落也統一為 CRLF。

## 程式整理

- `scripts/` 移出 15 支一次性腳本：v4 收尾（`train_closeout`、`evaluate_closeout`、`recalibrate_revision`、`prepare_closeout_stage`、`audit_closeout_data`、`verify_recalibration_impact`）與 10/25 身分整合比對（`build_identity_stage`、`export_identity_auxiliary`、`report_identity_*` 三支、`upgrade_replay_actor_context`、`verify_identity_export_lineage`、`diagnose_identity_decision_shift`、`audit_formal_identity`）。
- 移出前以 `git grep` 確認：除了彼此互相引用，沒有任何文件、測試或 CI 用到它們；v4 腳本在現行 `TRAINING_VERSION = 5` 下會直接報錯，其餘寫死的 `output/` 資料夾已不存在。
- 檔案保存在本機「多餘資料」，不再追蹤；`.gitattributes` 同步移除對應行，`.gitignore` 改為只追蹤 `多餘資料/README.md`。

## 驗證

- **瀏覽器（本機靜態站）**：桌機 1280 px 與手機 375 px 各走一遍；前端細修後再走一次代打評估、換投評估（全選牛棚後評估）、場上名單預設與單日分析預設按鈕。
  - 評估：看示範情境 → 評估結果、比分板、與現任比較、代打評估表。
  - 我方場上名單：守備配置與打擊順序。
  - 單日分析：當日總覽 → 查看當日打席 → 逐打席回放。
  - 深色與淺色主題切換。
  - 主控台只有本機預期的 `api/meta` 404（本機靜態伺服器沒有 API）。
- **離線 CI**：`data/rebas` 暫時改名後執行 `scripts/run_ci.py --require-no-raw`，17 個子檢查全部結束碼 0；跑完已改回原名，追蹤中的測試 fixture 沒有被改寫。

## 未處理（留待後續）

- `style.css` 約 45 個 class 在 HTML／JS／測試中都找不到；系統深色的 `@media` 區塊因主題一定寫入 `data-theme` 而不會單獨生效。兩者都不影響畫面，刪除需要逐段比對壓縮過的規則，留待專門的 CSS 清理。
- 隱藏的連投天數選單（`#myStreak`、牛棚每人的 `select.streak`）目前恆為 0，可能保留給日後功能，先不動。

- `src/pitch_change.py` 的 `add_pa` 只有測試在用，正式的 `observations()` 另有一套計數規則。要統一會改變換投資料的計數結果或測試範圍，不屬於行為不變的整理。
- 4 支 2026 研究稽核腳本（`audit_2026_replay_roster`、`audit_cross_game_bullpen_2026`、`audit_replay_model`、`evaluate_2026_holdout`）目前沒有文件引用，但時間較新，可能仍在使用，先保留。
- 檔案雜湊、JSON 指紋等小函式在多支腳本中重複，合併只省幾行，且部分腳本會刻意載入別的版本，暫不合併。
- 模型：`output/candidate-2026` 的候選模型和正式 `models/2026` 雜湊相同（`d8f160b4…`），已經採用。近期加權、季中迭代與新的不確定性區間，先前的實驗都沒有改善，因此這一輪不重新訓練。
