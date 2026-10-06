from pydantic import BaseModel
from typing import Optional, List


class PlayerBasic(BaseModel):
    player_id: str
    name: str
    matches_played: int

    class Config:
        from_attributes = True


class MatchPerformance(BaseModel):
    match_id: str
    date: str
    venue: Optional[str]
    opponent: Optional[str]
    team: Optional[str]

    runs_scored: int
    balls_faced: int
    fours: int
    sixes: int
    strike_rate: Optional[float]
    dismissal: Optional[str]

    wickets_taken: int
    runs_conceded: int
    overs_bowled: float
    economy: Optional[float]
    wicket_kinds: List[str] = []


class CareerSummary(BaseModel):
    player_id: str
    name: str
    team: Optional[str]

    matches_played: int
    innings_batted: int
    total_runs: int
    highest_score: int
    batting_average: Optional[float]
    strike_rate: Optional[float]
    hundreds: int
    fifties: int
    not_outs: int

    innings_bowled: int
    total_wickets: int
    bowling_average: Optional[float]
    economy: Optional[float]
    best_bowling: Optional[str]