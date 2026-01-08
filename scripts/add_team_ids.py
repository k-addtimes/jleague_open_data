#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import csv
import argparse
from pathlib import Path

EXPECTED_HEADER = [
    "year", "category", "term", "date", "kickoffdate",
    "homeTeam", "score", "awayTeam", "stadiumName",
    "visitors", "other", "homeTeamId", "awayTeamId",
    "competitionName", "jLeagueCompetitionId", "competitionId"
]
# competitionName -> IDs（GAS側で表記は固定されている前提）
JLEAGUE_COMP_MAP = {
    "明治安田J1百年構想": "35",
    "明治安田J2・J3百年構想": "36",
}

COMPETITION_ID_MAP = {
    "明治安田J1百年構想 EASTグループ": "35-E",
    "明治安田J1百年構想 WESTグループ": "35-W",
    "明治安田J2・J3百年構想 EAST-Aグループ": "36-E-A",
    "明治安田J2・J3百年構想 EAST-Bグループ": "36-E-B",
    "明治安田J2・J3百年構想 WEST-Aグループ": "36-W-A",
    "明治安田J2・J3百年構想 WEST-Bグループ": "36-W-B",
}

def build_team_maps(teams_csv_path):
    team_id_map = {}
    team_cat_map = {}
    with open(teams_csv_path, newline='', encoding='utf-8') as f:
        reader = csv.reader(f)
        rows = list(reader)
        if not rows:
            return team_id_map, team_cat_map

        # 1行目が "id" 等ならヘッダとみなしてスキップ
        start_idx = 0
        first0 = (rows[0][0] if rows[0] else "").strip().lower()
        if first0 in ("id", "teamid", "team_id"):
            start_idx = 1

        for r in rows[start_idx:]:
            # 想定: [id, teamName, shortName, category]
            if len(r) < 4:
                continue
            team_id = (r[0] or "").strip()
            team_name = (r[1] or "").strip()
            short_name = (r[2] or "").strip()
            category = (r[3] or "").strip()
            for key in (team_name, short_name):
                if not key:
                    continue
                if team_id:
                    team_id_map[key] = team_id
                if category:
                    team_cat_map[key] = category
    return team_id_map, team_cat_map

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

        year, competitionName, term, date, kickoff, home, score, away, stadium, visitors, other = [
            (x or "").strip() for x in r[:11]
        ]
        home_id = team_map.get(home, "")
        away_id = team_map.get(away, "")
        category = team_cat_map.get(home, "") or team_cat_map.get(away, "") or ""

        # competition ids
        jLeagueCompetitionId = JLEAGUE_COMP_MAP.get(
            "明治安田J1百年構想" if competitionName.startswith("明治安田J1百年構想")
            else "明治安田J2・J3百年構想" if competitionName.startswith("明治安田J2・J3百年構想")
            else "",
            ""
        )
        competitionId = COMPETITION_ID_MAP.get(competitionName, "")

        out_rows.append([
            year, category, term, date, kickoff,
            home, score, away, stadium,
            visitors, other,
            home_id, away_id,
            competitionName, jLeagueCompetitionId, competitionId
        ])

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
    args = ap.parse_args()

    team_id_map, team_cat_map = build_team_maps(args.teams)
    process_schedule(args.schedule, team_id_map, team_cat_map, args.out)

if __name__ == "__main__":
    main()
