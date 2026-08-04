import os
from google.cloud.sql.connector import Connector, IPTypes
import pg8000
from sqlalchemy import create_engine, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker

INSTANCE_CONNECTION_NAME = os.environ.get(
    "INSTANCE_CONNECTION_NAME",
    "prestij-nurazwann-smartassist:asia-southeast1:drespon-db"
)
DB_USER = os.environ.get("DB_USER", "drespon_user")
DB_NAME = os.environ.get("DB_NAME", "drespon")

def _get_db_pass():
    # Prefer explicit env var (local dev), else fetch from Secret Manager
    if os.environ.get("DB_PASS"):
        return os.environ["DB_PASS"]
    secret_name = os.environ.get("SECRET_NAME")
    if secret_name:
        from google.cloud import secretmanager
        client = secretmanager.SecretManagerServiceClient()
        response = client.access_secret_version(name=secret_name)
        return response.payload.data.decode("utf-8").strip()
    return ""

DB_PASS = _get_db_pass()

connector = Connector()

def getconn():
    return connector.connect(
        INSTANCE_CONNECTION_NAME,
        "pg8000",
        user=DB_USER,
        password=DB_PASS,
        db=DB_NAME,
        ip_type=IPTypes.PRIVATE,
    )

engine = create_engine("postgresql+pg8000://", creator=getconn)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class Base(DeclarativeBase):
    pass

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    with engine.connect() as conn:
        conn.execute(text("""
        CREATE TABLE IF NOT EXISTS complaints (
            id TEXT PRIMARY KEY,
            no_kes TEXT,
            tarikh TEXT,
            masa TEXT,
            jenis TEXT,
            keutamaan TEXT,
            status TEXT DEFAULT 'Baharu',
            nama_pengadu TEXT,
            emel TEXT,
            telefon TEXT,
            institusi TEXT,
            daerah TEXT,
            perihal TEXT,
            catatan TEXT,
            pegawai_agih TEXT,
            tarikh_agih TEXT,
            tarikh_tutup TEXT,
            oyd_nama TEXT,
            oyd_kp TEXT,
            oyd_jawatan TEXT,
            oyd_gred TEXT,
            created_at TIMESTAMPTZ DEFAULT NOW(),
            updated_at TIMESTAMPTZ DEFAULT NOW()
        );

        CREATE TABLE IF NOT EXISTS log_kerja (
            id SERIAL PRIMARY KEY,
            kes_id TEXT,
            masa TEXT,
            tindakan TEXT,
            catatan TEXT,
            oleh TEXT,
            created_at TIMESTAMPTZ DEFAULT NOW()
        );

        CREATE TABLE IF NOT EXISTS audit_trail (
            id SERIAL PRIMARY KEY,
            masa TEXT,
            kes TEXT,
            aksi TEXT,
            keterangan TEXT,
            oleh TEXT,
            created_at TIMESTAMPTZ DEFAULT NOW()
        );

        CREATE TABLE IF NOT EXISTS semak_state (
            kes_id TEXT PRIMARY KEY,
            checked_items TEXT[],
            updated_at TIMESTAMPTZ DEFAULT NOW()
        );
        """))
        conn.commit()
