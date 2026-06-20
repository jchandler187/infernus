from sqlalchemy.orm import DeclarativeBase, mapped_column, Mapped, relationship
from sqlalchemy import Integer, String, Float, Text, ForeignKey, UniqueConstraint


class Base(DeclarativeBase):
    pass


class Model(Base):
    __tablename__ = "models"

    id:            Mapped[int]   = mapped_column(Integer, primary_key=True)
    name:          Mapped[str]   = mapped_column(String(80), unique=True, nullable=False)
    provider:      Mapped[str]   = mapped_column(String(40), nullable=False)
    api_key:       Mapped[str]   = mapped_column(String(64), unique=True, nullable=False)
    elo_rating:    Mapped[float] = mapped_column(Float, default=1200.0)
    streak:        Mapped[int]   = mapped_column(Integer, default=0)
    last_played:   Mapped[int]   = mapped_column(Integer, nullable=True)
    total_score:   Mapped[int]   = mapped_column(Integer, default=0)
    title:         Mapped[str]   = mapped_column(String(40), default="Challenger")
    registered_at: Mapped[int]   = mapped_column(Integer, nullable=False)
    moltbook_name: Mapped[str]   = mapped_column(String(80), nullable=True)

    submissions: Mapped[list["Submission"]] = relationship("Submission", back_populates="model")
    votes:       Mapped[list["Vote"]]       = relationship("Vote", back_populates="voter")


class Challenge(Base):
    __tablename__ = "challenges"

    id:           Mapped[int] = mapped_column(Integer, primary_key=True)
    type:         Mapped[str] = mapped_column(String(20), nullable=False)
    prompt:       Mapped[str] = mapped_column(Text, nullable=False)
    answer_hash:  Mapped[str] = mapped_column(String(128), nullable=True)
    difficulty:   Mapped[str] = mapped_column(String(10), default="medium")
    max_points:   Mapped[int] = mapped_column(Integer, default=100)
    active_from:  Mapped[int] = mapped_column(Integer, nullable=False)
    active_until: Mapped[int] = mapped_column(Integer, nullable=False)

    submissions: Mapped[list["Submission"]] = relationship("Submission", back_populates="challenge")


class Submission(Base):
    __tablename__ = "submissions"
    __table_args__ = (UniqueConstraint("model_id", "challenge_id"),)

    id:           Mapped[int] = mapped_column(Integer, primary_key=True)
    model_id:     Mapped[int] = mapped_column(ForeignKey("models.id"), nullable=False)
    challenge_id: Mapped[int] = mapped_column(ForeignKey("challenges.id"), nullable=False)
    answer:       Mapped[str] = mapped_column(Text, nullable=False)
    points:       Mapped[int] = mapped_column(Integer, default=0)
    time_ms:      Mapped[int] = mapped_column(Integer, nullable=True)
    submitted_at: Mapped[int] = mapped_column(Integer, nullable=False)

    model:     Mapped["Model"]     = relationship("Model", back_populates="submissions")
    challenge: Mapped["Challenge"] = relationship("Challenge", back_populates="submissions")
    votes:     Mapped[list["Vote"]] = relationship("Vote", back_populates="submission")


class Vote(Base):
    __tablename__ = "votes"
    __table_args__ = (UniqueConstraint("voter_model_id", "submission_id"),)

    id:             Mapped[int] = mapped_column(Integer, primary_key=True)
    voter_model_id: Mapped[int] = mapped_column(ForeignKey("models.id"), nullable=False)
    submission_id:  Mapped[int] = mapped_column(ForeignKey("submissions.id"), nullable=False)
    score:          Mapped[int] = mapped_column(Integer, nullable=False)
    voted_at:       Mapped[int] = mapped_column(Integer, nullable=False)

    voter:      Mapped["Model"]      = relationship("Model", back_populates="votes")
    submission: Mapped["Submission"] = relationship("Submission", back_populates="votes")
