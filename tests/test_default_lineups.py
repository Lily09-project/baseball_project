import os
"""預設場上名單的棒球規則檢查（docs/data/default-lineups-<球季>.json，球季依目前執行設定）。"""
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "src"))
import server
from roster import can_play

POSITIONS = {"C", "1B", "2B", "3B", "SS", "LF", "CF", "RF", "DH"}


class DefaultLineupExportTests(unittest.TestCase):
    """不需原始資料：只用已發布的 default-lineups-*.json 與 model.json 的名單。"""

    @classmethod
    def setUpClass(cls):
        base = Path(os.environ.get("BASEBALL_STATIC_OUT", ROOT / "docs/data"))
        cls.files = sorted(base.glob("default-lineups-*.json"))
        if not cls.files:
            raise AssertionError("沒有任何已發布的預設先發名單")
        cls.model = json.loads((base / "model.json").read_text(encoding="utf-8"))

    def test_each_published_lineup_is_a_valid_dh_lineup_of_the_teams_own_players(self):
        for path in self.files:
            data = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(set(data["teams"]), set(self.model["rosters"]), path.name)
            for team, v in data["teams"].items():
                roster = self.model["rosters"][team]
                hitters = {h["name"]: h for h in roster["hitters"]}
                pitchers = {p["name"]: p for p in roster["pitchers"]}
                names = [s["name"] for s in v["slots"]]
                self.assertEqual((len(names), len(set(names))), (9, 9), f"{path.name} {team}")
                self.assertEqual({s["pos"] for s in v["slots"]}, POSITIONS, f"{path.name} {team}")
                self.assertNotIn(v["pitcher"], names, f"{team}：指定打擊制下投手不在打序中")
                self.assertEqual(pitchers[v["pitcher"]]["role"], "先發", f"{path.name} {team}")
                for s in v["slots"]:
                    self.assertIn(s["name"], hitters, f"{path.name} {team}")
                    player = hitters[s["name"]]
                    played = s["pos"] == "DH" or s["pos"] in player["positions"] or (s["pos"] == "C" and player.get("catcher"))
                    self.assertTrue(played, f"{team}：{player['display_name']} 沒有守 {s['pos']} 的紀錄")


class DefaultLineupTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from runtime_config import settings
        path = Path(os.environ.get("BASEBALL_STATIC_OUT",ROOT/"docs/data"))/f"default-lineups-{settings().season}.json"
        if not path.exists():
            raise unittest.SkipTest(f"{path.name} 未隨網站發布；名單與執行設定的球季不同")
        cls.data = json.loads(path.read_text(encoding="utf-8"))
        try:
            cls.rosters = server.rosters()
        except Exception as error:  # 沒有原始資料時無法重建名單
            raise unittest.SkipTest(f"需要原始資料才能核對守位資格：{type(error).__name__}")

    def test_every_team_has_a_default(self):
        self.assertEqual(set(self.data["teams"]), set(self.rosters))

    def test_nine_players_cover_each_position_once_with_dh(self):
        for team, v in self.data["teams"].items():
            names = [s["name"] for s in v["slots"]]
            self.assertEqual(len(names), 9, team)
            self.assertEqual(len(set(names)), 9, team)
            self.assertEqual({s["pos"] for s in v["slots"]}, POSITIONS, team)
            self.assertNotIn(v["pitcher"], names, f"{team}：指定打擊制下投手不在打序中")

    def test_players_belong_to_team_and_can_play_assigned_position(self):
        for team, v in self.data["teams"].items():
            hitters = {h["name"] for h in self.rosters[team]["hitters"]}
            for s in v["slots"]:
                self.assertIn(s["name"], hitters, team)
                self.assertTrue(can_play(s["name"], s["pos"]), f"{team}：{s['name']} 沒有守 {s['pos']} 的經驗")

    def test_pitcher_is_a_starter_on_the_roster(self):
        for team, v in self.data["teams"].items():
            pitchers = {p["name"]: p for p in self.rosters[team]["pitchers"]}
            self.assertIn(v["pitcher"], pitchers, team)
            self.assertEqual(pitchers[v["pitcher"]]["role"], "先發", team)


if __name__ == "__main__":
    unittest.main()
