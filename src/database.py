from sqlalchemy import create_engine, Column, Integer, String, Date
from sqlalchemy.orm import declarative_base, sessionmaker
import pandas as pd

Base = declarative_base()

class Holding(Base):
    __tablename__ = 'holdings'
    id = Column(Integer, primary_key=True)
    filing_date = Column(Date)
    ticker = Column(String)
    shares = Column(Integer)
    value = Column(Integer)
    issuer = Column(String)

def init_db():
    engine = create_engine('sqlite:///data/13f.db')
    Base.metadata.create_all(engine)
    return engine

def save_to_db(df):
    engine = init_db()
    df.to_sql('holdings', engine, if_exists='replace', index=False)

# Example usage:
if __name__ == "__main__":
    df = pd.read_csv("data/parsed_holdings.csv")
    save_to_db(df)