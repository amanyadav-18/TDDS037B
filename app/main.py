from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional
from collections import Counter

from app.database import get_db
from app.models import Player, Delivery, Wicket, Innings, Match, Team
from app.schemas import PlayerBasic, MatchPerformance, CareerSummary
from app.player_names import get_display_name

app = FastAPI(
    title="Cricket Analytics API",
    description="Player Performance Analysis Using Historical ODI Match Statistics",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {"message": "Cricket Analytics API is running"}


@app.get("/players", response_model=List[PlayerBasic])
def search_players(
    search: str = Query(..., min_length=2, description="Player name search (partial match)"),
    db: Session = Depends(get_db),
):
    matched_players = (
        db.query(Player)
        .filter(Player.name.ilike(f"%{search}%"))
        .limit(30)
        .all()
    )
    if not matched_players:
        raise HTTPException(status_code=404, detail="No players found matching that search.")

    player_ids = [p.player_id for p in matched_players]

    all_deliveries = (
        db.query(Delivery.batter_id, Delivery.bowler_id, Delivery.innings_id)
        .filter(
            (Delivery.batter_id.in_(player_ids)) | (Delivery.bowler_id.in_(player_ids))
        )
        .all()
    )

    player_innings_map = {pid: set() for pid in player_ids}
    for batter_id, bowler_id, innings_id in all_deliveries:
        if batter_id in player_innings_map:
            player_innings_map[batter_id].add(innings_id)
        if bowler_id in player_innings_map:
            player_innings_map[bowler_id].add(innings_id)

    all_innings_ids = set()
    for s in player_innings_map.values():
        all_innings_ids |= s

    innings_to_match = dict(
        db.query(Innings.innings_id, Innings.match_id)
        .filter(Innings.innings_id.in_(all_innings_ids))
        .all()
    ) if all_innings_ids else {}

    results = []
    for p in matched_players:
        innings_ids = player_innings_map.get(p.player_id, set())
        match_ids = {innings_to_match[i] for i in innings_ids if i in innings_to_match}
        results.append(PlayerBasic(
            player_id=p.player_id,
            name=get_display_name(p.name),
            matches_played=len(match_ids),
        ))

    results.sort(key=lambda x: x.matches_played, reverse=True)
    return results[:20]


def _compute_performances(player_id: str, db: Session):
    """Shared logic: returns list of MatchPerformance objects (unfiltered) and the player's most common team name."""
    all_deliveries = (
        db.query(Delivery)
        .filter((Delivery.batter_id == player_id) | (Delivery.bowler_id == player_id))
        .all()
    )

    innings_ids = {d.innings_id for d in all_deliveries}
    if not innings_ids:
        return [], None

    innings_rows = db.query(Innings).filter(Innings.innings_id.in_(innings_ids)).all()
    innings_by_id = {i.innings_id: i for i in innings_rows}
    match_ids = {i.match_id for i in innings_rows}

    match_rows = db.query(Match).filter(Match.match_id.in_(match_ids)).all()
    match_by_id = {m.match_id: m for m in match_rows}

    team_ids = set()
    for m in match_rows:
        team_ids.add(m.team1_id)
        team_ids.add(m.team2_id)
    team_rows = db.query(Team).filter(Team.team_id.in_(team_ids)).all()
    team_by_id = {t.team_id: t for t in team_rows}

    delivery_ids = [d.delivery_id for d in all_deliveries]
    wicket_rows = db.query(Wicket).filter(Wicket.delivery_id.in_(delivery_ids)).all()
    wickets_by_delivery_id = {}
    for w in wicket_rows:
        wickets_by_delivery_id.setdefault(w.delivery_id, []).append(w)

    deliveries_by_match = {}
    for d in all_deliveries:
        inn = innings_by_id.get(d.innings_id)
        if not inn:
            continue
        deliveries_by_match.setdefault(inn.match_id, []).append((d, inn))

    results = []
    team_name_votes = []

    for match_id, delivery_pairs in deliveries_by_match.items():
        match = match_by_id.get(match_id)
        if not match:
            continue
        team1 = team_by_id.get(match.team1_id)
        team2 = team_by_id.get(match.team2_id)

        batting_pairs = [(d, i) for d, i in delivery_pairs if d.batter_id == player_id]
        bowling_pairs = [(d, i) for d, i in delivery_pairs if d.bowler_id == player_id]

        runs_scored = sum(d.runs_batter for d, _ in batting_pairs)
        balls_faced = sum(1 for d, _ in batting_pairs if d.extra_type != "wides")
        fours = sum(1 for d, _ in batting_pairs if d.runs_batter == 4)
        sixes = sum(1 for d, _ in batting_pairs if d.runs_batter == 6)
        strike_rate = round((runs_scored / balls_faced) * 100, 2) if balls_faced > 0 else None

        dismissal = "not out"
        for d, _ in batting_pairs:
            for w in wickets_by_delivery_id.get(d.delivery_id, []):
                if w.player_out_id == player_id:
                    dismissal = w.kind
                    break

        legal_balls = sum(1 for d, _ in bowling_pairs if d.extra_type not in ("wides", "noballs"))
        runs_conceded = sum(d.runs_total for d, _ in bowling_pairs)
        overs_bowled = round(legal_balls // 6 + (legal_balls % 6) / 10, 1)

        wickets_taken = 0
        wicket_kinds_this_match = []
        for d, _ in bowling_pairs:
            for w in wickets_by_delivery_id.get(d.delivery_id, []):
                if w.kind not in ("run out", "retired hurt", "retired out"):
                    wickets_taken += 1
                    wicket_kinds_this_match.append(w.kind)

        economy = round(runs_conceded / (legal_balls / 6), 2) if legal_balls > 0 else None

        player_team_id = None
        for _, inn in batting_pairs:
            if inn.batting_team_id:
                player_team_id = inn.batting_team_id
                break
        if player_team_id is None:
            for _, inn in bowling_pairs:
                if inn.batting_team_id:
                    if team1 and inn.batting_team_id == team1.team_id:
                        player_team_id = team2.team_id if team2 else None
                    elif team2 and inn.batting_team_id == team2.team_id:
                        player_team_id = team1.team_id if team1 else None
                    break

        opponent_name = None
        team_name = None
        if player_team_id and team1 and team2:
            if player_team_id == team1.team_id:
                opponent_name = team2.name
                team_name = team1.name
            elif player_team_id == team2.team_id:
                opponent_name = team1.name
                team_name = team2.name

        if team_name:
            team_name_votes.append(team_name)

        results.append(
            MatchPerformance(
                match_id=match.match_id,
                date=str(match.date),
                venue=match.venue,
                opponent=opponent_name,
                team=team_name,
                runs_scored=runs_scored,
                balls_faced=balls_faced,
                fours=fours,
                sixes=sixes,
                strike_rate=strike_rate,
                dismissal=dismissal if batting_pairs else None,
                wickets_taken=wickets_taken,
                runs_conceded=runs_conceded,
                overs_bowled=overs_bowled,
                economy=economy,
                wicket_kinds=wicket_kinds_this_match,
            )
        )

    results.sort(key=lambda x: x.date)

    most_common_team = None
    if team_name_votes:
        most_common_team = Counter(team_name_votes).most_common(1)[0][0]

    return results, most_common_team


@app.get("/players/{player_id}/performances", response_model=List[MatchPerformance])
def player_performances(
    player_id: str,
    opponent: Optional[str] = Query(None),
    venue: Optional[str] = Query(None),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    last_n: Optional[int] = Query(None),
    db: Session = Depends(get_db),
):
    player = db.query(Player).filter(Player.player_id == player_id).first()
    if not player:
        raise HTTPException(status_code=404, detail="Player not found.")

    results, _ = _compute_performances(player_id, db)

    if opponent:
        results = [r for r in results if r.opponent and opponent.lower() in r.opponent.lower()]
    if venue:
        results = [r for r in results if r.venue and venue.lower() in r.venue.lower()]
    if date_from:
        results = [r for r in results if r.date >= date_from]
    if date_to:
        results = [r for r in results if r.date <= date_to]
    if last_n:
        results = results[-last_n:]

    return results


@app.get("/players/{player_id}/summary", response_model=CareerSummary)
def player_career_summary(player_id: str, db: Session = Depends(get_db)):
    player = db.query(Player).filter(Player.player_id == player_id).first()
    if not player:
        raise HTTPException(status_code=404, detail="Player not found.")

    _, most_common_team = _compute_performances(player_id, db)

    batting_deliveries = db.query(Delivery).filter(Delivery.batter_id == player_id).all()
    batting_innings_ids = {d.innings_id for d in batting_deliveries}

    total_runs = sum(d.runs_batter for d in batting_deliveries)
    total_balls_faced = sum(1 for d in batting_deliveries if d.extra_type != "wides")
    innings_batted = len(batting_innings_ids)

    runs_per_innings = {}
    for d in batting_deliveries:
        runs_per_innings.setdefault(d.innings_id, 0)
        runs_per_innings[d.innings_id] += d.runs_batter

    highest_score = max(runs_per_innings.values()) if runs_per_innings else 0
    hundreds = sum(1 for r in runs_per_innings.values() if r >= 100)
    fifties = sum(1 for r in runs_per_innings.values() if 50 <= r < 100)

    dismissals = (
        db.query(Wicket)
        .filter(
            Wicket.player_out_id == player_id,
            Wicket.delivery_id.in_(
                db.query(Delivery.delivery_id).filter(
                    Delivery.innings_id.in_(batting_innings_ids)
                )
            ),
        )
        .count()
    )
    not_outs = innings_batted - dismissals

    batting_average = round(total_runs / dismissals, 2) if dismissals > 0 else None
    strike_rate = round((total_runs / total_balls_faced) * 100, 2) if total_balls_faced > 0 else None

    bowling_deliveries = db.query(Delivery).filter(Delivery.bowler_id == player_id).all()
    bowling_innings_ids = {d.innings_id for d in bowling_deliveries}
    innings_bowled = len(bowling_innings_ids)

    legal_balls = sum(1 for d in bowling_deliveries if d.extra_type not in ("wides", "noballs"))
    total_runs_conceded = sum(d.runs_total for d in bowling_deliveries)

    bowling_delivery_ids = [d.delivery_id for d in bowling_deliveries]
    total_wickets = (
        db.query(Wicket)
        .filter(
            Wicket.delivery_id.in_(bowling_delivery_ids),
            Wicket.kind.notin_(["run out", "retired hurt", "retired out"]),
        )
        .count()
        if bowling_delivery_ids else 0
    )

    bowling_average = (
        round(total_runs_conceded / total_wickets, 2) if total_wickets > 0 else None
    )
    economy = round(total_runs_conceded / (legal_balls / 6), 2) if legal_balls > 0 else None

    best_bowling = None
    if bowling_innings_ids:
        best_wickets = -1
        best_runs = None
        for inn_id in bowling_innings_ids:
            inn_deliveries = [d for d in bowling_deliveries if d.innings_id == inn_id]
            inn_delivery_ids = [d.delivery_id for d in inn_deliveries]
            inn_wickets = (
                db.query(Wicket)
                .filter(
                    Wicket.delivery_id.in_(inn_delivery_ids),
                    Wicket.kind.notin_(["run out", "retired hurt", "retired out"]),
                )
                .count()
                if inn_delivery_ids else 0
            )
            inn_runs = sum(d.runs_total for d in inn_deliveries)
            if inn_wickets > best_wickets or (inn_wickets == best_wickets and (best_runs is None or inn_runs < best_runs)):
                best_wickets = inn_wickets
                best_runs = inn_runs
        if best_wickets >= 0:
            best_bowling = f"{best_wickets}/{best_runs}"

    innings_all = (
        db.query(Innings)
        .filter(Innings.innings_id.in_(batting_innings_ids | bowling_innings_ids))
        .all()
    )
    matches_played = len({inn.match_id for inn in innings_all})

    return CareerSummary(
        player_id=player.player_id,
        name=get_display_name(player.name),
        team=most_common_team,
        matches_played=matches_played,
        innings_batted=innings_batted,
        total_runs=total_runs,
        highest_score=highest_score,
        batting_average=batting_average,
        strike_rate=strike_rate,
        hundreds=hundreds,
        fifties=fifties,
        not_outs=not_outs,
        innings_bowled=innings_bowled,
        total_wickets=total_wickets,
        bowling_average=bowling_average,
        economy=economy,
        best_bowling=best_bowling,
    )