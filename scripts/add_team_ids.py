#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import csv
import argparse
from pathlib import Path

def build_team_map(teams_csv_path):
    """
    team_ids.csv 仕様:
      - id:        index 0
      - shortName: index 2
    """
    team_map = {}
    with open(teams_csv_path, newline='', encoding='utf-8') as f:
        reader = csv.reader(f)
        rows = list(reader)
        if not rows:
            return team_map

        # ヘッダらしき行をスキップ（先頭セルがID系ならヘッダとみなす）
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

def ensure_header(row_count, col_count, known_header=None):
    """
    入力にヘッダが無い場合にダミーのヘッダ名を生成
    known_header を渡せばそれを優先。
    """
    if known_header:
        return known_header
    # ダミー: col0, col1, ...
    return [f"col{i}" for i in range(col_count)]

def process_schedule(schedule_csv_path, team_map, out_csv_path,
                     home_name_idx=5, away_name_idx=7,
                     header_names=None):
    """
    current_schedule_file.csv 仕様（依頼）:
      - ホームチーム名: index 5
      - アウェイチーム名: index 7
    出力:
      - 先頭行に必ずヘッダを出力（入力に無ければ生成）
      - 末尾に homeTeamId / awayTeamId を追加
    """
    out_path = Path(out_csv_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    with open(schedule_csv_path, newline='', encoding='utf-8') as fin:
        reader = csv.reader(fin)
        rows = [list(r) for r in reader]

    if not rows:
        # 空ならヘッダだけでも書き出す
        hdr = ensure_header(0, max(home_name_idx, away_name_idx) + 1, header_names)
        with open(out_path, 'w', newline='', encoding='utf-8') as fout:
            writer = csv.writer(fout)
            writer.writerow(hdr + ["homeTeamId", "awayTeamId"])
        return

    # 1行目がヘッダっぽいか簡易判定（すべてが数値っぽくなければヘッダと推定）
    first = rows[0]
    def _is_numberish(s): 
        s = (s or "").strip().replace(".", "", 1).replace("-", "", 1)
        return s.isdigit()
    is_header_like = any(c and not _is_numberish(c) for c in first)

    if is_header_like:
        header = first
        data_rows = rows[1:]
    else:
        header = ensure_header(len(rows), max(len(r) for r in rows), header_names)
        data_rows = rows

    # 列が足りない行をパディング
    need_len = max(max(len(r) for r in data_rows) if data_rows else 0,
                   home_name_idx + 1, away_name_idx + 1)
    header = (header + [""] * (need_len - len(header))) if len(header) < need_len else header
    padded = []
    for r in data_rows:
        if len(r) < need_len:
            r = r + [""] * (need_len - len(r))
        padded.append(r)

    # ここまでで「ヘッダ付与」を完了（要求どおり先に実行）
    # 次に teamId 付与
    out_header = header + ["homeTeamId", "awayTeamId"]
    out_rows = []

    for r in padded:
        home_name = (r[home_name_idx] or "").strip()
        away_name = (r[away_name_idx] or "").strip()
        home_id = team_map.get(home_name, "")
        away_id = team_map.get(away_name, "")
        out_rows.append(r + [home_id, away_id])

    with open(out_path, 'w', newline='', encoding='utf-8') as fout:
        writer = csv.writer(fout)
        writer.writerow(out_header)
        writer.writerows(out_rows)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--schedule", required=True, help="path to current_schedule_file.csv")
    ap.add_argument("--teams", required=True, help="path to team_ids.csv")
    ap.add_argument("--out", required=True, help="output CSV path")
    ap.add_argument("--home_idx", type=int, default=5, help="home team name column index")
    ap.add_argument("--away_idx", type=int, default=7, help="away team name column index")
    # 既知のヘッダ名を（カンマ区切りで）指定可能: 例 "year,category,term,kickoffDate,home,..."
    ap.add_argument("--header", type=str, default="", help="explicit header names (comma separated)")

    args = ap.parse_args()
    team_map = build_team_map(args.teams)

    header_names = [h.strip() for h in args.header.split(",")] if args.header else None
    process_schedule(args.schedule, team_map, args.out,
                     args.home_idx, args.away_idx, header_names)

if __name__ == "__main__":
    main()
