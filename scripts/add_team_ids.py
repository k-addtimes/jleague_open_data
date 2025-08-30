#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import csv
import argparse
from pathlib import Path

EXPECTED_HEADER = [
    "year", "category", "term", "date", "kickoffdate",
    "homeTeam", "score", "awayTeam", "stadiumName",
    "visitors", "other", "homeTeamId", "awayTeamId"
]

def build_team_map(teams_csv_path):
    team_map = {}
    with open(teams_csv_path, newline='', encoding='utf-8') as f:
        reader = csv.reader(f)
        rows = list(reader)
        if not rows:
            return team_map

        # 1行目が "id" 等ならヘッダとみなしてスキップ
        start_idx = 0
        first0 = (rows[0][0] if rows[0] else "").strip().lower()
        if first0 in ("id", "teamid", "team_id"):
            start_idx = 1

        for r in rows[start_idx:]:
            if len(r) < 3:
                continue
            team_id = (r[0] or "").strip()
            short_name = (r[2] or "").strip()
            if short_name:
                team_map[short_name] = team_id
    return team_map

def process_schedule(schedule_csv_path, team_map, out_csv_path,
                     home_name_idx=5, away_name_idx=7):
    out_path = Path(out_csv_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    with open(schedule_csv_path, newline='', encoding='utf-8') as fin:
        reader = csv.reader(fin)
        rows = [list(r) for r in reader]

    if not rows:
        # 空ならヘッダだけ出力
        with open(out_path, 'w', newline='', encoding='utf-8') as fout:
            writer = csv.writer(fout)
            writer.writerow(EXPECTED_HEADER)
        return

    out_rows = []
    for r in rows:
        # 足りない列をパディング
        if len(r) < 11:  # 元の11列までは必須
            r = r + [""] * (11 - len(r))

        home_name = (r[home_name_idx] or "").strip()
        away_name = (r[away_name_idx] or "").strip()
        home_id = team_map.get(home_name, "")
        away_id = team_map.get(away_name, "")

        out_rows.append(r[:11] + [home_id, away_id])

    # 出力
    with open(out_path, 'w', newline='', encoding='utf-8') as fout:
        writer = csv.writer(fout)
        writer.writerow(EXPECTED_HEADER)  # 必ず先頭に固定ヘッダ
        writer.writerows(out_rows)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--schedule", required=True, help="path to current_schedule_file.csv")
    ap.add_argument("--teams", required=True, help="path to team_ids.csv")
    ap.add_argument("--out", required=True, help="output CSV path")
    ap.add_argument("--home_idx", type=int, default=5, help="home team name column index")
    ap.add_argument("--away_idx", type=int, default=7, help="away team name column index")
    args = ap.parse_args()

    team_map = build_team_map(args.teams)
    process_schedule(args.schedule, team_map, args.out, args.home_idx, args.away_idx)

if __name__ == "__main__":
    main()
