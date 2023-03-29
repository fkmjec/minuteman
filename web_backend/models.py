import logging
from typing import List

import sqlalchemy
from sqlalchemy import String, DateTime, ForeignKey
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
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    author: Mapped[str] = mapped_column(String(100), nullable=False)
    utterance: Mapped[str] = mapped_column(String(1000), nullable=False)
    time: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False)
    minuteman_session_id: Mapped[str] = mapped_column(ForeignKey("minuteman_session.id"), nullable=False)

    def __init__(self, session_id, utterance, timestamp, author):
        self.minuteman_session_id = session_id
        self.author = author
        self.utterance = utterance
        self.time = timestamp


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
        utterance_db_obj = TranscribedUtterance(session_id, utterance, timestamp, author)
        with Session(self.engine) as session:
            with session.begin():
                try:
                    session.add(utterance_db_obj)
                except:
                    session.rollback()
                    raise
                else:
                    session.commit()