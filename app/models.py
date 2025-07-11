from sqlalchemy import Column, Integer, String
from database import Base

class HistoricalFigure(Base):
    __tablename__ = "historical_figures"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    description = Column(String)
    picture_url = Column(String)