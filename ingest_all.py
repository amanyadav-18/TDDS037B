import json
import os
from datetime import datetime
from app.database import SessionLocal
from app.models import Team, Player, Match, Innings, Delivery, Wicket

FOLDER_PATH = r"C:\Users\Aman\OneDrive\Desktop\API\ODI"


def get_or_create_team(db, name, team_cache):
    if name in team_cache:
        return team_cache[name]
    team = db.query(Team).filter_by(name=name).first()
    if not team:
        team = Team(name=name)
        db.add(team)
        db.flush()
    team_cache[name] = team
    return team


def get_or_create_player(db, player_id, name, player_cache):
    if player_id in player_cache:
        return player_cache[player_id]
    player = db.query(Player).filter_by(player_id=player_id).first()
    if not player:
        player = Player(player_id=player_id, name=name)
        db.add(player)
        db.flush()
    player_cache[player_id] = player
    return player


def ingest_match(file_path, db):
    with open(file_path, encoding="utf-8") as f:
        data = json.load(f)

    info = data["info"]

    if info.get("match_type") != "ODI":
        return "skipped_not_odi"

    match_id = os.path.basename(file_path).replace(".json", "")

    existing_match = db.query(Match).filter_by(match_id=match_id).first()
    if existing_match:
        return "already_exists"

    team_cache = {}
    player_cache = {}

    team_names = info["teams"]
    teams = [get_or_create_team(db, name, team_cache) for name in team_names]

    registry = info.get("registry", {}).get("people", {})
    for name, pid in registry.items():
        get_or_create_player(db, pid, name, player_cache)

    outcome = info.get("outcome", {})
    winner_name = outcome.get("winner")
    winner_team = team_cache.get(winner_name) if winner_name else None

    win_by_type = None
    win_by_margin = None
    if "by" in outcome:
        if "runs" in outcome["by"]:
            win_by_type = "runs"
            win_by_margin = outcome["by"]["runs"]
        elif "wickets" in outcome["by"]:
            win_by_type = "wickets"
            win_by_margin = outcome["by"]["wickets"]

    toss = info.get("toss", {})
    toss_winner_team = team_cache.get(toss.get("winner"))

    pom_list = info.get("player_of_match", [])
    pom_id = None
    if pom_list:
        pom_id = registry.get(pom_list[0])

    match = Match(
        match_id=match_id,
        date=datetime.strptime(info["dates"][0], "%Y-%m-%d").date(),
        venue=info.get("venue"),
        city=info.get("city"),
        season=str(info.get("season", "")),
        match_type=info.get("match_type"),
        team1_id=teams[0].team_id,
        team2_id=teams[1].team_id,
        toss_winner_id=toss_winner_team.team_id if toss_winner_team else None,
        toss_decision=toss.get("decision"),
        winner_id=winner_team.team_id if winner_team else None,
        win_by_type=win_by_type,
        win_by_margin=win_by_margin,
        player_of_match_id=pom_id,
    )
    db.add(match)
    db.flush()

    for idx, inn in enumerate(data["innings"], start=1):
        batting_team = team_cache.get(inn["team"])
        innings_row = Innings(
            match_id=match.match_id,
            innings_number=idx,
            batting_team_id=batting_team.team_id if batting_team else None,
        )
        db.add(innings_row)
        db.flush()

        for over in inn["overs"]:
            over_num = over["over"]
            for ball_idx, delivery in enumerate(over["deliveries"], start=1):
                runs = delivery.get("runs", {})
                extras = delivery.get("extras", {})
                extra_type = next(iter(extras), None) if extras else None

                batter_id = registry.get(delivery["batter"])
                bowler_id = registry.get(delivery["bowler"])
                non_striker_id = registry.get(delivery["non_striker"])

                delivery_row = Delivery(
                    innings_id=innings_row.innings_id,
                    over_number=over_num,
                    ball_in_over=ball_idx,
                    batter_id=batter_id,
                    bowler_id=bowler_id,
                    non_striker_id=non_striker_id,
                    runs_batter=runs.get("batter", 0),
                    runs_extras=runs.get("extras", 0),
                    runs_total=runs.get("total", 0),
                    extra_type=extra_type,
                )
                db.add(delivery_row)
                db.flush()

                if "wickets" in delivery:
                    for w in delivery["wickets"]:
                        player_out_id = registry.get(w.get("player_out"))
                        fielders_list = w.get("fielders", [])
                        fielders_names = ", ".join(
                            f.get("name", "") for f in fielders_list
                        )
                        wicket_row = Wicket(
                            delivery_id=delivery_row.delivery_id,
                            player_out_id=player_out_id,
                            kind=w.get("kind"),
                            fielders=fielders_names or None,
                        )
                        db.add(wicket_row)

    db.commit()
    return "success"


def main():
    files = [f for f in os.listdir(FOLDER_PATH) if f.endswith(".json")]
    print(f"Found {len(files)} JSON files.")

    success_count = 0
    skipped_count = 0
    already_exists_count = 0
    failed_files = []

    for i, filename in enumerate(files, start=1):
        file_path = os.path.join(FOLDER_PATH, filename)
        db = SessionLocal()
        try:
            result = ingest_match(file_path, db)
            if result == "success":
                success_count += 1
            elif result == "skipped_not_odi":
                skipped_count += 1
            elif result == "already_exists":
                already_exists_count += 1
        except Exception as e:
            db.rollback()
            failed_files.append((filename, str(e)))
        finally:
            db.close()

        if i % 200 == 0:
            print(f"Progress: {i}/{len(files)} processed...")

    print("\n--- INGESTION SUMMARY ---")
    print(f"Total files found: {len(files)}")
    print(f"Successfully ingested: {success_count}")
    print(f"Skipped (not ODI): {skipped_count}")
    print(f"Already existed: {already_exists_count}")
    print(f"Failed: {len(failed_files)}")

    if failed_files:
        print("\nFirst 10 failures:")
        for fname, err in failed_files[:10]:
            print(f"  {fname}: {err}")


if __name__ == "__main__":
    main()