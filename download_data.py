"""下載 Rebas Open Data（2024–2026 例行賽）與 ldkrsi 守備資料到 data/，並整理 2026 守位。

用法：python download_data.py
"""
import io
import os
import re
import urllib.request
import zipfile

ROOT = os.path.dirname(os.path.abspath(__file__))
REBAS = {
    "2024": "https://github.com/rebas-tw/rebas.tw-open-data/releases/download/v0.1.0-2024/CPBL-2024-OpenData.zip",
    "2025": "https://github.com/rebas-tw/rebas.tw-open-data/releases/download/v0.1.0-2025/CPBL-2025-OpenData.zip",
    # 2024、2025 沿用 v5 訓練用的 v0.1.0；2026 為 v0.1.1（含逐打席守備陣容 fielderNames）
    "2026": "https://github.com/rebas-tw/rebas.tw-open-data/releases/download/v0.1.1-2026/CPBL-2026-OpenData.zip",
}
LDKRSI = "https://raw.githubusercontent.com/ldkrsi/cpbl-opendata/master/"


def fetch(url, timeout=120):
    print("下載", url)
    with urllib.request.urlopen(url, timeout=timeout) as r:
        return r.read()


def write_atomic(path, data):
    """先寫暫存檔再取代：下載或寫入中途失敗時，不會留下被截斷的檔案。"""
    tmp = path + ".tmp"
    with open(tmp, "wb") as f:
        f.write(data)
    os.replace(tmp, path)


def main():
    for year, url in REBAS.items():
        out = os.path.join(ROOT, "data", "rebas", year)
        os.makedirs(out, exist_ok=True)
        z = zipfile.ZipFile(io.BytesIO(fetch(url)))
        games = [(os.path.basename(name), name) for name in z.namelist()
                 if re.search(r"-G\d+\.json$", os.path.basename(name))]  # 只取逐場檔，不取合併檔
        if not games:
            # 壓縮檔改版或內容不對時直接中止，不要悄悄沿用舊資料
            raise SystemExit(f"{year}：壓縮檔內找不到逐場檔，已中止；既有資料未更動。")
        for base, name in games:
            write_atomic(os.path.join(out, base), z.read(name))
        print(f"  {year}：{len(games)} 場")

    out = os.path.join(ROOT, "data", "ldkrsi")
    os.makedirs(out, exist_ok=True)
    # 先全部下載成功，再寫檔；失敗時既有的守位檔保持原樣
    files = {f"fieldings_{y}.csv": fetch(f"{LDKRSI}CPBL/fieldings/{y}.csv") for y in (2022, 2023, 2024)}
    files["LICENSE"] = fetch(LDKRSI + "LICENSE")
    for name, data in files.items():
        target = os.path.join(out, name)
        if os.path.exists(target) and open(target, "rb").read() == data:
            continue  # 內容相同就不改寫（LICENSE 已被追蹤）
        write_atomic(target, data)
    export_fielding_2026()
    print("完成。若有權使用 2025 守位資料，可另放入 data/cpbl/positions_2025.csv，來源見「資料來源.md」。")


def export_fielding_2026():
    """由 2026 逐打席守備陣容整理守位出賽場數（網站 2026 批次的守位判斷使用）。"""
    import csv
    import sys
    from pathlib import Path
    sys.path[:0] = [os.path.join(ROOT, "scripts"), os.path.join(ROOT, "src")]
    from export_observed_fielding import collect
    rows, counts = collect(Path(ROOT, "data", "rebas", "2026"), 2026)
    out = Path(ROOT, "data", "rebas-fielding")
    out.mkdir(parents=True, exist_ok=True)
    with (out / "positions_2026.csv").open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(("season", "player_id", "team", "position", "observed_games"))
        writer.writerows((2026, *key, len(games)) for key, games in sorted(rows.items()))
    print(f"  2026 守位：{counts['games']} 場、{counts['rows']} 筆")


if __name__ == "__main__":
    main()
