from sqlalchemy import (
    Column, Integer, String, Date, ForeignKey, Text
)
from sqlalchemy.orm import relationship
from app.database import Base


class Team(Base):
    __tablename__ = "teams"

    team_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, unique=True, nullable=False)


class Player(Base):
    __tablename__ = "players"

    # Cricsheet's own stable hash ID (e.g. "39f01cdb") used as our primary key
    player_id = Column(String, primary_key=True)
    name = Column(String, nullable=False)


class Match(Base):
    __tablename__ = "matches"

    match_id = Column(String, primary_key=True)  # JSON filename, e.g. "1000887"
    date = Column(Date, nullable=False)
    venue = Column(String)
    city = Column(String)
    season = Column(String)
    match_type = Column(String)  # will always be "ODI" for us

    team1_id = Column(Integer, ForeignKey("teams.team_id"))
    team2_id = Column(Integer, ForeignKey("teams.team_id"))

    toss_winner_id = Column(Integer, ForeignKey("teams.team_id"))
    toss_decision = Column(String)

    winner_id = Column(Integer, ForeignKey("teams.team_id"), nullable=True)
    win_by_type = Column(String, nullable=True)   # "runs" or "wickets"
    win_by_margin = Column(Integer, nullable=True)

    player_of_match_id = Column(String, ForeignKey("players.player_id"), nullable=True)

    innings = relationship("Innings", back_populates="match")


class Innings(Base):
    __tablename__ = "innings"

    innings_id = Column(Integer, primary_key=True, autoincrement=True)
    match_id = Column(String, ForeignKey("matches.match_id"), nullable=False)
    innings_number = Column(Integer, nullable=False)  # 1 or 2
    batting_team_id = Column(Integer, ForeignKey("teams.team_id"))

    match = relationship("Match", back_populates="innings")
    deliveries = relationship("Delivery", back_populates="innings")


class Delivery(Base):
    __tablename__ = "deliveries"

    delivery_id = Column(Integer, primary_key=True, autoincrement=True)
    innings_id = Column(Integer, ForeignKey("innings.innings_id"), nullable=False)

    over_number = Column(Integer, nullable=False)
    ball_in_over = Column(Integer, nullable=False)

    batter_id = Column(String, ForeignKey("players.player_id"))
    bowler_id = Column(String, ForeignKey("players.player_id"))
    non_striker_id = Column(String, ForeignKey("players.player_id"))

    runs_batter = Column(Integer, default=0)
    runs_extras = Column(Integer, default=0)
    runs_total = Column(Integer, default=0)

    extra_type = Column(String, nullable=True)  # "wide", "noball", "bye", "legbye", or None

    innings = relationship("Innings", back_populates="deliveries")
    wickets = relationship("Wicket", back_populates="delivery")


class Wicket(Base):
    __tablename__ = "wickets"

    wicket_id = Column(Integer, primary_key=True, autoincrement=True)
    delivery_id = Column(Integer, ForeignKey("deliveries.delivery_id"), nullable=False)

    player_out_id = Column(String, ForeignKey("players.player_id"))
    kind = Column(String, nullable=False)
    fielders = Column(Text, nullable=True)  # comma-separated names, simplified

    delivery = relationship("Delivery", back_populates="wickets")