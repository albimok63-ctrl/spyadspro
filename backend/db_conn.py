from sqlalchemy import create_engine, Column, Integer, String, Float
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_URL = "sqlite:///spyads.db"

engine = create_engine(DATABASE_URL, echo=False, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()

class Annuncio(Base):
    __tablename__ = "annunci"

    id = Column(Integer, primary_key=True, index=True)
    titolo = Column(String)
    testo = Column(String)
    competitor = Column(String, index=True)
    piattaforma = Column(String, index=True)
    parole_chiave = Column(String, index=True)
    inserzionista = Column(String)
    dominio = Column(String)
    tipo_annuncio = Column(String, index=True)
    geo = Column(String, index=True)
    like = Column(Integer, default=0)
    commenti = Column(Integer, default=0)
    condivisioni = Column(Integer, default=0)
    visualizzazioni = Column(Integer, default=0)
    performance = Column(Float, default=0.0)
    ctr = Column(Float, default=0.0)
    cpc = Column(Float, default=0.0)

def init_db():
    Base.metadata.create_all(bind=engine)