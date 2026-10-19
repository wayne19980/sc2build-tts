from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    MetaData,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from .config import SCHEMA


class Base(DeclarativeBase):
    metadata = MetaData(schema=SCHEMA)


class Folder(Base):
    __tablename__ = "folders"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    path: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class Game(Base):
    __tablename__ = "games"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    folder_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey(f"{SCHEMA}.folders.id", ondelete="CASCADE"), nullable=False
    )
    file_path: Mapped[str] = mapped_column(Text, nullable=False)
    file_name: Mapped[str] = mapped_column(Text, nullable=False)
    file_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    file_size: Mapped[int] = mapped_column(BigInteger, nullable=False)

    map_name: Mapped[str | None] = mapped_column(Text)
    duration_sec: Mapped[float | None] = mapped_column(Float)
    game_version: Mapped[str | None] = mapped_column(Text)
    region: Mapped[str | None] = mapped_column(Text)
    played_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    frames: Mapped[int | None] = mapped_column(Integer)
    frames_per_second: Mapped[float | None] = mapped_column(Float)
    speed: Mapped[str | None] = mapped_column(Text)
    game_type: Mapped[str | None] = mapped_column(Text)

    raw: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    imported_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    __table_args__ = (
        Index("ix_games_folder_id", "folder_id"),
        Index("ix_games_played_at", "played_at"),
    )


class GamePlayer(Base):
    __tablename__ = "game_players"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    game_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey(f"{SCHEMA}.games.id", ondelete="CASCADE"), nullable=False
    )
    pid: Mapped[int] = mapped_column(Integer, nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    race: Mapped[str | None] = mapped_column(String(16))
    team: Mapped[int | None] = mapped_column(Integer)
    result: Mapped[str | None] = mapped_column(String(16))
    is_winner: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_human: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    uid: Mapped[int | None] = mapped_column(BigInteger)
    color: Mapped[str | None] = mapped_column(String(16))

    __table_args__ = (
        UniqueConstraint("game_id", "pid", name="uq_game_players_game_pid"),
        Index("ix_game_players_game_id", "game_id"),
        Index("ix_game_players_name", "name"),
    )


class Event(Base):
    __tablename__ = "events"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    game_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey(f"{SCHEMA}.games.id", ondelete="CASCADE"), nullable=False
    )
    player_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey(f"{SCHEMA}.game_players.id", ondelete="CASCADE")
    )
    frame: Mapped[float] = mapped_column(Float, nullable=False)
    t_sec: Mapped[float] = mapped_column(Float, nullable=False)
    kind: Mapped[str] = mapped_column(String(32), nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    display_name: Mapped[str | None] = mapped_column(Text)
    supply: Mapped[float | None] = mapped_column(Float)
    is_worker: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)

    __table_args__ = (
        Index("ix_events_game_player_time", "game_id", "player_id", "t_sec"),
        Index("ix_events_game_kind", "game_id", "kind"),
        Index("ix_events_game_name", "game_id", "name"),
        Index("ix_events_game_time", "game_id", "t_sec"),
    )


class Unit(Base):
    __tablename__ = "units"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    game_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey(f"{SCHEMA}.games.id", ondelete="CASCADE"), nullable=False
    )
    player_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey(f"{SCHEMA}.game_players.id", ondelete="CASCADE"), nullable=False
    )
    unit_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    first_type: Mapped[str] = mapped_column(Text, nullable=False)
    unit_type: Mapped[str] = mapped_column(Text, nullable=False)
    born_t_sec: Mapped[float] = mapped_column(Float, nullable=False)
    died_t_sec: Mapped[float | None] = mapped_column(Float)
    is_worker: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_army: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_building: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    morphs: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, nullable=False, default=list)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)

    __table_args__ = (
        UniqueConstraint("game_id", "unit_id", name="uq_units_game_unit"),
        Index("ix_units_game_player_born", "game_id", "player_id", "born_t_sec"),
        Index("ix_units_game_type", "game_id", "unit_type"),
        Index("ix_units_game_died", "game_id", "died_t_sec"),
    )


class StatsTimeline(Base):
    __tablename__ = "stats_timeline"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    game_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey(f"{SCHEMA}.games.id", ondelete="CASCADE"), nullable=False
    )
    player_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey(f"{SCHEMA}.game_players.id", ondelete="CASCADE"), nullable=False
    )
    frame: Mapped[float] = mapped_column(Float, nullable=False)
    t_sec: Mapped[float] = mapped_column(Float, nullable=False)

    minerals: Mapped[int | None] = mapped_column(Integer)
    vespene: Mapped[int | None] = mapped_column(Integer)
    workers: Mapped[int | None] = mapped_column(Integer)
    supply_used: Mapped[float | None] = mapped_column(Float)
    supply_made: Mapped[float | None] = mapped_column(Float)
    army_value: Mapped[int | None] = mapped_column(Integer)
    minerals_collection_rate: Mapped[int | None] = mapped_column(Integer)
    vespene_collection_rate: Mapped[int | None] = mapped_column(Integer)
    resources_lost: Mapped[int | None] = mapped_column(Integer)
    resources_killed: Mapped[int | None] = mapped_column(Integer)

    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)

    __table_args__ = (
        UniqueConstraint("game_id", "player_id", "frame", name="uq_stats_game_player_frame"),
        Index("ix_stats_game_player_time", "game_id", "player_id", "t_sec"),
    )


class AgentAnalysis(Base):
    __tablename__ = "agent_analyses"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    folder_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey(f"{SCHEMA}.folders.id", ondelete="CASCADE")
    )
    game_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey(f"{SCHEMA}.games.id", ondelete="CASCADE")
    )
    kind: Mapped[str] = mapped_column(String(32), nullable=False)
    name: Mapped[str | None] = mapped_column(Text)
    model: Mapped[str | None] = mapped_column(Text)
    prompt_version: Mapped[str | None] = mapped_column(Text)
    content: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    __table_args__ = (
        Index("ix_agent_analyses_game_id", "game_id"),
        Index("ix_agent_analyses_folder_id", "folder_id"),
    )
