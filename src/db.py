# src/db.py
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import datetime

# Definizione del Base per i modelli
Base = declarative_base()

# Modello per i Verbali
class Verbale(Base):
    __tablename__ = 'verbali'
    id = Column(Integer, primary_key=True, autoincrement=True)
    verbale_id = Column(String(50), unique=True, nullable=False)
    codice_fiscale = Column(String(16), nullable=False)
    targa = Column(String(10), nullable=False)
    importo = Column(Float, nullable=False)
    motivo = Column(String(255), nullable=False)
    stato = Column(String(20), nullable=False)
    data_emissione = Column(DateTime, default=datetime.datetime.utcnow)

# Connection strings per ogni tenant (esempio: Italia e Germania)
TENANT_DATABASES = {
    "IT": "postgresql://tenantuser:tenantpass@localhost:5433/tax_enforce_it",
    "DE": "postgresql://tenantuser:tenantpass@localhost:5434/tax_enforce_de",
}

def get_engine(tenant: str):
    """Restituisce l'engine SQLAlchemy per il tenant specificato."""
    if tenant not in TENANT_DATABASES:
        raise ValueError("Tenant non riconosciuto")
    engine = create_engine(TENANT_DATABASES[tenant], echo=True)
    return engine

def init_db(tenant: str):
    """Inizializza il database per il tenant (crea le tabelle se non esistono)."""
    engine = get_engine(tenant)
    Base.metadata.create_all(bind=engine)

def get_session(tenant: str):
    """Restituisce una sessione DB per il tenant specificato."""
    engine = get_engine(tenant)
    SessionLocal = sessionmaker(bind=engine)
    return SessionLocal()
