import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.models import Base

DB_DIR = os.path.join(os.path.dirname(__file__), "data")
os.makedirs(DB_DIR, exist_ok=True)
DB_PATH = os.path.join(DB_DIR, "software_dna.db")

DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(
    DATABASE_URL, 
    connect_args={"check_same_thread": False},
    echo=False
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    Base.metadata.create_all(bind=engine)
    # Perform automated column migrations for SQLite
    with engine.connect() as conn:
        try:
            # Check esdi_results columns
            res = conn.exec_driver_sql("PRAGMA table_info(esdi_results)")
            existing_cols = {row[1] for row in res}
            new_cols = {
                "metric_risk": "FLOAT DEFAULT 0.0",
                "loc_risk": "FLOAT DEFAULT 0.0",
                "cc_risk": "FLOAT DEFAULT 0.0",
                "wmc_risk": "FLOAT DEFAULT 0.0",
                "cbo_risk": "FLOAT DEFAULT 0.0",
                "lcom_risk": "FLOAT DEFAULT 0.0",
                "weighted_loc": "FLOAT DEFAULT 0.0",
                "weighted_cc": "FLOAT DEFAULT 0.0",
                "weighted_wmc": "FLOAT DEFAULT 0.0",
                "weighted_cbo": "FLOAT DEFAULT 0.0",
                "weighted_lcom": "FLOAT DEFAULT 0.0",
            }
            for col, col_type in new_cols.items():
                if col not in existing_cols:
                    conn.exec_driver_sql(f"ALTER TABLE esdi_results ADD COLUMN {col} {col_type}")
            conn.commit()
        except Exception as e:
            pass

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
