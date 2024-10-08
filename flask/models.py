import logging
from typing import List

from extensions import db
from sqlalchemy import DateTime, ForeignKey, Identity, String, select
from sqlalchemy.orm import Mapped, mapped_column, relationship


class MinutemanSession(db.Model):
    __tablename__ = "minuteman_session"
    id: Mapped[str] = mapped_column(String(20), primary_key=True)
    creation_time: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    utterances: Mapped[List["TranscribedUtterance"]] = relationship(
        "TranscribedUtterance"
    )

    def __init__(self, id, creation_time):
        self.id = id
        self.creation_time = creation_time


class TranscribedUtterance(db.Model):
    id: Mapped[int] = mapped_column(
        Identity(always=True, start=1), primary_key=True, autoincrement=True
    )
    author: Mapped[str] = mapped_column(String(100), nullable=False)
    utterance: Mapped[str] = mapped_column(String(1000), nullable=False)
    time: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False)
    minuteman_session_id: Mapped[str] = mapped_column(
        ForeignKey("minuteman_session.id"), nullable=False
    )


class GeneratedSummary(db.Model):
    id: Mapped[int] = mapped_column(
        Identity(always=True, start=1), primary_key=True, autoincrement=True
    )
    minuteman_session_id: Mapped[str] = mapped_column(
        ForeignKey("minuteman_session.id"), nullable=False
    )

    time: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False)
    # the raw text generated by the model
    text: Mapped[str] = mapped_column(DateTime(timezone=True), nullable=False)
    # where does the generated summary start and end in the transcript. Not necessary
    tr_char_from: Mapped[int]
    tr_char_to: Mapped[int]
    # whether the summary was overridden by the user by editing the line. Starts as false
    # if flipped to true, can never be taken back
    overridden: Mapped[bool] = mapped_column(nullable=False)


class DBInterface:
    def __init__(self, config):
        self.config = config

    def create_minuteman_session(self, session_id, timestamp):
        logging.debug(f"Creating session {session_id}")
        session_db_obj = MinutemanSession(session_id, timestamp)
        db.session.add(session_db_obj)
        db.session.commit()

    def store_utterance(self, session_id, utterance, timestamp, author):
        logging.debug(f"Storing utterance {utterance} from session {session_id}")
        utterance_db_obj = TranscribedUtterance(
            minuteman_session_id=session_id,
            utterance=utterance,
            time=timestamp,
            author=author,
        )
        db.session.add(utterance_db_obj)
        db.session.commit()

    def get_past_utterances(self, session_id):
        logging.debug(f"Loading minutes for session {session_id} from DB")
        results = db.session.execute(
            select(TranscribedUtterance)
            .where(TranscribedUtterance.minuteman_session_id == session_id)
            .order_by(TranscribedUtterance.time)
        )
        return results.all()

    def session_exists(self, session_id):
        result = None
        sessions = []
        result = db.session.execute(
            select(MinutemanSession).where(MinutemanSession.id == session_id)
        )
        sessions = result.all()
        assert len(sessions) < 2
        return len(sessions) == 1
