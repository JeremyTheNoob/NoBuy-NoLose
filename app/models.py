from datetime import datetime
from sqlalchemy import create_engine, Column, String, Text, DateTime, Float
from sqlalchemy.orm import declarative_base, sessionmaker

Base = declarative_base()


class AnalysisRecord(Base):
    __tablename__ = "analysis_records"

    id = Column(String(36), primary_key=True)
    symbol = Column(String(10), index=True, nullable=False)
    stock_name = Column(String(50))
    provider = Column(String(20))
    ai_provider = Column(String(20))
    reasons_json = Column(Text, nullable=False)
    summary = Column(Text)
    elapsed_seconds = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)


def init_db(db_path: str = "data/money_tracing.db"):
    import os
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    engine = create_engine(f"sqlite:///{db_path}", echo=False)
    Base.metadata.create_all(bind=engine)
    return sessionmaker(bind=engine)


def get_session(db_path: str = "data/money_tracing.db"):
    Session = init_db(db_path)
    return Session()
