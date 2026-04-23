import enum
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, BigInteger, String, DateTime, ForeignKey, Enum
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from config import DATABASE_URL

Base = declarative_base()
engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(bind=engine)


class TournamentStatus(str, enum.Enum):
    PENDING = "pending"
    REGISTRATION = "registration"
    ACTIVE = "active"
    FINISHED = "finished"


class Tournament(Base):
    __tablename__ = "tournaments"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    status = Column(Enum(TournamentStatus), default=TournamentStatus.PENDING)
    created_at = Column(DateTime, default=datetime.utcnow)
    groups_count = Column(Integer, default=1)
    max_participants = Column(Integer, default=32)
    chat_id = Column(BigInteger, nullable=True)  # группа где идет сбор и жеребьевка

    participants = relationship("Participant", back_populates="tournament", cascade="all, delete-orphan")
    groups = relationship("Group", back_populates="tournament", cascade="all, delete-orphan")
    matches = relationship("Match", back_populates="tournament", cascade="all, delete-orphan")


class Participant(Base):
    __tablename__ = "participants"
    id = Column(Integer, primary_key=True)
    tournament_id = Column(Integer, ForeignKey("tournaments.id"))
    user_id = Column(BigInteger, nullable=False)
    username = Column(String)
    game_nickname = Column(String, nullable=False)
    group_id = Column(Integer, ForeignKey("groups.id"), nullable=True)

    tournament = relationship("Tournament", back_populates="participants")
    group = relationship("Group", back_populates="participants")


class Group(Base):
    __tablename__ = "groups"
    id = Column(Integer, primary_key=True)
    tournament_id = Column(Integer, ForeignKey("tournaments.id"))
    name = Column(String, nullable=False)

    tournament = relationship("Tournament", back_populates="groups")
    participants = relationship("Participant", back_populates="group")


class Match(Base):
    __tablename__ = "matches"
    id = Column(Integer, primary_key=True)
    tournament_id = Column(Integer, ForeignKey("tournaments.id"))
    group_id = Column(Integer, ForeignKey("groups.id"), nullable=True)
    player1_id = Column(Integer, ForeignKey("participants.id"), nullable=True)
    player2_id = Column(Integer, ForeignKey("participants.id"), nullable=True)
    player1_score = Column(Integer, nullable=True)
    player2_score = Column(Integer, nullable=True)
    match_number = Column(Integer, default=1)
    status = Column(String, default="pending")
    winner_id = Column(Integer, ForeignKey("participants.id"), nullable=True)

    tournament = relationship("Tournament", back_populates="matches")
    player1 = relationship("Participant", foreign_keys=[player1_id])
    player2 = relationship("Participant", foreign_keys=[player2_id])


class Chat(Base):
    __tablename__ = "chats"
    id = Column(Integer, primary_key=True)
    chat_id = Column(BigInteger, nullable=False, unique=True)
    title = Column(String, nullable=False)
    is_active = Column(Integer, default=1)  # 1 = bot is in chat, 0 = kicked


def init_db():
    Base.metadata.create_all(engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
