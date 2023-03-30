import logging
from typing import List

import sqlalchemy
from sqlalchemy import String, DateTime, ForeignKey, Identity, select
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, relationship

class Base(DeclarativeBase):
    pass

class MinutemanSession(Base):
    __tablename__ = "minuteman_session"
    id: Mapped[str] = mapped_column(String(20), primary_key=True)
    creation_time: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False)
    utterances: Mapped[List["TranscribedUtterance"]] = relationship("TranscribedUtterance")

    def __init__(self, id, creation_time):
        self.id = id
        self.creation_time = creation_time


class TranscribedUtterance(Base):
    __tablename__ = "transcribed_utterance"
    id: Mapped[int] = mapped_column(Identity(always=True, start=0), primary_key=True, autoincrement=True)
    author: Mapped[str] = mapped_column(String(100), nullable=False)
    utterance: Mapped[str] = mapped_column(String(1000), nullable=False)
    time: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False)
    minuteman_session_id: Mapped[str] = mapped_column(ForeignKey("minuteman_session.id"), nullable=False)


class DBInterface:
    def __init__(self, config):
        self.config = config
        self.engine = sqlalchemy.create_engine(self.config.db_url, echo=True)
    
    def create_minuteman_session(self, session_id, timestamp):
        logging.debug(f"Creating session {session_id}")
        session_db_obj = MinutemanSession(session_id, timestamp)
        with Session(self.engine) as session:
            with session.begin():
                try:
                    session.add(session_db_obj)
                except:
                    session.rollback()
                    raise
                else:
                    session.commit()

    def store_utterance(self, session_id, utterance, timestamp, author):
        logging.debug(f"Storing utterance {utterance} from session {session_id}")
        utterance_db_obj = TranscribedUtterance(
            minuteman_session_id=session_id,
            utterance=utterance,
            time=timestamp,
            author=author
        )
        with Session(self.engine) as session:
            with session.begin():
                try:
                    session.add(utterance_db_obj)
                except:
                    session.rollback()
                    raise
                else:
                    session.commit()
    
    def get_past_utterances(self, session_id):
        logging.debug(f"Loading minutes for session {session_id} from DB")
        with Session(self.engine) as session:
            results = session.execute(select(TranscribedUtterance).where(TranscribedUtterance.minuteman_session_id == session_id).order_by(TranscribedUtterance.time))
            return results.all()
    
    def session_exists(self, session_id):
        result = None
        sessions = []
        with Session(self.engine) as session:
            result = session.execute(select(MinutemanSession).where(MinutemanSession.id == session_id))
            sessions = result.all()
            assert len(sessions) < 2
        return len(sessions) == 1